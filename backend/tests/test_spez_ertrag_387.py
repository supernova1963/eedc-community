"""Die Server-Hälfte der Zusage aus eedc v4.0.22 (#387, azywietz-web).

Zugesagt für den 01.09.2026, gebaut am 17.09.2026: Ein Teiljahr wird **saisonal**
hochgerechnet — mit der PVGIS-Erwartung des eigenen Standorts als Maßstab —, es
gibt **einen** Community-Durchschnitt (F-46) und keinen Vorgabe-Rang 1. SoT ist
``core/spez_ertrag.py``; die sechs früheren Kopien hängen daran.

**Die schärfste Probe ist die Identität:** zwölf volle Monate müssen bitgleich
denselben Wert liefern wie vorher — die Umstellung darf ausschließlich das
unvollständige Jahr treffen. Dazu der Melder-Fall mit seinen eigenen Zahlen
(978,5 statt 1.273,6) und je eine Probe für die Grenzen der Regel.

Reine Proben laufen ohne Datenbank gegen ``_auswerten``; die DB-Proben stellen
drei Anlagen nebeneinander (volles Jahr · Teiljahr mit SOLL · Teiljahr ohne
SOLL) und fragen jede Konsumentenstelle einzeln — eine Sammelprobe wäre grün,
sobald *eine* Stelle stimmt.
"""
from __future__ import annotations

import pytest

from api import benchmark as benchmark_api
from api import components as components_api
from api import statistics as statistics_api
from api import stats as stats_api
from api import submit as submit_api
from core.spez_ertrag import (
    FENSTER_MONATE,
    GRUND_KEIN_MASSSTAB,
    GRUND_VERALTET,
    _auswerten,
    jetzt_utc,
    lade_spez_jahresertraege,
)
from models import Anlage, Monatswert

# ── Der Melder-Fall (Journal Sitzung 71, 19.08.2026) ─────────────────────────
KWP = 2.0
IST_MRZ_JUL_KWH_KWP = 554.8          # sein IST über fünf abgeschlossene Monate
PVGIS_JAHR_KWH_KWP = 1024.7          # Süd 35°, NRW-Mittelpunkt
PVGIS_ANTEIL_MRZ_JUL = 0.567         # Anteil dieser fünf Monate am PVGIS-Jahr
ZUGESAGT = 978.5                     # CHANGELOG v4.0.22: „rund 980"


def _monate(werte: dict[tuple[int, int], float], soll: float | None = 90.0):
    return {ym: (ist, soll) for ym, ist in werte.items()}


def _vormonate(n: int, *, ab: tuple[int, int] | None = None) -> list[tuple[int, int]]:
    """Die ``n`` abgeschlossenen Monate vor ``ab`` (Default: laufender Monat), älteste zuerst."""
    jahr, monat = ab or jetzt_utc()
    out: list[tuple[int, int]] = []
    for _ in range(n):
        jahr, monat = (jahr - 1, 12) if monat == 1 else (jahr, monat - 1)
        out.append((jahr, monat))
    return list(reversed(out))


# ══ Reine Regel ══════════════════════════════════════════════════════════════


def test_identitaet_zwoelf_monate_sind_gemessen():
    """Zwölf lückenlose Monate: Σ ÷ kWp, bitgleich mit dem alten (Σ ÷ 12) × 12."""
    werte = {(2025, m): 100.0 * m for m in range(1, 13)}
    r = _auswerten(_monate(werte, soll=7777.0), 10.0, 999999.0, 2026, 9)
    summe = sum(werte.values())
    assert r.wert == summe / 10.0
    assert r.wert == (summe / 12 * 12) / 10.0
    assert r.basis_monate == FENSTER_MONATE and r.grund is None


def test_melder_fall_trifft_die_zugesagte_zahl():
    """azywietz: 554,8 kWh/kWp über Mrz–Jul, Süd 35° NRW → 978,5 statt 1.273,6."""
    soll_jahr = PVGIS_JAHR_KWH_KWP * KWP
    monate = {
        (2026, m): (IST_MRZ_JUL_KWH_KWP * KWP / 5, PVGIS_ANTEIL_MRZ_JUL * soll_jahr / 5)
        for m in range(3, 8)
    }
    r = _auswerten(monate, KWP, soll_jahr, 2026, 8)
    assert r.wert == pytest.approx(ZUGESAGT, abs=0.1)
    assert r.basis_monate == 5
    # Und die Gegenprobe, die der Melder selbst gerechnet hat: flach wären es 1.273,6.
    assert r.wert < 1000 < 636.8 / 6 * 12


