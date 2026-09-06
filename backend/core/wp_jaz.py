"""SoT der Wärmepumpen-Arbeitszahl auf dem Community-Server.

**Das Problem, das dieses Modul löst (06.09.2026, rapahl per PN 92196).**
Der Server bildete die JAZ an zwei Orten mit zwei verschiedenen Formeln — und
beide standen im selben Bildschirm untereinander:

* die **Kachel** (`api/benchmark.py`, „−19,1 % vs. Ø") und
* der **Balken** darunter (`api/components.py`, „JAZ nach Region").

Gemessen am 06.09.2026 an der öffentlichen API: Der Ø hinter der Kachel lag bei
rund **4,45**, der bauartgefilterte Schnitt derselben Community über
``/components/waermepumpe/by-art`` bei **3,99**. Zwei Zahlen über dieselbe
Grundgesamtheit, eine Seite.

⭐ **Die drei Unterschiede — und die Pointe: die vollständige Formel stand an
KEINER der beiden Stellen.** Jede hatte zwei von drei Bedingungen:

============================  ==================  ==================
Bedingung                     Kachel (vorher)     Balken (vorher)
============================  ==================  ==================
P12 ``wp_jaz_belastbar``      **fehlte**          vorhanden
W-14 Kühlstrom-Abzug          vorhanden           **fehlte**
Passiv gekühlt ausgeschl.     vorhanden           **fehlte**
============================  ==================  ==================

Deshalb gibt es hier **einen** Ort und keine dritte Variante.

**Die Regel, aus dem eedc-SOLL Wärme/Klima übernommen:**

* **P12 (ADR-002)** — ein Monatswert, dessen Zähler und Nenner verschieden
  abgegrenzt sind, trägt keine Arbeitszahl. Der Server hat die Geräte nie
  gesehen; ``wp_jaz_belastbar`` ist die Auskunft des Clients darüber, ob er
  darf. ``NULL`` (Altbestand) zählt mit — unbekannt ist nicht verboten.
  ⭐ Seit dem 06.09.2026 trägt das Flag **zwei** Hälften: die Abgrenzung *und*
  die Herkunft (gerechnete Wärme aus ``Strom × gepflegter JAZ`` sperrt die
  Kennzahl, weil sie den gepflegten Wert nur zurückgibt).
* **W-14 (SOLL §4.2 Fall 4)** — der Kühlstrom gehört nicht in den Nenner. Die
  abgeführte Kältemenge steht in keinem Zähler; wer kühlt, stünde sonst
  systematisch schlechter da als wer es nicht tut.
* **A5 (SOLL §4.1/§7)** — passiv gekühlte Anlagen zählen nicht in einen
  gemeinsamen Durchschnitt. Passive Kühlung läuft nur über Umwälzpumpen, ihre
  Effizienz liegt um ein Vielfaches höher. Ihre **eigene** Kennzahl bleibt
  richtig und wird weiter angezeigt.

⛔ **Gesperrt ist immer nur die KENNZAHL, nie die MENGE** (eedc E1 — Mengen
summiert, Kennzahlen getrennt). Strom-, Heiz- und Warmwassersummen bleiben
additiv richtig und fließen unverändert in alle Mengen-Auswertungen.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Anlage, Monatswert


def anlagen_filter(*, wp_art: str | None = None):
    """Das Anlagen-Prädikat für jeden JAZ-Vergleichswert.

    Wärmepumpe vorhanden, **nicht** passiv gekühlt (A5), optional auf eine
    Bauart eingegrenzt. ``kuehlung_art IS NULL`` ist Altbestand und zählt mit:
    unbekannt ist nicht passiv.
    """
    query = select(Anlage.id).where(
        Anlage.hat_waermepumpe == True,  # noqa: E712 — SQLAlchemy-Ausdruck
        (Anlage.kuehlung_art.is_(None)) | (Anlage.kuehlung_art != "passiv"),
    )
    if wp_art:
        query = query.where(Anlage.wp_art == wp_art)
    return query


async def anlagen_jaz(
    db: AsyncSession,
    anlage_id: int,
    *,
    von_jahr: int = 2020,
    von_monat: int = 1,
    bis_jahr: int = 2099,
    bis_monat: int = 12,
) -> float | None:
    """Die Arbeitszahl EINER Anlage über einen Zeitraum — oder ``None``.

    ``None`` heißt „nicht bildbar" und ist keine 0: kein Strom erfasst, keine
    belastbaren Monate, oder der ganze Strom ging ins Kühlen.
    """
    result = await db.execute(
        select(
            func.sum(Monatswert.wp_stromverbrauch_kwh),
            func.sum(Monatswert.wp_heizwaerme_kwh),
            func.sum(Monatswert.wp_warmwasser_kwh),
            func.sum(Monatswert.wp_strom_kuehlen_kwh),
        )
        .where(Monatswert.anlage_id == anlage_id)
        .where(
            (Monatswert.jahr > von_jahr)
            | ((Monatswert.jahr == von_jahr) & (Monatswert.monat >= von_monat))
        )
        .where(
            (Monatswert.jahr < bis_jahr)
            | ((Monatswert.jahr == bis_jahr) & (Monatswert.monat <= bis_monat))
        )
        # P12: der Filter steht in der QUERY, nicht hinter der Summe — sonst
        # mischte EIN Monat mit verschieden abgegrenztem Zähler und Nenner die
        # ganze Anlagenzahl.
        .where(Monatswert.wp_jaz_belastbar.isnot(False))
    )
    row = result.first()
    if not row or not row[0]:
        return None

    strom, heiz, ww, kuehl = row
    strom = strom or 0
    # Nie negativ, nie größer als der Gesamtstrom — der Client hält die
    # Invariante bereits, hier steht sie als Zusicherung gegen Altbestand.
    kuehl = min(max(kuehl or 0, 0), max(strom, 0))
    # W-14: der Nenner ist der Strom, der zu DIESER Wärme gehört.
    strom_waerme = strom - kuehl
    if strom_waerme <= 0:
        return None

    waerme_gesamt = (heiz or 0) + (ww or 0)
    if waerme_gesamt <= 0:
        return None
    return waerme_gesamt / strom_waerme


async def durchschnitts_jaz(db: AsyncSession, anlage_ids) -> tuple[float | None, int]:
    """Mittelwert der Anlagen-JAZ über eine Menge von Anlagen — **und ihre Zahl**.

    Ungewichtet: jede Anlage zählt einmal, unabhängig von ihrer Größe. Das ist
    die bestehende Bedeutung des Vergleichswerts und wird hier bewusst nicht
    geändert; es stand nur nie an einer Stelle, dass es so ist.

    ⭐ **Warum die Anzahl mitkommt.** Sie ist die Zahl der Anlagen, die
    tatsächlich einen Wert beigetragen haben — nicht die der Anlagen, die eine
    Wärmepumpe *besitzen*. Bis zum 06.09.2026 zählte ``by-region`` die zweite
    Menge und rechnete mit der ersten: „(54 Anlagen)" stand über einem Bild,
    das weniger zeigte. Wer eine Zahl neben einen Wert schreibt, schreibt die
    Zahl, aus der der Wert entstanden ist.
    """
    werte = []
    for aid in anlage_ids:
        jaz = await anlagen_jaz(db, aid)
        if jaz is not None:
            werte.append(jaz)
    if not werte:
        return None, 0
    return sum(werte) / len(werte), len(werte)
