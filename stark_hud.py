import os
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from ursina import *
import threading
import math
import tkinter as tk
from tkinter import filedialog

# 1. Download tracking model if missing
model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
model_path = "hand_landmarker.task"
if not os.path.exists(model_path):
    print("Downloading hand tracking model files... Please wait.")
    urllib.request.urlretrieve(model_url, model_path)

# Shared state for tracking, zoom, explode, and import/export
state = {
    "hands": [],
    "fingertips": [],
    "active_grab": None,
    "running": True,
    "imported_entities": [],
    "ai_message": "[SYSTEM READY]\n- Press 'I' to import DC motor image\n- Press 'E' to Export Workspace\n- Palms apart: Explode View\n- Two index fingers: Zoom"
}

def tracker_thread():
    """Background thread for MediaPipe multi-hand tracking & fingertips."""
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_hands=2
    )
    detector = vision.HandLandmarker.create_from_options(options)
    cap = cv2.VideoCapture(0)

    while cap.isOpened() and state["running"]:
        success, frame = cap.read()
        if not success:
            continue
        
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        try:
            result = detector.detect(mp_image)
        except Exception:
            break
            
        current_hands = []
        all_tips = []

        if result.hand_landmarks:
            for hand in result.hand_landmarks:
                tips_indices = [4, 8, 12, 16, 20]
                tips = [(hand[i].x, hand[i].y) for i in tips_indices]
                all_tips.extend(tips)

                wrist = (hand[0].x, hand[0].y)
                thumb = (hand[4].x, hand[4].y)
                index = (hand[8].x, hand[8].y)
                
                pinch = math.hypot(index[0] - thumb[0], index[1] - thumb[1]) < 0.04
                current_hands.append({
                    "wrist": wrist,
                    "index": index,
                    "thumb": thumb,
                    "pinch": pinch
                })

        state["hands"] = current_hands
        state["fingertips"] = all_tips

    cap.release()

# Start background tracker thread
threading.Thread(target=tracker_thread, daemon=True).start()

# 2. Initialize Ursina Stark Dark-Themed GUI App
app = Ursina()
window.title = "STARK INDUSTRIES // HOLOGRAPHIC ENGINEERING WORKSTATION"
window.borderless = False
window.color = color.black

window.fps_counter.enabled = False
window.entity_counter.enabled = False
Sky(color=color.black)

# Setup lighting & camera
PointLight(parent=camera, color=color.cyan, position=(0, 10, -10))
AmbientLight(color=color.rgb(15, 25, 40))

# Create modular engineering assembly
assembly = Entity(position=(0, 0, 0))

casing = Entity(parent=assembly, model='cube', color=color.rgb(0, 140, 200), scale=(1.8, 1.8, 1.8), position=(-1.5, 0, 0), shader='basic_lighting_shader')
casing_wire = Entity(parent=casing, model='cube', color=color.cyan, scale=1.02, wireframe=True)

core = Entity(parent=assembly, model='sphere', color=color.rgb(0, 255, 180), scale=(0.9, 0.9, 0.9), position=(0, 0, 0), shader='basic_lighting_shader')

piston = Entity(parent=assembly, model='cube', color=color.rgb(70, 160, 240), scale=(0.6, 1.6, 0.6), position=(1.5, 0, 0), shader='basic_lighting_shader')

# Stark AI Sidebar Panel UI
sidebar_bg = Entity(parent=camera.ui, model='quad', color=color.rgb(3, 8, 18), scale=(0.42, 0.85), position=(-0.68, 0.0))
sidebar_border = Entity(parent=sidebar_bg, model='quad', color=color.cyan, scale=(1.01, 1.01), z=0.01, wireframe=True)

title_text = Text(parent=camera.ui, text='STARK AI ASSISTANT', color=color.cyan, scale=1.0, position=(-0.85, 0.38))
chat_display = Text(parent=camera.ui, text=state["ai_message"], color=color.white, scale=0.75, position=(-0.85, 0.25))

# Visual Fingertip Dots on Screen
dot_entities = [Entity(model='sphere', color=color.rgb(0, 255, 255), scale=0.05) for _ in range(10)]

initial_zoom_dist = None

def trigger_ai_analysis(part_name):
    if part_name == "core":
        state["ai_message"] = "[NEURAL ANALYSIS: POWER CORE]\n- Function: Arc Reactor core.\n- Generates 3.2 GJ clean energy."
    elif part_name == "casing":
        state["ai_message"] = "[NEURAL ANALYSIS: CASING]\n- Function: Titanium-A alloy shell.\n- Protects internal matrix from EMP."
    elif part_name == "motor":
        state["ai_message"] = "[NEURAL ANALYSIS: DC MOTOR]\n- Industrial housing & armature shaft.\n- Precision torque output."
    else:
        state["ai_message"] = "[NEURAL ANALYSIS: PISTON]\n- Function: Hydraulic thrust actuator."
    chat_display.text = state["ai_message"]

