"""Spezifischer Jahresertrag — die EINE Rechenstelle (SoT).

**Anlass: eedc #387 (azywietz-web, 2026-08-19), Fehler F-45 und F-46. Zugesagt in
eedc v4.0.22 für den 01.09.2026, gebaut am 17.09.2026.**

Bis dahin stand dieselbe Rechnung **sechsmal** im Baum — ``api/benchmark.py``,
dreimal ``api/statistics.py``, zweimal ``api/stats.py`` —, jede Kopie als::

    select(Monatswert.ertrag_kwh).order_by(jahr.desc(), monat.desc()).limit(12)
    if len(ertraege) >= 6:
        jahr = (sum(ertraege) / len(ertraege)) * 12

**F-45 — die flache Hochrechnung.** ``n`` war die Zahl gespeicherter Zeilen, kein
Zeitraum: sechs Sommermonate wurden auf zwölf hochgerechnet und standen neben
echten Jahreswerten. Der Melder rechnete es an seiner 2-kWp-Anlage vor —
``636,8 ÷ 6 × 12 = 1.273,6``, Rang 3 von 112. Die Rangliste maß nicht, wer am
meisten erzeugt, sondern wer die wenigsten schwachen Monate hat.

**F-46 — zwei Durchschnitte.** ``benchmark.py`` zählte Anlagen unter sechs Monaten
mit ihrer **Rohsumme** mit, die anderen Kopien übersprangen sie: Add-on 662,0 gegen
Website 840,0 am 19.08., noch 688,5 gegen 862,0 am 17.09. Und ``next(..., 1)``
meldete einer Anlage ohne Wert die Platzierung **1**.

**Die Regel hier — saisonal statt flach (Weg A, Entscheid Maintainer 19.08.2026)::**

    Fenster = lückenlose Monate ab dem jüngsten ABGESCHLOSSENEN Monat rückwärts,
              höchstens FENSTER_MONATE
    n == 12 → wert = Σ IST / kWp                                (gemessen)
    n <  12 → wert = Σ IST / Σ SOLL(Fenster) × SOLL_Jahr / kWp   (hochgerechnet)

SOLL ist die PVGIS-Erwartung der Anlage, die der Client seit eedc v4.0.22 je Monat
(``Monatswert.soll_ertrag_kwh``, Anschaffungsmonat tagesgenau gekürzt) und je Jahr
(``Anlage.soll_jahr_kwh``) mitschickt. Der Server bildet sie nicht selbst — er kennt
weder Koordinaten noch Horizont noch Anschaffungstag. Ein Frühling zählt damit als
Frühling: der Melder-Fall ergibt **978,5** statt 1.273,6 kWh/kWp.

Zwei Eigenschaften, gegen die ``tests/test_spez_ertrag_387.py`` prüft:

* **Identität.** Bei zwölf Monaten ist ``Σ SOLL(Fenster) == SOLL_Jahr`` (beide aus
  derselben aktiven Prognose), der Faktor wird 1 — der Wert ist der gemessene und
  bitgleich mit dem ``(Σ ÷ 12) × 12`` von vorher. Die Umstellung trifft
  **ausschließlich** das unvollständige Jahr.
* **Skalierungsinvarianz.** Ein um einen Faktor falsch skaliertes SOLL ändert das
  Ergebnis nicht; nur die *Form* des Jahres geht ein. Deshalb braucht diese Rechnung
  kein Plausibilitätsband auf dem SOLL-Niveau.

**Mindestdauer ist ein Monat** (Entscheid Maintainer 19.08.: *„damit jeder, der seine
Daten teilt, auch Daten bekommt"*). Das trägt, weil der Anschaffungsmonat im SOLL
tagesgenau gekürzt ankommt — 13 Tage März gegen 13 Tage SOLL, nicht gegen 31.
``basis_monate`` sagt dem Client, worauf der Wert beruht („hochgerechnet aus 5 von 12
Monaten"); die Kennzeichnung ist im Add-on seit v4.0.22 ausgeliefert.

**Kein Wert — und der Grund steht dabei (``grund``):**

* ``veraltet`` — der jüngste abgeschlossene Monat liegt mehr als MAX_ALTER_MONATE
  zurück. Eine Anlage von 2023 gehört in keine Rangliste von heute.
* ``kein_massstab`` — unter zwölf Monaten und ohne SOLL (Client vor v4.0.22 oder keine
  aktive PVGIS-Prognose). ⛔ Bewusst **kein** Ersatzmaßstab aus dem Community-Profil:
  am Live-Profil 09/2025–08/2026 gemessen läge der Melder damit bei 846,7 statt 978,5
  (−13 %) — eine gefärbte Zahl in einer Rangliste, deren Kennzeichnung nur das Add-on
  zeigt. Ein fehlender Wert mit Grund ist ehrlicher; der Handgriff (Solarprognose
  aktivieren, erneut teilen) liegt beim Anwender. Entschieden 17.09.2026 (Gegenlese
  zum Bauplan #387, Option A).
* ``keine_monate`` / ``kein_kwp`` — nichts zu rechnen.

**Warum das Fenster je Anlage endet und nicht für alle gleich:** Das Teilen ist manuell
oder folgt dem Monatsabschluss; ein gemeinsames Fenster ließe jede Anlage aus der
Liste fallen, bis ihr Besitzer wieder teilt. Am 19.08.2026 hatten 38 von 112 Anlagen
einen Juli-Wert, am 17.09. waren es 87 — ein Monat füllt sich über etwa zwei Monate.
Deshalb: je Anlage die Monate, die auf ihren jüngsten abgeschlossenen Monat
zurückreichen; das Fensterende (``bis_*``) wird mitgeliefert („Stand Juli 2026").

Der **laufende Kalendermonat zählt nie mit** — er ist unvollständig (F-48). Für die
Monatsreihen (``statistics.py::get_monthly_averages``, ``stats.py::get_monats_statistiken``)
liefert :func:`nur_abgeschlossene_monate` denselben Ausschluss als SQL-Filter.

Gegenstück im Client: ``eedc-homeassistant/eedc/frontend/src/lib/communityFenster.ts``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Anlage, Monatswert

#: Länge des Vergleichsfensters in Kalendermonaten. Mit so vielen ist der Wert
#: gemessen, mit weniger hochgerechnet.
FENSTER_MONATE = 12

#: Wie alt der jüngste abgeschlossene Monat einer Anlage höchstens sein darf,
#: damit ihr Jahreswert noch in einen aktuellen Vergleich gehört.
MAX_ALTER_MONATE = 12

GRUND_VERALTET = "veraltet"
GRUND_KEIN_MASSSTAB = "kein_massstab"
GRUND_KEINE_MONATE = "keine_monate"
GRUND_KEIN_KWP = "kein_kwp"


@dataclass(frozen=True)
class SpezJahresertrag:
    """Der spezifische Jahresertrag einer Anlage — oder der Grund, warum nicht.

    ``wert`` ist gesetzt, wenn die Anlage mindestens einen abgeschlossenen Monat
    hat, nicht veraltet ist und bei weniger als FENSTER_MONATE ein SOLL trägt.
    Sonst ist er ``None`` und ``grund`` sagt, woran es liegt.
    """

    #: Lückenlose Kalendermonate ab dem jüngsten abgeschlossenen Monat rückwärts.
    basis_monate: int
    #: kWh/kWp über das Fenster — gemessen (12) oder saisonal hochgerechnet (< 12).
    wert: float | None = None
    #: Letzter Monat des Fensters (zum Beschriften: „Stand Juli 2026").
    bis_jahr: int | None = None
    bis_monat: int | None = None
    #: Jüngster abgeschlossener Monat liegt mehr als ``MAX_ALTER_MONATE`` zurück.
    veraltet: bool = False
    #: Warum es keinen Wert gibt — einer der ``GRUND_*``-Werte, sonst ``None``.
    grund: str | None = None


def _vormonat(jahr: int, monat: int) -> tuple[int, int]:
    return (jahr - 1, 12) if monat == 1 else (jahr, monat - 1)


def _monatsindex(jahr: int, monat: int) -> int:
    """Fortlaufende Monatsnummer — macht Abstände zwischen Monaten rechenbar."""
    return jahr * 12 + (monat - 1)


def jetzt_utc() -> tuple[int, int]:
    """(Jahr, Monat) des laufenden Kalendermonats — UTC wie der Rest des Servers."""
    jetzt = datetime.now(timezone.utc)
    return jetzt.year, jetzt.month


def _auswerten(
    monate: dict[tuple[int, int], tuple[float, float | None]],
    kwp: float | None,
    soll_jahr: float | None,
    jetzt_jahr: int,
    jetzt_monat: int,
) -> SpezJahresertrag:
    """Reine Funktion: ``{(jahr, monat): (ist_kwh, soll_kwh | None)}`` → Ergebnis.

    Ohne Datenbank, damit sie sich gegen gestellte Monatslisten prüfen lässt.
    """
    # Der laufende Monat zählt nie mit — er ist unvollständig (F-48).
    abgeschlossen = {
        ym: werte
        for ym, werte in monate.items()
        if _monatsindex(*ym) < _monatsindex(jetzt_jahr, jetzt_monat)
    }
    if not abgeschlossen:
        return SpezJahresertrag(basis_monate=0, grund=GRUND_KEINE_MONATE)

    bis_jahr, bis_monat = max(abgeschlossen)
    veraltet = (
        _monatsindex(jetzt_jahr, jetzt_monat) - _monatsindex(bis_jahr, bis_monat)
        > MAX_ALTER_MONATE
    )

    # Lückenlos rückwärts zählen — eine Lücke beendet das Fenster sofort.
    basis_monate = 0
    ist_summe = 0.0
    soll_summe = 0.0
    soll_vollstaendig = True
    jahr, monat = bis_jahr, bis_monat
    while (jahr, monat) in abgeschlossen and basis_monate < FENSTER_MONATE:
        ist, soll = abgeschlossen[(jahr, monat)]
        ist_summe += ist
        basis_monate += 1
        if soll is None or soll <= 0:
            soll_vollstaendig = False
        else:
            soll_summe += soll
        jahr, monat = _vormonat(jahr, monat)

    ohne_wert = dict(
        basis_monate=basis_monate, bis_jahr=bis_jahr, bis_monat=bis_monat, veraltet=veraltet
    )
    if veraltet:
        return SpezJahresertrag(grund=GRUND_VERALTET, **ohne_wert)
    if not kwp or kwp <= 0:
        return SpezJahresertrag(grund=GRUND_KEIN_KWP, **ohne_wert)

    if basis_monate >= FENSTER_MONATE:
        # Gemessen. Das SOLL spielt keine Rolle — auch dann nicht, wenn es da ist:
        # Σ SOLL(12 Monate) == SOLL_Jahr, der Faktor wäre ohnehin 1.
        wert = ist_summe / kwp
    elif soll_vollstaendig and soll_jahr and soll_jahr > 0 and soll_summe > 0:
        # Saisonal hochgerechnet: wie gut lief die Anlage gegenüber der Erwartung
        # ihres Standorts in genau diesen Monaten — und das aufs Jahr.
        wert = (ist_summe / soll_summe) * soll_jahr / kwp
    else:
        return SpezJahresertrag(grund=GRUND_KEIN_MASSSTAB, **ohne_wert)

    return SpezJahresertrag(wert=wert, **ohne_wert)


def nur_abgeschlossene_monate():
    """SQL-Filter „Monat liegt vor dem laufenden Kalendermonat" (Server-F-48).

    Für die Monatsreihen der Community: ein halber September neben lauter ganzen
    Monaten war am 19.08.2026 live messbar (08/2026 mit 46,3 kWh/kWp bei n = 5).
    Der Client sendet den laufenden Monat seit v4.0.22 nicht mehr; ein älterer
    Client kann es weiterhin, und dann fängt ihn dieser Filter.
    """
    jahr, monat = jetzt_utc()
    return or_(
        Monatswert.jahr < jahr,
        (Monatswert.jahr == jahr) & (Monatswert.monat < monat),
    )


async def lade_spez_jahresertraege(
    db: AsyncSession,
    *,
    anlage_ids: list[int] | None = None,
) -> dict[int, SpezJahresertrag]:
    """Jahresertrag je Anlage — **zwei** Abfragen für alle.

    Die abgelösten Kopien fragten je Anlage einzeln (138 Abfragen je Rangliste).
    Der Rückgabewert enthält **jede** Anlage, auch die ohne Wert — dort ist
    ``wert is None`` und ``grund`` gesetzt.
    """
    anlagen_query = select(Anlage.id, Anlage.kwp, Anlage.soll_jahr_kwh)
    if anlage_ids is not None:
        anlagen_query = anlagen_query.where(Anlage.id.in_(anlage_ids))
    stammdaten = {
        aid: (kwp, soll_jahr)
        for aid, kwp, soll_jahr in (await db.execute(anlagen_query)).all()
    }

    monate_query = select(
        Monatswert.anlage_id,
        Monatswert.jahr,
        Monatswert.monat,
        Monatswert.ertrag_kwh,
        Monatswert.soll_ertrag_kwh,
    ).where(Monatswert.ertrag_kwh.isnot(None))
    if anlage_ids is not None:
        monate_query = monate_query.where(Monatswert.anlage_id.in_(anlage_ids))

    je_anlage: dict[int, dict[tuple[int, int], tuple[float, float | None]]] = {}
    for anlage_id, jahr, monat, ertrag, soll in (await db.execute(monate_query)).all():
        je_anlage.setdefault(anlage_id, {})[(jahr, monat)] = (
            float(ertrag),
            float(soll) if soll is not None else None,
        )

    jetzt_jahr, jetzt_monat = jetzt_utc()
    return {
        anlage_id: _auswerten(
            je_anlage.get(anlage_id, {}), kwp, soll_jahr, jetzt_jahr, jetzt_monat
        )
        for anlage_id, (kwp, soll_jahr) in stammdaten.items()
    }


async def lade_spez_jahresertrag(db: AsyncSession, anlage_id: int) -> SpezJahresertrag:
    """Jahresertrag einer einzelnen Anlage."""
    ergebnisse = await lade_spez_jahresertraege(db, anlage_ids=[anlage_id])
    return ergebnisse.get(
        anlage_id, SpezJahresertrag(basis_monate=0, grund=GRUND_KEINE_MONATE)
    )


def werte(ertraege: dict[int, SpezJahresertrag]) -> list[float]:
    """Nur die Anlagen mit Wert — die Vergleichsgruppe."""
    return [e.wert for e in ertraege.values() if e.wert is not None]


def durchschnitt(ertraege: dict[int, SpezJahresertrag]) -> float:
    """Mittelwert über die Vergleichsgruppe. ``0``, wenn sie leer ist.

    Genau hier saß **F-46**: die eine Hälfte des Baums zählte Anlagen ohne
    vollständiges Fenster mit ihrer Rohsumme mit, die andere nicht.
    """
    gueltige = werte(ertraege)
    return sum(gueltige) / len(gueltige) if gueltige else 0
