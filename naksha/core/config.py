from pathlib import Path
from typing import List
from pydantic import model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.hazmat.primitives.asymmetric import ed25519

DEFAULT_DEV_SECRET = "dev-insecure-secret-key-change-in-production"
DEFAULT_DEV_NID_SECRET = "dev-insecure-nid-salt-key-change-in-production"
DEFAULT_DEV_LEDGER_KEY = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
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
    ledger_private_key: str = DEFAULT_DEV_LEDGER_KEY
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

    @field_validator("ledger_private_key")
    @classmethod
    def validate_ledger_private_key(cls, v: str) -> str:
        if v:
            clean = v.strip()
            try:
                b = bytes.fromhex(clean)
                if len(b) != 32:
                    raise ValueError(f"ledger_private_key must be exactly 32 bytes (64 hex characters), got {len(b)} bytes")
            except Exception as e:
                raise ValueError(f"Invalid ledger_private_key hex string: {e}")
            return clean
        return v

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
            if not self.ledger_private_key or self.ledger_private_key == DEFAULT_DEV_LEDGER_KEY:
                raise ValueError(
                    f"Production startup failure: Insecure default or missing ledger_private_key cannot be used in environment '{self.environment}'. "
                    "Configure NAKSHA_LEDGER_PRIVATE_KEY in production."
                )
        return self

    def get_ledger_signing_key(self) -> ed25519.Ed25519PrivateKey:
        raw_bytes = bytes.fromhex(self.ledger_private_key.strip())
        return ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)

    def get_ledger_public_key(self) -> ed25519.Ed25519PublicKey:
        return self.get_ledger_signing_key().public_key()

    def get_ledger_public_key_hex(self) -> str:
        return self.get_ledger_public_key().public_bytes_raw().hex()


from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