def test_skalierungsinvarianz_nur_die_form_zaehlt():
    """Ein um Faktor 3 falsch skaliertes SOLL ändert das Ergebnis nicht."""
    soll_jahr = PVGIS_JAHR_KWH_KWP * KWP
    monate = {
        (2026, m): (IST_MRZ_JUL_KWH_KWP * KWP / 5, PVGIS_ANTEIL_MRZ_JUL * soll_jahr / 5)
        for m in range(3, 8)
    }
    skaliert = {ym: (ist, soll * 3) for ym, (ist, soll) in monate.items()}
    assert _auswerten(skaliert, KWP, soll_jahr * 3, 2026, 8).wert == pytest.approx(
        _auswerten(monate, KWP, soll_jahr, 2026, 8).wert
    )


def test_laufender_monat_zaehlt_nie():
    monate = _monate({(2026, m): 100.0 for m in range(1, 10)})
    r = _auswerten(monate, 10.0, 1100.0, 2026, 9)
    assert r.basis_monate == 8 and (r.bis_jahr, r.bis_monat) == (2026, 8)


def test_luecke_beendet_das_fenster():
    werte = {(2025, m): 100.0 for m in range(1, 13)}
    del werte[(2025, 6)]
    r = _auswerten(_monate(werte), 10.0, 1100.0, 2026, 1)
    assert r.basis_monate == 6                      # Jul–Dez, die Lücke im Juni stoppt
    assert r.wert is not None and r.grund is None   # mit SOLL trotzdem ein Wert


def test_veraltet_kein_wert_mit_grund():
    r = _auswerten(_monate({(2024, m): 100.0 for m in range(1, 13)}), 10.0, 1100.0, 2026, 9)
    assert r.wert is None and r.veraltet and r.grund == GRUND_VERALTET
    assert r.basis_monate == 12                     # die Anlage IST vollständig, nur alt


def test_ohne_soll_unter_zwoelf_kein_wert_mit_grund():
    """Option A (17.09.2026): kein Ersatzmaßstab — der Grund steht dabei."""
    r = _auswerten(_monate({(2026, m): 100.0 for m in range(1, 8)}, soll=None), 10.0, None, 2026, 9)
    assert r.wert is None and r.grund == GRUND_KEIN_MASSSTAB and r.basis_monate == 7
    # Fehlt das SOLL nur in EINEM Fenstermonat, fehlt der Maßstab genauso.
    monate = _monate({(2026, m): 100.0 for m in range(1, 8)})
    monate[(2026, 3)] = (100.0, None)
    assert _auswerten(monate, 10.0, 1100.0, 2026, 9).grund == GRUND_KEIN_MASSSTAB


def test_ohne_soll_aber_zwoelf_monate_traegt_trotzdem():
    """Die Identität braucht kein SOLL — ein volles Jahr ist eine Messung."""
    r = _auswerten(_monate({(2025, m): 100.0 for m in range(1, 13)}, soll=None), 10.0, None, 2026, 9)
    assert r.wert == 120.0 and r.grund is None


def test_mindestdauer_ist_ein_monat():
    """Entscheid 19.08.2026: ein Monat mit tagesgenau gekürztem SOLL trägt.

    azywietz' März: 13 Tage, 30,4 kWh/kWp IST; PVGIS-März 86,4, gekürzt
    13/31 × 86,4 = 36,2 (Journal 70/5). Erwartung ~940 kWh/kWp im Jahr.
    """
    gekuerzt = _auswerten({(2026, 3): (30.4 * KWP, 36.2 * KWP)}, KWP, 940.0 * KWP, 2026, 4)
    assert gekuerzt.basis_monate == 1
    assert gekuerzt.wert == pytest.approx(30.4 / 36.2 * 940.0, abs=0.1)   # 789,4
    # Gegenprobe: mit UNGEKÜRZTEM März-SOLL (der Server könnte nicht kürzen)
    # wäre derselbe Monat grotesk — deshalb kommt das SOLL gekürzt vom Client.
    ungekuerzt = _auswerten({(2026, 3): (30.4 * KWP, 86.4 * KWP)}, KWP, 940.0 * KWP, 2026, 4)
    assert ungekuerzt.wert < 400 < gekuerzt.wert < 940


