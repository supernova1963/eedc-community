"""Prüfschicht für den Community-Vergleich der eigenen Anlage — die vier ungedeckten Achsen.

Vorhaben ``vorhaben-pruefschicht-community-vergleich.md`` (Go Gernot 18.09.2026).
Gedeckt waren spez. Jahresertrag (``test_spez_ertrag_387.py``) und WP-JAZ
(``core/wp_jaz.py`` + Add-on). Hier: **E-Auto PV-Anteil · Wallbox PV-Anteil ·
BKW spez. Ertrag · Speicher.**

**Die eine Invariante** (benchmark.py, Kommentar in ``berechne_wp_kpis``): eigener
Wert und Vergleichswert entstehen nach **derselben Regel** — dieselbe
Bildungsvorschrift, dieselben Filter (laufender Monat, Fenster), dieselbe
Nullbehandlung. Sonst vergleicht die Kachel zwei verschiedene Größen und nennt es
einen Rang. **Die zweite:** zu jedem Vergleichswert gehört seine Grundgesamtheit
``n`` (``KPIVergleich.von`` — so trägt es der PV-Jahresertrag seit #387).

Je Achse vier Fragen, jede als eigene Probe:

* **Identität** — eine Anlage allein in der Community: eigener Wert == Ø.
* **Grundgesamtheit** — zwei Anlagen mit Flag, eine trägt bei: ``von == 1``
  (nicht 2, nicht ``None``).
* **Laufender Monat** — ein halber Monat zählt auf keiner Seite (F-48).
* **Fenster** — der Vergleichswert folgt dem Zeitraum des eigenen Werts. Der
  Add-on-Proxy sendet ``letzte_12_monate`` (``routes/community.py:363``); eine
  Anlage, die seit drei Jahren teilt, darf nicht mit ihrer Drei-Jahres-Summe im Ø
  stehen und mit zwölf Monaten daneben.
* **Nullbehandlung** — 0 % PV-Anteil bzw. Monate ohne Wert: die Probe verlangt
  keine bestimmte Regel, sondern **dieselbe** auf beiden Seiten (Wahrheitstafel:
  zählt der eigene Wert, zählt er auch im Ø — und umgekehrt).

Die Proben fragen die **Route** (``get_anlage_benchmark``), nicht die Hilfsfunktion:
das ist die Antwort, die der Add-on-Client zeigt. Wo eine Probe ``pytest.approx``
braucht, steht sie an einem Quotienten; Summen und ``round(…, 0)`` sind bitgleich.

Speicher hat keinen Vergleichswert (``SpeicherBenchmark`` trägt nur eigene Werte);
dort prüft die Schicht, dass die eigenen KPIs ihre Grundlage nennen und den
laufenden Monat weglassen.
"""
from __future__ import annotations

import pytest

from api import benchmark as benchmark_api
from core.spez_ertrag import jetzt_utc
from models import Anlage, Monatswert

#: Was der Add-on-Proxy anfragt (``eedc/backend/api/routes/community.py:363``).
ZEITRAUM = "letzte_12_monate"

# Gestellte Monatszeilen — Ladung 100 kWh, davon PV 50 → 50 % (bzw. 10 → 10 %).
EAUTO_50 = dict(eauto_ladung_gesamt_kwh=100.0, eauto_ladung_pv_kwh=50.0, eauto_km=500.0)
EAUTO_10 = dict(eauto_ladung_gesamt_kwh=100.0, eauto_ladung_pv_kwh=10.0, eauto_km=500.0)
EAUTO_0 = dict(eauto_ladung_gesamt_kwh=100.0, eauto_ladung_pv_kwh=0.0, eauto_km=500.0)
WALLBOX_50 = dict(wallbox_ladung_kwh=100.0, wallbox_ladung_pv_kwh=50.0, wallbox_ladevorgaenge=10)
WALLBOX_10 = dict(wallbox_ladung_kwh=100.0, wallbox_ladung_pv_kwh=10.0, wallbox_ladevorgaenge=10)
WALLBOX_0 = dict(wallbox_ladung_kwh=100.0, wallbox_ladung_pv_kwh=0.0, wallbox_ladevorgaenge=10)
# 800 Wp, 60 kWh je Monat → 720 kWh ÷ 0,8 kWp = 900 kWh/kWp im Jahr.
BKW_WP = 800.0
BKW_60 = dict(bkw_erzeugung_kwh=60.0, bkw_eigenverbrauch_kwh=40.0)
BKW_SPEZ_JAHR = 12 * 60.0 / (BKW_WP / 1000)
# 7 kWh Speicher, je Monat 100 kWh geladen (20 aus dem Netz), 90 entladen.
SPEICHER_KWH = 7.0
SPEICHER = dict(speicher_ladung_kwh=100.0, speicher_entladung_kwh=90.0, speicher_ladung_netz_kwh=20.0)


