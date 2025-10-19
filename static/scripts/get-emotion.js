
// --- Your existing function to update the page ---
// (This is no longer called in a loop, only after we click the button)
async function fetchEmotion() {
    try {
        const response = await fetch("http://localhost:5000/emotion"); // Flask endpoint
        const data = await response.json();
        const emotionText = data.emotion || "None";

        // Update the text
        document.getElementById("emotion-text").innerText = emotionText.toUpperCase();

        // Update emotion-box color
        const box = document.getElementById("emotion-box");
        switch (emotionText.toLowerCase()) {
            case "happy": box.style.backgroundColor = "#89cff0"; break;
            case "sad": box.style.backgroundColor = "#6457a6"; break;
            case "angry": box.style.backgroundColor = "#ef959d"; break;
            case "surprise": box.style.backgroundColor = "#d8d78f"; break;
            case "neutral": box.style.backgroundColor = "#4a7c59"; break;
            default: box.style.backgroundColor = "#d8d78f";
        }
    } catch (err) {
        console.error("Error fetching emotion:", err);
    }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


// Get the button and video elements
const captureButton = document.getElementById("capture");
const video = document.getElementById('webcam');

// --- This function runs when the button is clicked ---
async function captureAndAnalyze() {
    // 1. Create a hidden canvas to grab a frame
    
    while (true) {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // 2. Convert the frame to a Base64 string
        const dataURL = canvas.toDataURL('image/jpeg'); // Smaller format

        try {
            // 3. SEND the image to our new /analyze endpoint
            await fetch("http://localhost:5000/analyze", {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: dataURL })
            });
            
            // 4. Now that the server has analyzed it, GET the result
            await fetchEmotion(); // Call your existing function

        } catch (err) {
            console.error("Error analyzing image:", err);
        }

        await delay(500);
    }
}

// --- Add the click listener to the button ---
captureButton.addEventListener("click", captureAndAnalyze);
document.addEventListener("DOMContentLoaded", captureAndAnalyze);


