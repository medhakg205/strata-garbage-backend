
import os
import uuid
import re
from datetime import datetime, timezone
from ai.predict import predict_image   # import your AI

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv



# ---------------- SETUP ----------------
load_dotenv()

app = FastAPI(title="Smart Waste Backend")

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

# ---------------- 1. CREATE REPORT ----------------


@app.post("/reports/")
async def create_report(file: UploadFile, lat: float, lng: float):

    # Save file locally (temp)
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # 🔥 RUN AI
    ai_result = predict_image(file_location)

    # 🔥 CLASSIFY
    if ai_result == 2:
        garbage_level = "high"
    elif ai_result == 1:
        garbage_level = "medium"
    else:
        return {"message": "Not garbage"}

    # 🔥 SAVE TO SUPABASE
    data = supabase.table("garbage_reports").insert({
        "image_url": file.filename,
        "location": f"POINT({lng} {lat})",
        "garbage_level": garbage_level
    }).execute()

    return {"message": "Report stored", "level": garbage_level}

# ---------------- 2. OPTIMIZE ROUTE ----------------
@app.get("/optimize-route/")
def optimize_route(lat: float, lng: float):
    try:
        response = supabase.table("garbage_reports").select("*").execute()
        reports = response.data

        if not reports:
            return {"total_spots": 0, "optimized_path": []}

        points = []

        for r in reports:
            loc = r.get("location")

            if not loc:
                continue

            try:
                if isinstance(loc, dict):
                    lng_val = loc["coordinates"][0]
                    lat_val = loc["coordinates"][1]
                else:
                    continue
            except:
                continue

            level = r.get("garbage_level", "medium")
            score = 3 if level == "high" else 2 if level == "medium" else 1

            points.append({
                "id": r["id"],
                "coord": [lng_val, lat_val],
                "level": level,
                "score": score
            })

        if not points:
            return {"total_spots": 0, "optimized_path": []}

        # 🔥 SMART ROUTE
        current = [lng, lat]
        route = []
        remaining = points.copy()

        while remaining:
            next_point = min(
                remaining,
                key=lambda p: (
                    ((p["coord"][0] - current[0]) ** 2 +
                     (p["coord"][1] - current[1]) ** 2) ** 0.5
                    - p["score"] * 0.01
                )
            )

            route.append(next_point)
            current = next_point["coord"]
            remaining.remove(next_point)

        return {
            "total_spots": len(route),
            "optimized_path": route
        }

    except Exception as e:
        return {"error": str(e)}

# ---------------- 3. AI UPDATE ----------------
@app.patch("/internal/ai-update/{report_id}")
async def ai_update(report_id: str, ai_level: str):
    supabase.table("garbage_reports").update({
        "garbage_level": ai_level
    }).eq("id", report_id).execute()

    return {"status": "updated"}
