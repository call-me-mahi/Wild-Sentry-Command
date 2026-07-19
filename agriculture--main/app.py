import cv2
import time
import threading
import os
import numpy as np
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request
from ultralytics import YOLO

# Import winsound conditionally (Windows only)
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


# ==============================
# PATH SETUP
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")
BEE_SOUND = os.path.join(SOUNDS_DIR, "bees.wav")
TIGER_SOUND = os.path.join(SOUNDS_DIR, "tiger.wav")

# Ensure sounds directory exists
if not os.path.exists(SOUNDS_DIR):
    os.makedirs(SOUNDS_DIR)

# ==============================
# GLOBAL STATE
# ==============================
CONFIG = {
    "confidence_threshold": 0.5,
    "cooldown_duration": 10,
    "persistence_frames": 15,
    "detected_elephant": True,
    "detected_boar": True,
    "detected_bear": True,
    "camera_enabled": True
}

STATUS = {
    "fps": 0,
    "camera_connected": False,
    "active_alert": False,
    "current_detection": None,
    "cooldown_active": False,
    "cooldown_end_time": 0
}

LOGS = [
    {
        "id": "SYS-INIT",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "animal": "SYSTEM INITIALIZED",
        "confidence": "100.0%",
        "status": "Nominal",
        "action": "Monitoring Started"
    }
]

# Detection parameters
ELEPHANT_ID = 20
BOAR_PROXY_ID = 19   # cow proxy
BEAR_ID = 21

# Cooldown and frames tracker
last_sound_time = 0
detection_counter = 0
current_detected_animal = None

# Mutex lock for thread safety
lock = threading.Lock()

# Load YOLO model
print("[INFO] Loading YOLOv8 Nano model...")
try:
    model = YOLO("yolov8n.pt")
    print("[INFO] Model loaded successfully")
except Exception as e:
    print(f"[ERROR] Failed to load YOLOv8 model: {e}")
    model = None

# ==============================
# SOUND CONTROL
# ==============================
def play_sound_async(path):
    def _play():
        if os.path.exists(path):
            try:
                if HAS_WINSOUND:
                    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    print(f"[INFO] Playing deterrent sound: {path}")
                else:
                    print(f"[INFO] Playing deterrent sound (MOCK on non-Windows): {path}")
            except Exception as e:
                print(f"[ERROR] Sound play failed: {e}")
        else:
            print(f"[ERROR] Sound file missing: {path}")
    threading.Thread(target=_play, daemon=True).start()

def stop_sounds():
    try:
        if HAS_WINSOUND:
            winsound.PlaySound(None, winsound.SND_PURGE)
        print("[INFO] All sounds stopped / muted")
    except Exception as e:
        print(f"[ERROR] Failed to stop sounds: {e}")

def trigger_sound(animal):
    global last_sound_time
    now = time.time()

    with lock:
        cooldown = CONFIG["cooldown_duration"]
        if now - last_sound_time < cooldown:
            return False

        last_sound_time = now
        STATUS["cooldown_active"] = True
        STATUS["cooldown_end_time"] = now + cooldown

    sound_played = "None"
    if animal == "elephant":
        play_sound_async(BEE_SOUND)
        sound_played = "bees.wav (Bee Buzz)"
    elif animal in ["boar", "bear"]:
        play_sound_async(TIGER_SOUND)
        sound_played = "tiger.wav (Tiger Growl)"

    # Add to log list
    log_entry = {
        "id": f"ALR-{int(time.time()) % 100000}",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "animal": animal.upper(),
        "confidence": "98.4%",  # Simulated confidence helper
        "status": "Deterrent Triggered",
        "action": f"Played {sound_played}"
    }
    LOGS.insert(0, log_entry)
    if len(LOGS) > 50:
        LOGS.pop()
    
    return True

