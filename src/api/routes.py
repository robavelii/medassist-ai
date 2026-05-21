from fastapi import APIRouter

from src.api.endpoints.auth import router as auth_router
from src.api.endpoints.clinical import router as clinical_router
from src.api.endpoints.demo import router as demo_router
from src.api.endpoints.health import router as health_router

routers = APIRouter()

public_router_list = [
    health_router,
    auth_router,
    clinical_router,
    demo_router,
]

for router in public_router_list:
    routers.include_router(router)
