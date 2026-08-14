
import os
import uuid
import tempfile
import subprocess
import re

from typing import List, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


# ============================================================
# Optional AI / ML Libraries
# ============================================================

try:
    import whisper
except Exception as e:
    raise RuntimeError(
        "Install openai-whisper: pip install -U openai-whisper"
    ) from e

try:
    from pydub import AudioSegment
except Exception as e:
    raise RuntimeError(
        "Install pydub: pip install pydub"
    ) from e


# Speaker diarization
try:
    from pyannote.audio import Pipeline as PyannotePipeline
    PYANNOTE_AVAILABLE = True
except Exception:
    PYANNOTE_AVAILABLE = False


# Emotion recognition
try:
    from speechbrain.pretrained import EncoderClassifier
    SPEECHBRAIN_AVAILABLE = True
except Exception:
    SPEECHBRAIN_AVAILABLE = False


# OpenAI summarization
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
USE_OPENAI = bool(OPENAI_API_KEY)

if USE_OPENAI:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
    except Exception:
        USE_OPENAI = False


# ============================================================
# Configuration
# ============================================================

MAX_FILE_SIZE = 200 * 1024 * 1024
CHUNK_LENGTH_MS = 60 * 1000

WHISPER_MODEL = os.environ.get(
    "WHISPER_MODEL",
    "tiny"
)


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="TANGLINT Transcription API",
    description="AI-powered Speech-to-Insight backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Load Whisper Model
# ============================================================

print(f"Loading Whisper model ({WHISPER_MODEL})...")

model = whisper.load_model(WHISPER_MODEL)

print("Whisper Model Loaded")


# ============================================================
# Load Pyannote Speaker Diarization
# ============================================================

pyannote_pipeline = None

if PYANNOTE_AVAILABLE and os.environ.get("PYANNOTE_AUTH_TOKEN"):

    try:
        pyannote_pipeline = PyannotePipeline.from_pretrained(
            "pyannote/speaker-diarization",
            use_auth_token=os.environ.get("PYANNOTE_AUTH_TOKEN")
        )

        print("Pyannote diarization pipeline loaded")

    except Exception as e:
        print("Failed to load Pyannote:", e)

else:

    if PYANNOTE_AVAILABLE:
        print(
            "Pyannote available but "
            "PYANNOTE_AUTH_TOKEN not set - diarization disabled."
        )
    else:
        print("Pyannote not installed - diarization disabled.")


# ============================================================
# Load SpeechBrain Emotion Recognition
# ============================================================

emotion_clf = None

if SPEECHBRAIN_AVAILABLE:

    try:

        emotion_clf = EncoderClassifier.from_hparams(
            source="speechbrain/emotion-recognition-wav2vec2",
            savedir="pretrained_models/emotion"
        )

        print("SpeechBrain emotion model loaded")

    except Exception as e:

        print(
            "Failed to load SpeechBrain emotion model:",
            e
        )

        emotion_clf = None


# ============================================================
# Audio Preprocessing
# ============================================================

def ffmpeg_to_wav(
    in_path: str,
    out_path: str,
    rate: int = 16000
):

    try:

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                in_path,
                "-ar",
                str(rate),
                "-ac",
                "1",
                out_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:

        raise RuntimeError(
            "FFmpeg failed. "
            "Install FFmpeg and ensure it is available in PATH."
        ) from e


# ============================================================
# Simple Summary Fallback
# ============================================================

def generate_simple_summary(
    text: str,
    max_sentences: int = 3
) -> str:

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    return " ".join(
        sentences[:max_sentences]
    ).strip()


# ============================================================
# Task Extraction
# ============================================================