# ══ DB-Proben: drei Anlagen, jede Konsumentenstelle einzeln ══════════════════


async def _anlage(db, hash_zeichen: str, *, monate: int, soll: bool, region="NW",
                  kwp=10.0, ist_je_monat=100.0) -> Anlage:
    anlage = Anlage(
        anlage_hash=hash_zeichen * 64, region=region, kwp=kwp, ausrichtung="süd",
        neigung_grad=30, installation_jahr=2024,
        soll_jahr_kwh=1200.0 if soll else None,
    )
    db.add(anlage)
    await db.flush()
    for jahr, monat in _vormonate(monate):
        db.add(Monatswert(
            anlage_id=anlage.id, jahr=jahr, monat=monat, ertrag_kwh=ist_je_monat,
            soll_ertrag_kwh=100.0 if soll else None,
        ))
    await db.commit()
    return anlage


async def _drei_anlagen(db):
    voll = await _anlage(db, "a", monate=12, soll=False)            # 1.200 ÷ 10 = 120
    teil = await _anlage(db, "b", monate=5, soll=True)              # 500/500 × 1200 ÷ 10 = 120
    ohne = await _anlage(db, "c", monate=5, soll=False, region="BY")  # kein Maßstab
    return voll, teil, ohne


@pytest.mark.asyncio
async def test_buendel_liefert_jede_anlage_mit_grund(db):
    voll, teil, ohne = await _drei_anlagen(db)
    ergebnisse = await lade_spez_jahresertraege(db)
    assert ergebnisse[voll.id].wert == pytest.approx(120.0)
    assert ergebnisse[teil.id].wert == pytest.approx(120.0) and ergebnisse[teil.id].basis_monate == 5
    assert ergebnisse[ohne.id].wert is None and ergebnisse[ohne.id].grund == GRUND_KEIN_MASSSTAB


@pytest.mark.asyncio
async def test_ein_durchschnitt_an_allen_vier_stellen(db):
    """F-46: benchmark.py, statistics.py (global + Verteilung) und stats.py — eine Zahl."""
    await _drei_anlagen(db)
    erwartet = 120.0
    assert await benchmark_api.berechne_community_durchschnitt(db) == pytest.approx(erwartet)
    assert await statistics_api.berechne_community_jahresertrag(db) == pytest.approx(erwartet)
    assert await stats_api.berechne_jahresertrag(db) == pytest.approx(erwartet)
    verteilung = await statistics_api._hole_metrik_werte(db, "spez_ertrag")
    assert len(verteilung) == 2 and all(w == pytest.approx(erwartet) for w in verteilung)
    # Und die Rangliste kennt dieselben zwei — mit der Monatszahl in der Zeile.
    ranking = await statistics_api._berechne_ranking(db, "spez_ertrag")
    assert sorted(e["basis_monate"] for e in ranking) == [5, 12]


@pytest.mark.asyncio
async def test_rang_none_statt_vorgabe_eins(db):
    """Der dritte Teil der Zusage: keine Platzierung 1 für eine Anlage ohne Wert."""
    voll, teil, ohne = await _drei_anlagen(db)
    rang, anzahl, rang_region, anzahl_region = await benchmark_api.berechne_rang_und_anzahl(
        db, ohne.id, ohne.region
    )
    assert rang is None and rang_region is None
    assert anzahl == 2 and anzahl_region == 0      # die Vergleichsgruppe, nicht „alle"
    rang_voll, anzahl_voll, _, _ = await benchmark_api.berechne_rang_und_anzahl(db, voll.id, "NW")
    assert rang_voll in (1, 2) and anzahl_voll == 2


