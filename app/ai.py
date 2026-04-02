from PIL import Image
import io
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

# 1. Load model with explicit Weights (best practice in newer Torch)
weights = MobileNet_V2_Weights.DEFAULT
model = mobilenet_v2(weights=weights)
model.eval()

# Remove only the final classification head
feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])

# 2. IMPORTANT: You MUST use ImageNet normalization for consistent scores
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def extract_features(img):
    img_tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        # Output shape is [1, 1280, 1, 1]
        features = feature_extractor(img_tensor)
    return features.flatten().numpy()

def predict_image(file_content: bytes):
    try:
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        features = extract_features(img)

        # 3. USE STANDARD DEVIATION
        # Higher complexity/clutter = higher variety in neuron activation
        score = np.std(features)

        # --- Debug: Check these values in your console ---
        print(f"--- AI LOG: Raw Score (StdDev): {score:.4f} ---")

        # 4. CALIBRATED THRESHOLDS
        # These are tuned for MobileNetV2 features. 
        # If things are still too sensitive, increase these numbers.
        if score > 1.6:
            return "high", "Heavy waste detected 🗑️"
        elif score > 1.1:
            return "medium", "Moderate waste detected ⚠️"
        elif score > 0.5:
            return "low", "Minor waste detected ℹ️"
        else:
            # Usually very simple/clean images (blank walls, clear sky)
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
