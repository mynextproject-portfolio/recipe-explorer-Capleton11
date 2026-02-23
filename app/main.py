import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.dependencies import get_storage
from app.routes import api
from app.services import cache

# App configuration
APP_NAME = "Recipe Explorer"
VERSION = "1.0.0"
DEBUG = True

SAMPLE_DATA_PATH = Path(__file__).parent.parent / "sample-recipes.json"
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed sample recipes on first run; skip if data already exists."""
    storage = get_storage()

    if not SAMPLE_DATA_PATH.exists():
        print(f"No sample data file found at {SAMPLE_DATA_PATH}")
    elif storage.get_all_recipes():
        print("Database already contains recipes, skipping seed")
    else:
        try:
            with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as sample_file:
                recipes_data = json.load(sample_file)
            count = storage.import_recipes(recipes_data)
            print(f"Seeded {count} recipes from {SAMPLE_DATA_PATH.name}")
        except Exception as error:
            print(f"Failed to seed sample data: {error}")

    yield

    # Shutdown: close the Redis connection cleanly
    await cache.close()


# Create FastAPI app
app = FastAPI(title=APP_NAME, version=VERSION, lifespan=lifespan)

# CORS — allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api.router)


# Basic health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Prometheus — exposes /metrics in Prometheus text format
# Must come AFTER routers are registered so all routes are instrumented
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# SPA catch-all — serve React app for all non-API routes
if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        return FileResponse(str(FRONTEND_DIST / "index.html"))
