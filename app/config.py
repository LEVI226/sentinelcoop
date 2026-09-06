"""Configuration centralisée de l'application (source unique : .env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Back-end_filtrage"
    ENVIRONMENT: str = "development"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = ""

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 30
    REFRESH_EXPIRES_DAYS: int = 7

    # Clé maîtresse AES-256-GCM (hex) pour chiffrer les champs sensibles clients
    ENCRYPTION_MASTER_KEY: str = ""
    # Nonce/salt statique dérivé pour le chiffrement déterministe (déréférencement)
    ENCRYPTION_FIXED_SALT: str = "cifguard-fixed-salt-v1"

    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_DIR: str = "./storage"

    CORS_ORIGINS: str = "*"

    # Délai des alertes SLA par priorité (minutes)
    ALERT_SLA_MINUTES: dict = {
        "low": 24 * 60,        # 24h
        "medium": 12 * 60,     # 12h
        "high": 6 * 60,        # 6h
        "critical": 2 * 60,    # 2h
    }

    # Seuils des niveaux de risque (configurables) — CDC §19
    RISK_LEVELS: dict = {
        "LOW": [0, 29],
        "MEDIUM": [30, 59],
        "HIGH": [60, 79],
        "CRITICAL": [80, 100],
    }

    @property
    def risk_bands(self) -> list[tuple[str, int, int]]:
        return [(name, lo, hi) for name, (lo, hi) in self.RISK_LEVELS.items()]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.DATABASE_URL:
        raise RuntimeError("DATABASE_URL manquant dans .env")
    if not s.JWT_SECRET:
        raise RuntimeError("JWT_SECRET manquant dans .env")
    if not s.ENCRYPTION_MASTER_KEY:
        raise RuntimeError("ENCRYPTION_MASTER_KEY manquant dans .env")
    return s