def extract_tasks_from_text(
    text: str
) -> List[Dict[str, Any]]:

    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        text.strip()
    )

    priority_map = {

        "emergency": [
            "urgent",
            "asap",
            "immediately",
            "emergency",
            "critical"
        ],

        "medium": [
            "tomorrow",
            "this week",
            "by",
            "due",
            "soon"
        ],

        "low": []
    }

    items = []

    for sentence in sentences:

        clean = sentence.strip()

        if len(clean) < 6:
            continue

        lowered = clean.lower()

        priority = "Low"

        if any(
            keyword in lowered
            for keyword in priority_map["emergency"]
        ):
            priority = "Emergency"

        elif any(
            keyword in lowered
            for keyword in priority_map["medium"]
        ):
            priority = "Medium"

        items.append({
            "task": clean,
            "priority": priority
        })


    # Remove duplicates
    unique = []
    seen = set()

    for item in items:

        if item["task"] not in seen:

            unique.append(item)
            seen.add(item["task"])


    return unique[:30]


# ============================================================
# TRANSCRIPTION API
# ============================================================

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...)
):

    data = await file.read()

    # File size validation
    if len(data) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 200 MB."
        )


    # Temporary input file
    tmp_in = os.path.join(
        tempfile.gettempdir(),
        f"{uuid.uuid4().hex}_{file.filename}"
    )

    with open(tmp_in, "wb") as f:
        f.write(data)


    tmp_wav = tmp_in + "_16k.wav"


    try:

        # ----------------------------------------------------
        # Audio preprocessing
        # ----------------------------------------------------

        ffmpeg_to_wav(
            tmp_in,
            tmp_wav,
            rate=16000
        )

        audio = AudioSegment.from_file(
            tmp_wav
        )


        segments_output = []

        detected_language = "unknown"

        full_transcript_text = ""


        # ----------------------------------------------------
        # Whisper transcription
        # ----------------------------------------------------

        for i in range(
            0,
            len(audio),
            CHUNK_LENGTH_MS
        ):

            chunk = audio[
                i:i + CHUNK_LENGTH_MS
            ]

            chunk_file = os.path.join(
                tempfile.gettempdir(),
                f"{uuid.uuid4().hex}_chunk.wav"
            )

            chunk.export(
                chunk_file,
                format="wav"
            )


            result = model.transcribe(
                chunk_file,
                task="transcribe"
            )


            detected_language = result.get(
                "language",
                detected_language
            )


            for seg in result["segments"]:

                segments_output.append({

                    "start":
                        seg["start"]
                        + (i / 1000.0),

                    "end":
                        seg["end"]
                        + (i / 1000.0),

                    "text":
                        seg["text"].strip()
                })


                full_transcript_text += (
                    seg["text"].strip()
                    + " "
                )


            try:
                os.remove(chunk_file)
            except Exception:
                pass


        # ----------------------------------------------------
        # Translation
        # ----------------------------------------------------

        translation_text = None

        try:

            translate_tmp = (
                tmp_in + "_translate.wav"
            )

            ffmpeg_to_wav(
                tmp_in,
                translate_tmp,
                rate=16000
            )


            translate_res = model.transcribe(
                translate_tmp,
                task="translate"
            )


            translation_text = (
                translate_res.get("text")
            )


            try:
                os.remove(translate_tmp)
            except Exception:
                pass

        except Exception:

            translation_text = None


        # ----------------------------------------------------
        # Speaker Diarization
        # ----------------------------------------------------

        diarization_result = []

        if pyannote_pipeline:

            try:

                diar = pyannote_pipeline(
                    tmp_wav
                )


                for (
                    turn,
                    track,
                    speaker
                ) in diar.itertracks(
                    yield_label=True
                ):

                    diarization_result.append({

                        "start":
                            float(turn.start),

                        "end":
                            float(turn.end),

                        "speaker":
                            speaker
                    })

            except Exception as e:

                print(
                    "Pyannote diarization error:",
                    e
                )

                diarization_result = []


        # ----------------------------------------------------
        # Emotion Recognition
        # ----------------------------------------------------

        emotion_result = []

        if emotion_clf:

            try:

                for seg in segments_output:

                    start_ms = int(
                        seg["start"] * 1000
                    )

                    end_ms = int(
                        seg["end"] * 1000
                    )


                    clip = audio[
                        start_ms:end_ms
                    ]


                    clip_path = os.path.join(
                        tempfile.gettempdir(),
                        f"{uuid.uuid4().hex}_emotion.wav"
                    )


                    clip.export(
                        clip_path,
                        format="wav"
                    )


                    output = (
                        emotion_clf
                        .classify_file(clip_path)
                    )


                    if (
                        isinstance(output, dict)
                        and "labels" in output
                    ):

                        label = output[
                            "labels"
                        ][0]

                    else:

                        label = str(output)


                    emotion_result.append({

                        "start":
                            seg["start"],

                        "end":
                            seg["end"],

                        "emotion":
                            label
                    })


                    try:
                        os.remove(clip_path)
                    except Exception:
                        pass


            except Exception as e:

                print(
                    "Emotion detection error:",
                    e
                )

                emotion_result = []


        # ----------------------------------------------------
        # Build Conversation Text
        # ----------------------------------------------------

        conversation_text = ""


        if diarization_result:

            for turn in diarization_result:

                start = turn["start"]
                end = turn["end"]
                speaker = turn["speaker"]

                pieces = []


                for seg in segments_output:

                    if (
                        seg["end"] <= start
                        or seg["start"] >= end
                    ):
                        continue

                    pieces.append(
                        seg["text"]
                    )


                if pieces:

                    conversation_text += (
                        f"\n[{speaker}] "
                        + " ".join(pieces)
                    )


        else:

            conversation_text = (
                full_transcript_text.strip()
            )


        # ----------------------------------------------------
        # Summarization
        # ----------------------------------------------------

        summary_text = None


        if (
            USE_OPENAI
            and conversation_text.strip()
        ):

            try:

                prompt = (
                    "Summarize the following "
                    "conversation into 3 concise "
                    "bullet points:\n\n"
                    + conversation_text
                )


                response = (
                    openai.ChatCompletion.create(

                        model="gpt-4o-mini",

                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],

                        max_tokens=300,

                        temperature=0.2
                    )
                )


                summary_text = (
                    response[
                        "choices"
                    ][0][
                        "message"
                    ][
                        "content"
                    ].strip()
                )


            except Exception as e:

                print(
                    "OpenAI summary error:",
                    e
                )

                summary_text = (
                    generate_simple_summary(
                        conversation_text
                    )
                )


        else:

            summary_text = (
                generate_simple_summary(
                    conversation_text
                )
            )


        # ----------------------------------------------------
        # Task Extraction
        # ----------------------------------------------------

        tasks = extract_tasks_from_text(
            summary_text
            if summary_text
            else conversation_text
        )


        # ----------------------------------------------------
        # Return Results
        # ----------------------------------------------------

        return {

            "language":
                detected_language,

            "segments":
                segments_output,

            "translation":
                translation_text,

            "diarization":
                diarization_result,

            "emotions":
                emotion_result,

            "summary":
                summary_text,

            "tasks":
                tasks,

            "conversation_text":
                conversation_text
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Transcription pipeline failed: {e}"
            )
        )


    finally:

        # Clean temporary files

        try:
            os.remove(tmp_in)
        except Exception:
            pass

        try:
            os.remove(tmp_wav)
        except Exception:
            pass


# ============================================================
# DOWNLOAD CONVERSATION
# ============================================================

@app.post("/download")
async def download_conversation(
    payload: Dict
):

    conversation_text = payload.get(
        "conversation_text",
        ""
    )


    if not conversation_text:

        raise HTTPException(
            status_code=400,
            detail="conversation_text required"
        )


    title = payload.get(
        "title",
        f"conversation_{uuid.uuid4().hex}.txt"
    )


    output_path = os.path.join(
        tempfile.gettempdir(),
        title
    )


    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(conversation_text)


    return FileResponse(
        output_path,
        filename=title,
        media_type="text/plain"
  )
