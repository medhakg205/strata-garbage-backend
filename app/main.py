import os
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv

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

        # save file
        file_path = f"temp_{file.filename}"
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        print("File saved")

        # simple fixed level (NO AI = NO CRASH)
        garbage_level = "medium"

        print("Inserting into Supabase...")

        res = supabase.table("garbage_reports").insert({
    "image_url": file.filename,
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
def optimize_route(lat: float, lng: float):
    try:
        response = supabase.table("garbage_reports").select("*").execute()
        data = response.data

        if not data:
            return {"total_spots": 0, "optimized_path": []}

        points = []

        for r in data:
            if r.get("lat") is None or r.get("lng") is None:
                continue

            points.append({
                "coord": [r["lng"], r["lat"]],
                "level": r.get("garbage_level", "medium")
            })

        return {
            "total_spots": len(points),
            "optimized_path": points
        }

    except Exception as e:
        return {"error": str(e)}