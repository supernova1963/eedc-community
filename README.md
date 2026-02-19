# EEDC Community Server

Anonymer Datensammel-Server für PV-Anlagen Vergleichsstatistiken.

## Features

- Anonyme Datenübertragung (nur Bundesland, keine PLZ/Adresse)
- Spezifischer Ertrag (kWh/kWp) Vergleich
- Regionale Statistiken
- Rate-Limiting und Plausibilitätsprüfung
- Dashboard mit Recharts-Visualisierungen

## API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/health` | GET | Health Check |
| `/api/submit` | POST | Anlagendaten einreichen |
| `/api/submit/{hash}` | DELETE | Eigene Daten löschen |
| `/api/stats` | GET | Aggregierte Statistiken |
| `/api/benchmark` | GET | Vergleichsdaten |

## Deployment

### Mit Docker Compose

```bash
docker compose up -d
```

### Mit Portainer

1. Stack erstellen aus Git-Repository
2. Repository URL: `https://github.com/supernova1963/eedc-community`
3. Compose-Datei: `docker-compose.portainer.yml`

### Umgebungsvariablen

```env
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/eedc_community
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=https://your-eedc-instance.local
```

## Datenschutz

- Keine persönlichen Daten werden gespeichert
- PLZ wird auf Bundesland reduziert
- Anlage-Hash ist nicht rückführbar
- Nutzer können ihre Daten jederzeit löschen

## Tech Stack

- FastAPI + SQLAlchemy (async)
- PostgreSQL
- React + Recharts (Dashboard)
- Docker + Nginx Proxy Manager

## Lizenz

MIT - Teil des EEDC Projekts
