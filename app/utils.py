import os
import math
from dotenv import load_dotenv

load_dotenv()

USE_LEAFLET = os.getenv("USE_LEAFLET", "true").lower() == "true"

def get_distance_matrix(coords):
    size = len(coords)
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]

    for i in range(size):
        for j in range(size):
            if i == j:
                continue

            lon1, lat1 = coords[i]
            lon2, lat2 = coords[j]

            r_lat1, r_lon1, r_lat2, r_lon2 = map(
                math.radians, [lat1, lon1, lat2, lon2]
            )

            dlat = r_lat2 - r_lat1
            dlon = r_lon2 - r_lon1

            a = math.sin(dlat / 2) ** 2 + \
                math.cos(r_lat1) * math.cos(r_lat2) * math.sin(dlon / 2) ** 2

            c = 2 * math.asin(math.sqrt(a))
            matrix[i][j] = c * 6371

    return matrix
