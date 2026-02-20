"""
EEDC Community - Benchmark API
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core import get_db
from models import Anlage, Monatswert
from schemas import (
    AnlageOutput, MonatswertOutput, BenchmarkData,
    KPIVergleich, PVBenchmark, SpeicherBenchmark, WaermepumpeBenchmark,
    EAutoBenchmark, WallboxBenchmark, BKWBenchmark, ErweiterteBenchmarkData,
)

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])

# Zeitraum-Typen
ZeitraumTyp = Literal["letzter_monat", "letzte_12_monate", "letztes_vollstaendiges_jahr", "jahr", "seit_installation"]


def get_zeitraum_filter(
    zeitraum: ZeitraumTyp,
    jahr: int | None = None,
    installation_jahr: int | None = None,
) -> tuple[int, int, int, int]:
    """
    Gibt (von_jahr, von_monat, bis_jahr, bis_monat) für den Zeitraum zurück.
    """
    now = datetime.utcnow()

    if zeitraum == "letzter_monat":
        # Vormonat
        if now.month == 1:
            return (now.year - 1, 12, now.year - 1, 12)
        return (now.year, now.month - 1, now.year, now.month - 1)

    elif zeitraum == "letzte_12_monate":
        # Letzte 12 Monate (ohne aktuellen Monat)
        if now.month == 1:
            return (now.year - 2, 1, now.year - 1, 12)
        von_jahr = now.year - 1 if now.month <= 12 else now.year
        von_monat = now.month
        bis_jahr = now.year
        bis_monat = now.month - 1 if now.month > 1 else 12
        return (von_jahr, von_monat, bis_jahr, bis_monat)

    elif zeitraum == "letztes_vollstaendiges_jahr":
        # Vorjahr komplett (Januar bis Dezember)
        vorjahr = now.year - 1
        return (vorjahr, 1, vorjahr, 12)

    elif zeitraum == "jahr" and jahr:
        return (jahr, 1, jahr, 12)

    elif zeitraum == "seit_installation" and installation_jahr:
        return (installation_jahr, 1, now.year, now.month - 1 if now.month > 1 else 12)

    # Default: letzte 12 Monate
    return get_zeitraum_filter("letzte_12_monate")


async def berechne_speicher_kpis(
    db: AsyncSession,
    anlage_id: int,
    kapazitaet: float,
    von_jahr: int, von_monat: int,
    bis_jahr: int, bis_monat: int,
) -> dict | None:
    """Berechnet Speicher-KPIs für einen Zeitraum."""
    if kapazitaet <= 0:
        return None

    result = await db.execute(
        select(
            func.sum(Monatswert.speicher_ladung_kwh),
            func.sum(Monatswert.speicher_entladung_kwh),
            func.sum(Monatswert.speicher_ladung_netz_kwh),
            func.count(Monatswert.id),
        )
        .where(Monatswert.anlage_id == anlage_id)
        .where(
            (Monatswert.jahr > von_jahr) |
            ((Monatswert.jahr == von_jahr) & (Monatswert.monat >= von_monat))
        )
        .where(
            (Monatswert.jahr < bis_jahr) |
            ((Monatswert.jahr == bis_jahr) & (Monatswert.monat <= bis_monat))
        )
    )
    row = result.first()
    if not row or not row[0]:
        return None

    ladung, entladung, ladung_netz, monate = row
    ladung = ladung or 0
    entladung = entladung or 0
    ladung_netz = ladung_netz or 0

    if ladung == 0:
        return None

    # Zyklen = Entladung / Kapazität (auf Jahr hochrechnen)
    zyklen = entladung / kapazitaet
    if monate > 0 and monate < 12:
        zyklen = zyklen * (12 / monate)

    # Wirkungsgrad = Entladung / Ladung
    wirkungsgrad = (entladung / ladung * 100) if ladung > 0 else None

    # Netz-Anteil
    netz_anteil = (ladung_netz / ladung * 100) if ladung > 0 else None

    return {
        "zyklen_jahr": round(zyklen, 0),
        "wirkungsgrad": round(wirkungsgrad, 1) if wirkungsgrad else None,
        "netz_anteil": round(netz_anteil, 1) if netz_anteil else None,
    }


async def berechne_wp_kpis(
    db: AsyncSession,
    anlage_id: int,
    von_jahr: int, von_monat: int,
    bis_jahr: int, bis_monat: int,
) -> dict | None:
    """Berechnet Wärmepumpe-KPIs für einen Zeitraum."""
    result = await db.execute(
        select(
            func.sum(Monatswert.wp_stromverbrauch_kwh),
            func.sum(Monatswert.wp_heizwaerme_kwh),
            func.sum(Monatswert.wp_warmwasser_kwh),
        )
        .where(Monatswert.anlage_id == anlage_id)
        .where(
            (Monatswert.jahr > von_jahr) |
            ((Monatswert.jahr == von_jahr) & (Monatswert.monat >= von_monat))
        )
        .where(
            (Monatswert.jahr < bis_jahr) |
            ((Monatswert.jahr == bis_jahr) & (Monatswert.monat <= bis_monat))
        )
    )
    row = result.first()
    if not row or not row[0]:
        return None

    strom, heiz, ww = row
    strom = strom or 0
    heiz = heiz or 0
    ww = ww or 0

    if strom == 0:
        return None

    waerme_gesamt = heiz + ww
    jaz = waerme_gesamt / strom if strom > 0 else None

    return {
        "stromverbrauch": round(strom, 1),
        "waermeerzeugung": round(waerme_gesamt, 1),
        "jaz": round(jaz, 2) if jaz else None,
    }


async def berechne_eauto_kpis(
    db: AsyncSession,
    anlage_id: int,
    von_jahr: int, von_monat: int,
    bis_jahr: int, bis_monat: int,
) -> dict | None:
    """Berechnet E-Auto-KPIs für einen Zeitraum."""
    result = await db.execute(
        select(
            func.sum(Monatswert.eauto_ladung_gesamt_kwh),
            func.sum(Monatswert.eauto_ladung_pv_kwh),
            func.sum(Monatswert.eauto_km),
            func.sum(Monatswert.eauto_v2h_kwh),
        )
        .where(Monatswert.anlage_id == anlage_id)
        .where(
            (Monatswert.jahr > von_jahr) |
            ((Monatswert.jahr == von_jahr) & (Monatswert.monat >= von_monat))
        )
        .where(
            (Monatswert.jahr < bis_jahr) |
            ((Monatswert.jahr == bis_jahr) & (Monatswert.monat <= bis_monat))
        )
    )
    row = result.first()
    if not row or not row[0]:
        return None

    ladung, pv, km, v2h = row
    ladung = ladung or 0
    pv = pv or 0
    km = km or 0
    v2h = v2h or 0

    if ladung == 0:
        return None

    pv_anteil = (pv / ladung * 100) if ladung > 0 else None
    verbrauch_100km = (ladung / km * 100) if km > 0 else None

    return {
        "ladung_gesamt": round(ladung, 1),
        "pv_anteil": round(pv_anteil, 1) if pv_anteil else None,
        "km": round(km, 0) if km > 0 else None,
        "verbrauch_100km": round(verbrauch_100km, 1) if verbrauch_100km else None,
        "v2h": round(v2h, 1) if v2h > 0 else None,
    }


async def berechne_community_avg_jaz(db: AsyncSession) -> float | None:
    """Berechnet den Community-Durchschnitt für JAZ."""
    # Hole alle Anlagen mit WP
    result = await db.execute(
        select(Anlage.id).where(Anlage.hat_waermepumpe == True)
    )
    anlage_ids = [row[0] for row in result.all()]

    if not anlage_ids:
        return None

    jaz_values = []
    for aid in anlage_ids:
        wp = await berechne_wp_kpis(db, aid, 2020, 1, 2099, 12)
        if wp and wp.get("jaz"):
            jaz_values.append(wp["jaz"])

    return sum(jaz_values) / len(jaz_values) if jaz_values else None


async def berechne_community_avg_pv_anteil_eauto(db: AsyncSession) -> float | None:
    """Berechnet den Community-Durchschnitt für E-Auto PV-Anteil."""
    result = await db.execute(
        select(Anlage.id).where(Anlage.hat_eauto == True)
    )
    anlage_ids = [row[0] for row in result.all()]

    if not anlage_ids:
        return None

    pv_anteile = []
    for aid in anlage_ids:
        ea = await berechne_eauto_kpis(db, aid, 2020, 1, 2099, 12)
        if ea and ea.get("pv_anteil"):
            pv_anteile.append(ea["pv_anteil"])

    return sum(pv_anteile) / len(pv_anteile) if pv_anteile else None


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
    zeitraum: ZeitraumTyp = Query("letzte_12_monate", description="Vergleichszeitraum"),
    jahr: int | None = Query(None, ge=2010, le=2050, description="Jahr für zeitraum=jahr"),
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert Vergleichsdaten für eine bestimmte Anlage.
    Der Hash identifiziert die Anlage ohne sensible Daten preiszugeben.

    Zeitraum-Optionen:
    - letzter_monat: Nur der Vormonat
    - letzte_12_monate: Die letzten 12 abgeschlossenen Monate (Standard)
    - jahr: Ein bestimmtes Jahr (Parameter 'jahr' erforderlich)
    - seit_installation: Alle Daten seit Installationsjahr
    """
    result = await db.execute(
        select(Anlage).where(Anlage.anlage_hash == anlage_hash)
    )
    anlage = result.scalar_one_or_none()

    if not anlage:
        raise HTTPException(status_code=404, detail="Anlage nicht gefunden")

    # Zeitraum-Filter bestimmen
    von_jahr, von_monat, bis_jahr, bis_monat = get_zeitraum_filter(
        zeitraum, jahr, anlage.installation_jahr
    )

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
            # Komponenten-KPIs
            speicher_ladung_kwh=mw.speicher_ladung_kwh,
            speicher_entladung_kwh=mw.speicher_entladung_kwh,
            speicher_ladung_netz_kwh=mw.speicher_ladung_netz_kwh,
            wp_stromverbrauch_kwh=mw.wp_stromverbrauch_kwh,
            wp_heizwaerme_kwh=mw.wp_heizwaerme_kwh,
            wp_warmwasser_kwh=mw.wp_warmwasser_kwh,
            eauto_ladung_gesamt_kwh=mw.eauto_ladung_gesamt_kwh,
            eauto_ladung_pv_kwh=mw.eauto_ladung_pv_kwh,
            eauto_ladung_extern_kwh=mw.eauto_ladung_extern_kwh,
            eauto_km=mw.eauto_km,
            eauto_v2h_kwh=mw.eauto_v2h_kwh,
            wallbox_ladung_kwh=mw.wallbox_ladung_kwh,
            wallbox_ladung_pv_kwh=mw.wallbox_ladung_pv_kwh,
            wallbox_ladevorgaenge=mw.wallbox_ladevorgaenge,
            bkw_erzeugung_kwh=mw.bkw_erzeugung_kwh,
            bkw_eigenverbrauch_kwh=mw.bkw_eigenverbrauch_kwh,
            bkw_speicher_ladung_kwh=mw.bkw_speicher_ladung_kwh,
            bkw_speicher_entladung_kwh=mw.bkw_speicher_entladung_kwh,
            sonstiges_verbrauch_kwh=mw.sonstiges_verbrauch_kwh,
        )
        for mw in monatswerte
    ]

    # Erweiterte Komponenten-Benchmarks berechnen
    erweiterte_benchmarks = None

    # PV-Benchmark (immer vorhanden)
    pv_benchmark = PVBenchmark(
        spez_ertrag=KPIVergleich(
            wert=round(spez_ertrag_anlage, 1),
            community_avg=round(spez_ertrag_durchschnitt, 1),
            rang=rang_gesamt,
            von=len(ertraege_alle),
        ),
    )

    # Speicher-Benchmark
    speicher_benchmark = None
    if anlage.speicher_kwh and anlage.speicher_kwh > 0:
        speicher_kpis = await berechne_speicher_kpis(
            db, anlage.id, anlage.speicher_kwh,
            von_jahr, von_monat, bis_jahr, bis_monat
        )
        if speicher_kpis:
            speicher_benchmark = SpeicherBenchmark(
                kapazitaet=KPIVergleich(wert=anlage.speicher_kwh),
                zyklen_jahr=KPIVergleich(wert=speicher_kpis["zyklen_jahr"]) if speicher_kpis.get("zyklen_jahr") else None,
                wirkungsgrad=KPIVergleich(wert=speicher_kpis["wirkungsgrad"]) if speicher_kpis.get("wirkungsgrad") else None,
                netz_anteil=KPIVergleich(wert=speicher_kpis["netz_anteil"]) if speicher_kpis.get("netz_anteil") else None,
            )

    # Wärmepumpe-Benchmark
    wp_benchmark = None
    if anlage.hat_waermepumpe:
        wp_kpis = await berechne_wp_kpis(db, anlage.id, von_jahr, von_monat, bis_jahr, bis_monat)
        if wp_kpis:
            community_jaz = await berechne_community_avg_jaz(db)
            wp_benchmark = WaermepumpeBenchmark(
                jaz=KPIVergleich(
                    wert=wp_kpis["jaz"],
                    community_avg=round(community_jaz, 2) if community_jaz else None,
                ) if wp_kpis.get("jaz") else None,
                stromverbrauch=KPIVergleich(wert=wp_kpis["stromverbrauch"]) if wp_kpis.get("stromverbrauch") else None,
                waermeerzeugung=KPIVergleich(wert=wp_kpis["waermeerzeugung"]) if wp_kpis.get("waermeerzeugung") else None,
            )

    # E-Auto-Benchmark
    eauto_benchmark = None
    if anlage.hat_eauto:
        eauto_kpis = await berechne_eauto_kpis(db, anlage.id, von_jahr, von_monat, bis_jahr, bis_monat)
        if eauto_kpis:
            community_pv_anteil = await berechne_community_avg_pv_anteil_eauto(db)
            eauto_benchmark = EAutoBenchmark(
                ladung_gesamt=KPIVergleich(wert=eauto_kpis["ladung_gesamt"]) if eauto_kpis.get("ladung_gesamt") else None,
                pv_anteil=KPIVergleich(
                    wert=eauto_kpis["pv_anteil"],
                    community_avg=round(community_pv_anteil, 1) if community_pv_anteil else None,
                ) if eauto_kpis.get("pv_anteil") else None,
                km=KPIVergleich(wert=eauto_kpis["km"]) if eauto_kpis.get("km") else None,
                verbrauch_100km=KPIVergleich(wert=eauto_kpis["verbrauch_100km"]) if eauto_kpis.get("verbrauch_100km") else None,
                v2h=KPIVergleich(wert=eauto_kpis["v2h"]) if eauto_kpis.get("v2h") else None,
            )

    erweiterte_benchmarks = ErweiterteBenchmarkData(
        pv=pv_benchmark,
        speicher=speicher_benchmark,
        waermepumpe=wp_benchmark,
        eauto=eauto_benchmark,
    )

    # Zeitraum-Label
    zeitraum_labels = {
        "letzter_monat": f"{bis_monat:02d}/{bis_jahr}",
        "letzte_12_monate": "letzte 12 Monate",
        "jahr": f"Jahr {jahr}" if jahr else "Jahr",
        "seit_installation": f"seit {anlage.installation_jahr}",
    }

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
            hat_balkonkraftwerk=anlage.hat_balkonkraftwerk,
            hat_sonstiges=anlage.hat_sonstiges,
            wallbox_kw=anlage.wallbox_kw,
            bkw_wp=anlage.bkw_wp,
            sonstiges_bezeichnung=anlage.sonstiges_bezeichnung,
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
        "benchmark_erweitert": erweiterte_benchmarks,
        "zeitraum": zeitraum,
        "zeitraum_label": zeitraum_labels.get(zeitraum, zeitraum),
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
