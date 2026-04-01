from PIL import Image
import io
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2

# --- LOAD MODEL ONCE ---
model = mobilenet_v2(weights="IMAGENET1K_V1")
model.eval()

# Remove classifier → feature extractor
feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])

# Transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

def extract_features(img):
    img = transform(img).unsqueeze(0)
    with torch.no_grad():
        features = feature_extractor(img)
    return features.flatten().numpy()


def predict_image(file_content: bytes):
    try:
        # --- LOAD IMAGE ---
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img).astype(np.float32)

        # --- 1. DEEP FEATURES (SEMANTIC UNDERSTANDING) ---
        features = extract_features(img)
        deep_score = np.std(features) / (np.mean(features) + 1e-5)

        # --- 2. TRASH AREA ---
        gray = img_array.mean(axis=2)
        trash_mask = gray < 120
        trash_ratio = np.sum(trash_mask) / trash_mask.size

        # --- 3. SPREAD ---
        blocks = np.array_split(trash_mask, 9)
        spread = np.mean([np.mean(b) for b in blocks])

        # --- 4. FINAL COMBINED SCORE ---
        score = (
            deep_score * 2 +
            trash_ratio * 3 +
            spread * 2
        )

        # --- 5. CLASSIFICATION ---
        if score > 4:
            return "high", "Heavy waste detected 🗑️"

        elif score > 2.5:
            return "medium", "Moderate waste detected ⚠️"

        elif score > 1:
            return "low", "Minor waste detected ℹ️"

        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
