
import numpy as np
from PIL import Image
from tensorflow.keras.applications.mobilenet import MobileNet, preprocess_input, decode_predictions

model = MobileNet(weights="imagenet")

GARBAGE_KEYWORDS = [
    "trash", "garbage", "dustbin", "bin", "plastic", "bottle",
    "can", "paper", "wrapper", "bag"
]

def classify_waste(img_path):
    img = Image.open(img_path).resize((224, 224))
    img_array = np.array(img)

    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    preds = model.predict(img_array)
    decoded = decode_predictions(preds, top=3)[0]

    labels = [item[1] for item in decoded]
    confidences = [item[2] for item in decoded]

    is_garbage = any(
        any(keyword in label for keyword in GARBAGE_KEYWORDS)
        for label in labels
    )

    if not is_garbage:
        return {
            "is_garbage": False,
            "garbage_level": None
        }

    max_conf = max(confidences)

    if max_conf > 0.75:
        level = "high"
    elif max_conf > 0.4:
        level = "medium"
    else:
        level = "low"

    return {
        "is_garbage": True,
        "garbage_level": level
    }
