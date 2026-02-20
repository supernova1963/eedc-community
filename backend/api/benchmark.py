"""
EEDC Community - Benchmark API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core import get_db
from models import Anlage, Monatswert
from schemas import AnlageOutput, MonatswertOutput, BenchmarkData

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])


async def berechne_spez_jahresertrag(db: AsyncSession, anlage_id: int, kwp: float) -> float:
    """Berechnet den spezifischen Jahresertrag für eine Anlage (letzte 12 Monate, hochgerechnet)."""
    if kwp <= 0:
        return 0

    monate_result = await db.execute(
        select(Monatswert.ertrag_kwh)
        .where(Monatswert.anlage_id == anlage_id)
        .order_by(Monatswert.jahr.desc(), Monatswert.monat.desc())
        .limit(12)
    )
    ertraege = [row[0] for row in monate_result.all() if row[0] is not None]

    if not ertraege:
        return 0

    summe_ertrag = sum(ertraege)
    anzahl_monate = len(ertraege)

    # Auf 12 Monate hochrechnen
    if anzahl_monate >= 6:
        jahres_ertrag = (summe_ertrag / anzahl_monate) * 12
    else:
        jahres_ertrag = summe_ertrag  # Nicht genug Daten zum Hochrechnen

    return jahres_ertrag / kwp


async def berechne_community_durchschnitt(db: AsyncSession) -> float:
    """Berechnet den Community-Durchschnitt (alle Anlagen, letzte 12 Monate)."""
    anlagen_result = await db.execute(select(Anlage))
    anlagen = anlagen_result.scalars().all()

    if not anlagen:
        return 0

    jahresertraege = []
    for anlage in anlagen:
        spez = await berechne_spez_jahresertrag(db, anlage.id, anlage.kwp)
        if spez > 0:
            jahresertraege.append(spez)

    return sum(jahresertraege) / len(jahresertraege) if jahresertraege else 0


async def berechne_region_durchschnitt(db: AsyncSession, region: str) -> float:
    """Berechnet den Regions-Durchschnitt."""
    anlagen_result = await db.execute(
        select(Anlage).where(Anlage.region == region)
    )
    anlagen = anlagen_result.scalars().all()

    if not anlagen:
        return 0

    jahresertraege = []
    for anlage in anlagen:
        spez = await berechne_spez_jahresertrag(db, anlage.id, anlage.kwp)
        if spez > 0:
            jahresertraege.append(spez)

    return sum(jahresertraege) / len(jahresertraege) if jahresertraege else 0


@router.get("/anlage/{anlage_hash}")
async def get_anlage_benchmark(
    anlage_hash: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert Vergleichsdaten für eine bestimmte Anlage.
    Der Hash identifiziert die Anlage ohne sensible Daten preiszugeben.
    """
    result = await db.execute(
        select(Anlage).where(Anlage.anlage_hash == anlage_hash)
    )
    anlage = result.scalar_one_or_none()

    if not anlage:
        raise HTTPException(status_code=404, detail="Anlage nicht gefunden")

    # Monatswerte laden
    result = await db.execute(
        select(Monatswert)
        .where(Monatswert.anlage_id == anlage.id)
        .order_by(Monatswert.jahr.desc(), Monatswert.monat.desc())
    )
    monatswerte = result.scalars().all()

    # Spez. Jahresertrag der Anlage (letzte 12 Monate, hochgerechnet)
    spez_ertrag_anlage = await berechne_spez_jahresertrag(db, anlage.id, anlage.kwp)

    # Community-Durchschnitt
    spez_ertrag_durchschnitt = await berechne_community_durchschnitt(db)

    # Regions-Durchschnitt
    spez_ertrag_region = await berechne_region_durchschnitt(db, anlage.region)

    # Anzahl Anlagen
    result = await db.execute(select(func.count(Anlage.id)))
    anzahl_gesamt = result.scalar() or 1

    result = await db.execute(
        select(func.count(Anlage.id)).where(Anlage.region == anlage.region)
    )
    anzahl_region = result.scalar() or 1

    # Rang berechnen - basierend auf spez. Jahresertrag
    # Hole alle Anlagen mit ihrem spez. Ertrag
    alle_anlagen = await db.execute(select(Anlage))
    alle = alle_anlagen.scalars().all()

    ertraege_alle = []
    ertraege_region = []

    for a in alle:
        spez = await berechne_spez_jahresertrag(db, a.id, a.kwp)
        if spez > 0:
            ertraege_alle.append((a.id, spez))
            if a.region == anlage.region:
                ertraege_region.append((a.id, spez))

    # Sortieren (höchster Ertrag zuerst)
    ertraege_alle.sort(key=lambda x: x[1], reverse=True)
    ertraege_region.sort(key=lambda x: x[1], reverse=True)

    # Rang finden
    rang_gesamt = 1
    for i, (aid, _) in enumerate(ertraege_alle):
        if aid == anlage.id:
            rang_gesamt = i + 1
            break

    rang_region = 1
    for i, (aid, _) in enumerate(ertraege_region):
        if aid == anlage.id:
            rang_region = i + 1
            break

    # Monatswerte mit spez. Ertrag anreichern
    monatswerte_output = [
        MonatswertOutput(
            jahr=mw.jahr,
            monat=mw.monat,
            ertrag_kwh=mw.ertrag_kwh,
            einspeisung_kwh=mw.einspeisung_kwh,
            netzbezug_kwh=mw.netzbezug_kwh,
            autarkie_prozent=mw.autarkie_prozent,
            eigenverbrauch_prozent=mw.eigenverbrauch_prozent,
            spez_ertrag_kwh_kwp=round(mw.ertrag_kwh / anlage.kwp, 1) if anlage.kwp > 0 else None,
        )
        for mw in monatswerte
    ]

    return {
        "anlage": AnlageOutput(
            anlage_hash=anlage.anlage_hash,
            region=anlage.region,
            kwp=anlage.kwp,
            ausrichtung=anlage.ausrichtung,
            neigung_grad=anlage.neigung_grad,
            speicher_kwh=anlage.speicher_kwh,
            installation_jahr=anlage.installation_jahr,
            hat_waermepumpe=anlage.hat_waermepumpe,
            hat_eauto=anlage.hat_eauto,
            hat_wallbox=anlage.hat_wallbox,
            monatswerte=monatswerte_output,
        ),
        "benchmark": BenchmarkData(
            spez_ertrag_anlage=round(spez_ertrag_anlage, 1),
            spez_ertrag_durchschnitt=round(spez_ertrag_durchschnitt, 1),
            spez_ertrag_region=round(spez_ertrag_region, 1),
            rang_gesamt=rang_gesamt,
            anzahl_anlagen_gesamt=len(ertraege_alle),
            rang_region=rang_region,
            anzahl_anlagen_region=len(ertraege_region),
        ),
        "vergleichs_jahr": "letzte 12 Monate",
    }


