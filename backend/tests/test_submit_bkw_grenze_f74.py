"""F-74 — ein Balkonkraftwerk über 2.000 Wp konnte nie teilen.

``AnlageSubmitInput.bkw_wp`` trug ``le=2000``. Ein Anwender mit 2.200 oder
2.400 Wp Modulleistung (seit dem Solarpaket I der Normalfall: 2.000 W
Wechselrichter, Module darüber) bekam seinen **gesamten** Submit mit 422
zurück — nicht nur das BKW-Feld. Gemessen im NPM-Zugriffslog 30.08.–17.09.2026:
21 Abweisungen mit Antwortlänge 149 Bytes, und 149 Bytes ist exakt die
Pydantic-Meldung zu ``bkw_wp`` mit einem Fließkommawert (nachgestellt an der
App: 2200.0 · 2400.0 · 3000.0 → 149; kein anderes Feld trifft die Länge).

Schwesterdatei: test_spez_ertrag_387.py (dieselbe Submit-Route, andere Grenzen).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas import AnlageSubmitInput

BASIS = {
    "region": "NW", "kwp": 2.4, "ausrichtung": "süd", "neigung_grad": 30,
    "installation_jahr": 2025, "hat_balkonkraftwerk": True,
    "monatswerte": [{"jahr": 2026, "monat": 7, "ertrag_kwh": 250.0}],
}


@pytest.mark.parametrize("wp", [2200.0, 2400.0, 3000.0, 8000.0])
def test_bkw_ueber_2000_wp_wird_angenommen(wp):
    daten = AnlageSubmitInput(**BASIS, bkw_wp=wp)
    assert daten.bkw_wp == wp


def test_die_grenze_faengt_weiterhin_fehleingaben():
    with pytest.raises(ValidationError):
        AnlageSubmitInput(**BASIS, bkw_wp=60_000.0)
    with pytest.raises(ValidationError):
        AnlageSubmitInput(**BASIS, bkw_wp=-1.0)
