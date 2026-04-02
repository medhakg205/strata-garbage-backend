from PIL import Image
import io
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2

# Load model once
model = mobilenet_v2(pretrained=True)
model.eval()

# Remove classifier → keep feature extractor
feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])

# Image transform
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

        features = extract_features(img)

        # --- Compute improved "complexity score" ---
        # 1. Absolute deviation from mean
        abs_dev = np.abs(features - np.mean(features))
        # 2. Mean of deviations
        score = np.mean(abs_dev)
        # 3. Optional: normalize to 0–1 (approx)
        score_norm = score / (np.max(features) - np.min(features) + 1e-5)

        # --- Debug: see real scores ---
        print(f"DEBUG score: {score:.4f}, normalized: {score_norm:.4f}")

        # --- Classification thresholds ---
        if score_norm > 0.25:
            return "high", "Heavy waste detected 🗑️"
        elif score_norm > 0.15:
            return "medium", "Moderate waste detected ⚠️"
        elif score_norm > 0.08:
            return "low", "Minor waste detected ℹ️"
        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
