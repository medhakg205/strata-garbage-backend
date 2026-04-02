from PIL import Image
import io
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

weights = MobileNet_V2_Weights.DEFAULT
model = mobilenet_v2(weights=weights)
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# ImageNet indices that relate to waste, clutter, or dirty environments
# You can expand this list — full list at: https://gist.github.com/yrevar/942d3a0ac09ec9e5eb3a
WASTE_CLASSES = {
    401,  # accordion (clutter)
    408,  # amphibian
    440,  # beer bottle
    441,  # beer glass
    463,  # bucket
    530,  # garbage truck
    720,  # plastic bag
    728,  # pop bottle
    737,  # punching bag
    757,  # rubber eraser
    790,  # steel drum
    822,  # toilet tissue
    849,  # tray
    897,  # washer
    # Outdoor/dirty scenes
    478,  # carton
    555,  # fire screen
    569,  # freight car
    609,  # lawn mower
    671,  # oil filter
    700,  # paper towel
    753,  # radiator
    876,  # washer
}

# Classes that strongly suggest a CLEAN scene — penalize waste score
CLEAN_CLASSES = {
    # nature
    970, 971, 972, 973, 974, 975, 976, 977, 978, 979, 980,  # various natural scenes
    # food (plated, clean)
    924, 925, 926, 927, 928, 929, 930, 931, 932,
    # interiors
    560, 762, 587,
}

def predict_image(file_content: bytes):
    try:
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            logits = model(tensor)
            probs = F.softmax(logits, dim=1)[0]

        top10_result = torch.topk(probs, 10)
        top10_idx = top10_result.indices.tolist()
        top10_probs = top10_result.values.tolist()

        # Debug — keep this on while tuning
        print("Top 10 predictions:")
        for idx, prob in zip(top10_idx, top10_probs):
            print(f"  Class {idx}: {prob:.4f}")

        top1_prob = top10_probs[0]

        # Low top-1 confidence = model is confused = likely cluttered/messy scene
        confusion_score = 1.0 - top1_prob

        # Explicit waste class hits
        waste_score = sum(
            probs[i].item() for i in top10_idx if i in WASTE_CLASSES
        )

        # Penalize if clean classes dominate
        clean_score = sum(
            probs[i].item() for i in top10_idx if i in CLEAN_CLASSES
        )

        final_score = (confusion_score * 0.6) + (waste_score * 0.4) - (clean_score * 0.3)

        print(f"confusion={confusion_score:.3f} waste={waste_score:.3f} clean={clean_score:.3f} final={final_score:.3f}")

        if final_score > 0.75:
            return "high", "Heavy waste detected 🗑️"
        elif final_score > 0.55:
            return "medium", "Moderate waste detected ⚠️"
        elif final_score > 0.35:
            return "low", "Minor waste detected ℹ️"
        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