# ==============================
# DUMMY FRAME GENERATOR (FALLBACK)
# ==============================
def generate_fallback_frame(width=640, height=480):
    """Generates a dummy surveillance screen with scanning effects for testing."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Grid background
    for y in range(0, height, 40):
        cv2.line(frame, (0, y), (width, y), (15, 15, 15), 1)
    for x in range(0, width, 40):
        cv2.line(frame, (x, 0), (x, height), (15, 15, 15), 1)
        
    # Scanning Line
    scan_y = int((time.time() * 100) % height)
    cv2.line(frame, (0, scan_y), (width, scan_y), (0, 0, 50), 2)
    
    # Text overlays
    cv2.putText(frame, "WILD SENTRY COMMAND", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.putText(frame, "CAMERA FEED INACTIVE / SIMULATED", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    cv2.putText(frame, f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Simulated animal if active
    if STATUS["active_alert"] and STATUS["current_detection"]:
        cv2.rectangle(frame, (150, 150), (450, 400), (0, 0, 255), 2)
        cv2.putText(frame, f"{STATUS['current_detection'].upper()} [SIMULATED DETECT]", (160, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
    ret, jpeg = cv2.imencode('.jpg', frame)
    return jpeg.tobytes()

# ==============================
# MAIN CAMERA PIPELINE
# ==============================
def gen_frames():
    global detection_counter, current_detected_animal, last_sound_time
    
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        STATUS["camera_connected"] = True
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    else:
        print("[WARNING] Physical camera not found. Operating in simulation mode.")
        STATUS["camera_connected"] = False
        cap = None

    prev_time = time.time()
    
    while True:
        # Check camera enabled state
        if not CONFIG["camera_enabled"]:
            time.sleep(0.1)
            continue
            
        if cap is None or not cap.isOpened():
            # Run simulation loop
            # Simulate a random intrusion every 30 seconds if config matches
            now_t = time.time()
            if not STATUS["active_alert"] and int(now_t) % 25 == 0:
                STATUS["active_alert"] = True
                STATUS["current_detection"] = "elephant" if CONFIG["detected_elephant"] else "boar"
                trigger_sound(STATUS["current_detection"])
            elif STATUS["active_alert"] and int(now_t) % 25 == 8:
                STATUS["active_alert"] = False
                STATUS["current_detection"] = None
                
            STATUS["fps"] = 30
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + generate_fallback_frame() + b'\r\n')
            time.sleep(0.033)
            continue

        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Camera frame capture failed. Yielding simulated feed.")
            STATUS["camera_connected"] = False
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + generate_fallback_frame() + b'\r\n')
            time.sleep(0.1)
            continue
            
        STATUS["camera_connected"] = True
        
        # FPS calculation
        curr_time = time.time()
        fps = int(1 / (curr_time - prev_time)) if prev_time != 0 else 0
        prev_time = curr_time
        STATUS["fps"] = fps
        
        # Run YOLO inference
        detected_in_frame = False
        detected_class_name = None
        
        if model:
            results = model(frame, conf=CONFIG["confidence_threshold"], verbose=False)
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    label = None
                    animal_key = None
                    
                    if cls_id == ELEPHANT_ID and CONFIG["detected_elephant"]:
                        label = f"ELEPHANT {int(conf*100)}%"
                        animal_key = "elephant"
                    elif cls_id == BOAR_PROXY_ID and CONFIG["detected_boar"]:
                        label = f"WILD BOAR {int(conf*100)}%"
                        animal_key = "boar"
                    elif cls_id == BEAR_ID and CONFIG["detected_bear"]:
                        label = f"BEAR {int(conf*100)}%"
                        animal_key = "bear"
                        
                    if animal_key:
                        detected_in_frame = True
                        detected_class_name = animal_key
                        
                        # Draw bounding box and label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(
                            frame,
                            label,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2
                        )
                        
        # Alert decision logic (Frame persistence)
        if detected_in_frame:
            if detected_class_name == current_detected_animal:
                detection_counter += 1
            else:
                current_detected_animal = detected_class_name
                detection_counter = 1
                
            if detection_counter >= CONFIG["persistence_frames"]:
                STATUS["active_alert"] = True
                STATUS["current_detection"] = current_detected_animal
                trigger_sound(current_detected_animal)
        else:
            detection_counter = 0
            current_detected_animal = None
            STATUS["active_alert"] = False
            STATUS["current_detection"] = None
            
        # Update cooldown state
        now = time.time()
        if STATUS["cooldown_active"] and now > STATUS["cooldown_end_time"]:
            STATUS["cooldown_active"] = False

        # Encode and stream frame
        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            
    if cap:
        cap.release()

# ==============================
# FLASK WEB ENDPOINTS
# ==============================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status', methods=['GET'])
def get_status():
    now = time.time()
    cooldown_remaining = max(0, int(STATUS["cooldown_end_time"] - now)) if STATUS["cooldown_active"] else 0
    
    return jsonify({
        "fps": STATUS["fps"],
        "camera_connected": STATUS["camera_connected"],
        "active_alert": STATUS["active_alert"],
        "current_detection": STATUS["current_detection"],
        "cooldown_active": STATUS["cooldown_active"],
        "cooldown_remaining": cooldown_remaining,
        "config": CONFIG
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify(LOGS)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
        
    if "confidence_threshold" in data:
        CONFIG["confidence_threshold"] = float(data["confidence_threshold"])
    if "cooldown_duration" in data:
        CONFIG["cooldown_duration"] = int(data["cooldown_duration"])
    if "persistence_frames" in data:
        CONFIG["persistence_frames"] = int(data["persistence_frames"])
    if "detected_elephant" in data:
        CONFIG["detected_elephant"] = bool(data["detected_elephant"])
    if "detected_boar" in data:
        CONFIG["detected_boar"] = bool(data["detected_boar"])
    if "detected_bear" in data:
        CONFIG["detected_bear"] = bool(data["detected_bear"])
    if "camera_enabled" in data:
        CONFIG["camera_enabled"] = bool(data["camera_enabled"])
        
    return jsonify({"status": "success", "config": CONFIG})

@app.route('/api/trigger', methods=['POST'])
def trigger_deterrent():
    data = request.json
    if not data or "animal" not in data:
        return jsonify({"status": "error", "message": "Missing animal argument"}), 400
        
    animal = data["animal"]
    triggered = trigger_sound(animal)
    
    if triggered:
        return jsonify({"status": "success", "message": f"Manual trigger sent for {animal}"})
    else:
        return jsonify({"status": "cooldown", "message": "Cannot trigger: system in cooldown"})

@app.route('/api/stop', methods=['POST'])
def stop_all_sounds():
    stop_sounds()
    return jsonify({"status": "success", "message": "All sounds stopped"})

if __name__ == "__main__":
    # Host on 0.0.0.0 to enable network access
    app.run(host="0.0.0.0", port=5000, debug=False)
