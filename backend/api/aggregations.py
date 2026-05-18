"""
EEDC Community - Shared Aggregations-Helpers

SoT-Helper für KPI-Berechnungen, die in mehreren Routen gleichzeitig
aufgerufen werden. Verhindert Drift zwischen Endpoints, die dieselbe
Statistik aus unterschiedlichen Stellen berechnen.

Aktuell:
- compute_speicher_stats: Mittelwert + Median + IQR + kWh/kWp-Ratio
  für `Anlage.speicher_kwh > 0`. Anlass: Rainer-PN 2026-05-18 — der
  reine Mittelwert (14 kWh) wurde als "Ø über alle Anlagen" gelesen,
  obwohl er nur Speicher-Anlagen gemittelt hat. Median + Spanne + Ratio
  geben dem Leser den Plausibilitäts-Anker; der Frontend-Label macht
  die Auswahl explizit.
"""

from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Anlage


@dataclass
class SpeicherStats:
    """Kennzahlen über die Anlagen mit `speicher_kwh > 0`.

    `n_gesamt` bezieht sich auf ALLE Anlagen in der DB und dient dem
    Frontend nur als Kontext (z. B. "X von Y Anlagen haben Speicher").
    """

    avg_kwh: float | None
    median_kwh: float | None
    p25_kwh: float | None
    p75_kwh: float | None
    avg_kwh_pro_kwp: float | None
    n_mit_speicher: int
    n_gesamt: int


async def compute_speicher_stats(db: AsyncSession) -> SpeicherStats:
    """Berechnet die Speicher-KPIs in einem SQL-Roundtrip.

    Die Filterbedingung `speicher_kwh > 0` ist bewusst — Anlagen ohne
    Speicher gehören nicht in eine Speicher-Statistik. Diese Auswahl
    muss im UI klar gelabeled werden, sonst entsteht die naive Lesart
    "Ø über alle Anlagen".
    """
    n_total = (await db.execute(select(func.count(Anlage.id)))).scalar() or 0

    has_speicher = Anlage.speicher_kwh.isnot(None) & (Anlage.speicher_kwh > 0)

    stmt = select(
        func.count(Anlage.id).label("n"),
        func.avg(Anlage.speicher_kwh).label("avg"),
        func.percentile_cont(0.5).within_group(Anlage.speicher_kwh.asc()).label("median"),
        func.percentile_cont(0.25).within_group(Anlage.speicher_kwh.asc()).label("p25"),
        func.percentile_cont(0.75).within_group(Anlage.speicher_kwh.asc()).label("p75"),
        func.avg(
            case((Anlage.kwp > 0, Anlage.speicher_kwh / Anlage.kwp), else_=None)
        ).label("avg_kwh_pro_kwp"),
    ).where(has_speicher)

    row = (await db.execute(stmt)).one()

    def _f(value):
        return float(value) if value is not None else None

    return SpeicherStats(
        avg_kwh=_f(row.avg),
        median_kwh=_f(row.median),
        p25_kwh=_f(row.p25),
        p75_kwh=_f(row.p75),
        avg_kwh_pro_kwp=_f(row.avg_kwh_pro_kwp),
        n_mit_speicher=int(row.n or 0),
        n_gesamt=int(n_total),
    )
