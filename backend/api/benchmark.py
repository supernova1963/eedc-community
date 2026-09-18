"""
EEDC Community - Benchmark API
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core import get_db
from core.spez_ertrag import (
    FENSTER_MONATE,
    durchschnitt,
    lade_spez_jahresertrag,
    lade_spez_jahresertraege,
    nur_abgeschlossene_monate,
)
from core.wp_jaz import (
    MONATS_ARBEITSZAHL_MAX,
    anlagen_filter,
    anlagen_jaz,
    durchschnitts_jaz,
    funktionsfremd_abzug_zeile,
)
from models import Anlage, Monatswert
from schemas import (
    AnlageOutput, MonatswertOutput, BenchmarkData,
    KPIVergleich, PVBenchmark, SpeicherBenchmark, WaermepumpeBenchmark,
    EAutoBenchmark, WallboxBenchmark, BKWBenchmark, ErweiterteBenchmarkData,
    MonatsVergleich, MonatsKPI, MonatsRegionVergleich,
)

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])

# Zeitraum-Typen
ZeitraumTyp = Literal["letzter_monat", "letzte_12_monate", "letztes_vollstaendiges_jahr", "jahr", "seit_installation", "monat"]


def get_zeitraum_filter(
    zeitraum: ZeitraumTyp,
    jahr: int | None = None,
    monat: int | None = None,
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

    elif zeitraum == "monat" and jahr and monat:
        return (jahr, monat, jahr, monat)

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
            # N-524: die Basis sind die Monate MIT Speicherwert — COUNT(id)
            # zählte auch Zeilen ohne ihn und machte die Hochrechnung schief.
            func.count(Monatswert.speicher_entladung_kwh),
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
        # F-76 (18.09.2026): der laufende Kalendermonat zählt in KEINEM Aggregat
        # (Server-F-48) — auf beiden Seiten des Vergleichs, mit derselben Filterzeile.
        .where(nur_abgeschlossene_monate())
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

    # Wirkungsgrad = Entladung / Ladung.
    # eedc F-23: über 100 % kann kein Speicher — solche Werte stammen aus
    # nicht zusammenpassenden Messstellen (DC gegen AC) und werden als
    # „unbekannt" ausgewiesen, nicht als Messung. Geklemmt wird NICHT: ein auf
    # 100 % gestutzter Wert sähe aus wie ein perfekter Speicher.
    # Import lokal — `components` liest `get_zeitraum_filter` aus diesem Modul.
    from api.components import (
        WIRKUNGSGRAD_MAX_PROZENT,
        WIRKUNGSGRAD_MIN_PROZENT,
    )

    wirkungsgrad = (entladung / ladung * 100) if ladung > 0 else None
    if wirkungsgrad is not None and not (
        WIRKUNGSGRAD_MIN_PROZENT <= wirkungsgrad <= WIRKUNGSGRAD_MAX_PROZENT
    ):
        wirkungsgrad = None

    # Netz-Anteil
    netz_anteil = (ladung_netz / ladung * 100) if ladung > 0 else None

    return {
        "zyklen_jahr": round(zyklen, 0),
        "wirkungsgrad": round(wirkungsgrad, 1) if wirkungsgrad else None,
        "netz_anteil": round(netz_anteil, 1) if netz_anteil else None,
        # N-524: worauf die Hochrechnung steht („aus 5 von 12 Monaten") — die
        # Klasse, die #387 für den spez. Ertrag geschlossen hat.
        "basis_monate": int(monate or 0),
    }


async def berechne_wp_kpis(
    db: AsyncSession,
    anlage_id: int,
    von_jahr: int, von_monat: int,
    bis_jahr: int, bis_monat: int,
) -> dict | None:
    """Berechnet Wärmepumpe-KPIs für einen Zeitraum.

    ⭐ **Der Kühlstrom gehört nicht in den JAZ-Nenner** (eedc **W-14**, SOLL
    Wärme/Klima §4.2 Fall 4). Der JAZ hier ist ``(Heizwärme + Warmwasser) ÷
    Stromverbrauch``. Wer kühlt, hat diesen Strom im Nenner — die zugehörige
    **Kältemenge** steht aber in keinem Zähler, weil eedc sie nicht als Wärme
    führt (und die meisten Anlagen keinen Kältemengenzähler haben). Eine
    kühlende Anlage stand damit systematisch schlechter da als eine, die nicht
    kühlt, und zwar unabhängig davon, ob aktiv oder passiv gekühlt wird.

    ⚠ **Der Server rechnet die Größe nicht aus — er bekommt sie geliefert.** Er
    hat die Betriebsart-Spur nie gesehen; ``wp_strom_kuehlen_kwh`` kommt aus dem
    Client (eedc ab 2026-08-26). ``NULL`` heißt „unbekannt" und wird wie 0 behandelt
    — das ist genau der Altbestand, für den bisher gar nichts abgezogen wurde.

    ⛔ **Der Abzug passiert hier NICHT mehr, sondern in ``anlagen_jaz``** — die
    Query unten liefert nur noch die **Mengen**. Bis zum 13.09.2026 summierte sie
    zusätzlich ``wp_strom_kuehlen_kwh`` und klemmte den Wert auf ``[0, strom]``;
    seit `85c75a2` (06.09.) kam die Kennzahl aber aus dem SoT, und **niemand las
    das Ergebnis mehr**. Entfernt, weil es sonst wie eine fünfte Rechenstelle
    aussieht: Bei der Erhebung zu N-454 wurde es genau so gezählt. *Toter Code an
    einer Regel-Stelle ist eine Behauptung über die Regel.*
    """
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
    # ⭐ 06.09.2026 — die KENNZAHL kommt aus dem SoT (`core/wp_jaz.py`), die
    # MENGEN aus der Query darueber (E1 — Mengen summiert, Kennzahlen getrennt).
    # Der Unterschied ist der P12-Filter: er darf die Arbeitszahl sperren, aber
    # nie eine gemessene Kilowattstunde aus einer Mengen-Auswertung nehmen.
    #
    # ⛔ Warum der eigene Wert dieselbe Formel braucht wie der Vergleichswert:
    # Sonst steht in der Kachel „dein 3,6 gegen Ø 4,45", und die zwei Zahlen
    # sind nach verschiedenen Regeln entstanden — genau der Befund, aus dem
    # dieses Modul hervorgegangen ist (rapahl, PN 92196).
    jaz = await anlagen_jaz(
        db, anlage_id,
        von_jahr=von_jahr, von_monat=von_monat,
        bis_jahr=bis_jahr, bis_monat=bis_monat,
    )

    return {
        # `stromverbrauch` bleibt der GESAMTE Verbrauch — er ist eine Menge und
        # wird als solche verglichen, nicht als Kennzahl-Nenner.
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
        # F-76 (18.09.2026): der laufende Kalendermonat zählt in KEINEM Aggregat
        # (Server-F-48) — auf beiden Seiten des Vergleichs, mit derselben Filterzeile.
        .where(nur_abgeschlossene_monate())
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


async def berechne_community_avg_jaz(db: AsyncSession, wp_art: str | None = None) -> tuple[float | None, int]:
    """
    Berechnet den Community-Durchschnitt für JAZ.

    Args:
        wp_art: Optional — wenn gesetzt, nur Anlagen mit gleicher WP-Art.

    ⛔ **Passiv gekühlte Anlagen zählen hier nicht mit** (eedc SOLL §4.1/§7 A5).
    Passive Kühlung läuft nur über Umwälzpumpen; ihre Effizienz liegt um ein
    Vielfaches über der aktiv gekühlter Anlagen. Ihre **eigene** Kennzahl ist
    korrekt und wird weiter angezeigt — was eine Falschaussage wäre, ist sie in
    denselben Durchschnitt zu werfen. ``NULL`` (Altbestand) zählt mit: unbekannt
    ist nicht passiv.
    """
    # ⭐ 06.09.2026 — EIN Rechenweg fuer alle Vergleichswerte (`core/wp_jaz.py`).
    # Hier stand bis dahin eine eigene Anlagen-Auswahl plus eine Schleife ueber
    # `berechne_wp_kpis`, die den **P12-Filter nicht kannte**: ein Monat mit
    # verschieden abgegrenztem Zaehler und Nenner ging in den Vergleichswert
    # ein, obwohl der Client ihn ausdruecklich als nicht belastbar meldet.
    result = await db.execute(anlagen_filter(wp_art=wp_art))
    anlage_ids = [row[0] for row in result.all()]
    if not anlage_ids:
        return None, 0
    # F-76 (18.09.2026): n reist mit — die Route trug `KPIVergleich.von` nie,
    # obwohl `durchschnitts_jaz` es liefert.
    return await durchschnitts_jaz(db, anlage_ids)


async def berechne_community_avg_pv_anteil_eauto(
    db: AsyncSession,
    von_jahr: int, von_monat: int, bis_jahr: int, bis_monat: int,
) -> tuple[float | None, int]:
    """Community-Ø des E-Auto-PV-Anteils **im Fenster des eigenen Werts** — und n.

    ⛔ **F-76 (18.09.2026):** Bis dahin rechnete diese Seite fest 2020-01…2099-12
    — die ganze Historie jeder Anlage samt laufendem Monat —, während der eigene
    Wert daneben das angefragte Fenster (zwölf abgeschlossene Monate) nahm.
    Gemessen: 50,0 % eigen gegen Ø 23,3 %. Die Kachel verglich zwei verschieden
    gebildete Größen und nannte es einen Vergleich. Jetzt bekommt der Ø dasselbe
    Fenster und nennt seine Grundgesamtheit (``KPIVergleich.von``).
    """
    result = await db.execute(
        select(Anlage.id).where(Anlage.hat_eauto == True)
    )
    anlage_ids = [row[0] for row in result.all()]

    if not anlage_ids:
        return None, 0

    pv_anteile = []
    for aid in anlage_ids:
        ea = await berechne_eauto_kpis(db, aid, von_jahr, von_monat, bis_jahr, bis_monat)
        if ea and ea.get("pv_anteil"):
            pv_anteile.append(ea["pv_anteil"])

    if not pv_anteile:
        return None, 0
    return sum(pv_anteile) / len(pv_anteile), len(pv_anteile)


async def berechne_wallbox_kpis(
    db: AsyncSession,
    anlage_id: int,
    von_jahr: int, von_monat: int,
    bis_jahr: int, bis_monat: int,
) -> dict | None:
    """Berechnet Wallbox-KPIs für einen Zeitraum."""
    result = await db.execute(
        select(
            func.sum(Monatswert.wallbox_ladung_kwh),
            func.sum(Monatswert.wallbox_ladung_pv_kwh),
            func.sum(Monatswert.wallbox_ladevorgaenge),
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
        # F-76 (18.09.2026): der laufende Kalendermonat zählt in KEINEM Aggregat
        # (Server-F-48) — auf beiden Seiten des Vergleichs, mit derselben Filterzeile.
        .where(nur_abgeschlossene_monate())
    )
    row = result.first()
    if not row or not row[0]:
        return None

    ladung, pv_ladung, ladevorgaenge, monate = row
    ladung = ladung or 0
    pv_ladung = pv_ladung or 0
    ladevorgaenge = ladevorgaenge or 0

    if ladung == 0:
        return None

    pv_anteil = (pv_ladung / ladung * 100) if ladung > 0 else None

    return {
        "ladung": round(ladung, 1),
        "pv_anteil": round(pv_anteil, 1) if pv_anteil else None,
        "ladevorgaenge": ladevorgaenge if ladevorgaenge > 0 else None,
    }


async def berechne_community_avg_pv_anteil_wallbox(
    db: AsyncSession,
    von_jahr: int, von_monat: int, bis_jahr: int, bis_monat: int,
) -> tuple[float | None, int]:
    """Community-Ø des Wallbox-PV-Anteils im Fenster des eigenen Werts — und n (F-76, s. E-Auto)."""
    result = await db.execute(
        select(Anlage.id).where(Anlage.hat_wallbox == True)
    )
    anlage_ids = [row[0] for row in result.all()]

    if not anlage_ids:
        return None, 0

    pv_anteile = []
    for aid in anlage_ids:
        wb = await berechne_wallbox_kpis(db, aid, von_jahr, von_monat, bis_jahr, bis_monat)
        if wb and wb.get("pv_anteil"):
            pv_anteile.append(wb["pv_anteil"])

    if not pv_anteile:
        return None, 0
    return sum(pv_anteile) / len(pv_anteile), len(pv_anteile)


async def berechne_bkw_kpis(
    db: AsyncSession,
    anlage_id: int,
    bkw_wp: float,
    von_jahr: int, von_monat: int,
    bis_jahr: int, bis_monat: int,
) -> dict | None:
    """Berechnet Balkonkraftwerk-KPIs für einen Zeitraum."""
    if bkw_wp <= 0:
        return None

    result = await db.execute(
        select(
            func.sum(Monatswert.bkw_erzeugung_kwh),
            func.sum(Monatswert.bkw_eigenverbrauch_kwh),
            # Basis = Monate MIT BKW-Wert (F-76-Bau; COUNT(id) zählte PV-Zeilen mit)
            func.count(Monatswert.bkw_erzeugung_kwh),
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
        # F-76 (18.09.2026): der laufende Kalendermonat zählt in KEINEM Aggregat
        # (Server-F-48) — auf beiden Seiten des Vergleichs, mit derselben Filterzeile.
        .where(nur_abgeschlossene_monate())
    )
    row = result.first()
    if not row or not row[0]:
        return None

    erzeugung, eigenverbrauch, monate = row
    erzeugung = erzeugung or 0
    eigenverbrauch = eigenverbrauch or 0

    if erzeugung == 0:
        return None

    # Spez. Ertrag (auf Jahr hochrechnen)
    kwp = bkw_wp / 1000  # Wp -> kWp
    if monate > 0 and monate < 12:
        jahres_erzeugung = erzeugung * (12 / monate)
    else:
        jahres_erzeugung = erzeugung

    spez_ertrag = jahres_erzeugung / kwp if kwp > 0 else 0
    ev_quote = (eigenverbrauch / erzeugung * 100) if erzeugung > 0 else None

    return {
        "erzeugung": round(erzeugung, 1),
        "spez_ertrag": round(spez_ertrag, 0),
        "eigenverbrauch_quote": round(ev_quote, 1) if ev_quote else None,
    }


async def berechne_community_avg_bkw_spez_ertrag(
    db: AsyncSession,
    von_jahr: int, von_monat: int, bis_jahr: int, bis_monat: int,
) -> tuple[float | None, int]:
    """Community-Ø des BKW-spez.-Ertrags im Fenster des eigenen Werts — und n (F-76).

    ⚠ Mit dem festen Fenster summierte der Ø ab zwölf Zeilen **ganze Jahre**
    (kein ×12/n ab 12 Monaten): eine Anlage mit drei Jahren à 60 kWh/Monat stand
    mit 2.700 kWh/kWp im Ø neben ihren eigenen 900.
    """
    result = await db.execute(
        select(Anlage.id, Anlage.bkw_wp)
        .where(Anlage.hat_balkonkraftwerk == True)
        .where(Anlage.bkw_wp > 0)
    )
    anlagen = result.all()

    if not anlagen:
        return None, 0

    spez_ertraege = []
    for aid, bkw_wp in anlagen:
        bkw = await berechne_bkw_kpis(db, aid, bkw_wp, von_jahr, von_monat, bis_jahr, bis_monat)
        if bkw and bkw.get("spez_ertrag"):
            spez_ertraege.append(bkw["spez_ertrag"])

    if not spez_ertraege:
        return None, 0
    return sum(spez_ertraege) / len(spez_ertraege), len(spez_ertraege)


async def berechne_community_durchschnitt(db: AsyncSession) -> float:
    """Mittelwert der Vergleichsgruppe — SoT ``core/spez_ertrag.py`` (#387).

    Bis zum 17.09.2026 stand hier eine eigene Kopie der Hochrechnung, die
    Anlagen unter sechs Monaten mit ihrer **Rohsumme** mitzählte, während
    Rangliste, Histogramm und ``/stats`` sie übersprangen — das war F-46
    (Add-on 688,5 gegen Website 862,0 am 17.09.). Eine Rechenstelle, eine Zahl.
    """
    return durchschnitt(await lade_spez_jahresertraege(db))


async def berechne_region_durchschnitt(db: AsyncSession, region: str) -> float:
    """Mittelwert der Vergleichsgruppe einer Region (SoT ``core/spez_ertrag.py``)."""
    ids = [
        row[0]
        for row in (await db.execute(select(Anlage.id).where(Anlage.region == region))).all()
    ]
    if not ids:
        return 0
    return durchschnitt(await lade_spez_jahresertraege(db, anlage_ids=ids))


async def berechne_rang_und_anzahl(
    db: AsyncSession, anlage_id: int, region: str
) -> tuple[int | None, int, int | None, int]:
    """Liefert (rang_gesamt, anzahl_gesamt, rang_region, anzahl_region).

    ``anzahl_*`` zählt die **Vergleichsgruppe** — die Anlagen, die einen Wert
    haben und damit in der Rangliste stehen. „Rang 14 von 138" mischte bis zum
    17.09.2026 einen Rang aus 95 bewerteten Anlagen mit der Zahl *aller*
    Anlagen, und Bestätigung und Dashboard zählten dazu noch verschieden; jetzt
    nennen beide Zahlen dieselbe Grundgesamtheit.

    ⚠ Der Rang ist ``None``, wenn die Anlage selbst keinen Wert hat. Vorher
    stand dort über den ``next(..., 1)``-Vorgabewert eine **1** — eine Anlage
    ohne vergleichbaren Wert wurde als Erstplatzierte gemeldet (#387, dritter
    Teil der Zusage aus eedc v4.0.22).
    """
    ertraege = await lade_spez_jahresertraege(db)
    region_je_anlage = {
        aid: r for aid, r in (await db.execute(select(Anlage.id, Anlage.region))).all()
    }

    gruppe_alle = sorted(
        ((aid, e.wert) for aid, e in ertraege.items() if e.wert is not None),
        key=lambda x: x[1],
        reverse=True,
    )
    gruppe_region = [
        (aid, wert) for aid, wert in gruppe_alle if region_je_anlage.get(aid) == region
    ]

    rang_gesamt = next(
        (i + 1 for i, (aid, _) in enumerate(gruppe_alle) if aid == anlage_id), None
    )
    rang_region = next(
        (i + 1 for i, (aid, _) in enumerate(gruppe_region) if aid == anlage_id), None
    )
    return rang_gesamt, len(gruppe_alle), rang_region, len(gruppe_region)


async def baue_benchmark_data(db: AsyncSession, anlage: Anlage) -> BenchmarkData:
    """Die EINE Konstruktionsstelle für ``BenchmarkData`` — Dashboard und Submit.

    Bis zum 17.09.2026 bauten ``get_anlage_benchmark`` und
    ``submit.py::calculate_benchmark`` das Objekt getrennt und zählten „von N"
    verschieden (alle Anlagen gegen Anlagen mit Wert). Jetzt gibt es eine
    Stelle, und sie trägt die ``basis_*``-Felder, die der Client seit v4.0.22
    liest (#387).
    """
    jahresertrag = await lade_spez_jahresertrag(db, anlage.id)
    spez_ertrag_durchschnitt = await berechne_community_durchschnitt(db)
    spez_ertrag_region = await berechne_region_durchschnitt(db, anlage.region)
    rang_gesamt, anzahl_gesamt, rang_region, anzahl_region = await berechne_rang_und_anzahl(
        db, anlage.id, anlage.region
    )
    return BenchmarkData(
        spez_ertrag_anlage=(
            round(jahresertrag.wert, 1) if jahresertrag.wert is not None else None
        ),
        spez_ertrag_durchschnitt=round(spez_ertrag_durchschnitt, 1) or None,
        spez_ertrag_region=round(spez_ertrag_region, 1) or None,
        rang_gesamt=rang_gesamt,
        anzahl_anlagen_gesamt=anzahl_gesamt,
        rang_region=rang_region,
        anzahl_anlagen_region=anzahl_region,
        basis_monate=jahresertrag.basis_monate,
        fenster_monate=FENSTER_MONATE,
        basis_bis_jahr=jahresertrag.bis_jahr,
        basis_bis_monat=jahresertrag.bis_monat,
        basis_veraltet=jahresertrag.veraltet,
        basis_grund=jahresertrag.grund,
    )


@router.get("/anlage/{anlage_hash}")
async def get_anlage_benchmark(
    anlage_hash: str,
    zeitraum: ZeitraumTyp = Query("letzte_12_monate", description="Vergleichszeitraum"),
    jahr: int | None = Query(None, ge=2010, le=2050, description="Jahr für zeitraum=jahr oder zeitraum=monat"),
    monat: int | None = Query(None, ge=1, le=12, description="Monat für zeitraum=monat"),
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert Vergleichsdaten für eine bestimmte Anlage.
    Der Hash identifiziert die Anlage ohne sensible Daten preiszugeben.

    Zeitraum-Optionen:
    - letzter_monat: Nur der Vormonat
    - letzte_12_monate: Die letzten 12 abgeschlossenen Monate (Standard)
    - monat: Ein bestimmter Monat (Parameter 'jahr' und 'monat' erforderlich)
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
        zeitraum, jahr, monat, anlage.installation_jahr
    )

    # Monatswerte laden
    result = await db.execute(
        select(Monatswert)
        .where(Monatswert.anlage_id == anlage.id)
        .order_by(Monatswert.jahr.desc(), Monatswert.monat.desc())
    )
    monatswerte = result.scalars().all()

    # Jahreswert, Durchschnitte, Rang — EINE Konstruktionsstelle, dieselbe wie
    # bei der Submit-Bestätigung (SoT core/spez_ertrag.py, #387).
    benchmark_daten = await baue_benchmark_data(db, anlage)

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

    # PV-Benchmark — der Jahres-KPI fehlt, wenn die Anlage keinen Jahreswert
    # hat (#387, Grund in `benchmark_daten.basis_grund`); die Monatsvergleiche
    # daneben bleiben.
    pv_benchmark = PVBenchmark(
        spez_ertrag=KPIVergleich(
            wert=benchmark_daten.spez_ertrag_anlage,
            community_avg=benchmark_daten.spez_ertrag_durchschnitt,
            rang=benchmark_daten.rang_gesamt,
            von=benchmark_daten.anzahl_anlagen_gesamt,
        ) if benchmark_daten.spez_ertrag_anlage is not None else None,
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
                basis_monate=speicher_kpis.get("basis_monate"),
                zyklen_jahr=KPIVergleich(wert=speicher_kpis["zyklen_jahr"]) if speicher_kpis.get("zyklen_jahr") else None,
                wirkungsgrad=KPIVergleich(wert=speicher_kpis["wirkungsgrad"]) if speicher_kpis.get("wirkungsgrad") else None,
                netz_anteil=KPIVergleich(wert=speicher_kpis["netz_anteil"]) if speicher_kpis.get("netz_anteil") else None,
            )

    # Wärmepumpe-Benchmark
    wp_benchmark = None
    if anlage.hat_waermepumpe:
        wp_kpis = await berechne_wp_kpis(db, anlage.id, von_jahr, von_monat, bis_jahr, bis_monat)
        if wp_kpis:
            # ⛔ **Wer passiv kühlt, bekommt seine Zahl — aber keinen Vergleich**
            # (eedc SOLL §4.1/§7 A5). Der Community-Durchschnitt enthält passiv
            # gekühlte Anlagen nicht mehr; sich selbst gegen einen Durchschnitt
            # zu stellen, in dem man nicht vorkommt, wäre die zweite Hälfte
            # derselben Falschaussage.
            kuehlt_passiv = anlage.kuehlung_art == "passiv"
            community_jaz, jaz_n = (None, 0) if kuehlt_passiv else await berechne_community_avg_jaz(db)
            # Typ-spezifischer JAZ-Vergleich (nur mit gleicher WP-Art)
            jaz_typ_vergleich = None
            if anlage.wp_art and wp_kpis.get("jaz") and not kuehlt_passiv:
                community_jaz_typ, jaz_typ_n = await berechne_community_avg_jaz(db, wp_art=anlage.wp_art)
                if community_jaz_typ is not None:
                    jaz_typ_vergleich = KPIVergleich(
                        wert=wp_kpis["jaz"],
                        community_avg=round(community_jaz_typ, 2),
                        von=jaz_typ_n,
                    )
            wp_benchmark = WaermepumpeBenchmark(
                jaz=KPIVergleich(
                    wert=wp_kpis["jaz"],
                    community_avg=community_jaz,
                    von=jaz_n if community_jaz is not None else None,
                ) if wp_kpis.get("jaz") else None,
                jaz_typ=jaz_typ_vergleich,
                wp_art=anlage.wp_art,
                stromverbrauch=KPIVergleich(wert=wp_kpis["stromverbrauch"]) if wp_kpis.get("stromverbrauch") else None,
                waermeerzeugung=KPIVergleich(wert=wp_kpis["waermeerzeugung"]) if wp_kpis.get("waermeerzeugung") else None,
            )

    # E-Auto-Benchmark
    eauto_benchmark = None
    if anlage.hat_eauto:
        eauto_kpis = await berechne_eauto_kpis(db, anlage.id, von_jahr, von_monat, bis_jahr, bis_monat)
        if eauto_kpis:
            # F-76: der Ø bekommt das Fenster des eigenen Werts und nennt n.
            community_pv_anteil, eauto_n = await berechne_community_avg_pv_anteil_eauto(
                db, von_jahr, von_monat, bis_jahr, bis_monat
            )
            eauto_benchmark = EAutoBenchmark(
                ladung_gesamt=KPIVergleich(wert=eauto_kpis["ladung_gesamt"]) if eauto_kpis.get("ladung_gesamt") else None,
                pv_anteil=KPIVergleich(
                    wert=eauto_kpis["pv_anteil"],
                    community_avg=round(community_pv_anteil, 1) if community_pv_anteil else None,
                    von=eauto_n if community_pv_anteil else None,
                ) if eauto_kpis.get("pv_anteil") else None,
                km=KPIVergleich(wert=eauto_kpis["km"]) if eauto_kpis.get("km") else None,
                verbrauch_100km=KPIVergleich(wert=eauto_kpis["verbrauch_100km"]) if eauto_kpis.get("verbrauch_100km") else None,
                v2h=KPIVergleich(wert=eauto_kpis["v2h"]) if eauto_kpis.get("v2h") else None,
            )

    # Wallbox-Benchmark
    wallbox_benchmark = None
    if anlage.hat_wallbox:
        wallbox_kpis = await berechne_wallbox_kpis(db, anlage.id, von_jahr, von_monat, bis_jahr, bis_monat)
        if wallbox_kpis:
            community_pv_anteil_wb, wallbox_n = await berechne_community_avg_pv_anteil_wallbox(
                db, von_jahr, von_monat, bis_jahr, bis_monat
            )
            wallbox_benchmark = WallboxBenchmark(
                ladung=KPIVergleich(wert=wallbox_kpis["ladung"]) if wallbox_kpis.get("ladung") else None,
                pv_anteil=KPIVergleich(
                    wert=wallbox_kpis["pv_anteil"],
                    community_avg=round(community_pv_anteil_wb, 1) if community_pv_anteil_wb else None,
                    von=wallbox_n if community_pv_anteil_wb else None,
                ) if wallbox_kpis.get("pv_anteil") else None,
                ladevorgaenge=KPIVergleich(wert=wallbox_kpis["ladevorgaenge"]) if wallbox_kpis.get("ladevorgaenge") else None,
            )

    # Balkonkraftwerk-Benchmark
    bkw_benchmark = None
    if anlage.hat_balkonkraftwerk and anlage.bkw_wp and anlage.bkw_wp > 0:
        bkw_kpis = await berechne_bkw_kpis(db, anlage.id, anlage.bkw_wp, von_jahr, von_monat, bis_jahr, bis_monat)
        if bkw_kpis:
            community_spez_ertrag_bkw, bkw_n = await berechne_community_avg_bkw_spez_ertrag(
                db, von_jahr, von_monat, bis_jahr, bis_monat
            )
            bkw_benchmark = BKWBenchmark(
                erzeugung=KPIVergleich(wert=bkw_kpis["erzeugung"]) if bkw_kpis.get("erzeugung") else None,
                spez_ertrag=KPIVergleich(
                    wert=bkw_kpis["spez_ertrag"],
                    community_avg=round(community_spez_ertrag_bkw, 0) if community_spez_ertrag_bkw else None,
                    von=bkw_n if community_spez_ertrag_bkw else None,
                ) if bkw_kpis.get("spez_ertrag") else None,
                eigenverbrauch=KPIVergleich(wert=bkw_kpis["eigenverbrauch_quote"]) if bkw_kpis.get("eigenverbrauch_quote") else None,
            )

    erweiterte_benchmarks = ErweiterteBenchmarkData(
        pv=pv_benchmark,
        speicher=speicher_benchmark,
        waermepumpe=wp_benchmark,
        eauto=eauto_benchmark,
        wallbox=wallbox_benchmark,
        balkonkraftwerk=bkw_benchmark,
    )

    # Zeitraum-Label
    zeitraum_labels = {
        "letzter_monat": f"{bis_monat:02d}/{bis_jahr}",
        "letzte_12_monate": "letzte 12 Monate",
        "monat": f"{monat:02d}/{jahr}" if monat and jahr else "Monat",
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
            wp_art=anlage.wp_art,
            monatswerte=monatswerte_output,
        ),
        "benchmark": benchmark_daten,
        "benchmark_erweitert": erweiterte_benchmarks,
        "zeitraum": zeitraum,
        "zeitraum_label": zeitraum_labels.get(zeitraum, zeitraum),
    }


@router.get("/monat/{jahr}/{monat}", response_model=MonatsVergleich)
async def get_monats_benchmark(
    jahr: int,
    monat: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert Community-Durchschnitte aller KPIs für einen bestimmten Monat.
    Ermöglicht Monats-Vergleiche: "Wie war der Februar 2026 in der Community?"
    """
    if monat < 1 or monat > 12:
        raise HTTPException(status_code=400, detail="Monat muss zwischen 1 und 12 liegen")

    # Alle Monatswerte für diesen Monat mit Anlagendaten laden
    result = await db.execute(
        select(Monatswert, Anlage)
        .join(Anlage)
        .where(Monatswert.jahr == jahr)
        .where(Monatswert.monat == monat)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Keine Daten für {monat:02d}/{jahr}")

    anzahl = len(rows)

    # --- PV-Kern-KPIs ---
    spez_ertraege = []
    autarkien = []
    eigenverbrauch_werte = []
    einspeisungen = []
    netzbezuege = []

    # --- Speicher ---
    sp_ladung_werte = []
    sp_entladung_werte = []
    sp_wirkungsgrad_werte = []

    # --- Wärmepumpe ---
    wp_strom_werte = []
    wp_waerme_werte = []
    wp_jaz_werte = []

    # --- E-Auto ---
    eauto_ladung_werte = []
    eauto_pv_anteil_werte = []
    eauto_km_werte = []

    # --- Wallbox ---
    wb_ladung_werte = []
    wb_pv_anteil_werte = []

    # --- BKW ---
    bkw_erzeugung_werte = []

    # --- Regional ---
    region_daten: dict[str, list[dict]] = {}

    for mw, anlage in rows:
        # Spez. Ertrag
        if mw.ertrag_kwh is not None and anlage.kwp and anlage.kwp > 0:
            spez = mw.ertrag_kwh / anlage.kwp
            spez_ertraege.append(spez)

            # Regional sammeln
            if anlage.region not in region_daten:
                region_daten[anlage.region] = []
            region_daten[anlage.region].append({
                "spez": spez,
                "autarkie": mw.autarkie_prozent,
            })

        if mw.autarkie_prozent is not None:
            autarkien.append(mw.autarkie_prozent)
        if mw.eigenverbrauch_prozent is not None:
            eigenverbrauch_werte.append(mw.eigenverbrauch_prozent)
        if mw.einspeisung_kwh is not None:
            einspeisungen.append(mw.einspeisung_kwh)
        if mw.netzbezug_kwh is not None:
            netzbezuege.append(mw.netzbezug_kwh)

        # Speicher
        if mw.speicher_ladung_kwh is not None:
            sp_ladung_werte.append(mw.speicher_ladung_kwh)
        if mw.speicher_entladung_kwh is not None:
            sp_entladung_werte.append(mw.speicher_entladung_kwh)
        if (mw.speicher_ladung_kwh and mw.speicher_ladung_kwh > 0
                and mw.speicher_entladung_kwh is not None):
            sp_wirkungsgrad_werte.append(
                mw.speicher_entladung_kwh / mw.speicher_ladung_kwh * 100
            )

        # Wärmepumpe
        if mw.wp_stromverbrauch_kwh is not None and mw.wp_stromverbrauch_kwh > 0:
            wp_strom_werte.append(mw.wp_stromverbrauch_kwh)
            waerme = (mw.wp_heizwaerme_kwh or 0) + (mw.wp_warmwasser_kwh or 0)
            if waerme > 0:
                wp_waerme_werte.append(waerme)
                # eedc ADR-002/P12: Die MENGEN oben zählen immer — sie sind
                # additiv und richtig. Der QUOTIENT entsteht nur, wenn Zähler
                # und Nenner dieselbe Abgrenzung tragen; das weiß der Client,
                # nicht der Server. `is not False` heißt: NULL (Altbestand)
                # zählt mit, unbekannt ist nicht unbelastbar.
                #
                # ⚠ Diese Stelle sieht wie reine Summierung aus — zwei
                # getrennte Mengen-Listen — und die Division steht eine Zeile
                # tiefer. Genau daran ist eine Erhebung schon vorbeigelaufen.
                # ⛔ HIER FEHLTEN BIS ZUM 07.09.2026 ZWEI DER VIER BEDINGUNGEN.
                # `85c75a2` (06.09.) hat vier der fünf JAZ-Stellen auf den SoT
                # gehoben — diese nicht: sein Diff berührt in dieser Datei nur
                # `berechne_wp_kpis` (~196) und `berechne_community_avg_jaz`
                # (~283). Der P12-Kommentar darüber handelt von P12 und sagt
                # nichts über W-14 und A5; wer ihn liest, hält die Stelle
                # trotzdem für erledigt. *Ein Kommentar ist eine Behauptung
                # über die Stelle, an der er steht, nicht über die Regel, die
                # man sucht.*
                #
                # W-14 — der Kühlstrom gehört nicht in den Nenner. A5 — passiv
                # gekühlte Anlagen zählen nicht in einen gemeinsamen Schnitt.
                # Dazu die Plausibilitätsgrenze desselben SoT: eine Zeile über
                # `MONATS_ARBEITSZAHL_MAX` behauptet mehr, als eine Wärmepumpe
                # kann (SOLL §3.2b Fall A7 — bivalenter Heizkreis).
                #
                # ⭐ 13.09.2026 (eedc WK-06b / N-454) — abgezogen wird die
                # ENTSCHEIDUNG des Clients, nicht die Menge. `wp_strom_kuehlen_kwh`
                # bleibt die Menge; `funktionsfremd_abzug_zeile` liest das neue
                # Feld und faellt nur fuer Zeilen ohne dieses Feld (Altbestand /
                # Client vor WK-06b) darauf zurueck. Der Fallback bleibt stehen
                # und faellt nicht automatisch weg — Altbestand heilt beim
                # naechsten Voll-Submit. Dieselbe Regel wie in den drei
                # SQL-Stellen, hier in Python, weil die Zeilen schon geladen sind.
                strom_waerme = mw.wp_stromverbrauch_kwh - min(
                    max(funktionsfremd_abzug_zeile(mw), 0),
                    mw.wp_stromverbrauch_kwh,
                )
                passiv = anlage.kuehlung_art == "passiv"
                if (
                    mw.wp_jaz_belastbar is not False
                    and not passiv
                    and strom_waerme > 0
                    and waerme <= MONATS_ARBEITSZAHL_MAX * strom_waerme
                ):
                    wp_jaz_werte.append(waerme / strom_waerme)

        # E-Auto
        if mw.eauto_ladung_gesamt_kwh is not None and mw.eauto_ladung_gesamt_kwh > 0:
            eauto_ladung_werte.append(mw.eauto_ladung_gesamt_kwh)
            if mw.eauto_ladung_pv_kwh is not None:
                eauto_pv_anteil_werte.append(
                    mw.eauto_ladung_pv_kwh / mw.eauto_ladung_gesamt_kwh * 100
                )
        if mw.eauto_km is not None and mw.eauto_km > 0:
            eauto_km_werte.append(mw.eauto_km)

        # Wallbox
        if mw.wallbox_ladung_kwh is not None and mw.wallbox_ladung_kwh > 0:
            wb_ladung_werte.append(mw.wallbox_ladung_kwh)
            if mw.wallbox_ladung_pv_kwh is not None:
                wb_pv_anteil_werte.append(
                    mw.wallbox_ladung_pv_kwh / mw.wallbox_ladung_kwh * 100
                )

        # BKW
        if mw.bkw_erzeugung_kwh is not None and mw.bkw_erzeugung_kwh > 0:
            bkw_erzeugung_werte.append(mw.bkw_erzeugung_kwh)

    # --- Regionale Aufschlüsselung ---
    regionen = []
    for region, daten in sorted(region_daten.items()):
        if len(daten) >= 1:
            spez_values = [d["spez"] for d in daten]
            autarkie_values = [d["autarkie"] for d in daten if d["autarkie"] is not None]
            regionen.append(MonatsRegionVergleich(
                region=region,
                anzahl_anlagen=len(daten),
                spez_ertrag=round(sum(spez_values) / len(spez_values), 1),
                autarkie=round(sum(autarkie_values) / len(autarkie_values), 1) if autarkie_values else None,
            ))

    return MonatsVergleich(
        jahr=jahr,
        monat=monat,
        anzahl_anlagen=anzahl,
        spez_ertrag=_make_monats_kpi(spez_ertraege),
        autarkie=_make_monats_kpi(autarkien) if autarkien else None,
        eigenverbrauch=_make_monats_kpi(eigenverbrauch_werte) if eigenverbrauch_werte else None,
        einspeisung=_make_monats_kpi(einspeisungen) if einspeisungen else None,
        netzbezug=_make_monats_kpi(netzbezuege) if netzbezuege else None,
        speicher_ladung=_make_monats_kpi(sp_ladung_werte) if sp_ladung_werte else None,
        speicher_entladung=_make_monats_kpi(sp_entladung_werte) if sp_entladung_werte else None,
        speicher_wirkungsgrad=_make_monats_kpi(sp_wirkungsgrad_werte) if sp_wirkungsgrad_werte else None,
        wp_stromverbrauch=_make_monats_kpi(wp_strom_werte) if wp_strom_werte else None,
        wp_waerme=_make_monats_kpi(wp_waerme_werte) if wp_waerme_werte else None,
        wp_jaz=_make_monats_kpi(wp_jaz_werte) if wp_jaz_werte else None,
        eauto_ladung=_make_monats_kpi(eauto_ladung_werte) if eauto_ladung_werte else None,
        eauto_pv_anteil=_make_monats_kpi(eauto_pv_anteil_werte) if eauto_pv_anteil_werte else None,
        eauto_km=_make_monats_kpi(eauto_km_werte) if eauto_km_werte else None,
        wallbox_ladung=_make_monats_kpi(wb_ladung_werte) if wb_ladung_werte else None,
        wallbox_pv_anteil=_make_monats_kpi(wb_pv_anteil_werte) if wb_pv_anteil_werte else None,
        bkw_erzeugung=_make_monats_kpi(bkw_erzeugung_werte) if bkw_erzeugung_werte else None,
        regionen=regionen if regionen else None,
    )


def _make_monats_kpi(werte: list[float]) -> MonatsKPI:
    """Erstellt ein MonatsKPI-Objekt aus einer Liste von Werten."""
    from statistics import median as stat_median
    werte_sorted = sorted(werte)
    return MonatsKPI(
        durchschnitt=round(sum(werte) / len(werte), 1),
        median=round(stat_median(werte), 1) if len(werte) >= 3 else None,
        min=round(werte_sorted[0], 1) if len(werte) >= 3 else None,
        max=round(werte_sorted[-1], 1) if len(werte) >= 3 else None,
        anzahl_anlagen=len(werte),
    )


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

    jahresertraege = await lade_spez_jahresertraege(
        db, anlage_ids=[a.id for a in anlagen]
    )
    for anlage in anlagen:
        spez = jahresertraege.get(anlage.id)
        if spez is None or spez.wert is None:
            continue
        ertraege_alle.append(spez.wert)
        if anlage.region == region.upper():
            ertraege_region.append(spez.wert)

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
