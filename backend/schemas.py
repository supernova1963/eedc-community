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

    # Speicher-KPIs
    speicher_ladung_kwh: float | None = Field(None, ge=0)
    speicher_entladung_kwh: float | None = Field(None, ge=0)
    speicher_ladung_netz_kwh: float | None = Field(None, ge=0)

    # Wärmepumpe-KPIs
    wp_stromverbrauch_kwh: float | None = Field(None, ge=0)
    wp_heizwaerme_kwh: float | None = Field(None, ge=0)
    wp_warmwasser_kwh: float | None = Field(None, ge=0)

    # E-Auto-KPIs
    eauto_ladung_gesamt_kwh: float | None = Field(None, ge=0)
    eauto_ladung_pv_kwh: float | None = Field(None, ge=0)
    eauto_ladung_extern_kwh: float | None = Field(None, ge=0)
    eauto_km: float | None = Field(None, ge=0)
    eauto_v2h_kwh: float | None = Field(None, ge=0)

    # Wallbox-KPIs
    wallbox_ladung_kwh: float | None = Field(None, ge=0)
    wallbox_ladung_pv_kwh: float | None = Field(None, ge=0)
    wallbox_ladevorgaenge: int | None = Field(None, ge=0)

    # Balkonkraftwerk-KPIs
    bkw_erzeugung_kwh: float | None = Field(None, ge=0)
    bkw_eigenverbrauch_kwh: float | None = Field(None, ge=0)
    bkw_speicher_ladung_kwh: float | None = Field(None, ge=0)
    bkw_speicher_entladung_kwh: float | None = Field(None, ge=0)

    # Sonstiges-KPIs
    sonstiges_verbrauch_kwh: float | None = Field(None, ge=0)

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
    hat_balkonkraftwerk: bool = False
    hat_sonstiges: bool = False

    # Komponenten-Details
    wallbox_kw: float | None = Field(None, ge=0, le=50)  # Ladeleistung in kW
    bkw_wp: float | None = Field(None, ge=0, le=2000)  # BKW Leistung in Wp
    sonstiges_bezeichnung: str | None = Field(None, max_length=100)

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

    # Speicher-KPIs
    speicher_ladung_kwh: float | None = None
    speicher_entladung_kwh: float | None = None
    speicher_ladung_netz_kwh: float | None = None

    # Wärmepumpe-KPIs
    wp_stromverbrauch_kwh: float | None = None
    wp_heizwaerme_kwh: float | None = None
    wp_warmwasser_kwh: float | None = None

    # E-Auto-KPIs
    eauto_ladung_gesamt_kwh: float | None = None
    eauto_ladung_pv_kwh: float | None = None
    eauto_ladung_extern_kwh: float | None = None
    eauto_km: float | None = None
    eauto_v2h_kwh: float | None = None

    # Wallbox-KPIs
    wallbox_ladung_kwh: float | None = None
    wallbox_ladung_pv_kwh: float | None = None
    wallbox_ladevorgaenge: int | None = None

    # Balkonkraftwerk-KPIs
    bkw_erzeugung_kwh: float | None = None
    bkw_eigenverbrauch_kwh: float | None = None
    bkw_speicher_ladung_kwh: float | None = None
    bkw_speicher_entladung_kwh: float | None = None

    # Sonstiges-KPIs
    sonstiges_verbrauch_kwh: float | None = None


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
    hat_balkonkraftwerk: bool = False
    hat_sonstiges: bool = False
    wallbox_kw: float | None = None
    bkw_wp: float | None = None
    sonstiges_bezeichnung: str | None = None
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


class KPIVergleich(BaseModel):
    """Ein einzelner KPI-Vergleichswert."""
    wert: float
    community_avg: float | None = None
    rang: int | None = None
    von: int | None = None


class SpeicherBenchmark(BaseModel):
    """Benchmark-Daten für Speicher."""
    kapazitaet: KPIVergleich | None = None
    zyklen_jahr: KPIVergleich | None = None
    nutzungsgrad: KPIVergleich | None = None
    wirkungsgrad: KPIVergleich | None = None
    netz_anteil: KPIVergleich | None = None


class WaermepumpeBenchmark(BaseModel):
    """Benchmark-Daten für Wärmepumpe."""
    jaz: KPIVergleich | None = None
    stromverbrauch: KPIVergleich | None = None
    waermeerzeugung: KPIVergleich | None = None
    pv_anteil: KPIVergleich | None = None


class EAutoBenchmark(BaseModel):
    """Benchmark-Daten für E-Auto."""
    ladung_gesamt: KPIVergleich | None = None
    pv_anteil: KPIVergleich | None = None
    km: KPIVergleich | None = None
    verbrauch_100km: KPIVergleich | None = None
    v2h: KPIVergleich | None = None


class WallboxBenchmark(BaseModel):
    """Benchmark-Daten für Wallbox."""
    ladung: KPIVergleich | None = None
    pv_anteil: KPIVergleich | None = None
    ladevorgaenge: KPIVergleich | None = None


class BKWBenchmark(BaseModel):
    """Benchmark-Daten für Balkonkraftwerk."""
    erzeugung: KPIVergleich | None = None
    spez_ertrag: KPIVergleich | None = None
    eigenverbrauch: KPIVergleich | None = None


class PVBenchmark(BaseModel):
    """Benchmark-Daten für PV-Anlage."""
    spez_ertrag: KPIVergleich
    eigenverbrauch: KPIVergleich | None = None
    autarkie: KPIVergleich | None = None


class ErweiterteBenchmarkData(BaseModel):
    """Erweiterte Benchmark-Daten mit allen Komponenten."""
    pv: PVBenchmark
    speicher: SpeicherBenchmark | None = None
    waermepumpe: WaermepumpeBenchmark | None = None
    eauto: EAutoBenchmark | None = None
    wallbox: WallboxBenchmark | None = None
    balkonkraftwerk: BKWBenchmark | None = None


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