# ── Bausteine ────────────────────────────────────────────────────────────────


def _vormonate(n: int, *, ab: tuple[int, int] | None = None) -> list[tuple[int, int]]:
    """Die ``n`` abgeschlossenen Monate vor ``ab`` (Default: laufender Monat), älteste zuerst."""
    jahr, monat = ab or jetzt_utc()
    out: list[tuple[int, int]] = []
    for _ in range(n):
        jahr, monat = (jahr - 1, 12) if monat == 1 else (jahr, monat - 1)
        out.append((jahr, monat))
    return list(reversed(out))


async def _anlage(db, zeichen: str, **ausstattung) -> Anlage:
    anlage = Anlage(
        anlage_hash=zeichen * 64, region="NW", kwp=10.0, ausrichtung="süd",
        neigung_grad=30, installation_jahr=2023, **ausstattung,
    )
    db.add(anlage)
    await db.flush()
    return anlage


async def _monate(db, anlage: Anlage, monate: list[tuple[int, int]], **felder) -> None:
    """Monatszeilen mit PV-Ertrag (damit die PV-Achse nicht stört) plus ``felder``."""
    for jahr, monat in monate:
        db.add(Monatswert(anlage_id=anlage.id, jahr=jahr, monat=monat, ertrag_kwh=100.0, **felder))
    await db.commit()


async def _kachel(db, anlage: Anlage):
    """Die erweiterten Benchmarks, wie der Add-on-Client sie bekommt."""
    antwort = await benchmark_api.get_anlage_benchmark(
        anlage.anlage_hash, zeitraum=ZEITRAUM, jahr=None, monat=None, db=db
    )
    return antwort["benchmark_erweitert"]


def _seiten(kpi, vorschrift: str) -> str:
    return (
        f"eigener Wert {kpi.wert} ({ZEITRAUM}) gegen Ø {kpi.community_avg} — {vorschrift}"
    )


# ══ E-Auto PV-Anteil ═════════════════════════════════════════════════════════
# eigener Wert: berechne_eauto_kpis(…, Fenster der Anfrage)   benchmark.py:239
# Ø:            berechne_community_avg_pv_anteil_eauto → berechne_eauto_kpis(…, 2020-01 … 2099-12)  :327
# n:            KPIVergleich.von — Route :720 setzt nur wert + community_avg


@pytest.mark.asyncio
async def test_eauto_identitaet_ein_wert_fuer_beide_seiten(db):
    """Eine Anlage allein in der Community: ihr Wert ist der Ø, bitgleich."""
    anlage = await _anlage(db, "a", hat_eauto=True)
    await _monate(db, anlage, _vormonate(12), **EAUTO_50)
    kpi = (await _kachel(db, anlage)).eauto.pv_anteil
    assert kpi.wert == 50.0
    assert kpi.community_avg == kpi.wert
    # F-76: die Ø-Seite bekommt das Fenster des eigenen Werts und liefert (Ø, n)
    assert await benchmark_api.berechne_community_avg_pv_anteil_eauto(
        db, *benchmark_api.get_zeitraum_filter("letzte_12_monate")
    ) == (50.0, 1)


@pytest.mark.asyncio
async def test_eauto_vergleichswert_nennt_seine_grundgesamtheit(db):
    """Zwei Anlagen mit E-Auto, eine trägt einen Wert bei — n ist 1 (nicht 2, nicht None)."""
    traegt = await _anlage(db, "a", hat_eauto=True)
    await _monate(db, traegt, _vormonate(12), **EAUTO_50)
    leer = await _anlage(db, "b", hat_eauto=True)        # Flag ja, Ladung nie gemeldet
    await _monate(db, leer, _vormonate(12))
    kpi = (await _kachel(db, traegt)).eauto.pv_anteil
    assert kpi.community_avg == 50.0                      # die leere Anlage zählt nicht mit …
    assert kpi.von == 1, (
        f"von={kpi.von}: der Ø nennt seine Grundgesamtheit nicht — "
        "berechne_community_avg_pv_anteil_eauto gibt nur float zurück (benchmark.py:315), "
        "die Route füllt KPIVergleich.von nicht (:720); der PV-Jahresertrag trägt es seit #387"
    )


