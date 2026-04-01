import numpy as np
import tensorflow as tf
from PIL import Image
import io

interpreter = tflite.Interpreter(model_path="mobilenet_v2.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

WASTE_CLASSES = [0,1,2,3,4,5]  # All classes are waste!

def predict_image(file_content: bytes):
    try:
        img = Image.open(io.BytesIO(file_content)).resize((224, 224)).convert("RGB")
        img_array = np.expand_dims(np.array(img, dtype=np.float32)/255.0, 0)
        interpreter.set_tensor(input_details[0]['index'], img_array)
        interpreter.invoke()
        probs = interpreter.get_tensor(output_details[0]['index'])[0]
        top_id = np.argmax(probs)
        conf = probs[top_id]
        if conf > 0.6:
            level = "high" if conf > 0.85 else "medium" if conf > 0.75 else "low"
            class_names = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
            return level, f"{class_names[top_id]} waste {level} ({conf:.1%}) 🗑️"
        return None, "Not garbage ❌"
    except Exception as e:
        print("Error:", e)
        return None, "Error ❌"
