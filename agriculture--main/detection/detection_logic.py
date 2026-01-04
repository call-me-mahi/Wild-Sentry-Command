import cv2
import numpy as np
from models.model_loader import load_model
from utils.roi import get_roi

# Load model ONCE
net, classes, output_layers = load_model()

# Detection configuration
CONFIDENCE_THRESHOLD = 0.6
TARGET_CLASSES = [
    "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe"
]


def detect_target(frame):
    """
    Input: one camera frame
    Output: True if target animal detected with high confidence
            False otherwise
    """

    if frame is None:
        return False

    # Apply ROI
    roi = get_roi(frame)

    # Convert ROI to blob
    blob = cv2.dnn.blobFromImage(
        roi,
        scalefactor=0.00392,
        size=(416, 416),
        mean=(0, 0, 0),
        swapRB=True,
        crop=False
    )

    net.setInput(blob)
    outputs = net.forward(output_layers)

    # Parse detections
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = int(np.argmax(scores))
            confidence = scores[class_id]

            detected_class = classes[class_id]

            # Q2 + Q3: class & confidence
            if detected_class in TARGET_CLASSES and confidence >= CONFIDENCE_THRESHOLD:
                return True

    return False
