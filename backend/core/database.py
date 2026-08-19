"""
EEDC Community - Datenbank-Konfiguration
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

engine = create_async_engine(settings.database_url, echo=False)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency für FastAPI - gibt eine DB-Session zurück."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Erstellt alle Tabellen und führt Migrationen aus."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await run_migrations(conn)


async def run_migrations(conn):
    """Führt Schema-Migrationen durch (neue Spalten zu bestehenden Tabellen)."""
    from sqlalchemy import text, inspect

    def _run(connection):
        inspector = inspect(connection)
        if "anlagen" in inspector.get_table_names():
            existing = {col["name"] for col in inspector.get_columns("anlagen")}
            # v3.5.x: Wärmepumpenart für fairen JAZ-Vergleich
            if "wp_art" not in existing:
                connection.execute(text("ALTER TABLE anlagen ADD COLUMN wp_art VARCHAR(20)"))
            # v3.30.2 (Issue #254): Rate-Limit-Fenster rollend 24h statt
            # Monatswechsel. Bestehende Anlagen starten mit NULL — beim
            # nächsten Submit beginnt ein frisches 24h-Fenster, der alte
            # Monatszähler wird ignoriert. Damit sind alle Anlagen, die am
            # Monats-Limit hingen, nach Deploy automatisch entsperrt.
            if "update_window_start" not in existing:
                connection.execute(text(
                    "ALTER TABLE anlagen ADD COLUMN update_window_start TIMESTAMP"
                ))
            # v4.0.22 (eedc #387): Jahres-SOLL der Anlage aus der Client-PVGIS-
            # Prognose. Nenner der saisonalen Hochrechnung; NULL bis der Besitzer
            # einmal mit einer aktuellen eedc-Version geteilt hat.
            if "soll_jahr_kwh" not in existing:
                connection.execute(text(
                    "ALTER TABLE anlagen ADD COLUMN soll_jahr_kwh FLOAT"
                ))
        if "monatswerte" in inspector.get_table_names():
            existing_mw = {col["name"] for col in inspector.get_columns("monatswerte")}
            # v4.0.22 (eedc #387 / F-47): Maßstab und Kanon-Größen vom Client.
            # `soll_ertrag_kwh` trägt den tagesgenau gekürzten Anschaffungsmonat
            # mit; `co2_vermieden_kg` und `eigenverbrauch_kwh` ersetzen die zwei
            # Stellen, an denen der Server bisher selbst gerechnet hat.
            for spalte in ("soll_ertrag_kwh", "co2_vermieden_kg", "eigenverbrauch_kwh"):
                if spalte not in existing_mw:
                    connection.execute(text(
                        f"ALTER TABLE monatswerte ADD COLUMN {spalte} FLOAT"
                    ))

    await conn.run_sync(_run)
