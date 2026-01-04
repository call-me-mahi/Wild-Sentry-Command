import cv2
import time
import threading
import winsound
import os
from ultralytics import YOLO

# ==============================
# PATH SETUP
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")

BEE_SOUND = os.path.join(SOUNDS_DIR, "bees.wav")
TIGER_SOUND = os.path.join(SOUNDS_DIR, "tiger.wav")

# ==============================
# SOUND CONTROL
# ==============================
last_sound_time = 0
SOUND_COOLDOWN = 5  # seconds

def play_sound(path):
    def _play():
        if os.path.exists(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            print(f"[ERROR] Sound file missing: {path}")
    threading.Thread(target=_play, daemon=True).start()

def trigger_sound(animal):
    global last_sound_time
    now = time.time()

    if now - last_sound_time < SOUND_COOLDOWN:
        return

    last_sound_time = now

    if animal == "elephant":
        play_sound(BEE_SOUND)
    elif animal == "boar":
        play_sound(TIGER_SOUND)

# ==============================
# MODEL LOAD
# ==============================
print("[INFO] Loading YOLOv8 Nano model...")
model = YOLO("yolov8n.pt")
print("[INFO] Model loaded successfully")

# ==============================
# CAMERA
# ==============================
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] Camera not accessible")
    exit()

prev_time = 0

# ==============================
# COCO CLASS IDS
# ==============================
ELEPHANT_ID = 20
BOAR_PROXY_ID = 19   # cow
BEAR_ID = 21

# ==============================
# MAIN LOOP
# ==============================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # FPS calculation
    curr_time = time.time()
    fps = int(1 / (curr_time - prev_time)) if prev_time != 0 else 0
    prev_time = curr_time

    # YOLO inference
    results = model(frame, conf=0.5, verbose=False)

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            label = None

            if cls_id == ELEPHANT_ID:
                label = f"ELEPHANT {int(conf*100)}%"
                trigger_sound("elephant")

            elif cls_id == BOAR_PROXY_ID:
                label = f"WILD BOAR {int(conf*100)}%"
                trigger_sound("boar")

            elif cls_id == BEAR_ID:
                label = f"BEAR {int(conf*100)}%"
                trigger_sound("boar")

            if label:
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

    # FPS display
    cv2.putText(
        frame,
        f"FPS: {fps}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Crop Protection System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ==============================
# CLEANUP
# ==============================
cap.release()
cv2.destroyAllWindows()
