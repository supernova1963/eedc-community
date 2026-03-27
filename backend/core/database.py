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

    await conn.run_sync(_run)
