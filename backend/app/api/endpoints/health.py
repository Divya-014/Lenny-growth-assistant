from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

class HealthResponse(BaseModel):
    status: str = Field(default="healthy")

@router.get("/health", response_model=HealthResponse, tags=["System Health"])
async def get_health():
    """
    Check the health status of the application backend.
    """
    return HealthResponse(status="healthy")
