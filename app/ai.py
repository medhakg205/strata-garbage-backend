from PIL import Image
import io
import numpy as np

def predict_image(file_content: bytes):
    try:
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img).astype(np.float32)

        # --- GRAYSCALE ---
        gray = img_array.mean(axis=2)

        # --- FEATURE 1: Trash Area ---
        trash_mask = gray < 120
        trash_ratio = np.sum(trash_mask) / trash_mask.size

        # --- FEATURE 2: Edge Density ---
        edges = np.abs(np.diff(gray, axis=0)).mean()

        # --- FEATURE 3: Color Variation ---
        color_variance = img_array.var()

        # --- FEATURE 4: Spread ---
        blocks = np.array_split(gray, 9)
        spread = np.mean([np.mean(b < 120) for b in blocks])

        # --- DECISION LOGIC ---
        score = 0

        if trash_ratio > 0.5:
            score += 3
        elif trash_ratio > 0.25:
            score += 2
        elif trash_ratio > 0.1:
            score += 1

        if spread > 0.5:
            score += 2
        elif spread > 0.3:
            score += 1

        if edges > 25:
            score += 1

        if color_variance > 2500:
            score += 1

        # --- FINAL OUTPUT ---
        if score >= 5:
            return "high", "Heavy waste detected"
        elif score >= 3:
            return "medium", "Moderate waste detected "
        elif score >= 1:
            return "low", "Minor waste detected"
        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
