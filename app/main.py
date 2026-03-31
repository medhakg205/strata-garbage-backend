from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.ai import predict_image
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel

from app.auth import get_current_user
from app.utils import get_distance_matrix

# --- INIT ---
load_dotenv()
app = FastAPI(title="Garbage Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MODELS ---
class ReportResponse(BaseModel):
    id: str
    priority_score: float
    location: Dict[str, float]
    garbage_level: str

# --- ROUTES ---
@app.get("/health")
async def health():
    return {"status": "OK", "supabase": bool(supabase)}

@app.post("/reports/", response_model=ReportResponse, status_code=201)
async def create_report(
    lat: float = Form(...),
    lng: float = Form(...),
    file: UploadFile = File(...)
):
    # Placeholder AI (Phase 3 will replace this)
    file_bytes = await file.read()
    garbage_level, message = predict_image(file_bytes)

    if garbage_level is None:
        raise HTTPException(status_code=400, detail=message)

    data = {
        "user_id": None,
        "image_url": "test.jpg",
        "location": f"SRID=4326;POINT({lng} {lat})",
        "lat": lat,
        "lng": lng,
        "garbage_level": garbage_level,
        "status": "pending",
        "priority_score": priority_score,
        "complaint_frequency": 1,
        "reported_at": datetime.utcnow().isoformat()
    }

    resp = supabase.table("garbage_reports").insert(data).execute()
    report_id = resp.data[0]["id"]

    return ReportResponse(
        id=report_id,
        priority_score=priority_score,
        location={"lat": lat, "lng": lng},
        garbage_level=garbage_level
    )

@app.get("/reports/")
async def get_reports():
    resp = supabase.table("garbage_reports") \
        .select("id, lat, lng, garbage_level, priority_score") \
        .execute()

    return resp.data or []

# 🚀 PHASE 2: REAL ROUTE OPTIMIZATION
@app.get("/optimize-route/")
async def optimize_route(user=Depends(get_current_user)):

    # --- AUTH CHECK ---
    if user["role"] != "collector":
        raise HTTPException(status_code=403, detail="Access denied")

    # --- FETCH REPORTS ---
    reports = supabase.table("garbage_reports") \
        .select("*") \
        .neq("status", "completed") \
        .order("priority_score", desc=True) \
        .limit(8) \
        .execute().data

    if not reports:
        return {"path": [], "message": "No reports"}

    # --- COORDINATES (IMPORTANT: [lng, lat]) ---
    coords = [[r["lng"], r["lat"]] for r in reports]

    # --- DISTANCE MATRIX ---
    matrix = get_distance_matrix(coords)

    # --- NEAREST NEIGHBOR ROUTE ---
    n = len(coords)
    visited = [False] * n
    route_indices = [0]
    visited[0] = True

    for _ in range(n - 1):
        last = route_indices[-1]

        next_city = min(
            [i for i in range(n) if not visited[i]],
            key=lambda i: matrix[last][i]
        )

        route_indices.append(next_city)
        visited[next_city] = True

    # --- CONVERT BACK TO LEAFLET FORMAT [lat, lng] ---
    leaflet_coords = [
        [coords[i][1], coords[i][0]]
        for i in route_indices
    ]

    # --- CALCULATE DISTANCE ---
    total_distance = 0
    for i in range(len(route_indices) - 1):
        total_distance += matrix[route_indices[i]][route_indices[i + 1]]

    # --- ESTIMATE TIME ---
    total_duration = total_distance * 2  # ~30 km/h assumption

    # --- SAVE ROUTE ---
    supabase.table("routes").insert({
        "collector_id": user["id"],
        "report_ids": [reports[i]["id"] for i in route_indices],
        "optimized_path": leaflet_coords
    }).execute()

    # --- RESPONSE ---
    return {
        "path": leaflet_coords,
        "total_spots": len(leaflet_coords),
        "distance_km": f"{total_distance:.2f}",
        "duration_min": f"{int(total_duration)}"
    }
