"""
Trend-Endpoints für zeitliche Entwicklungen.

Phase 4 der Community-Server-Erweiterung.
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, extract, case
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Anlage, Monatswert
from schemas import (
    TrendPunkt,
    TrendDaten,
    AlterErtrag,
    DegradationsAnalyse,
)

router = APIRouter(prefix="/trends", tags=["Trends"])


# WICHTIG: /degradation MUSS vor /{period} stehen, sonst wird es als period="degradation" gematcht!
@router.get("/degradation", response_model=DegradationsAnalyse)
async def get_degradation(
    db: AsyncSession = Depends(get_db)
):
    """
    Ertrags-Analyse nach Anlagenalter.

    Zeigt den durchschnittlichen spezifischen Ertrag gruppiert nach
    Anlagenalter (Jahre seit Installation). Ermöglicht Rückschlüsse
    auf die typische Degradation von PV-Anlagen.
    """
    now = datetime.now()
    aktuelles_jahr = now.year

    # Spezifischen Ertrag nach Anlagenalter berechnen
    # Nur Anlagen mit vollständigen Jahreswerten (mind. 3 Anlagen)

    alter_stats = []

    for alter in range(1, 16):  # 1 bis 15 Jahre
        installations_jahr = aktuelles_jahr - alter

        # Durchschnittlicher spez. Ertrag für Anlagen dieses Alters
        # Basierend auf den letzten 12 Monaten
        # JOIN über anlage_id (Fremdschlüssel)
        stmt = select(
            func.count(func.distinct(Anlage.anlage_hash)).label("anzahl"),
            func.sum(Monatswert.ertrag_kwh).label("gesamt_erzeugung"),
            func.sum(Anlage.kwp).label("gesamt_kwp"),
        ).select_from(Monatswert).join(
            Anlage, Monatswert.anlage_id == Anlage.id
        ).where(
            Anlage.installation_jahr == installations_jahr,
            Anlage.kwp > 0,
            Monatswert.ertrag_kwh > 0,
            # Letzte 12 Monate
            ((Monatswert.jahr == aktuelles_jahr) |
             ((Monatswert.jahr == aktuelles_jahr - 1) & (Monatswert.monat > now.month)))
        )

        result = await db.execute(stmt)
        row = result.first()

        if row and row.anzahl and row.anzahl >= 3 and row.gesamt_kwp and row.gesamt_kwp > 0:
            # Spezifischer Ertrag = Gesamterzeugung / Gesamt-kWp
            spez_ertrag = row.gesamt_erzeugung / row.gesamt_kwp
            alter_stats.append(AlterErtrag(
                alter_jahre=alter,
                anzahl=row.anzahl,
                durchschnitt_spez_ertrag=round(spez_ertrag, 0)
            ))

    # Degradation berechnen (lineare Regression)
    degradation_prozent = 0.0
    if len(alter_stats) >= 3:
        # Einfache lineare Approximation
        erster_ertrag = alter_stats[0].durchschnitt_spez_ertrag if alter_stats else 0
        letzter_ertrag = alter_stats[-1].durchschnitt_spez_ertrag if alter_stats else 0
        jahre_diff = alter_stats[-1].alter_jahre - alter_stats[0].alter_jahre if len(alter_stats) > 1 else 1

        if erster_ertrag > 0 and jahre_diff > 0:
            gesamt_verlust = (erster_ertrag - letzter_ertrag) / erster_ertrag * 100
            degradation_prozent = gesamt_verlust / jahre_diff

    return DegradationsAnalyse(
        nach_alter=alter_stats,
        durchschnittliche_degradation_prozent_jahr=round(degradation_prozent, 2)
    )


@router.get("/{period}", response_model=TrendDaten)
async def get_trends(
    period: Literal["12_monate", "24_monate", "gesamt"],
    db: AsyncSession = Depends(get_db)
):
    """
    Zeitliche Entwicklung der Community-Daten.

    Zeigt wie sich Anlagenzahl, durchschnittliche kWp, Speicher-Quote,
    Wärmepumpen-Quote und E-Auto-Quote über die Zeit entwickelt haben.
    """
    now = datetime.now()

    # Zeitraum bestimmen
    if period == "12_monate":
        monate_zurueck = 12
    elif period == "24_monate":
        monate_zurueck = 24
    else:  # gesamt
        monate_zurueck = 60  # Max 5 Jahre

    # Start-Monat berechnen
    start_jahr = now.year
    start_monat = now.month - monate_zurueck
    while start_monat <= 0:
        start_monat += 12
        start_jahr -= 1

    # Alle relevanten Monate generieren
    monate = []
    current_jahr = start_jahr
    current_monat = start_monat
    while (current_jahr, current_monat) <= (now.year, now.month):
        monate.append(f"{current_jahr:04d}-{current_monat:02d}")
        current_monat += 1
        if current_monat > 12:
            current_monat = 1
            current_jahr += 1

    # Trend-Daten pro Monat sammeln
    anzahl_anlagen_trend = []
    durchschnitt_kwp_trend = []
    speicher_quote_trend = []
    waermepumpe_quote_trend = []
    eauto_quote_trend = []

    for monat_str in monate:
        jahr, monat = map(int, monat_str.split("-"))

        # Anlagen die zu diesem Zeitpunkt existierten (basierend auf erstem Monatswert)
        # JOIN über anlage_id (Fremdschlüssel)
        stmt = select(
            func.count(func.distinct(Anlage.anlage_hash)).label("anzahl"),
            func.avg(Anlage.kwp).label("avg_kwp"),
            func.sum(case((Anlage.speicher_kwh > 0, 1), else_=0)).label("mit_speicher"),
            func.sum(case((Anlage.hat_waermepumpe == True, 1), else_=0)).label("mit_wp"),
            func.sum(case((Anlage.hat_eauto == True, 1), else_=0)).label("mit_eauto"),
        ).select_from(Monatswert).join(
            Anlage, Monatswert.anlage_id == Anlage.id
        ).where(
            (Monatswert.jahr < jahr) |
            ((Monatswert.jahr == jahr) & (Monatswert.monat <= monat))
        )

        result = await db.execute(stmt)
        row = result.first()

        if row and row.anzahl and row.anzahl > 0:
            anzahl = row.anzahl
            anzahl_anlagen_trend.append(TrendPunkt(monat=monat_str, wert=anzahl))

            if row.avg_kwp:
                durchschnitt_kwp_trend.append(TrendPunkt(monat=monat_str, wert=round(row.avg_kwp, 1)))

            # Quoten berechnen
            if row.mit_speicher is not None:
                quote = (row.mit_speicher / anzahl) * 100
                speicher_quote_trend.append(TrendPunkt(monat=monat_str, wert=round(quote, 1)))

            if row.mit_wp is not None:
                quote = (row.mit_wp / anzahl) * 100
                waermepumpe_quote_trend.append(TrendPunkt(monat=monat_str, wert=round(quote, 1)))

            if row.mit_eauto is not None:
                quote = (row.mit_eauto / anzahl) * 100
                eauto_quote_trend.append(TrendPunkt(monat=monat_str, wert=round(quote, 1)))

    return TrendDaten(
        period=period,
        trends={
            "anzahl_anlagen": anzahl_anlagen_trend,
            "durchschnitt_kwp": durchschnitt_kwp_trend,
            "speicher_quote": speicher_quote_trend,
            "waermepumpe_quote": waermepumpe_quote_trend,
            "eauto_quote": eauto_quote_trend,
        }
    )
