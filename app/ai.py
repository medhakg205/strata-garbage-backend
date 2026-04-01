from PIL import Image
import io
import numpy as np

def predict_image(file_content: bytes):
    try:
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img).astype(np.float32)

        gray = img_array.mean(axis=2)

        # --- DETECT DARK OBJECTS (trash candidates) ---
        mask = gray < 110

        # --- TOTAL AREA ---
        total_ratio = np.sum(mask) / mask.size

        # --- LARGEST CLUSTER SIZE ---
        # simple row grouping (lightweight cluster approx)
        row_sums = np.sum(mask, axis=1)
        max_cluster = np.max(row_sums) / mask.shape[1]

        # --- FINAL DECISION ---
        # HIGH → large area + spread
        if total_ratio > 0.35:
            return "high", "Heavy waste detected 🗑️"

        # MEDIUM → noticeable cluster
        elif max_cluster > 0.25:
            return "medium", "Moderate waste detected ⚠️"

        # LOW → small object 
        elif total_ratio > 0.02:
            return "low", "Minor waste detected ℹ️"

        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
        return None, "Not garbage ❌"
