import os, sys, cv2, base64, io
from deepface import DeepFace
from flask import Flask, jsonify, request, render_template
from PIL import Image
import numpy as np
from flask_cors import CORS # Make sure this is installed: pip install flask-cors

# --- Kronos Labs Setup ---
from kronoslabs import KronosLabs, APIError, AuthenticationError
# Initialize the client with your API key
API_KEY = "kl_8ddca67334b8b0fbe19699d6548a32988804c97c9e7161038dadfb2bfb72c7cc"
kronos_client = KronosLabs(api_key=API_KEY)


# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing

# --- New Global State ---
# We now track the last 2 emotions and the latest insight
global_state = {
    "emotions": ["None", "None"],
    "insight": "No insight generated yet."
}


# --- Endpoint to SEND the HTML webpage to the browser ---
# This part is for a different setup. For your file:/// setup, this route isn't used,
# but it's good practice to have.Z --- Endpoint to SEND the HTML webpage to the browser ---
# @app.route("/")
# def home():
#     """Serve the main webpage"""
    # This assumes your index.html is in a folder named 'templates'
    # return render_template("index.html")
    # For now, just confirm the server is running.
    # return "Flask server is running."
    # --- Endpoint to SEND the HTML webpage to the browser ---
@app.route("/")
def home():
    """Serve the main webpage"""
    # This assumes your index.html is in a folder named 'templates'
    return render_template("index.html")
    # For now, just confirm the server is running.
    # return "Flask server is running."


# --- Endpoint to RECEIVE an image for analysis ---
@app.route("/analyze", methods=["POST"])
def analyze_frame():
    global global_state
    try:
        # Get and decode the image
        data = request.get_json()
        base64_string = data.get("image").split(',')[1]
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Run DeepFace
        results = DeepFace.analyze(
            img_path=frame,
            actions=["emotion"],
            detector_backend="opencv",
            enforce_detection=False,
            align=True
        )
        
        top_emo = "None"
        if isinstance(results, list) and len(results) > 0:
            top_emo = results[0].get("dominant_emotion", "None")

        # --- Update the emotion list ---
        global_state["emotions"].append(top_emo)
        if len(global_state["emotions"]) > 2:
            global_state["emotions"].pop(0) # Keep only the last 2

        return jsonify({"status": "success", "emotion": top_emo})

    except Exception as e:
        print(f"Error during analysis: {e}")
        global_state["emotions"].append("Error")
        if len(global_state["emotions"]) > 2:
            global_state["emotions"].pop(0)
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Endpoint to SEND the latest emotion to the webpage ---
@app.route("/emotion")
def get_emotion():
    global global_state
    # Return the most recent emotion
    return jsonify({"emotion": global_state["emotions"][-1]})


# --- NEW Endpoint to GENERATE an insight ---
@app.route("/generate_insight", methods=["POST"])
def generate_insight():
    global global_state
    try:
        # Get the user's context from the request
        data = request.get_json()
        user_context = data.get("context")
        
        if not user_context:
            return jsonify({"status": "error", "message": "No context provided"}), 400

        # Get the last two emotions
        emo1, emo2 = global_state["emotions"]
        
        # Formulate the prompt for Hermes
        prompt_text = (
            f"Given this social context: '{user_context}'. "
            f"The person I am interacting with first showed the emotion '{emo1}', and then showed '{emo2}'. "
            f"What are some possible social cues or reasons that could have caused this change from {emo1} to {emo2}?"
        )

        # Call the Kronos Labs API
        response = kronos_client.chat.completions.create(
            prompt=prompt_text,
            model="hermes",
            is_stream=False
        )
        
        # Store the new insight
        global_state["insight"] = response.choices[0].message.content
        return jsonify({"status": "success", "insight": global_state["insight"]})

    except AuthenticationError as e:
        print(f"Kronos Labs Authentication failed: {e}")
        global_state["insight"] = "Authentication failed. Check API key."
        return jsonify({"status": "error", "message": "Authentication failed"}), 500
    except APIError as e:
        print(f"Kronos Labs API error: {e.message}")
        global_state["insight"] = "API error. Please try again."
        return jsonify({"status": "error", "message": f"API error: {e.message}"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        global_state["insight"] = "A server error occurred."
        return jsonify({"status": "error", "message": str(e)}), 500


# --- NEW Endpoint to GET the latest insight ---
@app.route("/insight")
def get_insight():
    global global_state
    insight_text = global_state["insight"]

    import re
    split_insights = re.split(r'\n\s*\d+\.\s*', insight_text.strip())

    formatted = [s.strip() for s in split_insights if s.strip()]

    return jsonify({
        "insight": global_state["insight"],
        "points": formatted
    })


# --- Run Backend ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)