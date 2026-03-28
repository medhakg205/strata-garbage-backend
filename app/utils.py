import os
import math
import googlemaps
from pathlib import Path
from dotenv import load_dotenv

# --- DYNAMIC ENV LOADING ---
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- CONFIG ---
GOOGLE_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
USE_LEAFLET = os.getenv("USE_LEAFLET", "true").lower() == "true"

# Initialize Google only if required and key exists
if GOOGLE_KEY and not USE_LEAFLET:
    try:
        gmaps = googlemaps.Client(key=GOOGLE_KEY)
        print("✅ Google Maps Client initialized.")
    except Exception as e:
        gmaps = None
        print(f"❌ Google Init Failed: {e}")
else:
    gmaps = None
    print("ℹ️ Using Free Mode (Haversine Math).")

def get_distance_matrix(coords: list[list[float]]) -> list[list[float]]:
    """
    Calculates distance matrix in km.
    Input format: [[lng, lat], [lng, lat], ...] -> standard from your Supabase setup.
    """
    size = len(coords)
    
    # 1. GOOGLE MAPS PATH
    if gmaps:
        try:
            # Google expects [lat, lng], so we flip your [lng, lat]
            flipped_coords = [[c[1], c[0]] for c in coords]
            
            # Google has a limit of 25 destinations per request
            result = gmaps.distance_matrix(flipped_coords, flipped_coords, mode="driving")["rows"]
            
            return [
                [row["elements"][j]["distance"]["value"] / 1000 for j in range(size)] 
                for row in result
            ]
        except Exception as e:
            print(f"⚠️ Google API failed: {e}. Falling back to Haversine.")

    # 2. FREE MATH PATH (Haversine Formula)
    # This is much more accurate than the simple (x²+y²) math for GPS coordinates.
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    
    for i in range(size):
        for j in range(size):
            if i == j:
                continue
            
            # Unpack lng/lat
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[j]
            
            # Convert degrees to radians
            r_lat1, r_lon1, r_lat2, r_lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = r_lat2 - r_lat1
            dlon = r_lon2 - r_lon1
            a = math.sin(dlat/2)**2 + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # 6371 is the Earth's radius in kilometers
            matrix[i][j] = c * 6371
                
    return matrix
