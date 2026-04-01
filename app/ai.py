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

        # --- Compute "complexity score" ---
        mean_val = np.mean(features)
        std_val = np.std(features)

        score = std_val / (mean_val + 1e-5)

        # --- Classification ---
        if score > 2.5:
            return "high", "Heavy waste detected 🗑️"
        elif score > 1.5:
            return "medium", "Moderate waste detected ⚠️"
        elif score > 0.8:
            return "low", "Minor waste detected ℹ️"
        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
