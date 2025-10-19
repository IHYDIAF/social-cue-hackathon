import os, sys, time, threading
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import cv2
from deepface import DeepFace
from flask import Flask, jsonify

# === Flask App Setup ===
app = Flask(__name__)
latest_emotion = {"emotion": "None"}  # shared global variable

# === Your Existing Code (Unchanged Core) ===

DETECTOR = "opencv"
FRAME_DOWNSCALE = 0.75
INFER_EVERY_N_FRAMES = 30

last_emotions = []
last_infer_time = 0.0
frame_count = 0

def draw_faces(frame, results):
    if not isinstance(results, list):
        return frame
    for r in results:
        region = r.get("region", {})
        x, y, w, h = region.get("x", 0), region.get("y", 0), region.get("w", 0), region.get("h", 0)
        emo_scores = r.get("emotion", {})
        if emo_scores:
            top_emo = max(emo_scores, key=emo_scores.get)
            top_val = emo_scores[top_emo]
            label = f"{top_emo.capitalize()} {top_val:.1f}%"
        else:
            label = "No face"
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.rectangle(frame, (x, max(y - 24, 0)), (x + max(120, w), y), (0, 255, 0), -1)
        cv2.putText(frame, label, (x + 4, y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2, cv2.LINE_AA)
    return frame

def find_camera():
    print("Searching for available cameras...")
    for index in range(6):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✓ Found working camera at index {index}")
                return cap, index
            cap.release()
    return None, -1

# === Background Emotion Detection Thread ===
def emotion_loop():
    global latest_emotion, last_emotions, frame_count, last_infer_time

    cap, cam_index = find_camera()
    if cap is None:
        print("ERROR: No camera found! Please check connections.")
        return

    print(f"Using camera index {cam_index}")
    print("Press 'q' in the window to quit\n")

    t0 = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to read frame - camera may have disconnected")
            break

        if FRAME_DOWNSCALE != 1.0:
            frame = cv2.resize(frame, None, fx=FRAME_DOWNSCALE, fy=FRAME_DOWNSCALE, interpolation=cv2.INTER_AREA)

        frame_count += 1
        do_infer = (frame_count % INFER_EVERY_N_FRAMES == 0)

        if do_infer:
            try:
                results = DeepFace.analyze(
                    img_path=frame,
                    actions=["emotion"],
                    detector_backend=DETECTOR,
                    enforce_detection=False,
                    align=True
                )
                if isinstance(results, dict):
                    results = [results]
                last_emotions = results

                # Extract top emotion for frontend
                if results and "emotion" in results[0]:
                    emo_scores = results[0]["emotion"]
                    top_emo = max(emo_scores, key=emo_scores.get)
                    latest_emotion["emotion"] = top_emo
                else:
                    latest_emotion["emotion"] = "None"

                last_infer_time = time.time()
            except Exception:
                last_emotions = []

        vis = frame.copy()
        vis = draw_faces(vis, last_emotions)
        dt = time.time() - t0
        fps = (frame_count / dt) if dt > 0 else 0.0
        cv2.putText(vis, f"FPS: {fps:.1f}  (infer every {INFER_EVERY_N_FRAMES})",
                    (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow("DeepFace Emotion (press 'q' to quit)", vis)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# === Flask Endpoint for Frontend ===
@app.route("/emotion")
def get_emotion():
    """Return the current detected emotion as JSON"""
    return jsonify(latest_emotion)

# === Run Backend ===
if __name__ == "__main__":
    # Start the camera/emotion thread
    thread = threading.Thread(target=emotion_loop, daemon=True)
    thread.start()

    # Run Flask server (for frontend access)
    app.run(host="0.0.0.0", port=5000)
