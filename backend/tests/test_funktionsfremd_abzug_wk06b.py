"""Der JAZ-Nenner zieht ab, was der Client entschieden hat (eedc WK-06b / N-454).

**Die Lage.** Der Server bildete seinen JAZ-Nenner als
``wp_stromverbrauch_kwh − wp_strom_kuehlen_kwh``. Das zweite Feld ist aber eine
**MENGE** („soviel ging ins Kühlen"), und ob sie abgezogen gehört, hängt am
**Gerät**: Bei getrennter Strommessung mit **abgeleitetem** Modus-Split ist der
Kühlanteil ein Ausschnitt genau der zwei Zähler, die den Nenner bilden — ihn
abzuziehen kürzt eine Messung um eine Verteilung ihrer selbst. Geräte hat der
Server nie gesehen; er **kann** die Bedingung nicht bilden.

Deshalb schickt der Client seit WK-06b die **Entscheidung** daneben:
``wp_strom_funktionsfremd_abzug_kwh`` (Kühlen + Lüften + Entfeuchten, bedingt).

**Gemessen an der Fixture des Add-ons** (``MONAT_F5_F3``, dieselben Zahlen wie im
Handbuch-Beispiel): 950 kWh Strom, 3600 kWh Wärme, 100 kWh abgeleiteter
Kühlanteil ⇒ **3,79** lokal gegen **4,24** hier, rund 12 %.

⛔ **Fünf Rechenstellen, fünf eigene Proben** — plus je eine für den Fallback
(Altbestand), den Sommerfall, die Migration, den Schema-Vertrag und den
Submit-Weg. Eine Sammelprobe über alle Stellen wäre grün, sobald *eine* stimmt;
genau so blieb `benchmark.py::berechne_wp_kpis` am 06.09. liegen.

**Schwesterdatei:** die Sender-Hälfte liegt im Add-on-Repo unter
``eedc/backend/tests/test_community_funktionsfremd_abzug.py``.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from models import Anlage, Monatswert

# ── Die Zahlen der Fixture `MONAT_F5_F3` ─────────────────────────────────────
STROM = 950.0        # zwei gemessene F5-Zähler: 750 Heizen + 200 Warmwasser
WAERME_HEIZ = 3000.0
WAERME_WW = 600.0
KUEHL_MENGE = 100.0  # abgeleiteter Kühlanteil — eine MENGE
JAZ_RICHTIG = 3600.0 / 950.0   # 3,789 — Abzug 0 (Option A)
JAZ_ALT = 3600.0 / 850.0       # 4,235 — Menge abgezogen (Fallback / Altbestand)


async def _anlage(db, **monatswert_felder) -> Anlage:
    """Eine Anlage mit Wärmepumpe und genau einem Monatswert (7/2026)."""
    anlage = Anlage(
        anlage_hash="h" * 64, region="BY", kwp=10.0, ausrichtung="süd",
        neigung_grad=30, installation_jahr=2020, hat_waermepumpe=True,
        wp_art="luft_wasser",
    )
    db.add(anlage)
    await db.flush()
    felder = dict(
        jahr=2026, monat=7, ertrag_kwh=1100.0,
        wp_stromverbrauch_kwh=STROM,
        wp_heizwaerme_kwh=WAERME_HEIZ,
        wp_warmwasser_kwh=WAERME_WW,
        wp_strom_kuehlen_kwh=KUEHL_MENGE,
        wp_jaz_belastbar=True,
    )
    felder.update(monatswert_felder)
    db.add(Monatswert(anlage_id=anlage.id, **felder))
    await db.commit()
    return anlage


# ══ R1 · core/wp_jaz.py::anlagen_jaz — der SoT ════════════════════════════════
#
# An ihm hängen vier Konsumenten: die Benchmark-Kachel (`berechne_wp_kpis`), der
# Community-Schnitt (`berechne_community_avg_jaz`), das Ranking
# (`statistics.py::_berechne_ranking_wert`) und beide `components.py`-Sichten.


@pytest.mark.asyncio
async def test_r1_neuer_client_zieht_nur_den_abzug_ab(db):
    """**Der Anlass.** Abzug 0.0 neben Menge 100 ⇒ Nenner 950, nicht 850."""
    from core.wp_jaz import anlagen_jaz

    anlage = await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=0.0)
    jaz = await anlagen_jaz(db, anlage.id)

    assert jaz == pytest.approx(JAZ_RICHTIG, abs=0.005), (
        f"Erwartet 3600/950 = {JAZ_RICHTIG:.3f}; 3600/850 = {JAZ_ALT:.3f} wäre "
        "die alte, um 12 % zu gute Zahl."
    )


@pytest.mark.asyncio
async def test_r1_alter_client_faellt_auf_die_menge_zurueck(db):
    """**Die andere Hälfte.** Ohne das neue Feld bleibt alles wie bisher.

    ⛔ Ohne diese Probe wäre der Bau auch dann grün, wenn der Fallback fehlte —
    und **jeder** Altbestand (zum Zeitpunkt der Migration: jede Zeile) verlöre
    seinen Abzug still.
    """
    from core.wp_jaz import anlagen_jaz

    anlage = await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=None)
    jaz = await anlagen_jaz(db, anlage.id)

    assert jaz == pytest.approx(JAZ_ALT, abs=0.005), (
        "NULL heisst 'aelterer Client, unbekannt' - dann gilt das bisherige "
        "Verhalten, nicht 'nichts abziehen'."
    )


@pytest.mark.asyncio
async def test_r1_null_und_null_komma_null_sind_verschieden(db):
    """Der Unterschied, der die ganze Regel trägt — an einer Anlage gemessen.

    Beide Zeilen tragen dieselbe Menge; nur die **Entscheidung** unterscheidet
    sie. Wer `None` wie `0.0` behandelt, kippt den Fallback; wer `0.0` wie
    `None` behandelt, kippt Option A.
    """
    from core.wp_jaz import anlagen_jaz

    a = await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=0.0)
    b = Anlage(anlage_hash="g" * 64, region="BY", kwp=10.0, ausrichtung="süd",
               neigung_grad=30, installation_jahr=2020, hat_waermepumpe=True,
               wp_art="luft_wasser")
    db.add(b)
    await db.flush()
    db.add(Monatswert(anlage_id=b.id, jahr=2026, monat=7, ertrag_kwh=1100.0,
                      wp_stromverbrauch_kwh=STROM, wp_heizwaerme_kwh=WAERME_HEIZ,
                      wp_warmwasser_kwh=WAERME_WW, wp_strom_kuehlen_kwh=KUEHL_MENGE,
                      wp_strom_funktionsfremd_abzug_kwh=None, wp_jaz_belastbar=True))
    await db.commit()

    assert await anlagen_jaz(db, a.id) == pytest.approx(JAZ_RICHTIG, abs=0.005)
    assert await anlagen_jaz(db, b.id) == pytest.approx(JAZ_ALT, abs=0.005)


@pytest.mark.asyncio
async def test_r1_der_abzug_wird_je_zeile_entschieden(db):
    """`coalesce` innen, `sum` außen — eine Anlage darf beide Formen haben.

    Zeile A (neuer Client): Strom 950, Menge 100, Abzug 0.
    Zeile B (Altbestand):   Strom 950, Menge 100, Abzug NULL ⇒ 100.
    Richtig: Σ Wärme 7200 ÷ (1900 − 100) = 4,0.
    Falsch wäre `coalesce(sum(abzug), sum(menge))` = 7200 ÷ 1900 = 3,79 — eine
    einzige neue Zeile schaltete damit den Fallback für den ganzen Zeitraum ab.
    """
    from core.wp_jaz import anlagen_jaz

    anlage = await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=0.0)
    db.add(Monatswert(anlage_id=anlage.id, jahr=2026, monat=8, ertrag_kwh=1000.0,
                      wp_stromverbrauch_kwh=STROM, wp_heizwaerme_kwh=WAERME_HEIZ,
                      wp_warmwasser_kwh=WAERME_WW, wp_strom_kuehlen_kwh=KUEHL_MENGE,
                      wp_strom_funktionsfremd_abzug_kwh=None, wp_jaz_belastbar=True))
    await db.commit()

    assert await anlagen_jaz(db, anlage.id) == pytest.approx(7200.0 / 1800.0, abs=0.005)


@pytest.mark.asyncio
async def test_r1b_sommerfall_die_zeile_bleibt_im_plausibilitaets_praedikat(db):
    """**Die zweite Rechenstelle in derselben Funktion** (`wp_jaz.py:157-167`).

    Sommer: 200 kWh Strom, davon 190 im Kühlbetrieb (abgeleitet), 450 kWh
    Warmwasser-Wärme. Richtig ist 450/200 = **2,25**.

    Zöge die Ungleichung weiter die **Menge** ab, stünde dort `450 <= 10 × 10`
    — falsch, die Zeile fiele aus der Query, und `anlagen_jaz` gäbe `None`: Die
    Anlage verschwände still aus jeder Statistik, statt ihre Zahl beizutragen.

    ⚠ Diese Probe hängt allein an der Ungleichung: Der Python-Abzug weiter unten
    ist hier bereits richtig, weil er dieselbe Summe liest.
    """
    from core.wp_jaz import anlagen_jaz

    anlage = await _anlage(
        db, wp_stromverbrauch_kwh=200.0, wp_heizwaerme_kwh=0.0,
        wp_warmwasser_kwh=450.0, wp_strom_kuehlen_kwh=190.0,
        wp_strom_funktionsfremd_abzug_kwh=0.0,
    )
    jaz = await anlagen_jaz(db, anlage.id)

    assert jaz is not None, (
        "Die Zeile darf nicht am Plausibilitäts-Prädikat hängenbleiben."
    )
    assert jaz == pytest.approx(2.25, abs=0.005)


# ══ R2 · api/stats.py — der Regionalwert ══════════════════════════════════════


@pytest.mark.asyncio
async def test_r2_regionalwert_waerme_je_kwh_strom(db):
    """`/api/stats` → `regionen[].avg_wp_jaz` (energiegewichtet)."""
    from api.stats import get_regionen_statistiken

    await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=0.0)
    regionen = await get_regionen_statistiken(db)

    assert len(regionen) == 1
    assert regionen[0].avg_wp_jaz == pytest.approx(round(JAZ_RICHTIG, 2), abs=0.005)
    assert regionen[0].wp_jaz_anzahl == 1


@pytest.mark.asyncio
async def test_r2_regionalwert_faellt_ohne_das_feld_auf_die_menge_zurueck(db):
    """Derselbe Weg für Altbestand — der Fallback gilt auch hier."""
    from api.stats import get_regionen_statistiken

    await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=None)
    regionen = await get_regionen_statistiken(db)

    assert regionen[0].avg_wp_jaz == pytest.approx(round(JAZ_ALT, 2), abs=0.005)


# ══ R3 · api/statistics.py — der globale Quotient (Impact-Tab) ════════════════


@pytest.mark.asyncio
async def test_r3_globaler_quotient(db):
    """`/api/statistics/global/totals` → `wp_waerme_je_kwh_strom`.

    ⚠ Die **Mengen** derselben Antwort bleiben ungefiltert (E1) — `wp_stromverbrauch_kwh`
    trägt weiter die vollen 950 kWh. Wer die zwei sichtbaren Zahlen teilt, bekommt
    deshalb nicht diesen Quotienten; das ist so gewollt und steht dort im Kommentar.
    """
    from api.statistics import get_global_totals

    await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=0.0)
    totals = await get_global_totals(db)

    assert totals.wp_waerme_je_kwh_strom == pytest.approx(round(JAZ_RICHTIG, 2), abs=0.005)
    assert totals.wp_quotient_anzahl == 1
    assert totals.wp_stromverbrauch_kwh == pytest.approx(STROM, abs=0.1), (
        "Die MENGE bleibt vollständig — gesperrt bzw. gekürzt wird nur der Nenner "
        "der Kennzahl."
    )


# ══ R4 · api/benchmark.py — je Monatswert (Python-Zweig) ══════════════════════


@pytest.mark.asyncio
async def test_r4_monats_benchmark_je_zeile(db):
    """`/api/benchmark/monat/{jahr}/{monat}` → `wp_jaz`.

    Der einzige Python-Zweig der Regel: Die Zeilen sind schon geladen, deshalb
    `funktionsfremd_abzug_zeile(mw)` statt des SQL-Ausdrucks.
    """
    from api.benchmark import get_monats_benchmark

    await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=0.0)
    vergleich = await get_monats_benchmark(2026, 7, db)

    assert vergleich.wp_jaz is not None
    # ⚠ `_make_monats_kpi` rundet auf EINE Nachkommastelle — 3,8 gegen 4,2 ist
    # der Unterschied, den diese Sicht überhaupt zeigen kann.
    assert vergleich.wp_jaz.durchschnitt == pytest.approx(round(JAZ_RICHTIG, 1), abs=0.001)


@pytest.mark.asyncio
async def test_r4_monats_benchmark_faellt_ohne_das_feld_auf_die_menge_zurueck(db):
    """Und der Fallback im Python-Zweig — er ist eigener Code, also eigene Probe."""
    from api.benchmark import get_monats_benchmark

    await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=None)
    vergleich = await get_monats_benchmark(2026, 7, db)

    assert vergleich.wp_jaz.durchschnitt == pytest.approx(round(JAZ_ALT, 1), abs=0.001)


# ══ R5 · api/benchmark.py::berechne_wp_kpis — die Kachel ══════════════════════


@pytest.mark.asyncio
async def test_r5_wp_kachel_zeigt_mengen_und_die_kennzahl_des_sot(db):
    """Die fünfte Stelle der Erhebung — sie **rechnete gar nichts** (Fund F-1).

    Bis zum 13.09.2026 summierte diese Query zusätzlich `wp_strom_kuehlen_kwh`
    und klemmte den Wert; gelesen hat ihn seit dem 06.09. niemand mehr. Entfernt.
    Diese Probe hält fest, was die Funktion liefert: die **Mengen** aus ihrer
    eigenen Query und die **Kennzahl** aus dem SoT.
    """
    from api.benchmark import berechne_wp_kpis

    anlage = await _anlage(db, wp_strom_funktionsfremd_abzug_kwh=0.0)
    kpis = await berechne_wp_kpis(db, anlage.id, 2020, 1, 2099, 12)

    assert kpis["stromverbrauch"] == pytest.approx(STROM, abs=0.1)
    assert kpis["waermeerzeugung"] == pytest.approx(3600.0, abs=0.1)
    assert kpis["jaz"] == pytest.approx(round(JAZ_RICHTIG, 2), abs=0.005)


# ══ Schema · Vertrag und Submit-Weg ═══════════════════════════════════════════


def test_schema_traegt_das_feld_und_unterscheidet_none_von_null():
    """`MonatswertInput`: `None` bleibt `None`, `0.0` bleibt `0.0`.

    Der Unterschied ist der Vertrag. Ein `Field(..., ge=0)` mit Default `None`
    ist die einzige Form, die beides kann.
    """
    from schemas import MonatswertInput

    ohne = MonatswertInput(jahr=2026, monat=7, ertrag_kwh=1100.0)
    assert ohne.wp_strom_funktionsfremd_abzug_kwh is None

    mit_null = MonatswertInput(jahr=2026, monat=7, ertrag_kwh=1100.0,
                               wp_strom_funktionsfremd_abzug_kwh=0.0)
    assert mit_null.wp_strom_funktionsfremd_abzug_kwh == 0.0

    mit_wert = MonatswertInput(jahr=2026, monat=7, ertrag_kwh=1100.0,
                               wp_strom_funktionsfremd_abzug_kwh=130.0)
    assert mit_wert.wp_strom_funktionsfremd_abzug_kwh == 130.0


@pytest.mark.asyncio
async def test_submit_speichert_den_abzug_beim_anlegen_und_beim_aktualisieren(db):
    """Beide Zweige von `submit.py` — Insert (`:304`) und Update (`:261`).

    ⛔ Der Update-Zweig muss auch `None` schreiben: Der Submit ist ein
    **Voll-Submit**, der Client sagt, was gilt. Ein alter Client schaltet die
    Zeile damit zurück auf den Fallback — heilbar, ein stehengebliebener
    Abzug wäre es nicht.
    """
    from starlette.requests import Request

    from api.submit import submit_anlage
    from schemas import AnlageSubmitInput, MonatswertInput

    request = Request({"type": "http", "client": ("10.0.0.1", 1), "headers": []})

    def _payload(abzug):
        return AnlageSubmitInput(
            region="BY", kwp=10.0, neigung_grad=30, installation_jahr=2020,
            hat_waermepumpe=True, wp_art="luft_wasser",
            monatswerte=[MonatswertInput(
                jahr=2026, monat=7, ertrag_kwh=1100.0,
                wp_stromverbrauch_kwh=STROM, wp_heizwaerme_kwh=WAERME_HEIZ,
                wp_warmwasser_kwh=WAERME_WW, wp_strom_kuehlen_kwh=KUEHL_MENGE,
                wp_strom_funktionsfremd_abzug_kwh=abzug,
            )],
        )

    # Insert
    await submit_anlage(_payload(0.0), request, db)
    zeile = (await db.execute(Monatswert.__table__.select())).first()
    assert zeile.wp_strom_funktionsfremd_abzug_kwh == 0.0
    assert zeile.wp_strom_kuehlen_kwh == pytest.approx(KUEHL_MENGE)

    # Update — derselbe Hash, anderer Abzug
    await submit_anlage(_payload(130.0), request, db)
    zeile = (await db.execute(Monatswert.__table__.select())).first()
    assert zeile.wp_strom_funktionsfremd_abzug_kwh == pytest.approx(130.0)

    # Update durch einen ALTEN Client — das Feld fehlt ⇒ zurück auf NULL
    await submit_anlage(_payload(None), request, db)
    zeile = (await db.execute(Monatswert.__table__.select())).first()
    assert zeile.wp_strom_funktionsfremd_abzug_kwh is None


# ══ Migration ═════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_migration_ergaenzt_die_spalte_an_einer_alten_tabelle():
    """`ALTER TABLE monatswerte ADD COLUMN …` an einer Tabelle ohne die Spalte.

    ⚠ Bestehende Zeilen bekommen `NULL` — und genau deshalb muss der Fallback
    stehen: Zum Zeitpunkt der Migration ist **jede** Zeile Altbestand.
    """
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import StaticPool

    from core.database import run_migrations

    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool,
                                 connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        # Eine „alte" Tabelle: die Spalte fehlt, eine Zeile steht drin.
        await conn.execute(text(
            "CREATE TABLE monatswerte (id INTEGER PRIMARY KEY, anlage_id INTEGER, "
            "jahr INTEGER, monat INTEGER, ertrag_kwh FLOAT, "
            "wp_strom_kuehlen_kwh FLOAT)"
        ))
        await conn.execute(text(
            "INSERT INTO monatswerte (anlage_id, jahr, monat, ertrag_kwh, "
            "wp_strom_kuehlen_kwh) VALUES (1, 2026, 7, 1100.0, 100.0)"
        ))
        await run_migrations(conn)
        spalten = {
            row[1] for row in
            (await conn.execute(text("PRAGMA table_info(monatswerte)"))).all()
        }
        assert "wp_strom_funktionsfremd_abzug_kwh" in spalten
        alt = (await conn.execute(text(
            "SELECT wp_strom_kuehlen_kwh, wp_strom_funktionsfremd_abzug_kwh "
            "FROM monatswerte"
        ))).first()
        assert alt[0] == 100.0, "Die Menge bleibt unangetastet."
        assert alt[1] is None, "Der Abzug ist unbekannt ⇒ Fallback auf die Menge."
    await engine.dispose()