@pytest.mark.asyncio
async def test_eauto_laufender_monat_zaehlt_auf_keiner_seite(db):
    """F-48: ein halber Monat mit 100 % PV darf den Ø nicht heben, wenn er den eigenen Wert nicht hebt."""
    anlage = await _anlage(db, "a", hat_eauto=True)
    await _monate(db, anlage, _vormonate(12), **EAUTO_50)
    await _monate(db, anlage, [jetzt_utc()], eauto_ladung_gesamt_kwh=100.0, eauto_ladung_pv_kwh=100.0)
    kpi = (await _kachel(db, anlage)).eauto.pv_anteil
    assert kpi.wert == 50.0                               # get_zeitraum_filter lässt ihn weg
    assert kpi.community_avg == kpi.wert, _seiten(
        kpi, "der Ø rechnet 2020-01 … 2099-12 und nimmt den laufenden Monat mit (benchmark.py:327); "
             "nur_abgeschlossene_monate() aus core/spez_ertrag.py steht dort nicht",
    )


@pytest.mark.asyncio
async def test_eauto_vergleichswert_folgt_dem_fenster_des_eigenen_werts(db):
    """Drei Jahre geteilt: zwölf Monate mit 50 %, davor 24 mit 10 %. Beide Seiten dasselbe Fenster."""
    anlage = await _anlage(db, "a", hat_eauto=True)
    fenster = _vormonate(12)
    await _monate(db, anlage, fenster, **EAUTO_50)
    await _monate(db, anlage, _vormonate(24, ab=fenster[0]), **EAUTO_10)
    kpi = (await _kachel(db, anlage)).eauto.pv_anteil
    assert kpi.community_avg == kpi.wert, _seiten(
        kpi, "der eigene Wert ist das angefragte Fenster, der Ø derselben Anlage ihre gesamte "
             "Historie (benchmark.py:327) — der zeitraum-Parameter erreicht die Ø-Seite nicht",
    )


@pytest.mark.asyncio
async def test_eauto_null_prozent_auf_beiden_seiten_gleich_behandelt(db):
    """0 % PV (lädt nur nachts): entweder ein Wert auf beiden Seiten oder auf keiner.

    Heute ist es auf keiner (``if pv_anteil`` in :281 und ``ea.get("pv_anteil")`` in :328).
    Wer 0 % zum Wert erklärt, ändert beide Stellen — dann verlangt die Probe Ø 30.
    """
    nachts = await _anlage(db, "a", hat_eauto=True)
    await _monate(db, nachts, _vormonate(12), **EAUTO_0)
    tags = await _anlage(db, "b", hat_eauto=True)
    await _monate(db, tags, _vormonate(12), eauto_ladung_gesamt_kwh=100.0, eauto_ladung_pv_kwh=60.0)
    eigene = (await _kachel(db, nachts)).eauto
    fremde = (await _kachel(db, tags)).eauto.pv_anteil
    zaehlt_eigen = eigene is not None and eigene.pv_anteil is not None
    zaehlt_im_schnitt = fremde.community_avg == pytest.approx(30.0)      # (0 + 60) ÷ 2
    assert zaehlt_eigen == zaehlt_im_schnitt, (
        f"0 % ist eigener Wert: {zaehlt_eigen}, zählt im Ø: {zaehlt_im_schnitt} (Ø={fremde.community_avg})"
    )
    assert fremde.community_avg == pytest.approx(30.0 if zaehlt_eigen else 60.0)


# ══ Wallbox PV-Anteil ════════════════════════════════════════════════════════
# eigener Wert: berechne_wallbox_kpis(…, Fenster der Anfrage)   benchmark.py:334
# Ø:            berechne_community_avg_pv_anteil_wallbox → berechne_wallbox_kpis(…, 2020-01 … 2099-12)  :391
# n:            KPIVergleich.von — Route :737 setzt nur wert + community_avg


