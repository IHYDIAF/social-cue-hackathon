import os, sys, time
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import cv2
from deepface import DeepFace

# Settings
SOURCE_INDEX = 0                 # 0 = default webcam
DETECTOR = "opencv"          # "retinaface" (better) or "opencv" (faster, no extra weights)
FRAME_DOWNSCALE = 0.75           # downscale to speed up (0.5–1.0). 1.0 = full size
INFER_EVERY_N_FRAMES = 10         # run model every N frames, reuse last result in between

# State
last_emotions = []               # list of results for each detected face in last inference
last_infer_time = 0.0
frame_count = 0

# Helper: draw labeled box + top emotion
def draw_faces(frame, results):
    if not isinstance(results, list):
        return frame
    for r in results:
        region = r.get("region", {})  # dict with x, y, w, h (coords are from resized frame)
        x, y, w, h = region.get("x", 0), region.get("y", 0), region.get("w", 0), region.get("h", 0)

        # Top emotion
        emo_scores = r.get("emotion", {})
        if emo_scores:
            top_emo = max(emo_scores, key=emo_scores.get)
            top_val = emo_scores[top_emo]
            label = f"{top_emo.capitalize()} {top_val:.1f}%"
        else:
            label = "No face"

        # Draw
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.rectangle(frame, (x, max(y - 24, 0)), (x + max(120, w), y), (0, 255, 0), -1)
        cv2.putText(frame, label, (x + 4, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2, cv2.LINE_AA)
    return frame

# Open webcam
cap = cv2.VideoCapture(SOURCE_INDEX)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam. Try changing SOURCE_INDEX to 1 or 2.")


t0 = time.time()
while True:
    ok, frame = cap.read()
    if not ok:
        break

    # Optional resize for speed
    if FRAME_DOWNSCALE != 1.0:
        frame = cv2.resize(frame, None, fx=FRAME_DOWNSCALE, fy=FRAME_DOWNSCALE, interpolation=cv2.INTER_AREA)

    frame_count += 1
    do_infer = (frame_count % INFER_EVERY_N_FRAMES == 0)

    if do_infer:
        try:
            # DeepFace.analyze returns a list (one entry per face) when enforce_detection=False
            results = DeepFace.analyze(
                img_path = frame,                 # pass numpy array directly
                actions = ["emotion"],
                detector_backend = DETECTOR,
                enforce_detection = False,        # don't crash if no face; returns empty list
                align = True
            )
            # DeepFace may return dict or list depending on version; normalize to list
            if isinstance(results, dict):
                results = [results]
            last_emotions = results
            last_infer_time = time.time()
        except Exception as e:
            # Keep previous results if any
            # print(f"Analyze error: {e}")  # uncomment for debugging
            last_emotions = []

    # Draw latest results (even on frames we didn’t infer)
    vis = frame.copy()
    vis = draw_faces(vis, last_emotions)

    # FPS-ish overlay
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
