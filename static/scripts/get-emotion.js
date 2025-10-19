// --- Global State Variables ---
let isAnalyzing = false;
let analysisTimeout = null;
const ANALYSIS_INTERVAL_MS = 1000; // 1 frames per second

// --- Get Elements ---
const captureButton = document.getElementById("capture");
const insightButton = document.getElementById("get-insight-btn");
const contextInput = document.getElementById("context-input");
const video = document.getElementById('webcam');

// --- Function to Fetch the Latest Insight ---
async function fetchInsight() {
    try {
        const response = await fetch("http://localhost:5000/insight"); // GET request
        const data = await response.json();
        document.getElementById("hermes-output").innerText = data.insight;
    } catch (err) {
        console.error("Error fetching insight:", err);
    }
}


// --- Function to Fetch the Latest Emotion ---
async function fetchEmotion() {
    try {
        const response = await fetch("http://localhost:5000/emotion");
        const data = await response.json();
        const emotionText = data.emotion || "None";

        // Update the text
        document.getElementById("emotion-text").innerText = emotionText.toUpperCase();

        // Update emotion-box color
        const box = document.getElementById("emotion-box");
        switch (emotionText.toLowerCase()) {
            case "happy": box.style.backgroundColor = "var(--emotion-color-happy)"; break;
            case "sad": box.style.backgroundColor = "var(--emotion-color-sad)"; break;
            case "angry": box.style.backgroundColor = "var(--emotion-color-angry)"; break;
            case "surprise": box.style.backgroundColor = "var(--emotion-color-surprised)"; break;
            case "neutral": box.style.backgroundColor = "var(--emotion-color-neutral)"; break;
            default: box.style.backgroundColor = "var(--emotion-color-surprised)";
        }
    } catch (err) {
        console.error("Error fetching emotion:", err);
    }
}

// --- Main Analysis Loop ---
async function runAnalysisLoop() {
    // If 'isAnalyzing' is false, stop the loop
    if (!isAnalyzing) {
        return; 
    }

    // 1. Create a canvas to grab a frame
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // 2. Convert to Base64
    const dataURL = canvas.toDataURL('image/jpeg');

    try {
        // 3. SEND the image to the /analyze endpoint
        await fetch("http://localhost:5000/analyze", {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: dataURL })
        });
        
        // 4. GET the result
        await fetchEmotion();

    } catch (err) {
        console.error("Error analyzing image:", err);
    }

    // 5. Schedule the next loop
    analysisTimeout = setTimeout(runAnalysisLoop, ANALYSIS_INTERVAL_MS);
}

// --- Toggle Function for Analysis Button ---
function toggleAnalysis() {
    if (isAnalyzing) {
        // --- STOPPING ANALYSIS ---
        isAnalyzing = false;
        if (analysisTimeout) {
            clearTimeout(analysisTimeout);
            analysisTimeout = null;
        }
        captureButton.innerText = "Start Analysis";
        captureButton.style.backgroundColor = "var(--color-2)"; // Reset color
    } else {
        // --- STARTING ANALYSIS ---
        isAnalyzing = true;
        captureButton.innerText = "Stop Analysis";
        captureButton.style.backgroundColor = "var(--color-3)"; // Use 'angry' color for "stop"
        runAnalysisLoop(); // Start the loop
    }
}

// --- Function to Generate Insight ---
async function generateInsight() {
    const userContext = contextInput.value;
    if (!userContext) {
        alert("Please provide some context for the conversation.");
        return;
    }

    const outputElement = document.getElementById("hermes-output");
    outputElement.innerText = "Generating insight... please wait.";

    try {
        // 1. POST the context to the new endpoint
        await fetch("http://localhost:5000/generate_insight", {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ context: userContext })
        });

        // 2. GET the new insight
        await fetchInsight();

    } catch (err) {
        console.error("Error generating insight:", err);
        outputElement.innerText = "An error occurred. Please check the console.";
    }
}




// --- Add Event Listeners ---
captureButton.addEventListener("click", toggleAnalysis);
insightButton.addEventListener("click", generateInsight);