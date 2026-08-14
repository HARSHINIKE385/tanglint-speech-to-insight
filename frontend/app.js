const API_BASE_URL = "http://127.0.0.1:8000";

const uploadArea = document.getElementById("uploadArea");
const audioFile = document.getElementById("audioFile");
const selectedFile = document.getElementById("selectedFile");

const processButton = document.getElementById("processButton");
const downloadButton = document.getElementById("downloadButton");

const statusElement = document.getElementById("status");

const languageElement = document.getElementById("language");
const transcriptElement = document.getElementById("transcript");
const translationElement = document.getElementById("translation");
const summaryElement = document.getElementById("summary");
const tasksElement = document.getElementById("tasks");

let selectedAudioFile = null;
let latestConversation = "";


// ============================================================
// File Selection
// ============================================================

uploadArea.addEventListener("click", () => {
    audioFile.click();
});


audioFile.addEventListener("change", (event) => {

    const file = event.target.files[0];

    if (file) {
        selectFile(file);
    }
});


// ============================================================
// Drag and Drop
// ============================================================

uploadArea.addEventListener("dragover", (event) => {

    event.preventDefault();

    uploadArea.classList.add("dragover");
});


uploadArea.addEventListener("dragleave", () => {

    uploadArea.classList.remove("dragover");
});


uploadArea.addEventListener("drop", (event) => {

    event.preventDefault();

    uploadArea.classList.remove("dragover");

    const file = event.dataTransfer.files[0];

    if (file) {
        selectFile(file);
    }
});


// ============================================================
// Select File
// ============================================================

function selectFile(file) {

    if (!file.type.startsWith("audio/")) {

        statusElement.textContent = "Invalid file";

        selectedFile.textContent =
            "Please select a valid audio file.";

        processButton.disabled = true;

        return;
    }


    selectedAudioFile = file;

    selectedFile.textContent =
        `${file.name} (${formatFileSize(file.size)})`;

    statusElement.textContent = "Ready";

    processButton.disabled = false;
}


function formatFileSize(bytes) {

    if (bytes < 1024) {
        return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}


// ============================================================
// Process Audio
// ============================================================

processButton.addEventListener("click", async () => {

    if (!selectedAudioFile) {
        return;
    }


    setProcessingState(true);


    const formData = new FormData();

    formData.append(
        "file",
        selectedAudioFile
    );


    try {

        const response = await fetch(
            `${API_BASE_URL}/transcribe`,
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Audio processing failed."
            );
        }


        displayResults(data);

        statusElement.textContent =
            "Completed";


    } catch (error) {

        console.error(error);

        statusElement.textContent =
            "Error";

        transcriptElement.textContent =
            error.message ||
            "Unable to connect to the backend.";

    } finally {

        setProcessingState(false);
    }
});


// ============================================================
// Display Results
// ============================================================

function displayResults(data) {

    // Language

    languageElement.textContent =
        data.language || "Unknown";


    // Transcript

    const segments =
        data.segments || [];


    if (segments.length === 0) {

        transcriptElement.textContent =
            "No transcript segments returned.";

    } else {

        transcriptElement.textContent =
            segments
                .map(segment => {

                    const start =
                        formatTime(segment.start);

                    const end =
                        formatTime(segment.end);

                    const speaker =
                        segment.speaker
                        ? `[${segment.speaker}] `
                        : "";

                    return (
                        `${start} - ${end}  ` +
                        `${speaker}` +
                        `${segment.text}`
                    );

                })
                .join("\n");
    }


    // Translation

    translationElement.textContent =
        data.translation ||
        "Translation not available.";


    // Summary

    summaryElement.textContent =
        data.summary ||
        "Summary not available.";


    // Tasks

    renderTasks(
        data.tasks || []
    );


    // Conversation

    latestConversation =
        data.conversation_text ||
        buildConversationFromSegments(
            segments
        );


    downloadButton.disabled =
        !latestConversation;
}


// ============================================================
// Format Time
// ============================================================

function formatTime(seconds) {

    const totalSeconds =
        Math.max(
            0,
            Math.floor(Number(seconds) || 0)
        );


    const minutes =
        Math.floor(
            totalSeconds / 60
        );


    const remainingSeconds =
        totalSeconds % 60;


    return (
        `${String(minutes).padStart(2, "0")}:` +
        `${String(remainingSeconds).padStart(2, "0")}`
    );
}


// ============================================================
// Build Conversation
// ============================================================

function buildConversationFromSegments(
    segments
) {

    return segments
        .map(segment => {

            const speaker =
                segment.speaker
                ? `[${segment.speaker}] `
                : "";

            return (
                `${speaker}${segment.text}`
            );

        })
        .join("\n");
}


// ============================================================
// Render Tasks
// ============================================================

function renderTasks(tasks) {

    tasksElement.innerHTML = "";


    if (!tasks.length) {

        tasksElement.textContent =
            "No actionable tasks detected.";

        return;
    }


    tasks.forEach(task => {

        const taskElement =
            document.createElement("div");

        taskElement.className =
            "task";


        const title =
            document.createElement("div");

        title.className =
            "task-title";

        title.textContent =
            task.task || task.text || "";


        const priority =
            document.createElement("div");

        priority.className =
            "task-priority";

        priority.textContent =
            task.priority
            ? `Priority: ${task.priority}`
            : "Action item";


        taskElement.appendChild(title);

        taskElement.appendChild(priority);

        tasksElement.appendChild(taskElement);
    });
}


// ============================================================
// Processing State
// ============================================================

function setProcessingState(
    processing
) {

    processButton.disabled =
        processing ||
        !selectedAudioFile;


    if (processing) {

        processButton.textContent =
            "Processing...";

        statusElement.textContent =
            "Processing";

        transcriptElement.textContent =
            "AI pipeline is processing the audio...";

        translationElement.textContent =
            "Processing...";

        summaryElement.textContent =
            "Processing...";

        tasksElement.textContent =
            "Processing...";

    } else {

        processButton.textContent =
            "Process Audio";
    }
}


// ============================================================
// Download Conversation
// ============================================================

downloadButton.addEventListener(
    "click",
    async () => {

        if (!latestConversation) {
            return;
        }


        try {

            const response = await fetch(
                `${API_BASE_URL}/download`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        conversation_text:
                            latestConversation,

                        title:
                            "tanglint_conversation.txt"
                    })
                }
            );


            if (!response.ok) {

                const error =
                    await response.json();

                throw new Error(
                    error.detail ||
                    "Download failed."
                );
            }


            const blob =
                await response.blob();


            const url =
                window.URL.createObjectURL(
                    blob
                );


            const link =
                document.createElement("a");


            link.href = url;

            link.download =
                "tanglint_conversation.txt";


            document.body.appendChild(link);

            link.click();

            link.remove();

            window.URL.revokeObjectURL(url);


        } catch (error) {

            console.error(error);

            statusElement.textContent =
                "Download failed";
        }
    }
);
