import os, sys, cv2, base64, io
from deepface import DeepFace
from flask import Flask, jsonify, request, render_template
from PIL import Image
import numpy as np

# --- Flask App Setup ---
app = Flask(__name__)
latest_emotion = {"emotion": "None"}  # shared global variable

# --- Endpoint to SEND the HTML webpage to the browser ---
@app.route("/")
def home():
    """Serve the main webpage"""
    return render_template("index.html")

# --- Endpoint to RECEIVE an image for analysis ---
@app.route("/analyze", methods=["POST"])
def analyze_frame():
    global latest_emotion
    try:
        # Get the Base64 image string from the webpage
        data = request.get_json()
        base64_string = data.get("image").split(',')[1]
        
        # Decode it into an image
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # --- Run DeepFace on the single frame ---
        results = DeepFace.analyze(
            img_path=frame,
            actions=["emotion"],
            detector_backend="opencv",
            enforce_detection=False,
            align=True
        )
        
        # DeepFace returns a list, get the first result
        if isinstance(results, list) and len(results) > 0:
            top_emo = results[0].get("dominant_emotion", "None")
            latest_emotion["emotion"] = top_emo
        else:
            latest_emotion["emotion"] = "None"
            
        return jsonify({"status": "success", "emotion": latest_emotion["emotion"]})

    except Exception as e:
        print(f"Error during analysis: {e}")
        latest_emotion["emotion"] = "Error"
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Endpoint to SEND the latest emotion to the webpage ---
@app.route("/emotion")
def get_emotion():
    """Return the current detected emotion as JSON"""
    return jsonify(latest_emotion)



# --- Run Backend ---
if __name__ == "__main__":
    # Just run the Flask server. No thread needed.
    app.run(host="0.0.0.0", port=5000)