"""
EEDC Community - Benchmark API
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core import get_db
from models import Anlage, Monatswert
from schemas import AnlageOutput, MonatswertOutput, BenchmarkData

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])


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

    # Benchmark berechnen
    current_year = datetime.utcnow().year
    target_year = current_year if datetime.utcnow().month > 6 else current_year - 1

    # Spez. Ertrag der Anlage
    anlage_ertrag = sum(
        mw.ertrag_kwh for mw in monatswerte if mw.jahr == target_year
    )
    spez_ertrag_anlage = anlage_ertrag / anlage.kwp if anlage.kwp > 0 else 0

    # Durchschnitt aller Anlagen
    result = await db.execute(
        select(
            func.sum(Monatswert.ertrag_kwh),
            func.sum(Anlage.kwp)
        )
        .join(Anlage)
        .where(Monatswert.jahr == target_year)
    )
    row = result.first()
    gesamt_ertrag = row[0] or 0
    gesamt_kwp = row[1] or 1
    spez_ertrag_durchschnitt = gesamt_ertrag / gesamt_kwp

    # Durchschnitt der Region
    result = await db.execute(
        select(
            func.sum(Monatswert.ertrag_kwh),
            func.sum(Anlage.kwp)
        )
        .join(Anlage)
        .where(Monatswert.jahr == target_year)
        .where(Anlage.region == anlage.region)
    )
    row = result.first()
    region_ertrag = row[0] or 0
    region_kwp = row[1] or 1
    spez_ertrag_region = region_ertrag / region_kwp

    # Anzahl Anlagen
    result = await db.execute(select(func.count(Anlage.id)))
    anzahl_gesamt = result.scalar() or 1

    result = await db.execute(
        select(func.count(Anlage.id)).where(Anlage.region == anlage.region)
    )
    anzahl_region = result.scalar() or 1

    # Rang berechnen (wie viele Anlagen haben höheren spez. Ertrag)
    result = await db.execute(
        select(func.count(Anlage.id))
        .join(Monatswert)
        .where(Monatswert.jahr == target_year)
        .group_by(Anlage.id)
        .having(func.sum(Monatswert.ertrag_kwh) / Anlage.kwp > spez_ertrag_anlage)
    )
    bessere_anlagen = len(result.all())
    rang_gesamt = bessere_anlagen + 1

    result = await db.execute(
        select(func.count(Anlage.id))
        .join(Monatswert)
        .where(Monatswert.jahr == target_year)
        .where(Anlage.region == anlage.region)
        .group_by(Anlage.id)
        .having(func.sum(Monatswert.ertrag_kwh) / Anlage.kwp > spez_ertrag_anlage)
    )
    bessere_in_region = len(result.all())
    rang_region = bessere_in_region + 1

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
            anzahl_anlagen_gesamt=anzahl_gesamt,
            rang_region=rang_region,
            anzahl_anlagen_region=anzahl_region,
        ),
        "vergleichs_jahr": target_year,
    }


@router.get("/vergleich")
async def get_vergleich(
    kwp: float = Query(..., gt=0, le=100),
    region: str = Query(..., min_length=2, max_length=2),
    jahr: int = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert Vergleichsdaten für eine Anlage ohne sie zu speichern.
    Nützlich für "Was wäre wenn"-Szenarien.
    """
    target_year = jahr or (datetime.utcnow().year - 1)

    # Durchschnitt aller Anlagen mit ähnlicher Größe (±20%)
    kwp_min = kwp * 0.8
    kwp_max = kwp * 1.2

    result = await db.execute(
        select(
            func.count(Anlage.id).label("anzahl"),
            func.sum(Monatswert.ertrag_kwh).label("sum_ertrag"),
            func.sum(Anlage.kwp).label("sum_kwp"),
        )
        .join(Monatswert)
        .where(Monatswert.jahr == target_year)
        .where(Anlage.kwp >= kwp_min)
        .where(Anlage.kwp <= kwp_max)
    )
    row = result.first()

    if not row or row.anzahl == 0:
        return {
            "nachricht": "Keine vergleichbaren Anlagen gefunden",
            "vergleichs_anlagen": 0,
        }

    spez_ertrag = row.sum_ertrag / row.sum_kwp if row.sum_kwp > 0 else 0

    # Region-spezifisch
    result = await db.execute(
        select(
            func.count(Anlage.id).label("anzahl"),
            func.sum(Monatswert.ertrag_kwh).label("sum_ertrag"),
            func.sum(Anlage.kwp).label("sum_kwp"),
        )
        .join(Monatswert)
        .where(Monatswert.jahr == target_year)
        .where(Anlage.kwp >= kwp_min)
        .where(Anlage.kwp <= kwp_max)
        .where(Anlage.region == region.upper())
    )
    region_row = result.first()
    spez_ertrag_region = (
        region_row.sum_ertrag / region_row.sum_kwp
        if region_row and region_row.sum_kwp > 0
        else None
    )

    return {
        "kwp": kwp,
        "region": region.upper(),
        "vergleichs_jahr": target_year,
        "vergleichs_anlagen_gesamt": row.anzahl,
        "vergleichs_anlagen_region": region_row.anzahl if region_row else 0,
        "durchschnitt_spez_ertrag": round(spez_ertrag, 1),
        "durchschnitt_spez_ertrag_region": (
            round(spez_ertrag_region, 1) if spez_ertrag_region else None
        ),
        "erwarteter_jahresertrag_kwh": round(kwp * spez_ertrag, 0),
    }
