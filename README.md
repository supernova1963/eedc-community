# EEDC Community Server

Anonymer Datensammel-Server für PV-Anlagen Vergleichsstatistiken.

**Live:** https://energy.raunet.eu

## Features

- Anonyme Datenübertragung (nur Bundesland, keine PLZ/Adresse)
- Spezifischer Ertrag (kWh/kWp) Vergleich
- Regionale Statistiken
- Personalisiertes Benchmark-Dashboard (mit `?anlage=HASH` Parameter)
- Rate-Limiting und Plausibilitätsprüfung
- Dashboard mit Recharts-Visualisierungen

## Projektstruktur

```
eedc-community/
├── backend/
│   ├── api/
│   │   ├── benchmark.py      # Benchmark-Vergleiche
│   │   ├── stats.py          # Community-Statistiken
│   │   └── submit.py         # Daten einreichen/löschen
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
└── PLAN_COMMUNITY_DASHBOARD_v2.md  # Roadmap für erweiterte Features
```

## API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/health` | GET | Health Check |
| `/api/submit` | POST | Anlagendaten einreichen |
| `/api/submit/{hash}` | DELETE | Eigene Daten löschen |
| `/api/stats` | GET | Aggregierte Statistiken |
| `/api/benchmark/anlage/{hash}` | GET | Personalisierter Benchmark |
| `/api/benchmark/vergleich` | GET | Vergleichsdaten ohne Speicherung |

## Entwicklung

### Voraussetzungen
- Python 3.11+
- Node.js 18+
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
- Community Highlights (Speicher, WP, E-Auto Anteile)
- Regionen-Ranking
- Monatsübersicht

### 2. Personalisiertes Benchmark (mit Parameter)
URL: `https://energy.raunet.eu/?anlage=HASH`

Zeigt:
- Ranking (Deutschland + Region)
- Eigener Ertrag vs. Community-Durchschnitt
- Ausstattungsvergleich
- Vergleichschart über Zeit

## Datenschutz

- Keine persönlichen Daten werden gespeichert
- PLZ wird auf Bundesland reduziert
- Anlage-Hash ist nicht rückführbar
- Nutzer können ihre Daten jederzeit löschen

## Tech Stack

- FastAPI + SQLAlchemy (async)
- PostgreSQL
- React + Vite + TypeScript
- Recharts (Visualisierungen)
- Tailwind CSS
- Docker + GitHub Actions + Docker Hub

## Roadmap

Siehe `PLAN_COMMUNITY_DASHBOARD_v2.md` für geplante Erweiterungen:
- Erweiterte KPIs (JAZ, PV-Anteile, Speicher-Zyklen)
- Zeitraum-Auswahl (letzte 12 Monate, Jahr, seit Installation)
- Historische Trends
- Komponenten-spezifische Benchmarks (WP, E-Auto, Wallbox, BKW)

## Lizenz

MIT - Teil des EEDC Projekts
