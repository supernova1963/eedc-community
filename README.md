# EEDC Community Server

Anonymer Datensammel-Server für PV-Anlagen Vergleichsstatistiken.

**Live:** https://energy.raunet.eu

## Features

- **Anonyme Datenübertragung** (nur Bundesland, keine PLZ/Adresse)
- **Spezifischer Ertrag** (kWh/kWp) Vergleich mit Min/Max/Durchschnitt
- **Regionale Statistiken** und Ranking nach Bundesland
- **Personalisiertes Benchmark** (mit `?anlage=HASH` Parameter)
- **Komponenten-Benchmarks** für Speicher, Wärmepumpe, E-Auto, Wallbox, Balkonkraftwerk
- **Performance-Metriken im Regional-Tab** (ab v2.2.0): Ø Speicher-Ladung/Entladung, Ø JAZ, Ø E-Auto km, Ø Wallbox-Ladung, Ø BKW-Ertrag pro Bundesland
- **Dark Mode** mit System-Präferenz-Erkennung
- **Rate-Limiting** und Plausibilitätsprüfung
- **Dashboard** mit Recharts-Visualisierungen

## Projektstruktur

```
eedc-community/
├── backend/
│   ├── api/
│   │   ├── benchmark.py      # Benchmark-Vergleiche
│   │   ├── components.py     # Komponenten-Benchmarks (Speicher, WP, E-Auto)
│   │   ├── statistics.py     # Erweiterte Statistiken (Global, Regional, Rankings)
│   │   ├── stats.py          # Community-Basisstatistiken
│   │   ├── submit.py         # Daten einreichen/löschen
│   │   └── trends.py         # Trend-Analysen (Zeitreihen, Degradation)
│   ├── core/
│   │   ├── config.py         # Einstellungen
│   │   └── database.py       # DB-Verbindung
│   ├── static/               # Gebautes Frontend (wird von vite build erzeugt)
│   ├── main.py               # FastAPI App
│   ├── models.py             # SQLAlchemy Modelle
│   ├── schemas.py            # Pydantic Schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Haupt-Komponente (Community + Personalisiert)
│   │   ├── main.tsx
│   │   └── index.css
│   ├── vite.config.ts        # Build nach ../backend/static
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml
└── docs/archive/                   # Archivierte Planungsdokumente
```

## API Endpoints (19 Endpoints)

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/health` | GET | Health Check |
| **Submit** |||
| `/api/submit` | POST | Anlagendaten einreichen/aktualisieren |
| `/api/submit/{hash}` | DELETE | Eigene Daten löschen |
| **Stats** |||
| `/api/stats` | GET | Aggregierte Community-Statistiken |
| `/api/stats/regionen` | GET | Alle Regionen mit Anlagenzahl |
| `/api/stats/monat/{jahr}/{monat}` | GET | Detail-Statistiken für einen Monat |
| **Benchmark** |||
| `/api/benchmark/anlage/{hash}` | GET | Personalisierter Benchmark (mit Zeitraum-Filter) |
| `/api/benchmark/vergleich` | GET | Was-wäre-wenn Vergleich ohne Speicherung |
| **Statistics** |||
| `/api/statistics/global` | GET | Globale Community-Kennzahlen |
| `/api/statistics/monthly-averages` | GET | Monatliche Ø-Erträge (Community-Trend) |
| `/api/statistics/regional` | GET | Performance-Metriken pro Bundesland/Land |
| `/api/statistics/regional/{region}` | GET | Detail-Statistiken für eine Region |
| `/api/statistics/distributions/{metric}` | GET | Verteilungshistogramm (kwp, spez_ertrag, speicher_kwh, autarkie, neigung) |
| `/api/statistics/rankings/{category}` | GET | Rankings (spez_ertrag, autarkie, speicher_effizienz, jaz, eauto_pv_anteil) |
| **Components** |||
| `/api/components/speicher/by-class` | GET | Speicher-Benchmark nach Kapazitätsklasse |
| `/api/components/waermepumpe/by-region` | GET | Wärmepumpen-Benchmark (JAZ) nach Region |
| `/api/components/eauto/by-usage` | GET | E-Auto-Benchmark nach Nutzungsintensität |
| **Trends** |||
| `/api/trends/{period}` | GET | Community-Trend (12_monate, 24_monate, gesamt) |
| `/api/trends/degradation` | GET | Degradations-Analyse (Ertrag nach Anlagenalter) |

## Entwicklung

### Voraussetzungen
- Python 3.11+
- Node.js 20+
- PostgreSQL (oder Docker)

### Backend starten (lokal)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### Frontend entwickeln
```bash
cd frontend
npm install
npm run dev    # Entwicklungsserver auf Port 5173
```

### Frontend bauen (für Produktion)
```bash
cd frontend
npm run build  # Baut nach ../backend/static/
```

**Wichtig:** Das Frontend wird nach `backend/static/` gebaut (siehe `vite.config.ts`).
Diese Dateien werden dann vom FastAPI-Server ausgeliefert.

## Deployment

### Automatisch via GitHub Actions

1. Code pushen zu `main`
2. GitHub Actions baut Docker-Image
3. Image wird zu Docker Hub gepusht: `supernova1963/eedc-community:latest`
4. In Portainer: Container "Recreate" mit "Pull latest image"

### Build-Workflow

```yaml
# .github/workflows/docker-publish.yml
# Trigger: Push auf main Branch
# 1. Checkout
# 2. Docker Buildx Setup
# 3. Docker Hub Login
# 4. Build & Push Image
```

### Mit Docker Compose (lokal)

```bash
docker compose up -d
```

### Portainer Stack

Umgebungsvariablen in Portainer setzen:
- `POSTGRES_PASSWORD`: Datenbank-Passwort
- `SECRET_KEY`: Geheimer Schlüssel für Hashing

```yaml
services:
  api:
    image: supernova1963/eedc-community:latest
    container_name: eedc-community-api
    environment:
      - DATABASE_URL=postgresql+asyncpg://eedc:${POSTGRES_PASSWORD}@db:5432/eedc_community
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
    networks:
      - nginxproxymanager_default
      - default

  db:
    image: postgres:16-alpine
    container_name: eedc-community-db
    environment:
      - POSTGRES_USER=eedc
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=eedc_community
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U eedc -d eedc_community"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

