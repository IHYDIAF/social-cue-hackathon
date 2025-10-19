// This function will be called when the page loads
async function setupCamera() {
    // 1. Get the video element from the HTML
    const video = document.getElementById('webcam');

    try {
        // 2. Ask the user for permission to use the camera
        // We are requesting video only, not audio
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: true,
            audio: false 
        });

        // 3. If permission is granted, set the video element's source
        // to be the camera stream
        video.srcObject = stream;

    } catch (err) {
        // 4. Handle errors (e.g., user denied permission)
        console.error("Error accessing the camera: ", err);
        alert("Could not access the camera. Please ensure you have granted permission.");
    }
}

// Run the setup function
setupCamera();