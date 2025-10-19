    // --- Global State Variables ---
    let isAnalyzing = false;
    let analysisTimeout = null;
    const ANALYSIS_INTERVAL_MS = 1000; // 1 frames per second

    function wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // --- Get Elements ---
    const captureButton = document.getElementById("capture");
    const insightButton = document.getElementById("get-insight-btn");
    const contextInput = document.getElementById("context-input");
    const video = document.getElementById('webcam');

    // --- Function to Fetch the Latest Insight ---
    async function fetchInsight() {
        try {
            const response = await fetch("http://localhost:5000/insight");
            const data = await response.json();

            const container = document.getElementById("insight-container");
            const intro = document.getElementById("insight-intro");
            const points = data.points || [];

            // Clear old content
            container.innerHTML = "";

            if (points.length === 0) {
                intro.textContent = "No insight data available yet. Try providing context and analyzing emotions.";
                return;
            }

            // Optional: Display the intro paragraph separately
            const firstLine = data.insight.split("\n")[0];
            intro.textContent = firstLine;

            // Create expandable boxes
            points.forEach((text, i) => {
                const box = document.createElement("div");
                box.classList.add("insight-box");

                // 🧠 Try multiple ways to separate title and body
                let title = text.trim();
                let body = "";

                // Case 1: Split by newline if Hermes formatted it as lines
                if (text.includes("\n")) {
                    const parts = text.split("\n").map(s => s.trim()).filter(Boolean);
                    title = parts[0];
                    body = parts.slice(1).join(" ");
                }

                // Case 2: Split by colon
                else if (text.includes(":")) {
                    const parts = text.split(":");
                    title = parts[0].trim();
                    body = parts.slice(1).join(":").trim();
                }

                // Case 3: Split by first period (fallback)
                else {
                    const firstPeriod = text.indexOf(".");
                    if (firstPeriod !== -1) {
                        title = text.slice(0, firstPeriod + 1).trim();
                        body = text.slice(firstPeriod + 1).trim();
                    }
                }

                // Create the DOM structure
                const header = document.createElement("button");
                header.classList.add("insight-header");
                header.textContent = `${i + 1}. ${title}`;

                const bodyDiv = document.createElement("div");
                bodyDiv.classList.add("insight-body");
                bodyDiv.textContent = body || "(No additional details provided.)";

                header.addEventListener("click", () => box.classList.toggle("active"));

                box.appendChild(header);
                box.appendChild(bodyDiv);
                container.appendChild(box);
            });
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
            const videoFrame = document.getElementsByClassName("video-frame")[0];

            switch (emotionText.toLowerCase()) {
                case "happy":
                    box.style.backgroundColor = "var(--emotion-color-happy)";
                    videoFrame.style.border = "8px solid var(--emotion-color-happy)";
                    box.textContent = "😊";
                    break;
                case "sad":
                    box.style.backgroundColor = "var(--emotion-color-sad)"; 
                    videoFrame.style.border = "8px solid var(--emotion-color-sad)";
                    box.textContent = "😢";
                    break;
                case "angry": 
                    box.style.backgroundColor = "var(--emotion-color-angry)"; 
                    videoFrame.style.border = "8px solid var(--emotion-color-angry)";
                    box.textContent = "😠";
                    break;
                case "surprise": 
                    box.style.backgroundColor = "var(--emotion-color-surprised)"; 
                    videoFrame.style.border = "8px solid var(--emotion-color-surprised)";
                    box.textContent = "😲";
                    break;
                case "neutral": 
                    box.style.backgroundColor = "var(--emotion-color-neutral)";
                    videoFrame.style.border = "8px solid var(--emotion-color-neutral)";
                    box.textContent = "😐";
                    break;
                case "fear":
                    box.style.backgroundColor = "var(--emotion-color-fear)";
                    videoFrame.style.border = "8px solid var(--emotion-color-fear)";
                    box.textContent = "😨";
                    break;
                case "disgust":
                    box.style.backgroundColor = "var(--emotion-color-disgust)";
                    videoFrame.style.border = "8px solid var(--emotion-color-disgust)";
                    box.textContent = "🤢";
                    break;
                default: 
                    box.style.backgroundColor = "var(--emotion-color-surprised)";
                    videoFrame.style.border = "8px solid var(--emotion-color-surprised)";
                    box.textContent = "❓";
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

            outputElement.innerText = "Insight generated successfully!";
            await wait(3000);
            outputElement.innerText = "Please provide some context for the conversation.";
        } catch (err) {
            console.error("Error generating insight:", err);
            outputElement.innerText = "An error occurred. Please check the console.";
        }
    }




    // --- Add Event Listeners ---
    captureButton.addEventListener("click", toggleAnalysis);
    insightButton.addEventListener("click", generateInsight);