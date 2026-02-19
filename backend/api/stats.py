"""
EEDC Community - Statistiken API
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from core import get_db
from models import Anlage, Monatswert
from schemas import GesamtStatistik, RegionStatistik, MonatsStatistik

router = APIRouter(prefix="/stats", tags=["Statistiken"])


@router.get("", response_model=GesamtStatistik)
async def get_statistiken(db: AsyncSession = Depends(get_db)):
    """
    Liefert aggregierte Statistiken über alle Anlagen.
    """
    # Anzahl Anlagen
    result = await db.execute(select(func.count(Anlage.id)))
    anzahl_anlagen = result.scalar() or 0

    if anzahl_anlagen == 0:
        return GesamtStatistik(
            anzahl_anlagen=0,
            anzahl_monatswerte=0,
            durchschnitt_kwp=0,
            durchschnitt_speicher_kwh=None,
            durchschnitt_spez_ertrag_jahr=0,
            regionen=[],
            letzte_monate=[],
        )

    # Anzahl Monatswerte
    result = await db.execute(select(func.count(Monatswert.id)))
    anzahl_monatswerte = result.scalar() or 0

    # Durchschnitt kWp
    result = await db.execute(select(func.avg(Anlage.kwp)))
    durchschnitt_kwp = result.scalar() or 0

    # Durchschnitt Speicher (nur Anlagen mit Speicher)
    result = await db.execute(
        select(func.avg(Anlage.speicher_kwh))
        .where(Anlage.speicher_kwh.isnot(None))
        .where(Anlage.speicher_kwh > 0)
    )
    durchschnitt_speicher_kwh = result.scalar()

    # Durchschnittlicher spez. Jahresertrag (letztes vollständiges Jahr)
    current_year = datetime.utcnow().year
    target_year = current_year - 1

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
    durchschnitt_spez_ertrag_jahr = gesamt_ertrag / gesamt_kwp if gesamt_kwp > 0 else 0

    # Regionen-Statistiken
    regionen = await get_regionen_statistiken(db, target_year)

    # Letzte 12 Monate
    letzte_monate = await get_monats_statistiken(db, limit=12)

    return GesamtStatistik(
        anzahl_anlagen=anzahl_anlagen,
        anzahl_monatswerte=anzahl_monatswerte,
        durchschnitt_kwp=round(durchschnitt_kwp, 1),
        durchschnitt_speicher_kwh=round(durchschnitt_speicher_kwh, 1) if durchschnitt_speicher_kwh else None,
        durchschnitt_spez_ertrag_jahr=round(durchschnitt_spez_ertrag_jahr, 0),
        regionen=regionen,
        letzte_monate=letzte_monate,
    )


async def get_regionen_statistiken(db: AsyncSession, jahr: int) -> list[RegionStatistik]:
    """Statistiken pro Region."""
    result = await db.execute(
        select(
            Anlage.region,
            func.count(Anlage.id).label("anzahl"),
            func.avg(Anlage.kwp).label("avg_kwp"),
            func.avg(
                case((Anlage.speicher_kwh > 0, 1), else_=0)
            ).label("anteil_speicher"),
            func.avg(
                case((Anlage.hat_waermepumpe == True, 1), else_=0)
            ).label("anteil_wp"),
            func.avg(
                case((Anlage.hat_eauto == True, 1), else_=0)
            ).label("anteil_eauto"),
        )
        .group_by(Anlage.region)
        .order_by(func.count(Anlage.id).desc())
    )

    regionen = []
    for row in result.all():
        # Spez. Ertrag für diese Region
        ertrag_result = await db.execute(
            select(
                func.sum(Monatswert.ertrag_kwh),
                func.sum(Anlage.kwp)
            )
            .join(Anlage)
            .where(Monatswert.jahr == jahr)
            .where(Anlage.region == row.region)
        )
        ertrag_row = ertrag_result.first()
        region_ertrag = ertrag_row[0] or 0
        region_kwp = ertrag_row[1] or 1
        spez_ertrag = region_ertrag / region_kwp if region_kwp > 0 else 0

        # Durchschnittliche Autarkie
        autarkie_result = await db.execute(
            select(func.avg(Monatswert.autarkie_prozent))
            .join(Anlage)
            .where(Monatswert.jahr == jahr)
            .where(Anlage.region == row.region)
            .where(Monatswert.autarkie_prozent.isnot(None))
        )
        avg_autarkie = autarkie_result.scalar()

        regionen.append(RegionStatistik(
            region=row.region,
            anzahl_anlagen=row.anzahl,
            durchschnitt_kwp=round(row.avg_kwp, 1),
            durchschnitt_spez_ertrag=round(spez_ertrag, 0),
            durchschnitt_autarkie=round(avg_autarkie, 1) if avg_autarkie else None,
            anteil_mit_speicher=round(row.anteil_speicher * 100, 0),
            anteil_mit_waermepumpe=round(row.anteil_wp * 100, 0),
            anteil_mit_eauto=round(row.anteil_eauto * 100, 0),
        ))

    return regionen


async def get_monats_statistiken(db: AsyncSession, limit: int = 12) -> list[MonatsStatistik]:
    """Statistiken pro Monat (letzte X Monate)."""
    # Letzte Monate ermitteln
    result = await db.execute(
        select(Monatswert.jahr, Monatswert.monat)
        .distinct()
        .order_by(Monatswert.jahr.desc(), Monatswert.monat.desc())
        .limit(limit)
    )
    monate = result.all()

    statistiken = []
    for jahr, monat in monate:
        # Aggregierte Werte für diesen Monat
        result = await db.execute(
            select(
                func.count(Monatswert.id).label("anzahl"),
                func.avg(Monatswert.ertrag_kwh).label("avg_ertrag"),
                func.min(Monatswert.ertrag_kwh / Anlage.kwp).label("min_spez"),
                func.max(Monatswert.ertrag_kwh / Anlage.kwp).label("max_spez"),
            )
            .join(Anlage)
            .where(Monatswert.jahr == jahr)
            .where(Monatswert.monat == monat)
        )
        row = result.first()

        # Spezifischer Ertrag (Summe / Summe kWp)
        spez_result = await db.execute(
            select(
                func.sum(Monatswert.ertrag_kwh),
                func.sum(Anlage.kwp)
            )
            .join(Anlage)
            .where(Monatswert.jahr == jahr)
            .where(Monatswert.monat == monat)
        )
        spez_row = spez_result.first()
        sum_ertrag = spez_row[0] or 0
        sum_kwp = spez_row[1] or 1
        avg_spez = sum_ertrag / sum_kwp if sum_kwp > 0 else 0

        statistiken.append(MonatsStatistik(
            jahr=jahr,
            monat=monat,
            anzahl_anlagen=row.anzahl or 0,
            durchschnitt_ertrag_kwh=round(row.avg_ertrag or 0, 1),
            durchschnitt_spez_ertrag=round(avg_spez, 1),
            median_spez_ertrag=round(avg_spez, 1),  # Vereinfacht
            min_spez_ertrag=round(row.min_spez or 0, 1),
            max_spez_ertrag=round(row.max_spez or 0, 1),
        ))

    return statistiken


@router.get("/regionen")
async def get_regionen(db: AsyncSession = Depends(get_db)):
    """Liefert alle Regionen mit Anlagenzahl."""
    result = await db.execute(
        select(Anlage.region, func.count(Anlage.id).label("anzahl"))
        .group_by(Anlage.region)
        .order_by(func.count(Anlage.id).desc())
    )
    return [{"region": r.region, "anzahl": r.anzahl} for r in result.all()]


@router.get("/monat/{jahr}/{monat}", response_model=MonatsStatistik)
async def get_monat_detail(
    jahr: int,
    monat: int,
    db: AsyncSession = Depends(get_db),
):
    """Detaillierte Statistik für einen bestimmten Monat."""
    monate = await get_monats_statistiken(db, limit=100)

    for m in monate:
        if m.jahr == jahr and m.monat == monat:
            return m

    return MonatsStatistik(
        jahr=jahr,
        monat=monat,
        anzahl_anlagen=0,
        durchschnitt_ertrag_kwh=0,
        durchschnitt_spez_ertrag=0,
        median_spez_ertrag=0,
        min_spez_ertrag=0,
        max_spez_ertrag=0,
    )
