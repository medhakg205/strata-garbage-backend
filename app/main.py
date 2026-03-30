import os
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
import sys
import os

# Ensure the local 'ai' module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from ai.gemini_predict import analyze_garbage_image
except ImportError:
    pass

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- TEST ROUTE ----------------
@app.get("/")
def test():
    return {"status": "working"}

# ---------------- REPORT ----------------
@app.post("/reports/")
async def create_report(file: UploadFile, lat: float, lng: float):
    try:
        print("Received request")

        import uuid
        
        content = await file.read()
        
        # 1. Generate a unique filename to prevent overwrite conflicts
        file_ext = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"

        # 2. Upload to Supabase Storage Bucket ('garbage_images')
        print("Uploading to Supabase Storage...")
        supabase.storage.from_("garbage_images").upload(
            path=unique_filename,
            file=content,
            file_options={"content-type": file.content_type}
        )
        
        # 3. Retrieve the generated public URL for the image
        image_url = supabase.storage.from_("garbage_images").get_public_url(unique_filename)
        print("Image URL generated:", image_url)

        # 4. Use Gemini AI to determine severity
        print("Analyzing with Gemini AI...")
        try:
            garbage_level = analyze_garbage_image(content)
        except Exception as e:
            print("AI classification failed, falling back to medium:", str(e))
            garbage_level = "medium"

        print(f"Assigned level: {garbage_level}")

        if garbage_level == "not_garbage":
            return {"message": "Not garbage ❌", "level": None}

        print("Inserting into Supabase...")

        res = supabase.table("garbage_reports").insert({
    "image_url": image_url,
    "lat": lat,
    "lng": lng,
    "garbage_level": garbage_level,

    # 👇 REQUIRED FOR SUPABASE
    "location": f"POINT({lng} {lat})"
}).execute()

        print("Insert response:", res)

        return {"message": "stored", "level": garbage_level}

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}

# ---------------- ROUTE ----------------
@app.get("/optimize-route/")
def optimize_route():
    try:
        response = supabase.table("garbage_reports").select("*").execute()
        data = response.data

        if not data:
            return {"total_spots": 0, "optimized_path": []}

        points = []

        for r in data:
            if r.get("lat") is None or r.get("lng") is None:
                continue

            points.append([r["lng"], r["lat"]])

        return {
            "total_spots": len(points),
            "optimized_path": points
        }

    except Exception as e:
        return {"error": str(e)}