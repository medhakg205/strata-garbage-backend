from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from supabase import create_client, Client

from app.ai import predict_image
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
    allow_headers=["*"],
)

# --- SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing Supabase environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- PRIORITY FUNCTION ---
def compute_priority(level, complaint_count, pending_minutes):
    level_score = {
        "low": 1,
        "medium": 2,
        "high": 3
    }[level]

    # cap time to prevent runaway growth
    time_component = min(pending_minutes or 0, 120)

    return (
        3 * level_score +
        2 * complaint_count +
        time_component
    )

# --- MODELS ---
class ReportResponse(BaseModel):
    id: str
    priority_score: float
    location: Dict[str, float]
    garbage_level: str

# --- HEALTH CHECK ---
@app.get("/health")
async def health():
    return {"status": "OK"}

# --- CREATE REPORT ---
@app.post("/reports/", response_model=ReportResponse, status_code=201)
async def create_report(
    lat: float = Form(...),
    lng: float = Form(...),
    file: UploadFile = File(...)
):
    # 🔧 normalize coords (prevents float mismatch)
    lat = round(lat, 5)
    lng = round(lng, 5)

    file_bytes = await file.read()
    garbage_level, message = predict_image(file_bytes)

    if garbage_level is None:
        raise HTTPException(status_code=400, detail=message)

    # 🔍 CHECK EXISTING REPORT
    existing = supabase.table("garbage_reports") \
        .select("*") \
        .eq("lat", lat) \
        .eq("lng", lng) \
        .neq("status", "completed") \
        .limit(1) \
        .execute()

    if existing.data:
        report = existing.data[0]

        new_count = (report.get("complaint_count") or 1) + 1

        new_priority = compute_priority(
            report["garbage_level"],
            new_count,
            report.get("pending_minutes", 0)
        )

        supabase.table("garbage_reports") \
            .update({
                "complaint_count": new_count,
                "priority_score": new_priority,
                "reported_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", report["id"]) \
            .execute()

        report_id = report["id"]
        priority_score = new_priority

    else:
        # 🆕 NEW REPORT
        priority_score = compute_priority(
            garbage_level,
            complaint_count=1,
            pending_minutes=0
        )

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
            "complaint_count": 1,
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

# --- GET REPORTS ---
@app.get("/reports/")
async def get_reports():
    resp = supabase.table("garbage_reports") \
        .select("id, lat, lng, garbage_level, priority_score") \
        .execute()

    return resp.data or []

# --- ROUTE OPTIMIZATION (AUTH PROTECTED) ---
@app.get("/optimize-route/")
async def optimize_route(user=Depends(get_current_user)):

    if user["role"] != "collector":
        raise HTTPException(status_code=403, detail="Access denied")

    reports = supabase.table("garbage_reports") \
        .select("*") \
        .neq("status", "completed") \
        .order("priority_score", desc=True) \
        .limit(8) \
        .execute().data

    if not reports:
        return {"path": [], "message": "No reports"}

    coords = [[r["lng"], r["lat"]] for r in reports]
    matrix = get_distance_matrix(coords)

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

    leaflet_coords = [[coords[i][1], coords[i][0]] for i in route_indices]

    total_distance = sum(
        matrix[route_indices[i]][route_indices[i + 1]]
        for i in range(len(route_indices) - 1)
    )

    total_duration = total_distance * 2

    supabase.table("routes").insert({
        "collector_id": user["id"],
        "report_ids": [reports[i]["id"] for i in route_indices],
        "optimized_path": leaflet_coords
    }).execute()

    return {
        "path": leaflet_coords,
        "total_spots": len(leaflet_coords),
        "distance_km": f"{total_distance:.2f}",
        "duration_min": f"{int(total_duration)}"
    }
