"""Minimale Test-Umgebung für den Community-Server.

⚠ **Dieses Repo hatte bis zum 13.09.2026 keine Testsuite** — geprüft wurde per
Modul-Import und `tsc --noEmit` im Frontend. Das trägt für Syntax, nicht für
Semantik: WK-06b ändert an vier Stellen, **was** ein SQL-Ausdruck rechnet, und
genau dort ist am 06.09. schon einmal eine Stelle liegengeblieben, ohne dass es
jemandem auffiel (`benchmark.py::berechne_wp_kpis`, s. den Bericht zu N-454).

**Bewusst klein gehalten:** eine `conftest.py`, SQLite in-memory, keine
`pytest.ini` (die Tests tragen `@pytest.mark.asyncio` selbst), keine CI-Datei,
kein venv im Repo. Gefahren wird mit dem vorhandenen venv des Add-on-Repos —
es erfüllt jede Zeile der `requirements.txt` außer `asyncpg`, das für SQLite
nicht gebraucht wird:

    cd backend && DATABASE_URL="sqlite+aiosqlite:///:memory:" \\
      /home/gernot/claude/eedc-homeassistant/eedc/backend/venv/bin/python \\
      -m pytest tests -q -p no:cacheprovider

⚠ **Was SQLite nicht leistet:** Es ist nicht PostgreSQL. `coalesce`, `sum`,
`case`, `distinct` und `ALTER TABLE … ADD COLUMN` verhalten sich gleich; keiner
der geprüften Ausdrücke dividiert in SQL (die Plausibilität ist als Ungleichung
formuliert). Der echte Postgres-Lauf bleibt der Deploy.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio

# `backend/` auf den Pfad — die Module importieren flach (`from models import …`).
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# ⛔ VOR dem ersten Import von `core.database`: dort entsteht die Engine auf
# Modulebene, und die Default-URL zieht `asyncpg`.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

from core.database import Base  # noqa: E402,F401
import models  # noqa: E402,F401 — registriert die Tabellen an `Base`


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """Eine leere In-Memory-Datenbank je Test.

    `StaticPool` hält **eine** Verbindung: sonst bekäme jede Session ihre eigene
    leere `:memory:`-Datenbank.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession,
                                         expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()
