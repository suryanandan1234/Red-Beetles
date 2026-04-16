#!/usr/bin/env python3
"""
Raspberry Pi Car - Web GUI with Live Streaming & Path Tracking
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import threading
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'picar_secret_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CONFIGURATION FILES ---
SETTINGS_FILE = "gui_settings.json"

# --- DEFAULT SETTINGS ---
DEFAULT_SETTINGS = {
    "rotation_calibration": 1.0,
    "zoom_level": 1.0,
    "turning_speed_multiplier": 1.0,
    "camera_index": 0
}

# --- GLOBAL STATE ---
settings = DEFAULT_SETTINGS.copy()
path_history = []
current_position = {"x": 0, "y": 0, "angle": 0}
points = {"A": None, "B": None}
car_state = {
    "mode": "IDLE",
    "at_point": "A",
    "halted": False,
    "left_motor": 0,
    "right_motor": 0
}

# --- CAMERA SETUP ---
camera = None
camera_lock = threading.Lock()

def init_camera():
    global camera
    with camera_lock:
        if camera is not None:
            camera.release()
        try:
            camera = cv2.VideoCapture(settings["camera_index"])
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_FPS, 30)
        except:
            camera = None

def generate_frames():
    """Generate video frames for streaming"""
    while True:
        with camera_lock:
            if camera is None or not camera.isOpened():
                break
            success, frame = camera.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- SETTINGS PERSISTENCE ---
def load_settings():
    global settings
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded = json.load(f)
                settings.update(loaded)
            print(f"Loaded settings: {settings}")
        except Exception as e:
            print(f"Error loading settings: {e}")
    else:
        save_settings()

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

# --- PATH TRACKING ---
def update_position(left_speed, right_speed):
    """
    Update car position based on tank turn mechanics
    FIXED: turning_speed_multiplier only affects visual rotation display, not movement distance
    """
    global current_position, path_history
    
    # Calculate movement delta
    avg_speed = (left_speed + right_speed) / 2.0
    speed_diff = (right_speed - left_speed)
    
    # Rotation - uses turning_speed_multiplier for visual display
    rotation_amount = speed_diff * settings["rotation_calibration"] * settings["turning_speed_multiplier"] * 0.01
    current_position["angle"] += rotation_amount
    current_position["angle"] %= 360
    
    # Forward/backward movement - ONLY uses avg_speed and zoom, NOT turning_speed
    import math
    movement = avg_speed * 0.05
    rad = math.radians(current_position["angle"])
    
    current_position["x"] += movement * math.cos(rad)
    current_position["y"] += movement * math.sin(rad)
    
    # Store path point
    path_history.append({
        "x": current_position["x"],
        "y": current_position["y"],
        "timestamp": datetime.now().isoformat()
    })
    
    # Limit path history
    if len(path_history) > 5000:
        path_history = path_history[-5000:]

def mark_point(point_name):
    """Mark current position as A or B"""
    global points
    points[point_name] = {
        "x": current_position["x"],
        "y": current_position["y"],
        "timestamp": datetime.now().isoformat()
    }

def reset_path():
    """Reset all path data"""
    global path_history, current_position, points
    path_history = []
    current_position = {"x": 0, "y": 0, "angle": 0}
    points = {"A": None, "B": None}

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    global settings
    if request.method == 'POST':
        data = request.json
        settings.update(data)
        save_settings()
        return jsonify({"status": "ok", "settings": settings})
    return jsonify(settings)

@app.route('/api/reset_path', methods=['POST'])
def api_reset_path():
    reset_path()
    return jsonify({"status": "ok"})

# --- SOCKETIO EVENTS ---
@socketio.on('connect')
def handle_connect():
    print(f"Client connected")
    emit('initial_state', {
        "settings": settings,
        "car_state": car_state,
        "position": current_position,
        "points": points,
        "path": path_history
    })

@socketio.on('update_motor_state')
def handle_motor_update(data):
    """Receive motor state from main controller script"""
    global car_state
    car_state.update(data)
    update_position(data.get('left_motor', 0), data.get('right_motor', 0))
    
    # Broadcast to all clients
    socketio.emit('car_update', {
        "position": current_position,
        "car_state": car_state,
        "path_point": path_history[-1] if path_history else None
    })

@socketio.on('mark_point')
def handle_mark_point(data):
    """Mark A or B point"""
    point_name = data.get('point')
    if point_name in ['A', 'B']:
        mark_point(point_name)
        socketio.emit('points_update', points)

@socketio.on('reset_all')
def handle_reset_all(data):
    """Full reset - clear path, points, position"""
    reset_path()
    socketio.emit('full_reset', {
        "position": current_position,
        "points": points,
        "path": []
    })

def run_flask():
    """Run Flask app"""
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    load_settings()
    init_camera()
    
    print("Starting web GUI on http://0.0.0.0:5000")
    print("Access from any device on your network at http://<pi-ip-address>:5000")
    run_flask()
