"""
EEDC Community - Statistiken API
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case, distinct
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

    # Durchschnittlicher spez. Jahresertrag
    # Berechnung: Für jede Anlage die letzten 12 Monate summieren, dann Durchschnitt
    durchschnitt_spez_ertrag_jahr = await berechne_jahresertrag(db)

    # Regionen-Statistiken
    regionen = await get_regionen_statistiken(db)

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


async def berechne_jahresertrag(db: AsyncSession) -> float:
    """
    Berechnet den durchschnittlichen spezifischen Jahresertrag.

    Für jede Anlage: Summe der letzten 12 Monate / kWp
    Dann Durchschnitt über alle Anlagen.
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
            # Auf 12 Monate hochrechnen wenn weniger vorhanden
            anzahl_monate = len(ertraege)
            if anzahl_monate >= 6:  # Mindestens 6 Monate für sinnvolle Hochrechnung
                jahres_ertrag_hochgerechnet = (summe_ertrag / anzahl_monate) * 12
                spez_ertrag = jahres_ertrag_hochgerechnet / anlage.kwp
                jahresertraege.append(spez_ertrag)

    if not jahresertraege:
        return 0

    return sum(jahresertraege) / len(jahresertraege)


async def get_regionen_statistiken(db: AsyncSession) -> list[RegionStatistik]:
    """Statistiken pro Region."""
    result = await db.execute(
        select(
            Anlage.region,
            func.count(distinct(Anlage.id)).label("anzahl"),
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
            func.avg(
                case((Anlage.hat_wallbox == True, 1), else_=0)
            ).label("anteil_wallbox"),
            func.avg(
                case((Anlage.hat_balkonkraftwerk == True, 1), else_=0)
            ).label("anteil_bkw"),
        )
        .group_by(Anlage.region)
        .order_by(func.count(Anlage.id).desc())
    )

    regionen = []
    for row in result.all():
        # Spez. Jahresertrag für diese Region (letzte 12 Monate, hochgerechnet)
        spez_ertrag = await berechne_region_jahresertrag(db, row.region)

        # Durchschnittliche Autarkie (alle verfügbaren Monatswerte)
        autarkie_result = await db.execute(
            select(func.avg(Monatswert.autarkie_prozent))
            .join(Anlage)
            .where(Anlage.region == row.region)
            .where(Monatswert.autarkie_prozent.isnot(None))
        )
        avg_autarkie = autarkie_result.scalar()

        # Performance: Speicher Ladung + Entladung (getrennt, Ø pro Monat)
        speicher_result = await db.execute(
            select(
                func.avg(Monatswert.speicher_ladung_kwh),
                func.avg(Monatswert.speicher_entladung_kwh),
            )
            .join(Anlage)
            .where(Anlage.region == row.region)
            .where(Monatswert.speicher_ladung_kwh.isnot(None))
            .where(Monatswert.speicher_entladung_kwh.isnot(None))
            .where(Monatswert.speicher_ladung_kwh + Monatswert.speicher_entladung_kwh > 0)
        )
        sp = speicher_result.one()
        avg_speicher_ladung = round(sp[0], 1) if sp[0] else None
        avg_speicher_entladung = round(sp[1], 1) if sp[1] else None

        # Performance: WP JAZ (Σ Wärme / Σ Strom)
        wp_result = await db.execute(
            select(
                func.sum(Monatswert.wp_heizwaerme_kwh + func.coalesce(Monatswert.wp_warmwasser_kwh, 0)),
                func.sum(Monatswert.wp_stromverbrauch_kwh),
            )
            .join(Anlage)
            .where(Anlage.region == row.region)
            .where(Monatswert.wp_stromverbrauch_kwh > 0)
            .where(Monatswert.wp_heizwaerme_kwh.isnot(None))
        )
        wp_row = wp_result.one()
        avg_wp_jaz = round(wp_row[0] / wp_row[1], 2) if wp_row[0] and wp_row[1] else None

        # Performance: E-Auto km + kWh zuhause geladen (gesamt − extern)
        eauto_result = await db.execute(
            select(
                func.avg(Monatswert.eauto_km),
                func.avg(
                    Monatswert.eauto_ladung_gesamt_kwh
                    - func.coalesce(Monatswert.eauto_ladung_extern_kwh, 0)
                ),
            )
            .join(Anlage)
            .where(Anlage.region == row.region)
            .where(Monatswert.eauto_km.isnot(None))
            .where(Monatswert.eauto_km > 0)
        )
        ea = eauto_result.one()
        avg_eauto_km = round(ea[0], 0) if ea[0] else None
        avg_eauto_ladung = round(ea[1], 1) if ea[1] and ea[1] > 0 else None

        # Performance: Wallbox kWh + PV-Anteil (Σ PV / Σ Gesamt)
        wallbox_result = await db.execute(
            select(
                func.avg(Monatswert.wallbox_ladung_kwh),
                func.sum(Monatswert.wallbox_ladung_pv_kwh),
                func.sum(Monatswert.wallbox_ladung_kwh),
            )
            .join(Anlage)
            .where(Anlage.region == row.region)
            .where(Monatswert.wallbox_ladung_kwh.isnot(None))
            .where(Monatswert.wallbox_ladung_kwh > 0)
        )
        wb = wallbox_result.one()
        avg_wallbox_kwh = round(wb[0], 1) if wb[0] else None
        avg_wallbox_pv_anteil = (
            round(wb[1] / wb[2] * 100, 1)
            if wb[1] and wb[2] and wb[2] > 0
            else None
        )

        # Performance: BKW Ertrag (Ø pro Monat)
        bkw_result = await db.execute(
            select(func.avg(Monatswert.bkw_erzeugung_kwh))
            .join(Anlage)
            .where(Anlage.region == row.region)
            .where(Monatswert.bkw_erzeugung_kwh.isnot(None))
            .where(Monatswert.bkw_erzeugung_kwh > 0)
        )
        avg_bkw_kwh = bkw_result.scalar()

        regionen.append(RegionStatistik(
            region=row.region,
            anzahl_anlagen=row.anzahl,
            durchschnitt_kwp=round(row.avg_kwp, 1),
            durchschnitt_spez_ertrag=round(spez_ertrag, 0),
            durchschnitt_autarkie=round(avg_autarkie, 1) if avg_autarkie else None,
            anteil_mit_speicher=round(row.anteil_speicher * 100, 0),
            anteil_mit_waermepumpe=round(row.anteil_wp * 100, 0),
            anteil_mit_eauto=round(row.anteil_eauto * 100, 0),
            anteil_mit_wallbox=round(row.anteil_wallbox * 100, 0),
            anteil_mit_balkonkraftwerk=round(row.anteil_bkw * 100, 0),
            avg_speicher_ladung_kwh=avg_speicher_ladung,
            avg_speicher_entladung_kwh=avg_speicher_entladung,
            avg_wp_jaz=avg_wp_jaz,
            avg_eauto_km=avg_eauto_km,
            avg_eauto_ladung_kwh=avg_eauto_ladung,
            avg_wallbox_kwh=avg_wallbox_kwh,
            avg_wallbox_pv_anteil=avg_wallbox_pv_anteil,
            avg_bkw_kwh=round(avg_bkw_kwh, 1) if avg_bkw_kwh else None,
        ))

    return regionen


