import os
import uuid
from datetime import datetime, timezone
from typing import List
from ai.predict import classify_waste
from ai.predict import predict_image 
from app.utils import get_distance_matrix

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from dotenv import load_dotenv

# --- LOCAL IMPORTS ---
try:
    from .models import ReportResponse, GarbageLevel
    from .auth import get_current_user
    from .utils import get_distance_matrix
except ImportError:
    from models import ReportResponse, GarbageLevel
    from auth import get_current_user
    from utils import get_distance_matrix

load_dotenv()
app = FastAPI(title="Garbage Backend - Full System")

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

# ---------------- HELPER: PRIORITY ----------------
def calculate_priority_score(report):
    try:
        level_map = {"high": 3, "medium": 2, "low": 1}
        base_score = level_map.get(report.get("garbage_level", "low"), 1)
        complaints = report.get("complaint_count", 1) or 1
        
        raw_time = report.get("reported_at")
        hours_pending = 0
        if raw_time:
            reported_at = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
            hours_pending = (datetime.now(timezone.utc) - reported_at).total_seconds() / 3600
            
        return max(1, base_score + complaints + int(hours_pending))
    except:
        return 1

# ---------------- 1. CREATE REPORT (WITH DUPLICATE CHECK) ---------------
@app.post("/reports/", response_model=ReportResponse, status_code=201)
async def create_report(
    lat: float = Form(...),
    lng: float = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    # ---------------- SAVE TEMP FILE ----------------
    file_content = await file.read()
    temp_path = f"temp_{uuid.uuid4()}.jpg"

    with open(temp_path, "wb") as f:
        f.write(file_content)

    # ---------------- AI CLASSIFICATION ----------------
    result = classify_waste(temp_path)

    # ❌ If not garbage → reject
    if not result["is_garbage"]:
        return {"message": "Not garbage ❌"}

    garbage_level = result["garbage_level"]

    # ---------------- DUPLICATE CHECK ----------------
    nearby = supabase.rpc(
        "check_nearby_reports",
        {"t_lat": lat, "t_lng": lng, "dist_meters": 20.0}
    ).execute()

    if nearby.data:
        existing_id = nearby.data[0]['id']
        supabase.rpc("increment_complaint", {"row_id": existing_id}).execute()

        return ReportResponse(
            id=existing_id,
            priority_score=0,
            location={"lat": lat, "lng": lng},
            garbage_level=garbage_level
        )

    # ---------------- UPLOAD IMAGE ----------------
    storage_path = f"images/{uuid.uuid4()}.jpg"
    supabase.storage.from_("images").upload(path=storage_path, file=file_content)

    image_url = supabase.storage.from_("images").get_public_url(storage_path)
    if not isinstance(image_url, str):
        image_url = image_url.get("publicURL") or image_url.get("public_url")

    # ---------------- INSERT INTO DB ----------------
    data = {
        "user_id": current_user["id"],
        "image_url": image_url,
        "location": f"POINT({lng} {lat})",
        "garbage_level": garbage_level,
        "status": "pending",
        "reported_at": datetime.now(timezone.utc).isoformat()
    }

    resp = supabase.table("garbage_reports").insert(data).execute()
    report = resp.data[0]

    return ReportResponse(
        id=report["id"],
        priority_score=1,
        location={"lat": lat, "lng": lng},
        garbage_level=garbage_level
    )

    # Check for duplicates nearby (Requires SQL function we wrote)
    nearby = supabase.rpc("check_nearby_reports", {"t_lat": lat, "t_lng": lng, "dist_meters": 20.0}).execute()
    if nearby.data:
        existing_id = nearby.data[0]['id']
        supabase.rpc("increment_complaint", {"row_id": existing_id}).execute()
        return ReportResponse(id=existing_id, priority_score=0, location={"lat": lat, "lng": lng}, garbage_level=garbage_level)

    # Upload Image
    file_content = await file.read()
    storage_path = f"images/{uuid.uuid4()}.jpg"
    supabase.storage.from_("images").upload(path=storage_path, file=file_content)
    image_url = supabase.storage.from_("images").get_public_url(storage_path)
    if not isinstance(image_url, str): image_url = image_url.get("publicURL") or image_url.get("public_url")

    # Insert
    data = {
        "user_id": current_user["id"],
        "image_url": image_url,
        "location": f"POINT({lng} {lat})",
        "garbage_level": garbage_level,
        "status": "pending",
        "reported_at": datetime.now(timezone.utc).isoformat()
    }
    resp = supabase.table("garbage_reports").insert(data).execute()
    report = resp.data[0]
    return ReportResponse(id=report["id"], priority_score=1, location={"lat": lat, "lng": lng}, garbage_level=report["garbage_level"])

# ---------------- 2. OPTIMIZE ROUTE (GPS START + MATH) ----------------



@app.get("/optimize-route/")
def optimize_route(lat: float, lng: float):
    try:
        response = supabase.table("reports").select("*").execute()
        reports = response.data

        if not reports:
            return {"total_spots": 0, "optimized_path": []}

        # 🔹 Start point (truck location)
        start = [lng, lat]

        coords = [start]
        enriched = []

        for r in reports:
            coord = [r["location"]["lng"], r["location"]["lat"]]

            level = r.get("garbage_level", "medium")

            score = 3 if level == "high" else 2 if level == "medium" else 1

            coords.append(coord)

            enriched.append({
                "id": r["id"],
                "coord": coord,
                "level": level,
                "score": score
            })

        # 🔹 Distance matrix
        matrix = get_distance_matrix(coords)

        # 🔹 Greedy optimization
        visited = set()
        path = []
        current = 0  # start index

        while len(visited) < len(enriched):
            best = None
            best_score = -999

            for i, point in enumerate(enriched):
                if i in visited:
                    continue

                distance = matrix[current][i + 1]

                # 🔥 MAGIC FORMULA
                priority_weight = point["score"] * 10
                score = priority_weight - distance

                if score > best_score:
                    best_score = score
                    best = i

            visited.add(best)
            path.append(enriched[best])
            current = best + 1

        return {
            "total_spots": len(path),
            "optimized_path": path
        }

    except Exception as e:
        return {"error": str(e)}

    # Map Coordinates
    report_ids = [r["id"] for r in reports]
    coords_query = supabase.rpc("get_coords", {"report_ids": report_ids}).execute()
    coord_map = {row["id"]: [row["lng"], row["lat"]] for row in coords_query.data}
    
    valid_reports = [r for r in reports if r["id"] in coord_map]
    
    # SETUP START POINT (Collector's current GPS or Depot)
    start_pos = [lng, lat] if (lat and lng) else [77.1025, 28.7041]
    
    # Merge collector start + garbage spots
    final_coords = [start_pos] + [coord_map[r["id"]] for r in valid_reports]
    final_scores = [1] + [calculate_priority_score(r) for r in valid_reports]

    dist_matrix = get_distance_matrix(final_coords)

    # OR-TOOLS Solver
    manager = pywrapcp.RoutingIndexManager(len(final_coords), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def transit_callback(from_idx, to_idx):
        from_node, to_node = manager.IndexToNode(from_idx), manager.IndexToNode(to_idx)
        dist = int(dist_matrix[from_node][to_node] * 1000)
        # Priority makes distance feel shorter
        return int(dist / final_scores[to_node])

    callback_index = routing.RegisterTransitCallback(transit_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(callback_index)

    # Penalties for skipping
    for i in range(1, len(final_coords)):
        routing.AddDisjunction([manager.NodeToIndex(i)], int(final_scores[i] * 10000))

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_parameters)

    path = []
    if solution:
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            # node 0 is the collector, we only return the garbage spots in path
            if node != 0:
                report_idx = node - 1
                path.append({
                    "id": valid_reports[report_idx]["id"],
                    "coord": final_coords[node],
                    "score": final_scores[node],
                    "level": valid_reports[report_idx]["garbage_level"]
                })
            index = solution.Value(routing.NextVar(index))

    return {"optimized_path": path, "total_spots": len(path)}

# ---------------- 3. TASK COMPLETION ----------------



@app.post("/reports/")
async def create_report(file: UploadFile, lat: float, lng: float):
    try:
        # 1. Save image temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 2. AI prediction
        prediction = predict_image(file_path)

        # 3. Convert AI output → level
        if prediction == 2:
            level = "high"
        elif prediction == 1:
            level = "medium"
        else:
            # ❌ Not garbage → reject
            return {"message": "Not garbage, report ignored"}

        # 4. Save to DB
        data = {
            "location": {"lat": lat, "lng": lng},
            "garbage_level": level
        }

        res = supabase.table("reports").insert(data).execute()

        return res.data

    except Exception as e:
        return {"error": str(e)}

# ---------------- 4. AI BRIDGE ----------------
@app.patch("/internal/ai-update/{report_id}")
async def ai_update(report_id: str, ai_level: str = Body(..., embed=True)):
    supabase.table("garbage_reports").update({"garbage_level": ai_level}).eq("id", report_id).execute()
    return {"status": "AI priority synced"}
