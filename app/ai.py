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

# Expanded and corrected waste-related ImageNet classes
WASTE_CLASSES = {
    440,  # beer bottle
    441,  # beer glass
    463,  # bucket
    530,  # garbage truck
    720,  # plastic bag
    728,  # pop bottle
    478,  # carton
    700,  # paper towel
    822,  # toilet tissue
    849,  # tray
    790,  # steel drum
    753,  # radiator
    671,  # oil filter
    569,  # freight car
    412,  # ashcan / trash can ← KEY ONE
    436,  # barn (outdoor clutter)
    468,  # cab (street scene)
    475,  # car wheel
    480,  # chain
    494,  # crate ← KEY ONE
    519,  # file cabinet
    532,  # gas pump
    545,  # dome (industrial)
    580,  # grille
    609,  # lawn mower
    660,  # mixing bowl
    681,  # oil drum ← KEY ONE
    703,  # park bench (outdoor)
    716,  # pickup truck
    734,  # pot
    757,  # rubber eraser
    779,  # screw
    783,  # shovel ← KEY ONE
    800,  # ski
    833,  # traffic cone ← KEY ONE  
    864,  # tub
    867,  # typewriter keyboard
    897,  # washer
    # Textures that appear in waste scenes
    992,  # hay (organic waste texture)
}

# Classes that strongly suggest clean/natural scenes
CLEAN_CLASSES = {
    # Clean nature
    970, 971, 972, 973, 974, 975, 976, 977, 978, 979, 980,
    # Clean food
    924, 925, 926, 927, 928, 929, 930, 931, 932,
    # Clean interiors / animals
    560, 762, 587, 
    # Sky / water
    978, 979,
    # People in clean settings
    200, 201, 202,
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

        top1_prob = top10_probs[0]
        top1_idx = top10_idx[0]

        # --- Score components ---

        # 1. Confusion: model can't identify a clear subject
        confusion_score = 1.0 - top1_prob

        # 2. Waste class hits across top 10
        waste_score = sum(probs[i].item() for i in top10_idx if i in WASTE_CLASSES)

        # 3. Clean class penalty
        clean_score = sum(probs[i].item() for i in top10_idx if i in CLEAN_CLASSES)

        # 4. Entropy of top 10 — high entropy = many competing guesses = cluttered scene
        top10_tensor = torch.tensor(top10_probs)
        top10_tensor = top10_tensor / top10_tensor.sum()  # renormalize
        entropy = -torch.sum(top10_tensor * torch.log(top10_tensor + 1e-9)).item()
        entropy_score = entropy / 2.3  # normalize: log(10)=2.3, so max=1.0

        # 5. Hard boost: if top1 class is directly waste-related
        direct_waste_boost = 0.3 if top1_idx in WASTE_CLASSES else 0.0

        final_score = (
            confusion_score  * 0.35 +
            waste_score      * 0.25 +
            entropy_score    * 0.30 +
            direct_waste_boost
        ) - (clean_score * 0.25)

        print(f"top1_idx={top1_idx} top1_prob={top1_prob:.3f}")
        print(f"confusion={confusion_score:.3f} waste={waste_score:.3f} "
              f"clean={clean_score:.3f} entropy={entropy_score:.3f} "
              f"direct_boost={direct_waste_boost:.1f} final={final_score:.3f}")

        if final_score > 0.65:
            return "high", "Heavy waste detected 🗑️"
        elif final_score > 0.45:
            return "medium", "Moderate waste detected ⚠️"
        elif final_score > 0.28:
            return "low", "Minor waste detected ℹ️"
        else:
            return None, "Not garbage ❌"

    except Exception as e:
        print("AI ERROR:", e)
        return None, "Not garbage ❌"
