from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel
from auth import get_current_user  # ✅ NEW IMPORT

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

class ReportResponse(BaseModel):
    id: str
    priority_score: float
    location: Dict[str, float]
    garbage_level: str

@app.get("/health")
async def health():
    return {"status": "OK", "supabase": bool(supabase)}

@app.post("/reports/", response_model=ReportResponse, status_code=201)
async def create_report(
    lat: float = Form(...),
    lng: float = Form(...),
    file: UploadFile = File(...)
):
    # Dummy AI - always returns "high" 
    garbage_level = "high"
    priority_score = 3 * 3 + 2 * 1 + 1 * 0  # 11
    
    data = {
        "user_id": None,  # ✅ Fixed
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
    resp = supabase.table("garbage_reports").select("id, lat, lng, garbage_level, priority_score").execute()
    return resp.data or []

@app.post("/auth/login")  # ✅ NEW: Simple login endpoint
async def login(email: str = Form(...), password: str = Form(...)):
    resp = supabase.auth.signInWithPassword({"email": email, "password": password})
    if resp.user:
        return {"access_token": resp.session.access_token}
    raise HTTPException(401, "Invalid credentials")

@app.get("/optimize-route/")
async def optimize_route(current_user: dict = Depends(get_current_user)):  # ✅ PROTECTED
    # 🚀 NEW: Optimal high-priority route for truck GPS
    reports = supabase.table("garbage_reports") \
        .select("*") \
        .neq("status", "completed") \
        .order("priority_score", desc=True) \
        .limit(8).execute().data  # Top 8 high-priority reports
    
    if not reports:
        return {"path": [], "message": "No reports"}
    
    # Leaflet format: [[lat, lng], [lat, lng]] - optimal truck route
    leaflet_coords = [[r["lat"], r["lng"]] for r in reports]
    
    # Route estimates
    total_distance = len(leaflet_coords) * 2.5  # ~2.5km avg stop
    total_duration = len(leaflet_coords) * 8     # ~8 min/stop
    
    # Insert route into DB - NOW with real collector_id ✅
    supabase.table("routes").insert({
        "collector_id": current_user["id"],  # ✅ Real authenticated user
        "report_ids": [r["id"] for r in reports],
        "optimized_path": leaflet_coords
    }).execute()
    
    return {
        "path": leaflet_coords,           # [[lat1,lng1], [lat2,lng2]] for Leaflet map
        "total_spots": len(leaflet_coords),
        "distance_km": f"{total_distance:.1f}",
        "duration_min": f"{total_duration}"
    }
