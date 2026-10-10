import os
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyautogui
import math

# Disable PyAutoGUI fail-safe for smooth testing
pyautogui.FAILSAFE = False

# Automatically download the Google hand-tracking model if missing
model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
model_path = "hand_landmarker.task"
if not os.path.exists(model_path):
    print("Downloading hand tracking model files... Please wait.")
    urllib.request.urlretrieve(model_url, model_path)
    print("Model download complete!")

# Initialize MediaPipe Hand Landmarker
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=1
)
detector = vision.HandLandmarker.create_from_options(options)

# Open laptop webcam and get screen size
cap = cv2.VideoCapture(0)
screen_w, screen_h = pyautogui.size()

# Hand skeleton bone connections for drawing lines
HAND_CONNECTIONS = [
    (0,1), (1,2), (2,3), (3,4),       # Thumb
    (0,5), (5,6), (6,7), (7,8),       # Index
    (5,9), (9,10),(10,11),(11,12),    # Middle
    (9,13),(13,14),(14,15),(15,16),   # Ring
    (13,17),(17,18),(18,19),(19,20),  # Pinky
    (0,17)                            # Palm base
]

print("Engineering Interface active. Move index to control cursor, pinch thumb+index to click. Press 'q' to exit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        continue

    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    detection_result = detector.detect(mp_image)

    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            pts = [(int(landmark.x * width), int(landmark.y * height)) for landmark in hand_landmarks]
            
            # Draw skeleton bones and joints
            for connection in HAND_CONNECTIONS:
                cv2.line(frame, pts[connection[0]], pts[connection[1]], (0, 255, 0), 2)
            for pt in pts:
                cv2.circle(frame, pt, 4, (0, 0, 255), -1)

            # Index Finger Tip is landmark 8, Thumb Tip is landmark 4
            ix, iy = pts[8][0], pts[8][1]
            tx, ty = pts[4][0], pts[4][1]

            # Map index finger position to screen cursor
            screen_x = int((ix / width) * screen_w)
            screen_y = int((iy / height) * screen_h)
            try:
                pyautogui.moveTo(screen_x, screen_y)
            except Exception:
                pass

            # Pinch detection (distance between thumb and index tip)
            distance = math.hypot(ix - tx, iy - ty)
            if distance < 35:
                cv2.circle(frame, (ix, iy), 15, (255, 0, 0), cv2.FILLED)
                pyautogui.click()

    cv2.imshow('Engineering Hand Interface', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()