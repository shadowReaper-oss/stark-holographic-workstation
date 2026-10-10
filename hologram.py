import os
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from ursina import *
import threading

# 1. Automatically download the Google hand-tracking model if missing
model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
model_path = "hand_landmarker.task"
if not os.path.exists(model_path):
    print("Downloading hand tracking model files... Please wait.")
    urllib.request.urlretrieve(model_url, model_path)

# Shared tracking variables between webcam thread and 3D graphics engine
hand_data = {"detected": False, "x": 0.5, "y": 0.5, "pinch": False}

def track_hands_background():
    """Runs the webcam and hand tracker in a background thread seamlessly."""
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_hands=1
    )
    detector = vision.HandLandmarker.create_from_options(options)
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue
        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        detection_result = detector.detect(mp_image)

        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                # Index finger tip (8) and Thumb tip (4)
                ix, iy = hand_landmarks[8].x, hand_landmarks[8].y
                tx, ty = hand_landmarks[4].x, hand_landmarks[4].y
                
                # Calculate pinch distance
                pinch_dist = ((ix - tx)**2 + (iy - ty)**2) ** 0.5

                hand_data["detected"] = True
                hand_data["x"] = ix
                hand_data["y"] = iy
                hand_data["pinch"] = pinch_dist < 0.05
        else:
            hand_data["detected"] = False

    cap.release()

# Start the tracker thread
threading.Thread(target=track_hands_background, daemon=True).start()

# 2. Initialize Ursina 3D Holographic Interface Window
app = Ursina()
window.title = "Stark Engineering Holographic Interface"
window.borderless = False
window.color = color.black

# Create a futuristic glowing 3D CAD engineering model (Cube/Assembly simulation)
holo_model = Entity(
    model='cube',
    color = color.cyan,
    scale = 2.5,
    shader = 'basic_lighting_shader'
)

# Add ambient glowing wireframe aesthetics for that Iron Man HUD look
holo_wire = Entity(
    model='cube',
    color = color.white,
    scale = 2.55,
    wireframe = True
)

# Lighting for 3D depth
PointLight(parent=camera, color=color.cyan, position=(0, 5, -5))
AmbientLight(color=color.rgba(50, 50, 50, 255))

def update():
    """Called every frame by Ursina to manipulate the model using hand coordinates."""
    if hand_data["detected"]:
        # Map hand coordinates to 3D rotation and scale
        target_rot_y = (hand_data["x"] - 0.5) * 360 * 2
        target_rot_x = (hand_data["y"] - 0.5) * 360 * 2
        
        # Smoothly interpolate model rotation (Stark-like fluid movement)
        holo_model.rotation_y = lerp(holo_model.rotation_y, target_rot_y, 0.1)
        holo_model.rotation_x = lerp(holo_model.rotation_x, target_rot_x, 0.1)
        holo_wire.rotation_y = holo_model.rotation_y
        holo_wire.rotation_x = holo_model.rotation_x

        # If pinching, scale/zoom the holographic model
        if hand_data["pinch"]:
            holo_model.scale = 3.5
            holo_wire.scale = 3.55
            holo_model.color = color.magenta
        else:
            holo_model.scale = 2.5
            holo_wire.scale = 2.55
            holo_model.color = color.cyan

print("Launching 3D Holographic Interface. Move your hand in the air to control the model!")
app.run()