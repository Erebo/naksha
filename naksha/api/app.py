"""FastAPI Application Factory for NAKSHA."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from naksha.core.config import settings
from naksha.api.routes import router


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

    # Register routes
    app.include_router(router)

    return app


app = create_app()
