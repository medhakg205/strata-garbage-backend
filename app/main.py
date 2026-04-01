from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import List, Dict
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
from app.ai import predict_image
from app.auth import get_current_user
from app.utils import get_distance_matrix
import uuid  # ✅ added for unique filenames

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
    lat = round(lat, 5)
    lng = round(lng, 5)

    file_bytes = await file.read()

    # ✅ UPLOAD IMAGE TO SUPABASE
    file_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"images/{file_name}"

    upload_res = supabase.storage.from_("images").upload(
        file_path,
        file_bytes,
        {"content-type": file.content_type}
    )

    print("UPLOAD RES:", upload_res)

    public_url = supabase.storage.from_("images").get_public_url(file_path)
    print("IMAGE URL:", public_url)

    # ✅ AI prediction still same
    garbage_level, message = predict_image(file_bytes)

    if garbage_level is None:
        raise HTTPException(status_code=400, detail=message)

    # 🔍 CHECK EXISTING REPORT
    existing = supabase.rpc(
        "get_nearby_garbage_report", 
        {"scan_lat": lat, "scan_lng": lng, "dist_threshold_meters": 0.1}
    ).execute()

    if existing.data:
        report = existing.data[0]

        opened_at_str = report.get("opened_at") or report.get("reported_at")
        opened_at_dt = datetime.fromisoformat(opened_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        duration = now - opened_at_dt
        actual_pending_minutes = int(duration.total_seconds() / 60)

        new_count = (report.get("complaint_count") or 1) + 1

        new_priority = compute_priority(
            report["garbage_level"],
            new_count,
            actual_pending_minutes
        )

        supabase.table("garbage_reports") \
            .update({
                "complaint_count": new_count,
                "complaint_frequency": new_count,
                "priority_score": new_priority,
                "pending_minutes": actual_pending_minutes,
                "reported_at": now.isoformat()
            }) \
            .eq("id", report["id"]) \
            .execute()

        report_id = report["id"]
        priority_score = new_priority

    else:
        # 🆕 NEW REPORT
        now_iso = datetime.now(timezone.utc).isoformat()
        
        priority_score = compute_priority(
            garbage_level,
            complaint_count=1,
            pending_minutes=0
        )

        data = {
            "user_id": None,
            "image_url": public_url,  # ✅ FIXED (was test.jpg)
            "location": f"SRID=4326;POINT({lng} {lat})",
            "lat": lat,
            "lng": lng,
            "garbage_level": garbage_level,
            "status": "pending",
            "priority_score": priority_score,
            "complaint_frequency": 1,
            "complaint_count": 1,
            "pending_minutes": 0,
            "opened_at": now_iso,
            "reported_at": now_iso
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

# --- ROUTE OPTIMIZATION ---
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

    def create_data_model():
        return {
            'distance_matrix': [[int(d * 1000) for d in row] for row in matrix],
            'num_vehicles': 1,
            'depot': 0
        }

    data = create_data_model()
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return data['distance_matrix'][manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return {"path": [], "message": "No solution found"}

    route_indices = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route_indices.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))

    leaflet_coords = [[coords[i][1], coords[i][0]] for i in route_indices]

    total_distance = sum(matrix[route_indices[i]][route_indices[i+1]] for i in range(len(route_indices)-1))
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
