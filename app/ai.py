from PIL import Image
import io
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2

# Load model once
model = mobilenet_v2(weights="IMAGENET1K_V1")
model.eval()

feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])

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
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img).astype(np.float32)

        # --- DEEP FEATURES (only for filtering) ---
        features = extract_features(img)
        deep_score = np.std(features) / (np.mean(features) + 1e-5)

        # --- TRASH AREA ---
        gray = img_array.mean(axis=2)
        trash_mask = gray < 120
        trash_ratio = np.sum(trash_mask) / trash_mask.size

        # --- SPREAD ---
        blocks = np.array_split(trash_mask, 9)
        spread = np.mean([np.mean(b) for b in blocks])

        # --- NON-GARBAGE FILTER (IMPORTANT) ---
        if deep_score < 0.8 and trash_ratio < 0.1:
            return None, "Not garbage ❌"

        # --- CLASSIFICATION (AREA DRIVEN) ---
        if clutter_ratio > 0.5:
            if spread > 0.5:
                return "high", "Heavy waste detected 🗑️"
            else:
                return "medium", "Moderate waste detected ⚠️"

        elif clutter_ratio > 0.2:
            return "medium", "Moderate waste detected ⚠️"

        elif clutter_ratio > 0.05:
            return "low", "Minor waste detected ℹ️"

        else:
            return None, "Not garbage ❌"
    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