networks:
  nginxproxymanager_default:
    external: true
```

### Nginx Proxy Manager

- Forward Hostname: `eedc-community-api`
- Forward Port: `8080`
- SSL: Let's Encrypt

## Frontend-Modi

### 1. Community-Übersicht (ohne Parameter)
URL: `https://energy.raunet.eu/`

Zeigt:
- Anzahl Anlagen und Monatswerte
- Durchschnittlicher Jahresertrag
- Ausstattungs-Verteilung (Speicher, WP, E-Auto, Wallbox, BKW)
- Community-Trend (12 Monate mit Min/Max/Durchschnitt)
- Regionen-Ranking nach Jahresertrag
- Dark Mode (automatisch nach System-Präferenz oder manuell)

### 2. Personalisiertes Benchmark (mit Parameter)
URL: `https://energy.raunet.eu/?anlage=HASH`

Zeigt zusätzlich zur Community-Übersicht:
- PV-Performance Ranking (gesamt und regional)
- Eigener Ertrag vs. Community-Durchschnitt (12-Monats-Chart)
- Deine Ausstattung im Vergleich (PV, Speicher, WP, E-Auto, Wallbox, BKW)

**Detaillierte Analysen:** Die erweiterten Funktionen (Zeitraum-Auswahl, Komponenten-KPIs,
monatliche Charts) sind im EEDC Add-on unter *Auswertungen → Community* verfügbar.

## Datenschutz

- Keine persönlichen Daten werden gespeichert
- PLZ wird auf Bundesland reduziert
- Anlage-Hash ist nicht rückführbar
- Nutzer können ihre Daten jederzeit löschen

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL
- **Frontend:** React + Vite + TypeScript + Tailwind CSS
- **Charts:** Recharts (ComposedChart, LineChart, BarChart)
- **Deployment:** Docker + GitHub Actions + Docker Hub
- **UI:** Dark Mode Support, Responsive Design

## Integration mit EEDC Add-on

Das EEDC Add-on (ab v2.3.0) bietet erweiterte Community-Funktionen:

| Feature | Web (energy.raunet.eu) | EEDC Add-on |
|---------|------------------------|-------------|
| PV-Benchmark (kWh/kWp) | ✓ | ✓ |
| Regionen-Ranking | ✓ | ✓ |
| Ausstattungs-Vergleich | ✓ (5 Typen) | ✓ |
| Community-Trend Chart (Min/Max/Avg) | ✓ | ✓ |
| Dark Mode | ✓ | ✓ |
| Zeitraum-Auswahl | - | ✓ |
| Komponenten-KPIs (Speicher, WP, E-Auto, Wallbox, BKW) | - | ✓ |
| Monatlicher Ertrag-Vergleich | - | ✓ |
| Detailliertes Ranking | - | ✓ |

**Prinzip:** Die Web-Seite bietet einen schnellen Überblick, das EEDC Add-on
ermöglicht umfassende Analysen (da dort alle Daten lokal vorliegen).

### Architektur

```
EEDC Add-on                          Community Server
┌─────────────────────┐              ┌─────────────────┐
│ CommunityShare.tsx  │ ─ POST ────→ │ /api/submit     │
│                     │              │                 │
│ CommunityVergleich  │ ─ Proxy ───→ │ /api/benchmark/ │
│ .tsx (embedded)     │              │ anlage/{hash}   │
│                     │              │                 │
│ "Im Browser öffnen" │ ─ Link ────→ │ /?anlage=HASH   │
└─────────────────────┘              └─────────────────┘
```

## Lizenz

MIT - Teil des EEDC Projekts
