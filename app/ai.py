import numpy as np
import onnxruntime as ort
from PIL import Image
import io

# Convert TFLite to ONNX once (or use repo's ONNX if available)
# For now, use ONNXRuntime direct TFLite support or pre-convert
session = ort.InferenceSession("mobilenet_v2.tflite", providers=['CPUExecutionProvider'])  # Direct TFLite support

input_name = session.get_inputs()[0].name
WASTE_CLASSES = list(range(6))  # 0-5 all waste

def predict_image(file_content: bytes):
    try:
        img = Image.open(io.BytesIO(file_content)).resize((224, 224)).convert("RGB")
        img_array = np.array(img, dtype=np.float32).transpose(2, 0, 1)[np.newaxis, :] / 255.0
        outputs = session.run(None, {input_name: img_array})[0][0]
        top_id = np.argmax(outputs)
        conf = outputs[top_id]
        if conf > 0.6:
            level = "high" if conf > 0.85 else "medium" if conf > 0.75 else "low"
            class_names = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
            return level, f"{class_names[top_id]} waste {level} ({conf:.1%}) 🗑️"
        return None, "Not garbage ❌"
    except Exception as e:
        print("Error:", e)
        return None, "Error ❌"
