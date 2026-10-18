"""FastAPI Application Factory for NAKSHA."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from naksha.core.config import settings
from naksha.api.routes import router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        title="NAKSHA Canonical Land Data Engine",
        description=(
            "Inter-Agency Land Data Interoperability & Canonical Spatial Engine for the "
            "LandTech 2026 Innovation Hackathon. Reconciles records across Sub-Registry, "
            "AC Land, Union Land Office, DLRS, DC Office, and Banks."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for frontend / Chrome extension development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(router)

    # Mount static assets if static directory exists
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_index():
            """Serve the Bangla-first 2D GIS interactive map."""
            return FileResponse(STATIC_DIR / "index.html")

        @app.get("/map", include_in_schema=False)
        async def serve_map():
            """Direct alias to serve the 2D GIS side panel."""
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
