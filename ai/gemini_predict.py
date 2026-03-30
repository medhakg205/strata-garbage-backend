import os
import google.generativeai as genai
from io import BytesIO
from PIL import Image

def analyze_garbage_image(image_bytes: bytes) -> str:
    """
    Sends the image to Gemini 1.5 Flash to determine if it is garbage
    and what priority level it should be assigned.
    Returns: 'high', 'medium', 'low', or 'not_garbage'.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("WARNING: GEMINI_API_KEY is not set. Falling back to 'medium'.")
        return "medium"

    genai.configure(api_key=gemini_key)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # We need to convert bytes to a PIL image so generative AI module handles it easily
        img = Image.open(BytesIO(image_bytes))

        # Prompt
        prompt = (
            "You are a smart waste classification assistant. Look at this image "
            "and determine if it contains garbage or waste that needs to be collected. "
            "If it DOES NOT contain any obvious garbage or waste, reply strictly with 'not_garbage'. "
            "If it DOES contain garbage, assess the severity (amount, toxicity, messiness) "
            "and reply strictly with exactly one of these words: 'high', 'medium', or 'low'. "
            "Do not include any other text."
        )

        response = model.generate_content([prompt, img])
        text = response.text.strip().lower()

        # Sanitize response
        if "high" in text: return "high"
        elif "medium" in text: return "medium"
        elif "low" in text: return "low"
        else: return "not_garbage"

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "medium" # Fallback so the app doesn't crash
