"""
EEDC Community Server

Anonyme Aggregation von PV-Anlagendaten für Community-Statistiken.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from core import settings, init_db
from api import submit_router, stats_router, benchmark_router, statistics_router, components_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown Events."""
    # Startup: Datenbank initialisieren
    await init_db()
    print("✓ Datenbank initialisiert")
    yield
    # Shutdown
    print("Server wird beendet...")


app = FastAPI(
    title="EEDC Community",
    description="Anonyme PV-Anlagen-Statistiken für die Community",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS für Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API-Router einbinden
app.include_router(submit_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(benchmark_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")
app.include_router(components_router, prefix="/api")


# Health-Check
@app.get("/api/health")
async def health():
    """Health-Check Endpoint."""
    return {"status": "ok", "version": "0.1.0"}


# Statische Dateien (Frontend)
static_path = Path(__file__).parent / "static"
assets_path = static_path / "assets"
index_path = static_path / "index.html"

# Frontend nur einbinden wenn assets UND index.html existieren
if assets_path.exists() and index_path.exists():
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/")
    async def serve_frontend():
        """Liefert das Frontend."""
        return FileResponse(index_path)

    @app.get("/favicon.svg")
    async def serve_favicon():
        """Liefert das Favicon."""
        return FileResponse(static_path / "favicon.svg")
else:
    @app.get("/")
    async def redirect_to_docs():
        """Redirect zur API-Dokumentation wenn kein Frontend vorhanden."""
        return RedirectResponse(url="/docs")
