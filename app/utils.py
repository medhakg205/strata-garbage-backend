import googlemaps
import os
from supabase import Client

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

def get_distance_matrix(coords: list[list[float]]) -> list[list[float]]:
    """Returns distance matrix in km."""
    result = gmaps.distance_matrix(coords, coords, mode="driving")["rows"]
    return [[result[i]["elements"][j]["distance"]["value"] / 1000 for j in range(len(coords))] for i in range(len(coords))]