@pytest.mark.asyncio
async def test_wallbox_identitaet_ein_wert_fuer_beide_seiten(db):
    anlage = await _anlage(db, "a", hat_wallbox=True)
    await _monate(db, anlage, _vormonate(12), **WALLBOX_50)
    kpi = (await _kachel(db, anlage)).wallbox.pv_anteil
    assert kpi.wert == 50.0
    assert kpi.community_avg == kpi.wert
    # F-76: die Ø-Seite bekommt das Fenster des eigenen Werts und liefert (Ø, n)
    assert await benchmark_api.berechne_community_avg_pv_anteil_wallbox(
        db, *benchmark_api.get_zeitraum_filter("letzte_12_monate")
    ) == (50.0, 1)


@pytest.mark.asyncio
async def test_wallbox_vergleichswert_nennt_seine_grundgesamtheit(db):
    traegt = await _anlage(db, "a", hat_wallbox=True)
    await _monate(db, traegt, _vormonate(12), **WALLBOX_50)
    leer = await _anlage(db, "b", hat_wallbox=True)
    await _monate(db, leer, _vormonate(12))
    kpi = (await _kachel(db, traegt)).wallbox.pv_anteil
    assert kpi.community_avg == 50.0
    assert kpi.von == 1, (
        f"von={kpi.von}: berechne_community_avg_pv_anteil_wallbox gibt nur float zurück "
        "(benchmark.py:379), die Route füllt KPIVergleich.von nicht (:737)"
    )


@pytest.mark.asyncio
async def test_wallbox_laufender_monat_zaehlt_auf_keiner_seite(db):
    anlage = await _anlage(db, "a", hat_wallbox=True)
    await _monate(db, anlage, _vormonate(12), **WALLBOX_50)
    await _monate(db, anlage, [jetzt_utc()], wallbox_ladung_kwh=100.0, wallbox_ladung_pv_kwh=100.0)
    kpi = (await _kachel(db, anlage)).wallbox.pv_anteil
    assert kpi.wert == 50.0
    assert kpi.community_avg == kpi.wert, _seiten(
        kpi, "der Ø rechnet 2020-01 … 2099-12 und nimmt den laufenden Monat mit (benchmark.py:391)",
    )


@pytest.mark.asyncio
async def test_wallbox_vergleichswert_folgt_dem_fenster_des_eigenen_werts(db):
    anlage = await _anlage(db, "a", hat_wallbox=True)
    fenster = _vormonate(12)
    await _monate(db, anlage, fenster, **WALLBOX_50)
    await _monate(db, anlage, _vormonate(24, ab=fenster[0]), **WALLBOX_10)
    kpi = (await _kachel(db, anlage)).wallbox.pv_anteil
    assert kpi.community_avg == kpi.wert, _seiten(
        kpi, "der Ø derselben Anlage ist ihre gesamte Historie (benchmark.py:391), "
             "der eigene Wert das angefragte Fenster",
    )


@pytest.mark.asyncio
async def test_wallbox_null_prozent_auf_beiden_seiten_gleich_behandelt(db):
    """Heute auf keiner Seite ein Wert (``if pv_anteil`` :374, ``wb.get("pv_anteil")`` :392)."""
    nachts = await _anlage(db, "a", hat_wallbox=True)
    await _monate(db, nachts, _vormonate(12), **WALLBOX_0)
    tags = await _anlage(db, "b", hat_wallbox=True)
    await _monate(db, tags, _vormonate(12), wallbox_ladung_kwh=100.0, wallbox_ladung_pv_kwh=60.0)
    eigene = (await _kachel(db, nachts)).wallbox
    fremde = (await _kachel(db, tags)).wallbox.pv_anteil
    zaehlt_eigen = eigene is not None and eigene.pv_anteil is not None
    zaehlt_im_schnitt = fremde.community_avg == pytest.approx(30.0)
    assert zaehlt_eigen == zaehlt_im_schnitt, (
        f"0 % ist eigener Wert: {zaehlt_eigen}, zählt im Ø: {zaehlt_im_schnitt} (Ø={fremde.community_avg})"
    )
    assert fremde.community_avg == pytest.approx(30.0 if zaehlt_eigen else 60.0)


# ══ BKW spez. Ertrag ═════════════════════════════════════════════════════════
# eigener Wert: berechne_bkw_kpis(…, Fenster der Anfrage)   benchmark.py:398
#               Σ Erzeugung ÷ kWp; unter 12 Zeilen flach × 12/n (:439), ab 12 Zeilen die Summe wie sie ist (:441)
# Ø:            berechne_community_avg_bkw_spez_ertrag → berechne_bkw_kpis(…, 2020-01 … 2099-12)  :467
# n:            KPIVergleich.von — Route :752 setzt nur wert + community_avg


