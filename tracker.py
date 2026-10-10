import os
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Automatically download the Google hand-tracking model if it's missing
model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
model_path = "hand_landmarker.task"
if not os.path.exists(model_path):
    print("Downloading hand tracking model files... Please wait.")
    urllib.request.urlretrieve(model_url, model_path)
    print("Model download complete!")

# Initialize the modern MediaPipe Hand Landmarker
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=2
)
detector = vision.HandLandmarker.create_from_options(options)

# Open the laptop webcam
cap = cv2.VideoCapture(0)
print("Starting hand tracker. Press 'q' to exit.")

# Hand skeleton bone connections for drawing lines
HAND_CONNECTIONS = [
    (0,1), (1,2), (2,3), (3,4),       # Thumb
    (0,5), (5,6), (6,7), (7,8),       # Index
    (5,9), (9,10),(10,11),(11,12),    # Middle
    (9,13),(13,14),(14,15),(15,16),   # Ring
    (13,17),(17,18),(18,19),(19,20),  # Pinky
    (0,17)                            # Palm base
]

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # Flip frame horizontally for a natural mirror view
    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape

    # Convert OpenCV BGR image to MediaPipe RGB Image format
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    # Detect hand landmarks
    detection_result = detector.detect(mp_image)

    # Draw hand landmarks and bones if hands are detected
    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            # Convert normalized coordinates back to pixel coordinates
            pts = [(int(landmark.x * width), int(landmark.y * height)) for landmark in hand_landmarks]
            
            # Draw connecting lines (bones)
            for connection in HAND_CONNECTIONS:
                pt1 = pts[connection[0]]
                pt2 = pts[connection[1]]
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
            
            # Draw joint dots
            for pt in pts:
                cv2.circle(frame, pt, 4, (0, 0, 255), -1)

    # Display the live window
    cv2.imshow('Engineering Hand Interface', frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()