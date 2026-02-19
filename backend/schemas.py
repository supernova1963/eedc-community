"""
EEDC Community - Pydantic Schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Literal


# =============================================================================
# Eingabe-Schemas (für API-Requests)
# =============================================================================

class MonatswertInput(BaseModel):
    """Ein Monatswert für die Einreichung."""
    jahr: int = Field(..., ge=2010, le=2050)
    monat: int = Field(..., ge=1, le=12)
    ertrag_kwh: float = Field(..., ge=0)
    einspeisung_kwh: float | None = Field(None, ge=0)
    netzbezug_kwh: float | None = Field(None, ge=0)
    autarkie_prozent: float | None = Field(None, ge=0, le=100)
    eigenverbrauch_prozent: float | None = Field(None, ge=0, le=100)

    @field_validator("ertrag_kwh")
    @classmethod
    def validate_ertrag(cls, v: float, info) -> float:
        # Max ~180 kWh/kWp/Monat ist realistisch (Sommer in DE)
        # Wir prüfen das später gegen kWp der Anlage
        if v > 50000:  # Absolute Obergrenze für sehr große Anlagen
            raise ValueError("Ertrag unrealistisch hoch")
        return v


class AnlageSubmitInput(BaseModel):
    """Eingabedaten für eine neue Anlage oder Update."""

    # Wird vom Backend generiert wenn nicht angegeben
    anlage_hash: str | None = None

    # Anlagendaten
    region: str = Field(..., min_length=2, max_length=2)  # Bundesland-Kürzel
    kwp: float = Field(..., gt=0, le=100)  # 0.5 - 100 kWp für Privatanlagen
    ausrichtung: Literal["süd", "ost", "west", "ost-west", "gemischt"] = "süd"
    neigung_grad: int = Field(..., ge=0, le=90)
    speicher_kwh: float | None = Field(None, ge=0, le=100)
    installation_jahr: int = Field(..., ge=2000, le=2050)

    # Ausstattung
    hat_waermepumpe: bool = False
    hat_eauto: bool = False
    hat_wallbox: bool = False

    # Monatswerte
    monatswerte: list[MonatswertInput] = Field(..., min_length=1)

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        valid_regions = {
            "BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV",
            "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH",
            "AT", "CH"  # Österreich, Schweiz
        }
        v = v.upper()
        if v not in valid_regions:
            raise ValueError(f"Ungültige Region: {v}")
        return v

    @field_validator("monatswerte")
    @classmethod
    def validate_monatswerte(cls, v: list[MonatswertInput]) -> list[MonatswertInput]:
        # Keine Duplikate erlaubt
        seen = set()
        for mw in v:
            key = (mw.jahr, mw.monat)
            if key in seen:
                raise ValueError(f"Doppelter Monat: {mw.jahr}-{mw.monat:02d}")
            seen.add(key)
        return v


# =============================================================================
# Ausgabe-Schemas (für API-Responses)
# =============================================================================

class MonatswertOutput(BaseModel):
    """Monatswert in der Ausgabe."""
    jahr: int
    monat: int
    ertrag_kwh: float
    einspeisung_kwh: float | None
    netzbezug_kwh: float | None
    autarkie_prozent: float | None
    eigenverbrauch_prozent: float | None
    spez_ertrag_kwh_kwp: float | None = None  # Berechnet


class AnlageOutput(BaseModel):
    """Anlage in der Ausgabe (ohne sensible Daten)."""
    anlage_hash: str
    region: str
    kwp: float
    ausrichtung: str
    neigung_grad: int
    speicher_kwh: float | None
    installation_jahr: int
    hat_waermepumpe: bool
    hat_eauto: bool
    hat_wallbox: bool
    monatswerte: list[MonatswertOutput]

    class Config:
        from_attributes = True


class SubmitResponse(BaseModel):
    """Antwort nach erfolgreicher Einreichung."""
    success: bool
    message: str
    anlage_hash: str
    anzahl_monate: int
    # Vergleichsdaten
    benchmark: "BenchmarkData | None" = None


class BenchmarkData(BaseModel):
    """Vergleichsdaten für die eingereichte Anlage."""
    spez_ertrag_anlage: float  # kWh/kWp der Anlage (letztes Jahr)
    spez_ertrag_durchschnitt: float  # Durchschnitt aller Anlagen
    spez_ertrag_region: float  # Durchschnitt der Region
    rang_gesamt: int  # Platzierung gesamt
    anzahl_anlagen_gesamt: int
    rang_region: int  # Platzierung in Region
    anzahl_anlagen_region: int


class DeleteResponse(BaseModel):
    """Antwort nach erfolgreicher Löschung."""
    success: bool
    message: str
    anzahl_geloeschte_monate: int


# =============================================================================
# Statistik-Schemas
# =============================================================================

class RegionStatistik(BaseModel):
    """Statistik für eine Region."""
    region: str
    anzahl_anlagen: int
    durchschnitt_kwp: float
    durchschnitt_spez_ertrag: float
    durchschnitt_autarkie: float | None
    anteil_mit_speicher: float
    anteil_mit_waermepumpe: float
    anteil_mit_eauto: float


class MonatsStatistik(BaseModel):
    """Aggregierte Statistik für einen Monat."""
    jahr: int
    monat: int
    anzahl_anlagen: int
    durchschnitt_ertrag_kwh: float
    durchschnitt_spez_ertrag: float
    median_spez_ertrag: float
    min_spez_ertrag: float
    max_spez_ertrag: float


class GesamtStatistik(BaseModel):
    """Gesamtübersicht aller Daten."""
    anzahl_anlagen: int
    anzahl_monatswerte: int
    durchschnitt_kwp: float
    durchschnitt_speicher_kwh: float | None
    durchschnitt_spez_ertrag_jahr: float
    regionen: list[RegionStatistik]
    letzte_monate: list[MonatsStatistik]


# Forward reference auflösen
SubmitResponse.model_rebuild()
