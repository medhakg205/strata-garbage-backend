from PIL import Image
import io
import numpy as np

def predict_image(file_content: bytes):
    try:
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img)

        # --- GRAYSCALE ---
        gray = img_array.mean(axis=2)

        # --- NON-GARBAGE FILTER (NEW) ---
        blue_ratio = np.sum(img_array[:, :, 2] > 150) / img_array.size
        green_ratio = np.sum(img_array[:, :, 1] > 120) / img_array.size

        if blue_ratio > 0.3 or green_ratio > 0.3:
            return None, "Not garbage ❌"

        # --- FEATURE 1: Brightness ---
        brightness = img_array.mean()

        # --- FEATURE 2: Color variance ---
        color_variance = img_array.var()

        # --- FEATURE 3: Edge detection ---
        edges = np.abs(np.diff(gray, axis=0)).mean()

        # --- NEW: Trash Area (IMPORTANT) ---
        trash_ratio = np.sum(gray < 120) / gray.size

        # --- NEW: Spread ---
        blocks = np.array_split(gray, 9)
        spread = np.mean([np.mean(b < 120) for b in blocks])

        # --- STRONG HIGH DETECTION ---
        if trash_ratio > 0.35 and spread > 0.4:
            return "high", "Heavy waste detected 🗑️"

        if trash_ratio > 0.5:
            return "high", "Heavy waste detected 🗑️"

        # --- SCORING ---
        score = 0

        if brightness < 100:
            score += 1

        if color_variance > 2000:
            score += 1

        if edges > 20:
            score += 1

        if trash_ratio > 0.25:
            score += 1

        if spread > 0.3:
            score += 1

        # --- FINAL CLASSIFICATION ---
        if score >= 4:
            return "high", "Heavy waste detected 🗑️"
        elif score >= 2:
            return "medium", "Moderate waste detected ⚠️"
        elif score >= 1:
            return "low", "Minor waste detected ℹ️"
        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
