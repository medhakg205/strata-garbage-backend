# ai.py
from PIL import Image
import io
import numpy as np
from ultralytics import YOLO

# Load YOLOv8-nano model once
model = YOLO('yolov8n.pt')  # Nano model: small, fast, CPU-friendly

# Define trash-related COCO classes
TRASH_CLASSES = ['bottle', 'cup', 'bag', 'banana', 'apple', 'orange', 'wine glass']  # add more if needed

def predict_image(file_content: bytes):
    """
    Predicts trash severity in an image using YOLOv8-nano.
    Returns: (severity: str, message: str)
    """
    try:
        # Load image
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img_np = np.array(img)

        # Run YOLO detection
        results = model.predict(img_np, verbose=False)[0]

        # Filter detected trash objects
        detected_trash = [
            box for box, cls_id in zip(results.boxes.xyxy, results.boxes.cls)
            if model.names[int(cls_id)] in TRASH_CLASSES
        ]

        if not detected_trash:
            return None, "Not garbage ❌"

        # Compute number of objects and average box area
        areas = [(x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in detected_trash]
        avg_area = np.mean(areas)
        count = len(detected_trash)

        # Simple thresholds for severity (tune as needed)
        if count > 5 or avg_area > 5000:
            severity = "high"
            msg = "Heavy waste detected 🗑️"
        elif count > 2 or avg_area > 2000:
            severity = "medium"
            msg = "Moderate waste detected ⚠️"
        else:
            severity = "low"
            msg = "Minor waste detected ℹ️"

        return severity, msg

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
