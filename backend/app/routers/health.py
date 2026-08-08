import httpx
from fastapi import APIRouter

from app.config import get_settings
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])
settings = get_settings()

APP_VERSION = "0.1.0"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    ollama_reachable = None
    try:
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=1.0)
        ollama_reachable = resp.status_code == 200
    except httpx.HTTPError:
        ollama_reachable = False

    return HealthResponse(status="ok", version=APP_VERSION, ollama_reachable=ollama_reachable)
