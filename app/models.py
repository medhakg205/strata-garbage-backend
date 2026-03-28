from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class GarbageLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ReportCreate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    garbage_level: GarbageLevel = "medium"

class ReportResponse(BaseModel):
    id: str
    priority_score: float
    location: dict[str, float]
    garbage_level: GarbageLevel

class RouteResponse(BaseModel):
    path: List[list[float]]
    total_spots: int