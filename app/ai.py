import numpy as np
from PIL import Image
import io
from tensorflow.keras.applications.mobilenet import MobileNet, preprocess_input, decode_predictions

model = MobileNet(weights="imagenet")

def predict_image(file_content: bytes):
    try:
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img = img.resize((224, 224))

        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        preds = model.predict(img_array)
        decoded = decode_predictions(preds, top=1)[0][0]

        label = decoded[1]
        confidence = decoded[2]

        if "trash" in label or "garbage" in label or "bin" in label:
            return "high", "Garbage detected ✅"
        elif confidence > 0.6:
            return "medium", "Possible waste detected ⚠️"
        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
