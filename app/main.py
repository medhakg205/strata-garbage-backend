import os
import uuid
from datetime import datetime
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv

# OR-Tools
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# LOCAL IMPORTS
from .models import ReportResponse
from .utils import get_distance_matrix
from .ai import predict_image

load_dotenv()

app = FastAPI(title="Garbage Backend")

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ✅ Supabase init
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("❌ Missing Supabase environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# 🚀 CREATE REPORT (FULLY FIXED)
# =========================================================
@app.post("/reports/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    lat: float = Form(...),
    lng: float = Form(...),
    file: UploadFile = File(...),
    token: str = Form(None)  # ✅ From frontend FormData
):
    try:
        # 0. ✅ Auth (simple token check - replace with real JWT later)
        if not token or "eyJhbGci" not in token:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # ✅ Mock user for now (UUID format for FK)
        current_user = {"id": "00000000-0000-0000-0000-000000000001", "role": "citizen"}

        # 1. Validate file
        if not file:
            raise HTTPException(400, "File is required")

        file_content = await file.read()
        if not file_content:
            raise HTTPException(400, "Empty file uploaded")

        # 2. AI Prediction
        garbage_level, ai_message = predict_image(file_content)
        print(f"🤖 AI Result: {garbage_level}, {ai_message}")

        # 3. Not garbage case
        if garbage_level is None:
            return ReportResponse(
                id="not-garbage",
                priority_score=0,
                location={"lat": lat, "lng": lng},
                garbage_level="none",
                message="Not garbage ❌"
            )

        # 4. Upload to Supabase Storage
        file_ext = file.filename.split(".")[-1] if file.filename else "jpg"
        storage_path = f"images/{uuid.uuid4()}.{file_ext}"

        try:
            supabase.storage.from_("images").upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": file.content_type}
            )
            print(f"✅ Uploaded to storage: {storage_path}")
        except Exception as e:
            print("❌ Storage Error:", e)
            raise HTTPException(500, f"Image upload failed: {str(e)}")

        # 5. Get public URL
        public_url_resp = supabase.storage.from_("images").get_public_url(storage_path)
        image_url = (
            public_url_resp
            if isinstance(public_url_resp, str)
            else public_url_resp.get("publicURL") or public_url_resp.get("public_url")
        )

        if not image_url:
            raise HTTPException(500, "Failed to retrieve image URL")
        
        print(f"✅ Public URL: {image_url}")

        # 6. Priority score mapping (numeric for schema)
        score_map = {"high": 10.0, "medium": 5.0, "low": 1.0}
        priority_score = score_map.get(garbage_level, 0.0)

        # 7. ✅ FIXED Insert data (matches your schema perfectly)
        data = {
            "user_id": current_user["id"],  # UUID string
            "image_url": image_url,
            "location": f"POINT({lng} {lat})",  # PostGIS geography
            "garbage_level": garbage_level,
            "status": "pending",
            "priority_score": priority_score,  # numeric
            "reported_at": datetime.utcnow().isoformat()
        }
        
        print("🧪 Inserting to Supabase:", data)

        # 8. Insert into DB
        resp = supabase.table("garbage_reports").insert(data).execute()
        print("✅ Supabase insert response:", resp)

        if not resp.data:
            raise HTTPException(500, "Database insertion failed")

        report = resp.data[0]
        print(f"🎉 Report created: ID={report['id']}")

        return ReportResponse(
            id=report["id"],
            priority_score=float(report.get("priority_score", 0)),
            location={"lat": lat, "lng": lng},
            garbage_level=report["garbage_level"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print("❌ CREATE REPORT ERROR:", str(e))
        raise HTTPException(500, f"Unexpected error: {str(e)}")

# =========================================================
# 📄 GET ALL REPORTS (Fixed location parsing)
# =========================================================
@app.get("/reports/", response_model=List[ReportResponse])
async def get_all_reports(token: str = Form(None)):  # ✅ Form token
    try:
        # ✅ Simple auth
        if not token or "eyJhbGci" not in token:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        current_user = {"role": "collector"}  # Mock for now

        if current_user.get("role") != "collector":
            raise HTTPException(
                status_code=403,
                detail="Access denied. Only collectors can view reports."
            )

        resp = supabase.table("garbage_reports").select(
            "id, location, garbage_level, priority_score"
        ).execute()

        if not resp.data:
            return []

        formatted = []
        for report in resp.data:
            try:
                # ✅ Fixed PostGIS parsing: POINT(lng lat)
                if report["location"]:
                    coords_str = str(report["location"]).replace("POINT(", "").replace(")", "")
                    coords = coords_str.split()
                    lng, lat = float(coords[0]), float(coords[1])
                else:
                    lat, lng = 0.0, 0.0
            except Exception as e:
                print(f"Location parse error: {e}")
                lat, lng = 0.0, 0.0

            formatted.append({
                "id": report["id"],
                "location": {"lat": lat, "lng": lng},
                "garbage_level": report["garbage_level"],
                "priority_score": float(report.get("priority_score", 0))
            })

        return formatted

    except HTTPException:
        raise
    except Exception as e:
        print("❌ GET REPORTS ERROR:", e)
        raise HTTPException(500, f"Error: {str(e)}")

# =========================================================
# 🧭 OPTIMIZE ROUTE (Fixed)
# =========================================================
@app.get("/optimize-route/")
async def optimize_route(token: str = Form(None)):
    try:
        # ✅ Simple auth
        if not token or "eyJhbGci" not in token:
            raise HTTPException(401, "Invalid token")
        
        current_user = {"id": "collector-001", "role": "collector"}

        if current_user.get("role") != "collector":
            raise HTTPException(403, "Collector only")

        # High priority reports only
        resp = supabase.table("garbage_reports") \
            .select("id, location, priority_score") \
            .gte("priority_score", 5) \
            .execute()

        reports = resp.data
        if not reports or len(reports) < 2:
            return {"path": [], "message": "Insufficient high-priority reports"}

        # Extract coordinates
        coords = []
        for report in reports:
            try:
                coords_str = str(report["location"]).replace("POINT(", "").replace(")", "")
                coords_parts = coords_str.split()
                coords.append([float(coords_parts[0]), float(coords_parts[1])])  # [lng, lat]
            except:
                continue

        if len(coords) < 2:
            return {"path": [], "message": "Invalid coordinates"}

        # Distance matrix + OR-Tools (unchanged)
        dist_matrix = get_distance_matrix(coords)

        manager = pywrapcp.RoutingIndexManager(len(coords), 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def dist_cb(from_idx, to_idx):
            return int(
                dist_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)] * 1000
            )

        transit_cb = routing.RegisterTransitCallback(dist_cb)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

        params = pywrapcp.DefaultRoutingSearchParameters()
        params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

        solution = routing.SolveWithParameters(params)

        path = []
        if solution:
            idx = routing.Start(0)
            while not routing.IsEnd(idx):
                node = manager.IndexToNode(idx)
                path.append(coords[node])
                idx = solution.Value(routing.NextVar(idx))
        else:
            path = coords

        # Save route
        supabase.table("routes").insert({
            "collector_id": current_user["id"],
            "report_ids": [r["id"] for r in reports],
            "optimized_path": path
        }).execute()

        return {"path": path, "total_spots": len(path)}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ ROUTE OPTIMIZE ERROR:", e)
        return {"path": [], "error": str(e)}