async def berechne_region_jahresertrag(db: AsyncSession, region: str) -> float:
    """Berechnet den spezifischen Jahresertrag für eine Region."""
    # Hole alle Anlagen dieser Region
    anlagen_result = await db.execute(
        select(Anlage).where(Anlage.region == region)
    )
    anlagen = anlagen_result.scalars().all()

    if not anlagen:
        return 0

    jahresertraege = []

    for anlage in anlagen:
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
            if anzahl_monate >= 6:
                jahres_ertrag_hochgerechnet = (summe_ertrag / anzahl_monate) * 12
                spez_ertrag = jahres_ertrag_hochgerechnet / anlage.kwp
                jahresertraege.append(spez_ertrag)

    if not jahresertraege:
        return 0

    return sum(jahresertraege) / len(jahresertraege)


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

        # Berechne Statistiken
        anzahl = len(rows)
        ertraege = [r[0] for r in rows if r[0] is not None]
        spez_ertraege = [r[0] / r[1] for r in rows if r[0] is not None and r[1] and r[1] > 0]

        avg_ertrag = sum(ertraege) / len(ertraege) if ertraege else 0
        avg_spez = sum(spez_ertraege) / len(spez_ertraege) if spez_ertraege else 0
        min_spez = min(spez_ertraege) if spez_ertraege else 0
        max_spez = max(spez_ertraege) if spez_ertraege else 0

        statistiken.append(MonatsStatistik(
            jahr=jahr,
            monat=monat,
            anzahl_anlagen=anzahl,
            durchschnitt_ertrag_kwh=round(avg_ertrag, 1),
            durchschnitt_spez_ertrag=round(avg_spez, 1),
            median_spez_ertrag=round(avg_spez, 1),  # Vereinfacht
            min_spez_ertrag=round(min_spez, 1),
            max_spez_ertrag=round(max_spez, 1),
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
