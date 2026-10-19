"""Core configuration for NAKSHA."""
from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()

