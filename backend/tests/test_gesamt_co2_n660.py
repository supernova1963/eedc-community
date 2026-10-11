"""Das Gesamt-CO₂ summiert die gelieferten Monatswerte (eedc N-660).

**Die Lage.** ``statistics.py::get_global_totals`` rechnete das CO₂ der
Gemeinschaft als ``max(0, Σ Erzeugung − Σ Einspeisung) × 0,38`` über alle
Zeilen — obwohl der Client seit eedc v4.0.22 (F-47) je Monat
``co2_vermieden_kg`` liefert, eedcs einzigen Kanon (ADR-001/DI-2, inklusive
Wärmepumpe und E-Mobilität). Gespeichert wurde der Wert, gelesen nie.

**Die Regel.** Je Zeile: geliefert ⇒ der Wert; nicht geliefert (Altbestand) ⇒
der bisherige Rückfall über genau diese Zeilen.

Drei Proben: der Mischfall (die Summe ist Wert + Rückfall — und weder die alte
Zahl noch ``coalesce(Σ co2, …)``), der reine Altbestand (bitgleich mit der
alten Rechnung) und der reine Neubestand (kein Rückfall-Anteil, auch wenn die
Mengen-Bilanz einen ergäbe).
"""
from __future__ import annotations

import pytest

from models import Anlage, Monatswert

# Zeile A (neuer Client): trägt die Client-Bilanz — WP und E-Mob inklusive,
# deshalb deutlich über (1000 − 400) × 0,38 = 228.
A_ERTRAG, A_EINSP, A_CO2 = 1000.0, 400.0, 512.3
# Zeile B (Altbestand): kein Wert ⇒ (800 − 300) × 0,38 = 190.
B_ERTRAG, B_EINSP = 800.0, 300.0
B_RUECKFALL = (B_ERTRAG - B_EINSP) * 0.38


async def _anlage_mit(db, zeichen: str, zeilen: list[dict]) -> Anlage:
    anlage = Anlage(
        anlage_hash=zeichen * 64, region="BY", kwp=10.0, ausrichtung="süd",
        neigung_grad=30, installation_jahr=2020,
    )
    db.add(anlage)
    await db.flush()
    for z in zeilen:
        db.add(Monatswert(anlage_id=anlage.id, **z))
    await db.commit()
    return anlage


@pytest.mark.asyncio
async def test_mischfall_summe_ist_wert_plus_rueckfall(db):
    """Eine Zeile mit ``co2_vermieden_kg``, eine ohne ⇒ 512,3 + 190 = 702,3."""
    from api.statistics import get_global_totals

    await _anlage_mit(db, "a", [
        dict(jahr=2026, monat=7, ertrag_kwh=A_ERTRAG, einspeisung_kwh=A_EINSP,
             co2_vermieden_kg=A_CO2),
        dict(jahr=2026, monat=8, ertrag_kwh=B_ERTRAG, einspeisung_kwh=B_EINSP,
             co2_vermieden_kg=None),
    ])
    totals = await get_global_totals(db)

    alt = (A_ERTRAG + B_ERTRAG - A_EINSP - B_EINSP) * 0.38   # 418,0
    assert totals.co2_vermieden_kg == pytest.approx(A_CO2 + B_RUECKFALL, abs=0.05), (
        f"Erwartet {A_CO2} + {B_RUECKFALL:.1f}; {alt:.1f} wäre die alte "
        f"Server-Rechnung, {A_CO2} ein Rückfall, der nicht je Zeile greift."
    )
    # Die Mengen-Sicht bleibt unberührt — sie ist nicht mehr die CO₂-Basis.
    assert totals.pv_eigenverbrauch_kwh == pytest.approx(1100.0)


@pytest.mark.asyncio
async def test_nur_altbestand_bitgleich_mit_der_alten_rechnung(db):
    """Keine Zeile trägt einen Wert ⇒ exakt ``max(0, Σ E − Σ Einsp) × 0,38``."""
    from api.statistics import get_global_totals

    await _anlage_mit(db, "b", [
        dict(jahr=2026, monat=7, ertrag_kwh=A_ERTRAG, einspeisung_kwh=A_EINSP),
        dict(jahr=2026, monat=8, ertrag_kwh=B_ERTRAG, einspeisung_kwh=B_EINSP),
    ])
    totals = await get_global_totals(db)

    assert totals.co2_vermieden_kg == round((1800.0 - 700.0) * 0.38, 1)


@pytest.mark.asyncio
async def test_nur_geliefert_kein_rueckfall_anteil(db):
    """Zwei Anlagen, beide mit Wert ⇒ Σ der Werte, kein ``EV × 0,38`` daneben."""
    from api.statistics import get_global_totals

    await _anlage_mit(db, "c", [
        dict(jahr=2026, monat=7, ertrag_kwh=A_ERTRAG, einspeisung_kwh=A_EINSP,
             co2_vermieden_kg=A_CO2),
    ])
    await _anlage_mit(db, "d", [
        dict(jahr=2026, monat=7, ertrag_kwh=B_ERTRAG, einspeisung_kwh=B_EINSP,
             co2_vermieden_kg=100.0),
    ])
    totals = await get_global_totals(db)

    assert totals.co2_vermieden_kg == pytest.approx(A_CO2 + 100.0, abs=0.05)
