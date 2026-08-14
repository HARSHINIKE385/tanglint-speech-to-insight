# TANGLINT — AI Speech-to-Insight Platform

An end-to-end AI-powered speech intelligence platform that transforms unstructured audio conversations into structured, actionable insights.

TANGLINT integrates speech recognition, speaker diarization, emotion recognition, translation, summarization, and task extraction into a unified processing pipeline exposed through REST APIs and a web-based interface.

---

## Overview

Long-form conversations contain valuable information, but manually reviewing and extracting important points from audio recordings is time-consuming.

TANGLINT addresses this problem by processing conversational audio and converting it into structured information such as:

- Timestamped speech transcripts
- Speaker-attributed segments
- Emotion information
- Translated text
- Concise summaries
- Actionable tasks

The project was developed with a focus on integrating multiple AI components into a single end-to-end application rather than treating each model as an isolated experiment.

---

## System Architecture

```text
                         Audio Input
                              |
                              v
                    Audio Preprocessing
                              |
                              v
                  Speech-to-Text (Whisper)
                              |
                              v
                    Speaker Diarization
                         (Pyannote)
                              |
                              v
                    Emotion Recognition
                       (SpeechBrain)
                              |
                              v
                         Translation
                              |
                              v
                       Summarization
                              |
                              v
                       Task Extraction
                              |
                              v
                  Structured JSON Output
                              |
                              v
                    FastAPI REST Layer
                              |
                              v
                       Web Interface

The pipeline is designed as a sequence of processing stages where the output of one stage becomes structured input for subsequent stages.


---

**Key Capabilities**

1. Speech Transcription

Uses OpenAI Whisper to convert recorded speech into timestamped text and identify the detected language.

2. Speaker Diarization

Uses Pyannote-based diarization to identify and distinguish speakers within multi-speaker conversations.

3. Emotion Recognition

Uses SpeechBrain-based emotion recognition to associate emotional information with transcript segments.

4. Translation

Provides translation of recognized speech into a target language, supporting multilingual conversation analysis.

5. Summarization

Generates concise summaries from longer conversations to reduce the effort required to review complete recordings.

6. Task Extraction

Identifies actionable items from conversations and represents them as structured tasks.

7. REST API

The core processing pipeline is exposed through FastAPI, allowing the speech intelligence functionality to be accessed programmatically.

8. Web Interface

A browser-based interface provides audio upload and visualization of the generated transcript, translation, summary, and task information.


---

**Technology Stack**

**Category	  --      Technologies**

Programming Language -	Python
Backend Framework - FastAPI
Speech Recognition - OpenAI Whisper
Speaker Diarization	- Pyannote
Emotion Recognition	- SpeechBrain
Audio Processing - FFmpeg, Pydub
NLP Processing -	Translation, Summarization, Task Extraction
Frontend -	HTML, CSS, JavaScript
API Architecture - 	REST
Storage / Integration -	Firebase
Development Tools -	VS Code, Jupyter Notebook, Google Colab



---

**End-to-End Processing Workflow**

1. Audio Upload
      |
2. File Validation
      |
3. Audio Preprocessing
      |
4. Language Detection
      |
5. Speech Transcription
      |
6. Speaker Diarization
      |
7. Emotion Recognition
      |
8. Translation
      |
9. Summarization
      |
10. Task Extraction
      |
11. Structured JSON Generation
      |
12. API Response / Web Visualization


---

**Evaluation**

The speech transcription component was evaluated against human reference transcripts across multiple scenarios.

Test	Scenario	Reported Accuracy

A	English speech	92.5%
B	Hindi/Kannada to English	91.7%
C	Multi-speaker meeting	90.5%
D	Noisy environment	86.0%
E	Emotion-rich speech	92.2%
Average	Overall	~90.6%


The results demonstrate strong transcription performance across English, multilingual, multi-speaker, and emotion-rich scenarios. Performance decreased in noisy environments, highlighting the importance of audio quality and preprocessing.


---
**
**Engineering Challenges

Audio Standardization

Audio recordings may differ in format, sampling rate, and encoding. The preprocessing stage converts uploaded recordings into a standardized format before speech recognition.

Multi-Speaker Conversations

Speaker attribution becomes challenging when multiple people speak simultaneously or when speech overlaps.

The system combines transcription timestamps with speaker diarization to associate transcript segments with individual speakers.

Multi-Model Integration

The project integrates several AI components within a single workflow:

Whisper
   |
   +----> Pyannote
   |
   +----> SpeechBrain
   |
   +----> Translation
   |
   +----> Summarization
   |
   +----> Task Extraction
   |
   v
Structured Output

This required coordinating different model inputs and outputs and converting their results into a consistent application-level representation.

Noisy Audio

Evaluation showed that noisy recordings produced lower transcription performance than cleaner recordings. This identified audio quality and preprocessing as important areas for further improvement.


---

API

The backend is implemented using FastAPI.

Health Check

GET /health

Process Audio

POST /transcribe

The transcription endpoint accepts an audio file and returns structured processing results.

Example response structure:

{
  "language": "English",
  "segments": [
    {
      "start": 0.0,
      "end": 4.2,
      "speaker": "SPEAKER_00",
      "emotion": "neutral",
      "text": "Welcome to today's meeting."
    }
  ],
  "translation": "...",
  "summary": "...",
  "tasks": []
}


---

**Project Structure**

tanglint-speech-to-insight/
|
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
|
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
|
├── docs/
│   └── architecture.md
|
└── screenshots/
    ├── 01-dashboard.png
    ├── 02-transcription.png
    ├── 03-insights.png
    └── 04-api.png


---

**Running the Project**

1. Clone the repository

git clone https://github.com/HARSHINIE385/tanglint-speech-to-insight.git
cd tanglint-speech-to-insight

2. Create a virtual environment

python -m venv venv

Activate the environment according to your operating system.

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Create a .env file based on .env.example.

Required credentials depend on the enabled AI components and services.

5. Start the FastAPI application

uvicorn app:app --reload

6. Open the application

http://127.0.0.1:8000

FastAPI API documentation is available at:

http://127.0.0.1:8000/docs


---

## 📸 Screenshots

### 🎙️ Short Audio Transcription

The system supports short audio transcription using OpenAI Whisper with automatic language detection and timestamped output.

<img width="1003" height="208" alt="Image" src="https://github.com/user-attachments/assets/eba488aa-88dc-43bc-a16b-a326c32802cb" />


### 🎧 Long Audio Processing

Long audio files are divided into smaller chunks, processed independently, and then merged using adjusted timestamps to reconstruct the complete conversation.

![Long Audio Processing](https://github.com/user-attachments/assets/c80e1b3a-b753-46f3-9a8b-1a655849241a)

### 🔥 Firebase Authentication

Firebase Authentication is integrated for user authentication and account management.

<img width="800" alt="firebase" src="https://github.com/user-attachments/assets/c15f1ca0-df83-45ce-b33c-4fa1e6051d3c" />


### 🖥️ AI Speech-to-Insight Web Interface

The web interface displays timestamped speaker-wise transcription, translation, emotion information, summary, and automatically generated tasks.

<img width="800" alt="web interface" src="https://github.com/user-attachments/assets/c7636403-43b3-4c69-949d-632a6242e8c2" />


### 📝 Conversation Export

The processed conversation can be downloaded as a text file for further reference.

<img width="800" alt="conversation export" src="https://github.com/user-attachments/assets/91d45383-722f-49ce-a3fa-dcbb4ac06b4e" />

### ✅ Automatic To-Do List

The system extracts actionable tasks from the conversation and displays them with priority, responsible person, and deadline information.

<img width="800" alt="todo list" src="https://github.com/user-attachments/assets/5f272801-f9ae-4398-b9d3-3076639d61ef" />





---

**Engineering Takeaways
**
This project provided practical experience in:

Designing end-to-end AI processing pipelines

Integrating multiple AI models into a single application

Building REST APIs using FastAPI

Processing unstructured audio data

Working with timestamps and structured outputs

Integrating speech and NLP components

Evaluating AI system performance

Building a user-facing interface around AI functionality

Identifying system limitations through testing




---

**Future Improvements**

Potential future improvements include:

More robust overlapping-speech handling

Improved noisy-audio preprocessing

Expanded multilingual emotion recognition

Larger-scale evaluation datasets

More advanced conversation analytics

Production-oriented deployment and monitoring

Improved scalability for longer recordings



---

Author

Harshini K.E

Integrated M.Tech. Software Engineering
Vellore Institute of Technology

Vellore, Tamil Nadu, India



---

Project Summary

TANGLINT demonstrates an end-to-end approach to building an AI application by combining audio preprocessing, speech recognition, speaker diarization, emotion recognition, NLP processing, backend APIs, structured outputs, and evaluation into a single system.

