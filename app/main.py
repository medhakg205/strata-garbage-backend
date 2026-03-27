import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from dotenv import load_dotenv
from typing import List

# --- LOCAL IMPORTS ---
from models import ReportResponse, GarbageLevel
from auth import get_current_user
from utils import get_distance_matrix

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

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
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/reports/", response_model=ReportResponse, status_code=201)
async def create_report(
    lat: float, 
    lng: float, 
    file: UploadFile = File(...), 
    garbage_level: GarbageLevel = "medium", 
    current_user=Depends(get_current_user)
):
    # 1. Read the file content into memory IMMEDIATELY
    file_content = await file.read()
    file_ext = file.filename.split(".")[-1]
    storage_path = f"images/{uuid.uuid4()}.{file_ext}"
    
    try:
        # FIX: Pass 'file_content' (the bytes), NOT the 'file' object.
        # Also, specify the content-type from the UploadFile object.
        supabase.storage.from_("images").upload(
            path=storage_path, 
            file=file_content, # Pass the bytes here
            file_options={"content-type": file.content_type}
        )
    except Exception as e:
        print(f"Storage Error: {e}")
        raise HTTPException(500, f"Image upload failed: {str(e)}")
        
    # ... rest of your code ...
        
    # Get Public URL (Handling potential different return types from SDK)
    res = supabase.storage.from_("images").get_public_url(storage_path)
    image_url = res if isinstance(res, str) else res.get("publicURL") or res.get("public_url")
    
    # 2. Insert report
    data = {
        "user_id": current_user["id"],  # Dictionary syntax
        "image_url": image_url,
        "location": f"POINT({lng} {lat})", # Geography format
        "garbage_level": garbage_level,
        "status": "pending",
        "priority_score": 0,
        "reported_at": datetime.utcnow().isoformat()
    }
    
    resp = supabase.table("garbage_reports").insert(data).execute()
    
    if not resp.data:
        raise HTTPException(500, "DB insert failed")
    
    report = resp.data[0]
    
    return ReportResponse(
        id=report["id"],
        priority_score=report.get("priority_score", 0),
        location={"lat": lat, "lng": lng},
        garbage_level=report["garbage_level"]
    )
@app.get("/reports/", response_model=List[ReportResponse])
async def get_all_reports(current_user=Depends(get_current_user)):
    # 1. Role-based Access Control (RBAC)
    # Checking if the user dict has the 'collector' role
    if current_user.get("role") != "collector":
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only collectors can view all reports."
        )

    # 2. Fetch reports from Supabase
    # We select the fields requested in your teammate's screenshot
    # 'location' in Supabase (PostGIS) usually returns as 'POINT(lng lat)'
    resp = supabase.table("garbage_reports").select(
        "id, location, garbage_level, priority_score"
    ).execute()

    if not resp.data:
        return []

    # 3. Format data to match the teammate's expected response format
    formatted_reports = []
    for report in resp.data:
        # Simple parser for "POINT(lng lat)" string if returned as text
        # If your RPC/SQL returns coordinates differently, adjust this part
        loc_str = report["location"] 
        # Example: "POINT(12.34 56.78)" -> [12.34, 56.78]
        try:
            coords = loc_str.replace("POINT(", "").replace(")", "").split()
            lng, lat = float(coords[0]), float(coords[1])
        except (ValueError, AttributeError):
            lat, lng = 0.0, 0.0

        formatted_reports.append({
            "id": report["id"],
            "location": {"lat": lat, "lng": lng},
            "garbage_level": report["garbage_level"],
            "priority_score": report["priority_score"]
        })

    return formatted_reports
@app.get("/optimize-route/")
async def optimize_route(current_user=Depends(get_current_user)):
    # Fix: current_user is a dict
    if current_user.get("role") != "collector":
        raise HTTPException(403, "Collector only")
    
    resp = supabase.table("garbage_reports").select("id, location, priority_score").gte("priority_score", 5).execute()
    reports = resp.data
    if not reports or len(reports) < 2:
        return {"path": [], "message": "Insufficient reports"}
    
    coords_query = supabase.rpc("get_coords", {"report_ids": [r["id"] for r in reports]}).execute()
    coords = [[row["lng"], row["lat"]] for row in coords_query.data]
    
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
    
    supabase.table("routes").insert({
        "collector_id": current_user["id"], # Dictionary syntax
        "report_ids": [r["id"] for r in reports],
        "optimized_path": path
    }).execute()
    
    return {"path": path, "total_spots": len(path)}