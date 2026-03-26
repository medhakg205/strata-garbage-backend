import numpy as np
from PIL import Image
from tensorflow.keras.applications.mobilenet import MobileNet, preprocess_input, decode_predictions

model = MobileNet(weights="imagenet")

def predict_image(img_path):
    img = Image.open(img_path).resize((224, 224))
    img_array = np.array(img)

    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    preds = model.predict(img_array)
    decoded = decode_predictions(preds, top=1)[0][0]

    label = decoded[1]
    confidence = decoded[2]

    if "trash" in label or "garbage" in label or "dustbin" in label:
        return 2
    elif confidence > 0.5:
        return 1
    else:
        return 0