from PIL import Image
import io
import numpy as np

def predict_image(file_content: bytes):
    try:
        # Convert bytes → image
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img = img.resize((224, 224))

        img_array = np.array(img)

        # --- FEATURE 1: Brightness ---
        brightness = img_array.mean()

        # --- FEATURE 2: Color variance (messy scenes = more variation) ---
        color_variance = img_array.var()

        # --- FEATURE 3: Edge detection (simple diff) ---
        edges = np.abs(np.diff(img_array, axis=0)).mean()

        # --- DECISION LOGIC ---
        score = 0

        if brightness < 100:   # darker = dirtier
            score += 1

        if color_variance > 2000:  # mixed colors = clutter
            score += 1

        if edges > 20:  # lots of edges = messy
            score += 1

        # --- FINAL CLASSIFICATION ---
        if score >= 3:
            return "high", "Heavy waste detected 🗑️"
        elif score == 2:
            return "medium", "Moderate waste detected ⚠️"
        elif score == 1:
            return "low", "Minor waste detected ℹ️"
        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
