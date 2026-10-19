from pathlib import Path
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_SECRET = "dev-insecure-secret-key-change-in-production"
DEFAULT_DEV_NID_SECRET = "dev-insecure-nid-salt-key-change-in-production"
DB_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_URL = f"sqlite:///{DB_DIR / 'naksha_spatial.db'}"
DEFAULT_TEST_POSTGRES_URL = "postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_test"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NAKSHA_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "NAKSHA Land Data Platform"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    debug: bool = False
    synthetic_mode: bool = True
    environment: str = "development"
    database_url: str = DEFAULT_SQLITE_URL
    test_database_url: str | None = DEFAULT_TEST_POSTGRES_URL

    # Authentication & Security
    secret_key: str = DEFAULT_DEV_SECRET
    nid_hmac_secret: str = DEFAULT_DEV_NID_SECRET
    jwt_issuer: str = "naksha-auth-service"
    jwt_expiry_seconds: int = 900
    allowed_origins: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    auth_rate_limit_max_requests: int = 5
    auth_rate_limit_window_seconds: int = 60

    # Statutory Rule Thresholds (Configurable via environment variables)
    khas_overlap_limit_decimals: float = 0.0
    area_tolerance_decimals: float = 0.20
    owner_name_match_threshold: float = 0.80
    max_tax_arrears_years: int = 1
    max_unmutated_days: int = 30

    # Statutory Legal References (Defaulted to unverified notice per standing rules)
    khas_encroachment_legal_ref: str = "TODO: verify with legal source"
    area_tolerance_legal_ref: str = "TODO: verify with legal source"
    owner_name_match_legal_ref: str = "TODO: verify with legal source"
    ld_tax_compliance_legal_ref: str = "TODO: verify with legal source"
    mutation_status_legal_ref: str = "TODO: verify with legal source"

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        env = (self.environment or "").strip().lower()
        if env not in ("development", "test", "testing"):
            if self.secret_key == DEFAULT_DEV_SECRET:
                raise ValueError(
                    f"Production startup failure: Insecure default secret_key cannot be used in environment '{self.environment}'. "
                    "Configure NAKSHA_SECRET_KEY in production."
                )
            if self.nid_hmac_secret == DEFAULT_DEV_NID_SECRET:
                raise ValueError(
                    f"Production startup failure: Insecure default nid_hmac_secret cannot be used in environment '{self.environment}'. "
                    "Configure NAKSHA_NID_HMAC_SECRET in production."
                )
        return self


from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = Settings()
