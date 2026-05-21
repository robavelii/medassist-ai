from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware

from src.api.routes import routers
from src.core.config import configs
from src.core.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    container = Container()
    db = container.db()
    db.create_database()
    app.state.container = container
    app.state.db = db
    yield


app = FastAPI(
    title=configs.PROJECT_NAME,
    description=(
        "Clinical decision support platform for healthcare professionals. "
        "Provides structured clinical analysis across triage, diagnosis, "
        "medication management, lab interpretation, and more."
    ),
    version=configs.APP_VERSION,
    openapi_url=f"{configs.API}/openapi.json",
    root_path=configs.API_ROOT_PATH,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
if configs.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in configs.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routes
app.include_router(routers, prefix=configs.API_STR)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")
