# CLAUDE.md - Entwickler-Kontext für Claude Code

## Projektübersicht

**EEDC Community Server** - Anonymer Datensammel-Server für PV-Anlagen Vergleichsstatistiken.

**Live URL:** https://energy.raunet.eu
**GitHub:** https://github.com/supernova1963/eedc-community
**Docker Hub:** supernova1963/eedc-community:latest

## Quick Reference

### Lokale Entwicklung

```bash
# Backend
cd backend
source venv/bin/activate  # Falls venv existiert
uvicorn main:app --reload --port 8080

# Frontend (separates Terminal)
cd frontend
npm run dev  # http://localhost:5173

# Frontend bauen (für Produktion)
cd frontend
npm run build  # Baut nach ../backend/static/
```

### Deployment-Workflow

```bash
# 1. Änderungen machen
# 2. Frontend bauen (wenn geändert)
cd frontend && npm run build

# 3. Committen und Pushen
cd /home/gernot/claude/eedc-community
git add -A
git commit -m "beschreibung"
git push

# 4. GitHub Actions baut automatisch Docker-Image
# 5. In Portainer: Container "Recreate" mit "Pull latest image"
```

### Wichtige Pfade

```
/home/gernot/claude/eedc-community/
├── backend/
│   ├── api/
│   │   ├── benchmark.py      # GET /api/benchmark/anlage/{hash}
│   │   ├── stats.py          # GET /api/stats
│   │   └── submit.py         # POST/DELETE /api/submit
│   ├── static/               # ← Frontend Build-Output (von vite)
│   │   ├── index.html
│   │   └── assets/
│   ├── main.py               # FastAPI Entry Point
│   ├── models.py             # Anlage, Monatswert, RateLimit
│   └── schemas.py            # Pydantic Input/Output
├── frontend/
│   ├── src/App.tsx           # Haupt-Komponente
│   └── vite.config.ts        # outDir: ../backend/static
└── PLAN_COMMUNITY_DASHBOARD_v2.md  # Roadmap
```

## Datenmodell

### Anlage
```python
class Anlage(Base):
    id: int
    anlage_hash: str          # SHA256, unique
    region: str               # BY, NW, BW, etc. (2 Zeichen)
    kwp: float
    ausrichtung: str          # süd, ost, west, ost-west, gemischt
    neigung_grad: int
    speicher_kwh: float | None
    installation_jahr: int
    hat_waermepumpe: bool
    hat_eauto: bool
    hat_wallbox: bool
```

### Monatswert
```python
class Monatswert(Base):
    id: int
    anlage_id: int            # FK → Anlage
    jahr: int
    monat: int
    ertrag_kwh: float
    einspeisung_kwh: float | None
    netzbezug_kwh: float | None
    autarkie_prozent: float | None
    eigenverbrauch_prozent: float | None
```

## API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/health` | GET | Health Check |
| `/api/stats` | GET | Community-Statistiken |
| `/api/submit` | POST | Anlagendaten einreichen |
| `/api/submit/{hash}` | DELETE | Daten löschen |
| `/api/benchmark/anlage/{hash}` | GET | Personalisierter Benchmark |
| `/api/benchmark/vergleich` | GET | Was-wäre-wenn Vergleich |

## Frontend-Modi

1. **Community-Übersicht** (`/`)
   - Zeigt aggregierte Statistiken
   - Für Besucher ohne EEDC

2. **Personalisiertes Benchmark** (`/?anlage=HASH`)
   - Zeigt Ranking, Vergleiche, Ausstattung
   - Für EEDC-Nutzer nach dem Teilen

## Bekannte Fallstricke

| Problem | Lösung |
|---------|--------|
| Frontend-Änderungen nicht sichtbar | `cd frontend && npm run build` ausführen |
| Container zeigt alte Version | Portainer: "Recreate" mit "Pull latest image" |
| Push rejected (workflow scope) | Workflow-Datei nicht ändern oder manuell auf GitHub |
| API-Route gibt HTML zurück | Catch-all Route wurde entfernt, sollte nicht mehr passieren |

## Verbindung zu EEDC

Das EEDC Add-on (supernova1963/eedc-homeassistant) sendet Daten hierher:

```
EEDC Add-on                          Community Server
┌─────────────────┐                  ┌─────────────────┐
│ CommunityShare  │ ── POST ──────→  │ /api/submit     │
│ .tsx            │ ← Benchmark ───  │                 │
│                 │                  │                 │
│ "Benchmark      │ ── GET ───────→  │ /api/benchmark/ │
│  öffnen" Link   │                  │ anlage/{hash}   │
└─────────────────┘                  └─────────────────┘
```

**EEDC-Dateien:**
- `eedc/backend/services/community_service.py` - Datenaufbereitung
- `eedc/backend/api/routes/community.py` - API Routes
- `eedc/frontend/src/pages/CommunityShare.tsx` - UI
- `eedc/frontend/src/api/community.ts` - API Client

## Roadmap

Siehe `PLAN_COMMUNITY_DASHBOARD_v2.md`:
- Erweiterte KPIs (JAZ, PV-Anteile, Speicher-Zyklen)
- Zeitraum-Auswahl
- Historische Trends
- Alle Komponenten: PV, Speicher, WP, E-Auto, Wallbox, BKW, Sonstiges

## Portainer/Docker Konfiguration

**Container:** eedc-community-api
**Image:** supernova1963/eedc-community:latest
**Port:** 8080 (intern)
**Netzwerk:** nginxproxymanager_default

**Umgebungsvariablen (in Portainer):**
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