@pytest.mark.asyncio
async def test_bkw_identitaet_ein_wert_fuer_beide_seiten(db):
    anlage = await _anlage(db, "a", hat_balkonkraftwerk=True, bkw_wp=BKW_WP)
    await _monate(db, anlage, _vormonate(12), **BKW_60)
    kpi = (await _kachel(db, anlage)).balkonkraftwerk.spez_ertrag
    assert kpi.wert == BKW_SPEZ_JAHR == 900.0
    assert kpi.community_avg == kpi.wert
    # F-76: die Ø-Seite bekommt das Fenster des eigenen Werts und liefert (Ø, n)
    assert await benchmark_api.berechne_community_avg_bkw_spez_ertrag(
        db, *benchmark_api.get_zeitraum_filter("letzte_12_monate")
    ) == (900.0, 1)


@pytest.mark.asyncio
async def test_bkw_vergleichswert_nennt_seine_grundgesamtheit(db):
    traegt = await _anlage(db, "a", hat_balkonkraftwerk=True, bkw_wp=BKW_WP)
    await _monate(db, traegt, _vormonate(12), **BKW_60)
    leer = await _anlage(db, "b", hat_balkonkraftwerk=True, bkw_wp=BKW_WP)
    await _monate(db, leer, _vormonate(12))
    kpi = (await _kachel(db, traegt)).balkonkraftwerk.spez_ertrag
    assert kpi.community_avg == 900.0
    assert kpi.von == 1, (
        f"von={kpi.von}: berechne_community_avg_bkw_spez_ertrag gibt nur float zurück "
        "(benchmark.py:453), die Route füllt KPIVergleich.von nicht (:752)"
    )


@pytest.mark.asyncio
async def test_bkw_laufender_monat_zaehlt_auf_keiner_seite(db):
    anlage = await _anlage(db, "a", hat_balkonkraftwerk=True, bkw_wp=BKW_WP)
    await _monate(db, anlage, _vormonate(12), **BKW_60)
    await _monate(db, anlage, [jetzt_utc()], bkw_erzeugung_kwh=100.0, bkw_eigenverbrauch_kwh=50.0)
    kpi = (await _kachel(db, anlage)).balkonkraftwerk.spez_ertrag
    assert kpi.wert == 900.0
    assert kpi.community_avg == kpi.wert, _seiten(
        kpi, "der Ø rechnet 2020-01 … 2099-12 (benchmark.py:467): 13 Zeilen, keine Normierung (:441) — "
             "der halbe Monat kommt obendrauf",
    )


@pytest.mark.asyncio
async def test_bkw_vergleichswert_folgt_dem_fenster_des_eigenen_werts(db):
    """Drei Jahre je 60 kWh/Monat: 900 kWh/kWp im Jahr — auf beiden Seiten.

    Ab zwölf Zeilen nimmt ``berechne_bkw_kpis`` die Summe, wie sie ist (:441). Für das
    angefragte Fenster stimmt das; über die ganze Historie (:467) wird daraus die
    Drei-Jahres-Summe ÷ kWp.
    """
    anlage = await _anlage(db, "a", hat_balkonkraftwerk=True, bkw_wp=BKW_WP)
    fenster = _vormonate(12)
    await _monate(db, anlage, fenster, **BKW_60)
    await _monate(db, anlage, _vormonate(24, ab=fenster[0]), **BKW_60)
    kpi = (await _kachel(db, anlage)).balkonkraftwerk.spez_ertrag
    assert kpi.community_avg == kpi.wert, _seiten(
        kpi, "die Ø-Seite summiert 36 Monate ohne Normierung auf ein Jahr (benchmark.py:441 + :467)",
    )


