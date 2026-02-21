"""
EEDC Community - Erweiterte Statistiken API

Diese Endpoints unterstützen das Community-Feature in eedc-homeassistant.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from statistics import median, stdev

from core import get_db
from models import Anlage, Monatswert
from schemas import (
    GlobaleStatistik,
    AusstattungsQuoten,
    TypischeAnlage,
    MonatlicheDurchschnitte,
    MonatsDurchschnitt,
    Verteilung,
    VerteilungsBin,
    VerteilungsStatistik,
    Ranking,
    RankingEintrag,
    RegionStatistik,
)

router = APIRouter(prefix="/statistics", tags=["Erweiterte Statistiken"])


@router.get("/global", response_model=GlobaleStatistik)
async def get_global_statistics(db: AsyncSession = Depends(get_db)):
    """
    Liefert globale Community-Statistiken mit Ausstattungsquoten.

    Verwendet für:
    - Statistiken Tab: Ausstattungsquoten
    - Statistiken Tab: "Die typische Community-Anlage"
    """
    # Anzahl Anlagen
    result = await db.execute(select(func.count(Anlage.id)))
    anzahl_anlagen = result.scalar() or 0

    if anzahl_anlagen == 0:
        return GlobaleStatistik(
            anzahl_anlagen=0,
            anzahl_regionen=0,
            durchschnitt={
                "kwp": 0,
                "spez_ertrag": 0,
                "speicher_kwh": None,
                "autarkie_prozent": None,
                "eigenverbrauch_prozent": None,
            },
            ausstattungsquoten=AusstattungsQuoten(
                speicher=0, waermepumpe=0, eauto=0, wallbox=0, balkonkraftwerk=0
            ),
            typische_anlage=TypischeAnlage(
                kwp=0, ausrichtung="süd", neigung_grad=30, speicher_kwh=None
            ),
            stand=datetime.utcnow().isoformat() + "Z",
        )

    # Anzahl Regionen
    result = await db.execute(select(func.count(distinct(Anlage.region))))
    anzahl_regionen = result.scalar() or 0

    # Durchschnittswerte
    result = await db.execute(
        select(
            func.avg(Anlage.kwp).label("avg_kwp"),
            func.avg(case((Anlage.speicher_kwh > 0, Anlage.speicher_kwh))).label("avg_speicher"),
        )
    )
    row = result.one()
    avg_kwp = row.avg_kwp or 0
    avg_speicher = row.avg_speicher

    # Durchschnittlicher spez. Ertrag (Jahresertrag)
    spez_ertrag = await berechne_community_jahresertrag(db)

    # Durchschnittliche Autarkie und Eigenverbrauch
    result = await db.execute(
        select(
            func.avg(Monatswert.autarkie_prozent).label("avg_autarkie"),
            func.avg(Monatswert.eigenverbrauch_prozent).label("avg_eigenverbrauch"),
        )
        .where(Monatswert.autarkie_prozent.isnot(None))
    )
    row = result.one()
    avg_autarkie = row.avg_autarkie
    avg_eigenverbrauch = row.avg_eigenverbrauch

    # Ausstattungsquoten
    result = await db.execute(
        select(
            func.avg(case((Anlage.speicher_kwh > 0, 1.0), else_=0.0)).label("q_speicher"),
            func.avg(case((Anlage.hat_waermepumpe == True, 1.0), else_=0.0)).label("q_wp"),
            func.avg(case((Anlage.hat_eauto == True, 1.0), else_=0.0)).label("q_eauto"),
            func.avg(case((Anlage.hat_wallbox == True, 1.0), else_=0.0)).label("q_wallbox"),
            func.avg(case((Anlage.hat_balkonkraftwerk == True, 1.0), else_=0.0)).label("q_bkw"),
        )
    )
    row = result.one()

    ausstattungsquoten = AusstattungsQuoten(
        speicher=round((row.q_speicher or 0) * 100, 1),
        waermepumpe=round((row.q_wp or 0) * 100, 1),
        eauto=round((row.q_eauto or 0) * 100, 1),
        wallbox=round((row.q_wallbox or 0) * 100, 1),
        balkonkraftwerk=round((row.q_bkw or 0) * 100, 1),
    )

    # Typische Anlage (häufigste Ausrichtung, Median-Neigung)
    result = await db.execute(
        select(Anlage.ausrichtung, func.count(Anlage.id).label("cnt"))
        .group_by(Anlage.ausrichtung)
        .order_by(func.count(Anlage.id).desc())
        .limit(1)
    )
    row = result.first()
    typische_ausrichtung = row.ausrichtung if row else "süd"

    result = await db.execute(select(Anlage.neigung_grad))
    neigungen = [r[0] for r in result.all() if r[0] is not None]
    typische_neigung = int(median(neigungen)) if neigungen else 30

    typische_anlage = TypischeAnlage(
        kwp=round(avg_kwp, 1),
        ausrichtung=typische_ausrichtung,
        neigung_grad=typische_neigung,
        speicher_kwh=round(avg_speicher, 1) if avg_speicher else None,
    )

    return GlobaleStatistik(
        anzahl_anlagen=anzahl_anlagen,
        anzahl_regionen=anzahl_regionen,
        durchschnitt={
            "kwp": round(avg_kwp, 1),
            "spez_ertrag": round(spez_ertrag, 0),
            "speicher_kwh": round(avg_speicher, 1) if avg_speicher else None,
            "autarkie_prozent": round(avg_autarkie, 1) if avg_autarkie else None,
            "eigenverbrauch_prozent": round(avg_eigenverbrauch, 1) if avg_eigenverbrauch else None,
        },
        ausstattungsquoten=ausstattungsquoten,
        typische_anlage=typische_anlage,
        stand=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/monthly-averages", response_model=MonatlicheDurchschnitte)
async def get_monthly_averages(
    monate: int = Query(12, ge=1, le=60, description="Anzahl Monate"),
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert monatliche Community-Durchschnitte (spez. Ertrag).

    Verwendet für:
    - PV-Ertrag Tab: Monatliche Vergleichslinie
    - Trends Tab: Community-Trend
    """
    # Letzte Monate ermitteln
    result = await db.execute(
        select(Monatswert.jahr, Monatswert.monat)
        .distinct()
        .order_by(Monatswert.jahr.desc(), Monatswert.monat.desc())
        .limit(monate)
    )
    monate_list = result.all()

    durchschnitte = []
    for jahr, monat in reversed(monate_list):  # Chronologisch sortieren
        # Hole alle Monatswerte für diesen Monat mit den zugehörigen Anlagen-kWp
        result = await db.execute(
            select(
                Monatswert.ertrag_kwh,
                Anlage.kwp
            )
            .join(Anlage)
            .where(Monatswert.jahr == jahr)
            .where(Monatswert.monat == monat)
        )
        rows = result.all()

        if not rows:
            continue

        # Berechne spezifischen Ertrag
        spez_ertraege = [r[0] / r[1] for r in rows if r[0] is not None and r[1] and r[1] > 0]

        if spez_ertraege:
            avg_spez = sum(spez_ertraege) / len(spez_ertraege)
            durchschnitte.append(MonatsDurchschnitt(
                jahr=jahr,
                monat=monat,
                spez_ertrag_avg=round(avg_spez, 1),
                anzahl_anlagen=len(spez_ertraege),
            ))

    return MonatlicheDurchschnitte(monate=durchschnitte)


