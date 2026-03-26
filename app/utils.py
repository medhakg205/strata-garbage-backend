import os
import googlemaps
from pathlib import Path
from dotenv import load_dotenv

# --- DYNAMIC ENV LOADING ---
# This looks one folder up (..) from /app/utils.py to find the .env in /backend/
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- GOOGLE MAPS CONFIG ---
GOOGLE_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
USE_LEAFLET = os.getenv("USE_LEAFLET", "true").lower() == "true"

# Only initialize Google if we have a key AND we aren't forcing Leaflet
if GOOGLE_KEY and not USE_LEAFLET:
    gmaps = googlemaps.Client(key=GOOGLE_KEY)
    print("✅ Google Maps Client initialized.")
else:
    gmaps = None
    print("ℹ️ Using Free Leaflet mode: Google Maps Client skipped.")

def get_distance_matrix(coords: list[list[float]]) -> list[list[float]]:
    """
    Returns distance matrix in km. 
    Uses Google Maps if available, otherwise falls back to basic math.
    """
    # 1. Try to use Google Maps if initialized
    if gmaps:
        try:
            result = gmaps.distance_matrix(coords, coords, mode="driving")["rows"]
            return [
                [row["elements"][j]["distance"]["value"] / 1000 for j in range(len(coords))] 
                for row in result
            ]
        except Exception as e:
            print(f"⚠️ Google Maps API error: {e}. Falling back to math.")

    # 2. FALLBACK: Simple mathematical distance (Euclidean)
    # This prevents the app from crashing and keeps your route optimization working
    size = len(coords)
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    
    for i in range(size):
        for j in range(size):
            if i == j:
                matrix[i][j] = 0.0
            else:
                # Basic straight-line distance calculation
                lat1, lon1 = coords[i]
                lat2, lon2 = coords[j]
                dist = ((lat2 - lat1)**2 + (lon2 - lon1)**2)**0.5
                # Multiply by 111 to approximate km (crude but works for testing)
                matrix[i][j] = dist * 111.0 
                
    return matrix