@pytest.mark.asyncio
async def test_bkw_monate_ohne_wert_auf_beiden_seiten_gleich_behandelt(db):
    """BKW erst seit sechs Monaten: sechs Zeilen mit, sechs ohne BKW-Wert.

    Verlangt wird nicht die Zahl, sondern dass beide Seiten dieselbe bilden — die
    Probe legt damit die Regel „Zeilen ohne BKW-Wert zählen im Nenner mit" (:413)
    nicht fest, sie hält nur ihre Symmetrie fest.
    """
    anlage = await _anlage(db, "a", hat_balkonkraftwerk=True, bkw_wp=BKW_WP)
    fenster = _vormonate(12)
    await _monate(db, anlage, fenster[:6])                 # PV ja, BKW noch nicht
    await _monate(db, anlage, fenster[6:], **BKW_60)
    kpi = (await _kachel(db, anlage)).balkonkraftwerk.spez_ertrag
    assert kpi.wert > 0
    assert kpi.community_avg == kpi.wert, _seiten(kpi, "Zeilen ohne BKW-Wert")
    # Und die 0-Erzeugung: kein eigener KPI, kein Beitrag zum Ø — oder beides.
    still = await _anlage(db, "b", hat_balkonkraftwerk=True, bkw_wp=BKW_WP)
    await _monate(db, still, _vormonate(12), bkw_erzeugung_kwh=0.0, bkw_eigenverbrauch_kwh=0.0)
    eigene = (await _kachel(db, still)).balkonkraftwerk
    fremde = (await _kachel(db, anlage)).balkonkraftwerk.spez_ertrag
    zaehlt_eigen = eigene is not None and eigene.spez_ertrag is not None
    zaehlt_im_schnitt = fremde.community_avg == pytest.approx(kpi.wert / 2)
    assert zaehlt_eigen == zaehlt_im_schnitt, (
        f"0 kWh ist eigener Wert: {zaehlt_eigen}, zählt im Ø: {zaehlt_im_schnitt} (Ø={fremde.community_avg})"
    )


# ══ Speicher ═════════════════════════════════════════════════════════════════
# eigener Wert: berechne_speicher_kpis(…, Fenster der Anfrage)   benchmark.py:85
#               Zyklen = Σ Entladung ÷ Kapazität, unter 12 Zeilen flach × 12/n (:128)
# Ø:            — (SpeicherBenchmark trägt nur eigene Werte, Route :671)
# n / Grundlage: nichts — weder die Funktion (:151) noch das Schema nennen die Monatszahl


@pytest.mark.asyncio
async def test_speicher_kpis_nennen_ihre_grundlage(db):
    """Fünf Monate → „Zyklen/Jahr" ist eine Hochrechnung; die Antwort muss sagen, worauf sie beruht.

    Dieselbe Klasse wie #387 (``BenchmarkData.basis_monate``) und N-291 (keine
    flache Hochrechnung der Zyklen in der Klassen-Statistik): ein Wert, der aus
    fünf Monaten ×12/5 entsteht, ohne dass es dabeisteht.
    """
    anlage = await _anlage(db, "a", speicher_kwh=SPEICHER_KWH)
    await _monate(db, anlage, _vormonate(5), **SPEICHER)
    speicher = (await _kachel(db, anlage)).speicher
    assert speicher is not None and speicher.zyklen_jahr is not None
    assert getattr(speicher, "basis_monate", None) == 5, (
        "SpeicherBenchmark nennt keine Grundlage: zyklen_jahr ist aus 5 Monaten flach ×12/5 "
        "hochgerechnet (benchmark.py:128), berechne_speicher_kpis gibt `monate` nicht zurück (:151), "
        "das Schema (schemas.py:462) hat kein basis_monate"
    )


@pytest.mark.asyncio
async def test_speicher_eigener_wert_ohne_laufenden_monat(db):
    """Zwölf volle Monate plus ein halber mit unsinnigem Verhältnis — der zählt nicht.

    Kein Vergleichswert auf dieser Achse: die Probe hält die Regel des eigenen
    Werts fest (Zyklen = Σ Entladung ÷ Kapazität, Wirkungsgrad, Netzanteil).
    """
    anlage = await _anlage(db, "a", speicher_kwh=SPEICHER_KWH)
    await _monate(db, anlage, _vormonate(12), **SPEICHER)
    await _monate(db, anlage, [jetzt_utc()], speicher_ladung_kwh=1000.0, speicher_entladung_kwh=100.0)
    speicher = (await _kachel(db, anlage)).speicher
    assert speicher.kapazitaet.wert == SPEICHER_KWH
    assert speicher.zyklen_jahr.wert == round(12 * 90.0 / SPEICHER_KWH, 0) == 154.0
    assert speicher.wirkungsgrad.wert == 90.0
    assert speicher.netz_anteil.wert == 20.0
