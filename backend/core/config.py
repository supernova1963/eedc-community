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
    rate_limit_per_hour: int = 30  # Max DELETE-Anfragen pro IP/Stunde
    # Max Updates pro Anlage in einem rollenden 24-Stunden-Fenster.
    # 30 reichten bei Reparatur-/Nachpflege-Sessions schnell nicht (Issue #254
    # kingcap1: Datenpflege 2023→2026 in einer Session). 50 ist Schmerz-Hebel-
    # tolerant, bleibt Spam-Schutz pro Hash.
    max_updates_per_24h: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
