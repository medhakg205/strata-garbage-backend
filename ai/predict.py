from PIL import Image
import numpy as np

def predict_image(img_path):
    try:
        img = Image.open(img_path).convert("RGB")
        img = img.resize((100, 100))
        img_array = np.array(img)

        avg_color = img_array.mean()
        std_dev = img_array.std()

        # 🔥 smarter detection
        if std_dev > 50 and avg_color < 160:
            return 2   # HIGH garbage (messy + dark)
        elif std_dev > 30:
            return 1   # MEDIUM
        else:
            return 0   # NOT garbage

    except:
        return 0