@router.get("/regional", response_model=list[RegionStatistik])
async def get_regional_statistics(db: AsyncSession = Depends(get_db)):
    """
    Liefert Statistiken pro Region für Deutschland-Karte.

    Verwendet für:
    - Regional Tab: Choropleth-Karte
    - Regional Tab: Bundesland-Vergleich
    """
    from api.stats import get_regionen_statistiken
    return await get_regionen_statistiken(db)


@router.get("/regional/{region}", response_model=RegionStatistik)
async def get_region_detail(
    region: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert Detail-Statistiken für eine bestimmte Region.
    """
    from api.stats import get_regionen_statistiken

    region = region.upper()
    regionen = await get_regionen_statistiken(db)

    for r in regionen:
        if r.region == region:
            return r

    # Region nicht gefunden - leere Statistik
    return RegionStatistik(
        region=region,
        anzahl_anlagen=0,
        durchschnitt_kwp=0,
        durchschnitt_spez_ertrag=0,
        durchschnitt_autarkie=None,
        anteil_mit_speicher=0,
        anteil_mit_waermepumpe=0,
        anteil_mit_eauto=0,
        anteil_mit_wallbox=0,
        anteil_mit_balkonkraftwerk=0,
    )


# =============================================================================
# Hilfsfunktionen
# =============================================================================

async def berechne_community_jahresertrag(db: AsyncSession) -> float:
    """
    Berechnet den durchschnittlichen spezifischen Jahresertrag der Community.
    """
    # Hole alle Anlagen
    anlagen_result = await db.execute(select(Anlage))
    anlagen = anlagen_result.scalars().all()

    if not anlagen:
        return 0

    jahresertraege = []

    for anlage in anlagen:
        # Letzte 12 Monate für diese Anlage holen
        monate_detail = await db.execute(
            select(Monatswert.ertrag_kwh)
            .where(Monatswert.anlage_id == anlage.id)
            .order_by(Monatswert.jahr.desc(), Monatswert.monat.desc())
            .limit(12)
        )
        ertraege = [row[0] for row in monate_detail.all() if row[0] is not None]

        if ertraege and anlage.kwp and anlage.kwp > 0:
            summe_ertrag = sum(ertraege)
            anzahl_monate = len(ertraege)
            if anzahl_monate >= 6:  # Mindestens 6 Monate für sinnvolle Hochrechnung
                jahres_ertrag_hochgerechnet = (summe_ertrag / anzahl_monate) * 12
                spez_ertrag = jahres_ertrag_hochgerechnet / anlage.kwp
                jahresertraege.append(spez_ertrag)

    if not jahresertraege:
        return 0

    return sum(jahresertraege) / len(jahresertraege)
