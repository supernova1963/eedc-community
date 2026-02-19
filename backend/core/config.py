"""
EEDC Community - Konfiguration
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Anwendungs-Einstellungen aus Umgebungsvariablen."""

    # Datenbank
    database_url: str = "postgresql+asyncpg://eedc:password@db:5432/eedc_community"

    # Sicherheit
    secret_key: str = "change-me-in-production"

    # CORS
    allowed_origins: str = "https://energie.raunet.eu"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    # Rate Limiting
    rate_limit_per_hour: int = 10  # Max Einreichungen pro IP/Stunde
    max_updates_per_month: int = 12  # Max Updates pro Anlage/Monat

    class Config:
        env_file = ".env"


settings = Settings()