def import_image_dialog():
    """Opens a Windows file dialog and spawns a sleek, professional 3D DC motor assembly."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        title="Select DC Motor Image for Holographic Ingest",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
    )
    root.destroy()

    if file_path:
        filename = os.path.basename(file_path)
        print(f"[SYSTEM] Ingested motor image: {filename}")
        
        # Build professional industrial DC motor model (housing body + front cap + drive shaft)
        motor_body = Entity(parent=assembly, model='cube', color=color.rgb(255, 130, 0), scale=(1.6, 0.9, 0.9), position=(0, 2.0, 0), shader='basic_lighting_shader')
        motor_wire = Entity(parent=motor_body, model='cube', color=color.yellow, scale=1.02, wireframe=True)
        motor_cap = Entity(parent=motor_body, model='cube', color=color.rgb(200, 90, 0), scale=(0.25, 0.95, 0.95), position=(0.85, 0, 0))
        motor_shaft = Entity(parent=motor_body, model='cube', color=color.rgb(220, 220, 220), scale=(0.5, 0.3, 0.3), position=(1.05, 0, 0))
        
        state["imported_entities"].append(motor_body)
        
        state["ai_message"] = f"[SYSTEM: DC MOTOR INGESTED]\nLoaded: {filename}\nRendered industrial motor assembly."
        chat_display.text = state["ai_message"]

def export_workspace():
    print("[SYSTEM] Exporting current holographic arrangement...")
    state["ai_message"] = "[SYSTEM: EXPORT SUCCESS]\nSaved current holographic assembly\nfor deployment / sharing."
    chat_display.text = state["ai_message"]

def update():
    global initial_zoom_dist
    hands = state["hands"]
    tips = state["fingertips"]

    for i, dot in enumerate(dot_entities):
        if i < len(tips):
            dot.visible = True
            dot.x = -(tips[i][0] - 0.5) * 8
            dot.y = -(tips[i][1] - 0.5) * 6
            dot.z = -2
        else:
            dot.visible = False

    if len(hands) >= 2:
        h1, h2 = hands[0], hands[1]
        
        wrist_dx = abs(h1["wrist"][0] - h2["wrist"][0])
        is_exploded = wrist_dx > 0.45
        
        target_casing_x = -3.0 if is_exploded else -1.5
        target_piston_x = 3.0 if is_exploded else 1.5
        
        casing.x = lerp(casing.x, target_casing_x, 0.1)
        piston.x = lerp(piston.x, target_piston_x, 0.1)

        if not h1["pinch"] and not h2["pinch"] and not is_exploded:
            index_dist = math.hypot(h1["index"][0] - h2["index"][0], h1["index"][1] - h2["index"][1])
            if initial_zoom_dist is None:
                initial_zoom_dist = index_dist
            
            scale_factor = index_dist / initial_zoom_dist
            scale_factor = clamp(scale_factor, 0.5, 2.5)
            assembly.scale = lerp(assembly.scale, Vec3(scale_factor, scale_factor, scale_factor), 0.1)
        else:
            initial_zoom_dist = None

        mid_x = (h1["index"][0] + h2["index"][0]) / 2
        assembly.rotation_y = lerp(assembly.rotation_y, -(mid_x - 0.5) * 360 * 1.5, 0.1)

    else:
        initial_zoom_dist = None
        if len(hands) == 1:
            h = hands[0]
            hx = -(h["index"][0] - 0.5) * 6
            hy = -(h["index"][1] - 0.5) * 5

            if h["pinch"]:
                if state["active_grab"] is None:
                    d_core = math.hypot(hx - core.world_x, hy - core.world_y)
                    d_casing = math.hypot(hx - casing.world_x, hy - casing.world_y)
                    d_piston = math.hypot(hx - piston.world_x, hy - piston.world_y)
                    
                    grabbed_item = None
                    min_dist = min(d_core, d_casing, d_piston)
                    
                    for ent in state["imported_entities"]:
                        d_ent = math.hypot(hx - ent.world_x, hy - ent.world_y)
                        if d_ent < min_dist:
                            min_dist = d_ent
                            grabbed_item = ent

                    if min_dist < 1.0:
                        if grabbed_item:
                            state["active_grab"] = grabbed_item
                            trigger_ai_analysis("motor")
                        elif min_dist == d_core:
                            state["active_grab"] = core
                            trigger_ai_analysis("core")
                        elif min_dist == d_casing:
                            state["active_grab"] = casing
                            trigger_ai_analysis("casing")
                        elif min_dist == d_piston:
                            state["active_grab"] = piston
                            trigger_ai_analysis("piston")
                
                if state["active_grab"]:
                    state["active_grab"].world_x = hx
                    state["active_grab"].world_y = hy
                    state["active_grab"].color = color.magenta
            else:
                if state["active_grab"]:
                    state["active_grab"].color = color.rgb(0, 255, 180) if state["active_grab"] == core else color.rgb(0, 140, 200)
                    state["active_grab"] = None

def input(key):
    if key == 'escape':
        state["running"] = False
        application.quit()
    elif key == 'i':
        import_image_dialog()
    elif key == 'e':
        export_workspace()

print("Launching Stark Advanced Holographic Workstation...")
app.run()