@router.get("/vergleich")
async def get_vergleich(
    kwp: float = Query(..., gt=0, le=100),
    region: str = Query(..., min_length=2, max_length=2),
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert Vergleichsdaten für eine Anlage ohne sie zu speichern.
    Nützlich für "Was wäre wenn"-Szenarien.
    """
    # Durchschnitt aller Anlagen mit ähnlicher Größe (±30%)
    kwp_min = kwp * 0.7
    kwp_max = kwp * 1.3

    anlagen_result = await db.execute(
        select(Anlage)
        .where(Anlage.kwp >= kwp_min)
        .where(Anlage.kwp <= kwp_max)
    )
    anlagen = anlagen_result.scalars().all()

    if not anlagen:
        return {
            "nachricht": "Keine vergleichbaren Anlagen gefunden",
            "vergleichs_anlagen": 0,
        }

    ertraege_alle = []
    ertraege_region = []

    for anlage in anlagen:
        spez = await berechne_spez_jahresertrag(db, anlage.id, anlage.kwp)
        if spez > 0:
            ertraege_alle.append(spez)
            if anlage.region == region.upper():
                ertraege_region.append(spez)

    avg_spez = sum(ertraege_alle) / len(ertraege_alle) if ertraege_alle else 0
    avg_spez_region = sum(ertraege_region) / len(ertraege_region) if ertraege_region else None

    return {
        "kwp": kwp,
        "region": region.upper(),
        "vergleichs_anlagen_gesamt": len(ertraege_alle),
        "vergleichs_anlagen_region": len(ertraege_region),
        "durchschnitt_spez_ertrag": round(avg_spez, 1),
        "durchschnitt_spez_ertrag_region": round(avg_spez_region, 1) if avg_spez_region else None,
        "erwarteter_jahresertrag_kwh": round(kwp * avg_spez, 0),
    }
