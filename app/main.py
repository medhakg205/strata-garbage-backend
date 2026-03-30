import os
from datetime import datetime
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv

# OR-Tools for route optimization
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# --- LOCAL IMPORTS ---
from .models import ReportResponse
from .auth import get_current_user
from .utils import get_distance_matrix
from .ai import predict_image

# Load environment variables
load_dotenv()

app = FastAPI(title="Garbage Backend")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- SUPABASE CLIENT ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================================
# 🚀 CREATE REPORT
# =========================================================
@app.post("/reports/", response_model=ReportResponse, status_code=201)
async def create_report(
    lat: float = Form(...),
    lng: float = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    file_content = await file.read()

    # AI Prediction
    garbage_level, _ = predict_image(file_content)

    if garbage_level is None:
        return ReportResponse(
            id="not-garbage",
            priority_score=0,
            location={"lat": lat, "lng": lng},
            garbage_level="none",
            message="Not garbage ❌"
        )

    image_url = "test-url"

    # Check for existing nearby reports (~50m radius)
    RADIUS = 0.0005
    existing = supabase.table("garbage_reports") \
        .select("*") \
        .gte("lat", lat - RADIUS) \
        .lte("lat", lat + RADIUS) \
        .gte("lng", lng - RADIUS) \
        .lte("lng", lng + RADIUS) \
        .neq("status", "completed") \
        .execute()

    level_score = {"low": 1, "medium": 2, "high": 3}

    # Case 1: Existing report → UPDATE
    if existing.data:
        report = existing.data[0]
        new_count = (report.get("complaint_frequency") or 1) + 1
        pending_minutes = report.get("pending_minutes") or 0
        hours_since = pending_minutes / 60

        priority_score = (
            level_score.get(garbage_level, 0) * 3 +
            new_count * 2 +
            int(hours_since)
        )

        supabase.table("garbage_reports") \
            .update({
                "complaint_frequency": new_count,
                "garbage_level": garbage_level,
                "priority_score": priority_score
            }) \
            .eq("id", report["id"]) \
            .execute()

        report_id = report["id"]

    # Case 2: New report → INSERT
    else:
        priority_score = level_score.get(garbage_level, 0) * 3 + 2
        data = {
            "user_id": current_user["id"],
            "image_url": image_url,
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
        if not resp.data:
            raise HTTPException(500, "Database insertion failed")

        report_id = resp.data[0]["id"]

    return ReportResponse(
        id=report_id,
        priority_score=priority_score,
        location={"lat": lat, "lng": lng},
        garbage_level=garbage_level
    )


# =========================================================
# 📄 GET ALL REPORTS (Collector Only)
# =========================================================
@app.get("/reports/", response_model=List[ReportResponse])
async def get_all_reports(current_user=Depends(get_current_user)):
    if current_user.get("role") != "collector":
        raise HTTPException(403, "Access denied. Only collectors can view all reports.")

    resp = supabase.table("garbage_reports").select(
        "id, location, garbage_level, priority_score"
    ).execute()

    if not resp.data:
        return []

    formatted_reports = []
    for report in resp.data:
        loc_str = report["location"]
        try:
            coords = loc_str.replace("POINT(", "").replace(")", "").split()
            lng, lat = float(coords[0]), float(coords[1])
        except Exception:
            lat, lng = 0.0, 0.0

        formatted_reports.append({
            "id": report["id"],
            "location": {"lat": lat, "lng": lng},
            "garbage_level": report["garbage_level"],
            "priority_score": report["priority_score"]
        })

    return formatted_reports


# =========================================================
# 🧭 OPTIMIZE ROUTE
# =========================================================
@app.get("/optimize-route/")
async def optimize_route(current_user=Depends(get_current_user)):
    if current_user.get("role") != "collector":
        raise HTTPException(403, "Collector only")

    resp = supabase.table("garbage_reports") \
        .select("*") \
        .neq("status", "completed") \
        .execute()

    if not resp.data:
        return {"path": [], "message": "No reports"}

    updated_reports = []
    level_score = {"low": 1, "medium": 2, "high": 3}

    # Recalculate priority
    for r in resp.data:
        pending_minutes = r.get("pending_minutes") or 0
        hours_since = pending_minutes / 60
        complaint_count = r.get("complaint_frequency") or 1

        priority = (
            level_score.get(r.get("garbage_level"), 0) * 3 +
            complaint_count * 2 +
            int(hours_since)
        )

        supabase.table("garbage_reports") \
            .update({"priority_score": priority}) \
            .eq("id", r["id"]) \
            .execute()

        r["priority_score"] = priority
        updated_reports.append(r)

    # Filter high-priority reports
    reports = [r for r in updated_reports if r["priority_score"] >= 5]

    if len(reports) < 2:
        return {"path": [], "message": "Insufficient high-priority reports"}

    # Get valid coordinates
    coords = []
    report_ids = []
    for r in reports:
        lat = r.get("lat")
        lng = r.get("lng")
        if lat is None or lng is None:
            continue
        coords.append([lng, lat])
        report_ids.append(r["id"])

    if len(coords) < 2:
        return {"path": [], "message": "Insufficient valid coordinates"}

    dist_matrix = get_distance_matrix(coords)

    manager = pywrapcp.RoutingIndexManager(len(coords), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def dist_cb(from_idx, to_idx):
        return int(dist_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)] * 1000)

    transit_cb = routing.RegisterTransitCallback(dist_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(params)

    path = []
    if solution:
        idx = routing.Start(0)
        while not routing.IsEnd(idx):
            path.append(coords[manager.IndexToNode(idx)])
            idx = solution.Value(routing.NextVar(idx))
    else:
        path = coords

    # Insert route into DB
    supabase.table("routes").insert({
        "collector_id": current_user["id"],
        "report_ids": report_ids,
        "optimized_path": path
    }).execute()

    return {"path": path, "total_spots": len(path)}
