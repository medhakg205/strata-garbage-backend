import os
from ai.predict import predict_image
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from supabase import create_client, Client
import uuid
from datetime import datetime
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from .models import ReportCreate, ReportResponse, GarbageLevel
from .auth import get_current_user
from .utils import get_distance_matrix

app = FastAPI(title="Garbage Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

@app.post("/reports/", response_model=ReportResponse, status_code=201)
async def create_report(
    lat: float, 
    lng: float, 
    file: UploadFile = File(...), 
    garbage_level: GarbageLevel = "medium", 
    current_user=Depends(get_current_user)
):
    # Upload image
    file_ext = file.filename.split(".")[-1]
    path = f"images/{uuid.uuid4()}.{file_ext}"
    with open(file.filename, "wb") as f:
        f.write(await file.read())
    
    pred = predict_image(file.filename)

    level_map = {0: "low", 1: "medium", 2: "high"}
    garbage_level = level_map[pred]
    supabase.storage.from_("images").upload(path, open(file.filename, "rb"))
    image_url = supabase.storage.from_("images").get_public_url(path)["publicUrl"]
    
    # Insert report
    data = {
        "user_id": current_user.id,
        "image_url": image_url,
        "location": f"POINT({lng} {lat})",
        "garbage_level": garbage_level,
        "reported_at": datetime.utcnow()
    }
    resp = supabase.table("garbage_reports").insert(data).execute()
    if not resp.data:
        raise HTTPException(500, "DB insert failed")
    
    report = resp.data[0]
    
    return ReportResponse(
        id=report["id"],
        priority_score=report["priority_score"],
        location={"lat": lat, "lng": lng},
        garbage_level=report["garbage_level"]
    )

@app.get("/optimize-route/")
async def optimize_route(current_user=Depends(get_current_user)):
    if current_user.user_metadata.get("role") != "collector":
        raise HTTPException(403, "Collector only")
    
    resp = supabase.table("garbage_reports").select("id, location, priority_score").gte("priority_score", 5).execute()
    reports = resp.data
    if len(reports) < 2:
        return {"path": [], "message": "Insufficient reports"}
    
    coords_query = supabase.rpc("get_coords", {"report_ids": [r["id"] for r in reports]}).execute()
    coords = [[row["lng"], row["lat"]] for row in coords_query.data]
    
    dist_matrix = get_distance_matrix(coords)
    
    manager = pywrapcp.RoutingIndexManager(len(coords), 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    
    def dist_cb(from_idx, to_idx):
        from_n = manager.IndexToNode(from_idx)
        to_n = manager.IndexToNode(to_idx)
        return int(dist_matrix[from_n][to_n] * 1000)
    
    transit_cb = routing.RegisterTransitCallback(dist_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(params)
    
    if solution:
        idx = routing.Start(0)
        path = []
        while not routing.IsEnd(idx):
            path.append(coords[manager.IndexToNode(idx)])
            idx = solution.Value(routing.NextVar(idx))
    else:
        path = coords
    
    supabase.table("routes").insert({
        "collector_id": current_user.id,
        "report_ids": [r["id"] for r in reports],
        "optimized_path": path
    }).execute()
    
    return {"path": path, "total_spots": len(path)}

@app.get("/health")
def health():
    return {"status": "ok"}