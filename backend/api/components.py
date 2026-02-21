"""
EEDC Community - Komponenten Deep-Dive API

Erweiterte Vergleiche für Speicher, Wärmepumpe, E-Auto, etc.
gruppiert nach Klassen und Regionen.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from core import get_db
from models import Anlage, Monatswert

router = APIRouter(prefix="/components", tags=["Komponenten Deep-Dives"])


# =============================================================================
# Schemas
# =============================================================================

class SpeicherKlasse(BaseModel):
    """Speicher-Statistiken nach Kapazitätsklasse."""
    von_kwh: float
    bis_kwh: float | None
    anzahl: int
    durchschnitt_wirkungsgrad: float | None
    durchschnitt_zyklen: float | None
    durchschnitt_netz_anteil: float | None


class SpeicherByClass(BaseModel):
    """Speicher-Vergleich nach Kapazitätsklassen."""
    klassen: list[SpeicherKlasse]


class WPRegion(BaseModel):
    """Wärmepumpen-Statistiken nach Region."""
    region: str
    anzahl: int
    durchschnitt_jaz: float | None


class WPByRegion(BaseModel):
    """Wärmepumpen-JAZ nach Region."""
    regionen: list[WPRegion]


class EAutoKlasse(BaseModel):
    """E-Auto-Statistiken nach Nutzungsintensität."""
    klasse: str
    beschreibung: str
    anzahl: int
    durchschnitt_pv_anteil: float | None
    durchschnitt_verbrauch_100km: float | None


class EAutoByUsage(BaseModel):
    """E-Auto-Vergleich nach Nutzungsklassen."""
    klassen: list[EAutoKlasse]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/speicher/by-class", response_model=SpeicherByClass)
async def get_speicher_by_class(db: AsyncSession = Depends(get_db)):
    """
    Liefert Speicher-Statistiken gruppiert nach Kapazitätsklassen.

    Klassen: 5-10 kWh, 10-15 kWh, >15 kWh

    Verwendet für:
    - Komponenten Tab: Speicher-Vergleich nach Größe
    """
    # Definiere Kapazitätsklassen
    klassen_def = [
        (5, 10, "5-10 kWh"),
        (10, 15, "10-15 kWh"),
        (15, None, ">15 kWh"),
    ]

    klassen = []

    for von, bis, label in klassen_def:
        # Anlagen in dieser Klasse
        query = select(Anlage).where(Anlage.speicher_kwh >= von)
        if bis is not None:
            query = query.where(Anlage.speicher_kwh < bis)

        anlagen_result = await db.execute(query)
        anlagen = anlagen_result.scalars().all()

        if not anlagen:
            klassen.append(SpeicherKlasse(
                von_kwh=von,
                bis_kwh=bis,
                anzahl=0,
                durchschnitt_wirkungsgrad=None,
                durchschnitt_zyklen=None,
                durchschnitt_netz_anteil=None,
            ))
            continue

        # Statistiken berechnen
        wirkungsgrade = []
        zyklen_liste = []
        netz_anteile = []

        for anlage in anlagen:
            # Monatswerte für diese Anlage
            result = await db.execute(
                select(
                    func.sum(Monatswert.speicher_ladung_kwh),
                    func.sum(Monatswert.speicher_entladung_kwh),
                    func.sum(Monatswert.speicher_ladung_netz_kwh),
                )
                .where(Monatswert.anlage_id == anlage.id)
                .where(Monatswert.speicher_ladung_kwh.isnot(None))
            )
            row = result.one()

            ladung = row[0] or 0
            entladung = row[1] or 0
            netz_ladung = row[2] or 0

            # Wirkungsgrad
            if ladung > 0:
                wirkungsgrad = (entladung / ladung) * 100
                wirkungsgrade.append(wirkungsgrad)

                # Netz-Anteil
                netz_anteil = (netz_ladung / ladung) * 100
                netz_anteile.append(netz_anteil)

            # Zyklen pro Jahr (basierend auf Kapazität)
            if anlage.speicher_kwh and anlage.speicher_kwh > 0:
                # Anzahl Monate
                monate_result = await db.execute(
                    select(func.count(Monatswert.id))
                    .where(Monatswert.anlage_id == anlage.id)
                    .where(Monatswert.speicher_entladung_kwh.isnot(None))
                )
                anzahl_monate = monate_result.scalar() or 0

                if anzahl_monate >= 6 and entladung > 0:
                    # Hochrechnung auf Jahr
                    jahres_entladung = (entladung / anzahl_monate) * 12
                    zyklen = jahres_entladung / anlage.speicher_kwh
                    zyklen_liste.append(zyklen)

        klassen.append(SpeicherKlasse(
            von_kwh=von,
            bis_kwh=bis,
            anzahl=len(anlagen),
            durchschnitt_wirkungsgrad=round(sum(wirkungsgrade) / len(wirkungsgrade), 1) if wirkungsgrade else None,
            durchschnitt_zyklen=round(sum(zyklen_liste) / len(zyklen_liste), 0) if zyklen_liste else None,
            durchschnitt_netz_anteil=round(sum(netz_anteile) / len(netz_anteile), 1) if netz_anteile else None,
        ))

    return SpeicherByClass(klassen=klassen)


@router.get("/waermepumpe/by-region", response_model=WPByRegion)
async def get_wp_by_region(db: AsyncSession = Depends(get_db)):
    """
    Liefert Wärmepumpen-JAZ gruppiert nach Region (Klimazone).

    Verwendet für:
    - Komponenten Tab: WP-Vergleich nach Region
    """
    # Alle Anlagen mit Wärmepumpe, gruppiert nach Region
    result = await db.execute(
        select(Anlage.region, func.count(Anlage.id).label("anzahl"))
        .where(Anlage.hat_waermepumpe == True)
        .group_by(Anlage.region)
        .order_by(func.count(Anlage.id).desc())
    )
    regionen_raw = result.all()

    regionen = []

    for region_code, anzahl in regionen_raw:
        # JAZ für diese Region berechnen
        anlagen_result = await db.execute(
            select(Anlage)
            .where(Anlage.region == region_code)
            .where(Anlage.hat_waermepumpe == True)
        )
        anlagen = anlagen_result.scalars().all()

        jaz_werte = []
        for anlage in anlagen:
            result = await db.execute(
                select(
                    func.sum(Monatswert.wp_stromverbrauch_kwh),
                    func.sum(Monatswert.wp_heizwaerme_kwh),
                    func.sum(Monatswert.wp_warmwasser_kwh),
                )
                .where(Monatswert.anlage_id == anlage.id)
                .where(Monatswert.wp_stromverbrauch_kwh.isnot(None))
            )
            row = result.one()

            strom = row[0] or 0
            waerme = (row[1] or 0) + (row[2] or 0)

            if strom > 0:
                jaz = waerme / strom
                jaz_werte.append(jaz)

        regionen.append(WPRegion(
            region=region_code,
            anzahl=anzahl,
            durchschnitt_jaz=round(sum(jaz_werte) / len(jaz_werte), 2) if jaz_werte else None,
        ))

    return WPByRegion(regionen=regionen)


@router.get("/eauto/by-usage", response_model=EAutoByUsage)
async def get_eauto_by_usage(db: AsyncSession = Depends(get_db)):
    """
    Liefert E-Auto-Statistiken gruppiert nach Nutzungsintensität.

    Klassen: Wenig (<500 km/Monat), Mittel (500-1000), Viel (>1000)

    Verwendet für:
    - Komponenten Tab: E-Auto-Vergleich nach Nutzung
    """
    # Alle Anlagen mit E-Auto
    anlagen_result = await db.execute(
        select(Anlage).where(Anlage.hat_eauto == True)
    )
    anlagen = anlagen_result.scalars().all()

    # Kategorisieren
    wenig = {"anzahl": 0, "pv_anteile": [], "verbraeuche": []}
    mittel = {"anzahl": 0, "pv_anteile": [], "verbraeuche": []}
    viel = {"anzahl": 0, "pv_anteile": [], "verbraeuche": []}

    for anlage in anlagen:
        result = await db.execute(
            select(
                func.sum(Monatswert.eauto_km),
                func.sum(Monatswert.eauto_ladung_gesamt_kwh),
                func.sum(Monatswert.eauto_ladung_pv_kwh),
                func.count(Monatswert.id),
            )
            .where(Monatswert.anlage_id == anlage.id)
            .where(Monatswert.eauto_km.isnot(None))
        )
        row = result.one()

        km_gesamt = row[0] or 0
        ladung_gesamt = row[1] or 0
        ladung_pv = row[2] or 0
        anzahl_monate = row[3] or 0

        if anzahl_monate == 0:
            continue

        km_pro_monat = km_gesamt / anzahl_monate

        # PV-Anteil
        pv_anteil = (ladung_pv / ladung_gesamt * 100) if ladung_gesamt > 0 else None

        # Verbrauch pro 100km
        verbrauch = (ladung_gesamt / km_gesamt * 100) if km_gesamt > 0 else None

        # Kategorisieren
        if km_pro_monat < 500:
            kategorie = wenig
        elif km_pro_monat < 1000:
            kategorie = mittel
        else:
            kategorie = viel

        kategorie["anzahl"] += 1
        if pv_anteil is not None:
            kategorie["pv_anteile"].append(pv_anteil)
        if verbrauch is not None:
            kategorie["verbraeuche"].append(verbrauch)

    klassen = [
        EAutoKlasse(
            klasse="wenig",
            beschreibung="<500 km/Monat",
            anzahl=wenig["anzahl"],
            durchschnitt_pv_anteil=round(sum(wenig["pv_anteile"]) / len(wenig["pv_anteile"]), 1) if wenig["pv_anteile"] else None,
            durchschnitt_verbrauch_100km=round(sum(wenig["verbraeuche"]) / len(wenig["verbraeuche"]), 1) if wenig["verbraeuche"] else None,
        ),
        EAutoKlasse(
            klasse="mittel",
            beschreibung="500-1000 km/Monat",
            anzahl=mittel["anzahl"],
            durchschnitt_pv_anteil=round(sum(mittel["pv_anteile"]) / len(mittel["pv_anteile"]), 1) if mittel["pv_anteile"] else None,
            durchschnitt_verbrauch_100km=round(sum(mittel["verbraeuche"]) / len(mittel["verbraeuche"]), 1) if mittel["verbraeuche"] else None,
        ),
        EAutoKlasse(
            klasse="viel",
            beschreibung=">1000 km/Monat",
            anzahl=viel["anzahl"],
            durchschnitt_pv_anteil=round(sum(viel["pv_anteile"]) / len(viel["pv_anteile"]), 1) if viel["pv_anteile"] else None,
            durchschnitt_verbrauch_100km=round(sum(viel["verbraeuche"]) / len(viel["verbraeuche"]), 1) if viel["verbraeuche"] else None,
        ),
    ]

    return EAutoByUsage(klassen=klassen)
