"""eedc N-523: ein unplausibler Monat wird übersprungen — nicht der ganze Submit abgewiesen.

Bis zum 19.09.2026 warf `validate_monatswerte_plausibility` bei Zukunftsmonat,
Ertrag ≤ 0 oder über 180 kWh/kWp eine 400 für den GESAMTEN Payload. Im Proxy-Log
des Servers stand das als tägliche „400, 59 Bytes" einer aktuellen Installation
(UA `eedc-homeassistant/4.0.47`), die damit seit Wochen keinen Datensatz mehr in
der Community hatte. Jetzt: der Monat wird übersprungen und im Hinweis genannt,
der Rest angenommen; erst ohne einen einzigen plausiblen Monat gibt es 400.

Die Proben rufen den Endpunkt direkt (`submit_anlage`), mit der In-Memory-DB der
`conftest.py`; `request` wird im Submit-Pfad nicht gelesen.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from api.submit import submit_anlage, validate_monatswerte_plausibility
from models import Monatswert
from schemas import AnlageSubmitInput

# 2,4 kWp: 250 kWh = 104 kWh/kWp (plausibel), 500 kWh = 208 kWh/kWp (über 180)
BASIS = {
    "region": "NW", "kwp": 2.4, "ausrichtung": "süd", "neigung_grad": 30,
    "installation_jahr": 2024,
}


def _vormonate(n: int) -> list[tuple[int, int]]:
    """Die n abgeschlossenen Monate vor dem laufenden, älteste zuerst."""
    jetzt = datetime.now(timezone.utc)
    j, m = jetzt.year, jetzt.month
    out = []
    for _ in range(n):
        m -= 1
        if m == 0:
            j, m = j - 1, 12
        out.append((j, m))
    return list(reversed(out))


def _payload(monate: list[dict], **extra) -> AnlageSubmitInput:
    return AnlageSubmitInput(**BASIS, monatswerte=monate, **extra)


def test_der_unplausible_monat_wird_uebersprungen_der_rest_angenommen():
    (j1, m1), (j2, m2), (j3, m3) = _vormonate(3)
    daten = _payload([
        {"jahr": j1, "monat": m1, "ertrag_kwh": 250.0},
        {"jahr": j2, "monat": m2, "ertrag_kwh": 500.0},   # 208 kWh/kWp
        {"jahr": j3, "monat": m3, "ertrag_kwh": 0.0},     # Ertrag 0
    ])
    angenommen, hinweise = validate_monatswerte_plausibility(daten)
    assert [(mw.jahr, mw.monat) for mw in angenommen] == [(j1, m1)]
    assert hinweise == [
        f"{j2}-{m2:02d} übersprungen: unrealistischer Ertrag (208 kWh/kWp)",
        f"{j3}-{m3:02d} übersprungen: Ertrag 0 oder negativ",
    ]


def _naechster_monat() -> tuple[int, int]:
    """Der Monat nach dem laufenden — das Schema deckelt `jahr` auf 2050, ein fernes Jahr fiele dort schon."""
    jetzt = datetime.now(timezone.utc)
    return (jetzt.year + 1, 1) if jetzt.month == 12 else (jetzt.year, jetzt.month + 1)


def test_ein_zukunftsmonat_wird_uebersprungen_statt_abgewiesen():
    (j1, m1) = _vormonate(1)[0]
    (jz, mz) = _naechster_monat()
    daten = _payload([
        {"jahr": j1, "monat": m1, "ertrag_kwh": 250.0},
        {"jahr": jz, "monat": mz, "ertrag_kwh": 250.0},
    ])
    angenommen, hinweise = validate_monatswerte_plausibility(daten)
    assert len(angenommen) == 1
    assert hinweise == [f"{jz}-{mz:02d} übersprungen: Zukunftsmonat"]


def test_ohne_einen_plausiblen_monat_bleibt_es_400_mit_allen_gruenden():
    (j1, m1), (j2, m2) = _vormonate(2)
    daten = _payload([
        {"jahr": j1, "monat": m1, "ertrag_kwh": 500.0},
        {"jahr": j2, "monat": m2, "ertrag_kwh": 0.0},
    ])
    with pytest.raises(HTTPException) as exc:
        validate_monatswerte_plausibility(daten)
    assert exc.value.status_code == 400
    assert "Kein plausibler Monat" in exc.value.detail
    assert f"{j1}-{m1:02d} übersprungen" in exc.value.detail
    assert f"{j2}-{m2:02d} übersprungen" in exc.value.detail


def test_sehr_hoher_ertrag_bleibt_ein_hinweis_ohne_ueberspringen():
    (j1, m1) = _vormonate(1)[0]
    daten = _payload([{"jahr": j1, "monat": m1, "ertrag_kwh": 400.0}])  # 167 kWh/kWp
    angenommen, hinweise = validate_monatswerte_plausibility(daten)
    assert len(angenommen) == 1
    assert hinweise == [f"{j1}-{m1:02d}: Sehr hoher Ertrag (167 kWh/kWp)"]


@pytest.mark.asyncio
async def test_der_endpunkt_speichert_die_angenommenen_und_nennt_die_hinweise(db):
    (j1, m1), (j2, m2) = _vormonate(2)
    daten = _payload([
        {"jahr": j1, "monat": m1, "ertrag_kwh": 250.0},
        {"jahr": j2, "monat": m2, "ertrag_kwh": 500.0},
    ])
    antwort = await submit_anlage(daten, SimpleNamespace(client=None), db)
    assert antwort.success
    assert antwort.anzahl_monate == 1
    assert antwort.hinweise == [f"{j2}-{m2:02d} übersprungen: unrealistischer Ertrag (208 kWh/kWp)"]
    assert "Hinweise:" in antwort.message and f"{j2}-{m2:02d} übersprungen" in antwort.message
    gespeichert = (await db.execute(select(Monatswert.jahr, Monatswert.monat))).all()
    assert gespeichert == [(j1, m1)]


@pytest.mark.asyncio
async def test_ein_uebersprungener_monat_behaelt_seinen_frueheren_wert_auch_beim_voll_submit(db):
    (j1, m1), (j2, m2) = _vormonate(2)
    erst = _payload([
        {"jahr": j1, "monat": m1, "ertrag_kwh": 250.0},
        {"jahr": j2, "monat": m2, "ertrag_kwh": 260.0},
    ], monate_vollstaendig=True)
    antwort1 = await submit_anlage(erst, SimpleNamespace(client=None), db)
    assert antwort1.anzahl_monate == 2

    # Derselbe Hash, jetzt mit unplausiblem Wert für den zweiten Monat: er wird
    # weder überschrieben noch als „nicht gesendet" gelöscht.
    zweit = _payload([
        {"jahr": j1, "monat": m1, "ertrag_kwh": 250.0},
        {"jahr": j2, "monat": m2, "ertrag_kwh": 500.0},
    ], monate_vollstaendig=True, anlage_hash=antwort1.anlage_hash)
    antwort2 = await submit_anlage(zweit, SimpleNamespace(client=None), db)
    assert antwort2.anzahl_monate == 1
    assert antwort2.hinweise == [f"{j2}-{m2:02d} übersprungen: unrealistischer Ertrag (208 kWh/kWp)"]
    zeilen = (await db.execute(select(Monatswert.jahr, Monatswert.monat, Monatswert.ertrag_kwh))).all()
    assert sorted(zeilen) == sorted([(j1, m1, 250.0), (j2, m2, 260.0)])
