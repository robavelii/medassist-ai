import time

from fastapi import APIRouter

from src.core.config import configs

_start_time = time.time()

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    """Service health check with uptime and version info."""
    uptime_seconds = int(time.time() - _start_time)
    return {
        "status": "ok",
        "service": configs.PROJECT_NAME,
        "version": configs.APP_VERSION,
        "uptime_seconds": uptime_seconds,
    }