@pytest.mark.asyncio
async def test_benchmark_route_traegt_basis_felder_und_keinen_absturz(db):
    voll, teil, ohne = await _drei_anlagen(db)

    antwort = await benchmark_api.get_anlage_benchmark(
        teil.anlage_hash, zeitraum="letzte_12_monate", jahr=None, monat=None, db=db
    )
    bd = antwort["benchmark"]
    assert bd.spez_ertrag_anlage == pytest.approx(120.0)
    assert bd.basis_monate == 5 and bd.fenster_monate == 12 and bd.basis_grund is None
    assert (bd.basis_bis_jahr, bd.basis_bis_monat) == _vormonate(1)[0]
    assert bd.anzahl_anlagen_gesamt == 2
    assert antwort["benchmark_erweitert"].pv.spez_ertrag.rang == bd.rang_gesamt

    antwort = await benchmark_api.get_anlage_benchmark(
        ohne.anlage_hash, zeitraum="letzte_12_monate", jahr=None, monat=None, db=db
    )
    bd = antwort["benchmark"]
    assert bd.spez_ertrag_anlage is None and bd.rang_gesamt is None
    assert bd.basis_grund == GRUND_KEIN_MASSSTAB and bd.basis_monate == 5
    assert antwort["benchmark_erweitert"].pv.spez_ertrag is None
    # Der Durchschnitt der anderen steht trotzdem da — der Vergleich fehlt, nicht die Community.
    assert bd.spez_ertrag_durchschnitt == pytest.approx(120.0)


@pytest.mark.asyncio
async def test_submit_bestaetigung_gleich_dashboard(db):
    """Bestätigung und Dashboard nennen dieselbe Zahl und dieselbe Grundgesamtheit."""
    voll, teil, ohne = await _drei_anlagen(db)
    bestaetigung = await submit_api.calculate_benchmark(db, teil)
    dashboard = (await benchmark_api.get_anlage_benchmark(
        teil.anlage_hash, zeitraum="letzte_12_monate", jahr=None, monat=None, db=db
    ))["benchmark"]
    assert bestaetigung == dashboard
    # Auch ohne Wert kommt ein Objekt zurück — der Client zeigt dann den Grund.
    assert (await submit_api.calculate_benchmark(db, ohne)).basis_grund == GRUND_KEIN_MASSSTAB


@pytest.mark.asyncio
async def test_monatsreihen_ohne_laufenden_monat(db):
    """Server-F-48: ein halber Monat gehört in keine Monatsreihe."""
    anlage = await _anlage(db, "d", monate=3, soll=True)
    jahr, monat = jetzt_utc()
    db.add(Monatswert(anlage_id=anlage.id, jahr=jahr, monat=monat, ertrag_kwh=5.0))
    await db.commit()

    reihe = await statistics_api.get_monthly_averages(monate=60, db=db)
    assert (jahr, monat) not in {(m.jahr, m.monat) for m in reihe.monate}
    assert len(reihe.monate) == 3

    reihe_stats = await stats_api.get_monats_statistiken(db, limit=12)
    assert (jahr, monat) not in {(m.jahr, m.monat) for m in reihe_stats}
    assert len(reihe_stats) == 3


@pytest.mark.asyncio
async def test_zyklen_nur_aus_vollem_jahr_und_als_median(db):
    """N-291: keine flache Hochrechnung der Speicher-Zyklen, Median statt Mittel."""
    async def speicher_anlage(zeichen: str, monate: int, entladung: float) -> None:
        anlage = Anlage(
            anlage_hash=zeichen * 64, region="BY", kwp=10.0, ausrichtung="süd",
            neigung_grad=30, installation_jahr=2020, speicher_kwh=7.0,
        )
        db.add(anlage)
        await db.flush()
        for jahr, monat in _vormonate(monate):
            db.add(Monatswert(
                anlage_id=anlage.id, jahr=jahr, monat=monat, ertrag_kwh=100.0,
                speicher_ladung_kwh=entladung * 1.1, speicher_entladung_kwh=entladung,
            ))
        await db.commit()

    await speicher_anlage("e", 12, 70.0)    # 840 ÷ 7 = 120 Zyklen
    await speicher_anlage("f", 12, 77.0)    # 132
    await speicher_anlage("g", 12, 84.0)    # 144
    await speicher_anlage("h", 6, 140.0)    # flach wären das 240 — darf nicht zählen

    antwort = await components_api.get_speicher_by_class(db=db)
    klasse = next(k for k in antwort.klassen if k.von_kwh == 5.0)
    assert klasse.anzahl == 4
    assert klasse.durchschnitt_zyklen == pytest.approx(132.0)   # Median der drei vollen
