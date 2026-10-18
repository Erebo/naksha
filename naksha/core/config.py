"""Core configuration for NAKSHA."""
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "NAKSHA Land Data Platform"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    debug: bool = False
    synthetic_mode: bool = True

settings = Settings()
