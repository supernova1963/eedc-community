# CLAUDE.md - Entwickler-Kontext für Claude Code

## Projektübersicht

**EEDC Community Server** - Anonymer Datensammel-Server für PV-Anlagen Vergleichsstatistiken.

**Live URL:** https://energy.raunet.eu
**GitHub:** https://github.com/supernova1963/eedc-community
**Docker Hub:** supernova1963/eedc-community:latest

## Git-Workflow (WICHTIG – gilt für alle Sessions und Rechner!)

1. **Immer auf `main` arbeiten** — keine Feature-Branches. Einzelentwickler-Projekt.
2. **`eedc` ist Source of Truth** für shared Code (backend/, frontend/). Dort zuerst ändern.
3. **Nach Push auf `eedc/main`** → sofort `subtree pull` in `eedc-homeassistant`.
4. **Versionsnummern + Release** nur wenn der User es explizit anfordert.
5. **`eedc-community`** (dieses Repo) ist unabhängig, aber bei Datenmodell-Änderungen beide Repos synchron anpassen (Schemas hier + community_service.py in eedc).
6. **Versionen synchron halten** – `eedc` und `eedc-homeassistant` bekommen immer die gleiche Versionsnummer.

### Verboten ohne explizite Aufforderung durch den User!

- **`git push`** (in ALLEN Repos) – niemals eigenständig pushen
- **Releases, Tags, Versionsnummern ändern**
- **Änderungen in anderen Repos** – nur dieses Repo bearbeiten, es sei denn der User fordert es explizit

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
│   │   ├── benchmark.py      # GET /api/benchmark/anlage/{hash}, /vergleich
│   │   ├── components.py     # GET /api/components/speicher/by-class, waermepumpe/by-region, eauto/by-usage
│   │   ├── statistics.py     # GET /api/statistics/global, monthly-averages, regional, distributions, rankings
│   │   ├── stats.py          # GET /api/stats, /regionen, /monat/{jahr}/{monat}
│   │   ├── submit.py         # POST/DELETE /api/submit
│   │   └── trends.py         # GET /api/trends/{period}, /degradation
│   ├── static/               # ← Frontend Build-Output (von vite)
│   │   ├── index.html
│   │   └── assets/
│   ├── main.py               # FastAPI Entry Point (6 Router)
│   ├── models.py             # Anlage, Monatswert, RateLimit
│   └── schemas.py            # Pydantic Input/Output
├── frontend/
│   ├── src/App.tsx           # Haupt-Komponente
│   └── vite.config.ts        # outDir: ../backend/static
└── docs/archive/             # Archivierte Planungsdokumente
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
    hat_balkonkraftwerk: bool
    hat_sonstiges: bool
    wallbox_kw: float | None
    bkw_wp: float | None
    sonstiges_bezeichnung: str | None
    update_count: int         # default: 0
```

### Monatswert
```python
class Monatswert(Base):
    id: int
    anlage_id: int            # FK → Anlage
    jahr: int
    monat: int
    # Energie-Basisdaten
    ertrag_kwh: float
    einspeisung_kwh: float | None
    netzbezug_kwh: float | None
    autarkie_prozent: float | None
    eigenverbrauch_prozent: float | None
    # Speicher-KPIs
    speicher_ladung_kwh: float | None
    speicher_entladung_kwh: float | None
    speicher_ladung_netz_kwh: float | None
    # WP-KPIs
    wp_stromverbrauch_kwh: float | None
    wp_heizwaerme_kwh: float | None
    wp_warmwasser_kwh: float | None
    wp_strom_kuehlen_kwh: float | None            # MENGE (Teilmenge des Stroms)
    wp_strom_funktionsfremd_abzug_kwh: float | None  # ENTSCHEIDUNG: soviel darf
                                                     # vom JAZ-Nenner weg.
                                                     # NULL ⇒ Fallback auf die Menge
    wp_jaz_belastbar: bool | None                 # ENTSCHEIDUNG: JAZ bildbar?
    # E-Auto-KPIs
    eauto_ladung_gesamt_kwh: float | None
    eauto_ladung_pv_kwh: float | None
    eauto_km: float | None
    eauto_v2h_kwh: float | None
    # Wallbox-KPIs
    wallbox_ladung_kwh: float | None
    wallbox_ladung_pv_kwh: float | None
    wallbox_ladevorgaenge: int | None
    # BKW-KPIs
    bkw_erzeugung_kwh: float | None
    bkw_eigenverbrauch_kwh: float | None
```

> ⚠ **Auszug** — die vollständige Liste steht in `backend/models.py`.
>
> ⭐ **Zwei Sorten Feld, und sie werden nie vermischt: MENGEN und ENTSCHEIDUNGEN.**
> Eine Menge (`wp_strom_kuehlen_kwh`, jede kWh-Zahl) ist additiv und geht in jede
> Mengen-Auswertung. Eine Entscheidung (`wp_jaz_belastbar`,
> `wp_strom_funktionsfremd_abzug_kwh`, `kuehlung_art`) beantwortet eine Frage, die
> **nur der Client** beantworten kann, weil sie an den **Geräten** hängt — die hat
> der Server nie gesehen. *Er rechnet nichts nach; er liest, was entschieden wurde.*
>
> **Bei jeder Entscheidung heißt `NULL` „älterer Client, unbekannt" — nie „nein".**
> Was dann gilt, steht im Docstring des Feldes in `backend/schemas.py`
> (`wp_jaz_belastbar`: zählt mit; `wp_strom_funktionsfremd_abzug_kwh`: Fallback auf
> die Menge). Altbestand heilt beim nächsten Voll-Submit, nicht durch ein Datum.
>
> ⛔ Wer eine Menge als Entscheidung verwendet, baut den Fehler von **WK-06b**
> nach: Der Server zog `wp_strom_kuehlen_kwh` selbst vom JAZ-Nenner ab und stand
> für dieselbe Anlage bei 4,24, wo eedc 3,79 zeigte.

## API Endpoints (19 Endpoints, 6 Router)

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/health` | GET | Health Check |
| **Submit** |||
| `/api/submit` | POST | Anlagendaten einreichen/aktualisieren |
| `/api/submit/{hash}` | DELETE | Daten löschen |
| **Stats** |||
| `/api/stats` | GET | Community-Basisstatistiken |
| `/api/stats/regionen` | GET | Alle Regionen mit Anlagenzahl |
| `/api/stats/monat/{jahr}/{monat}` | GET | Detail-Statistiken für einen Monat |
| **Benchmark** |||
| `/api/benchmark/anlage/{hash}` | GET | Personalisierter Benchmark (Query: zeitraum, jahr) |
| `/api/benchmark/vergleich` | GET | Was-wäre-wenn Vergleich (Query: kwp, region) |
| **Statistics** |||
| `/api/statistics/global` | GET | Globale Community-Kennzahlen |
| `/api/statistics/monthly-averages` | GET | Monatliche Ø-Erträge (Query: monate=12) |
| `/api/statistics/regional` | GET | Performance-Metriken pro Bundesland |
| `/api/statistics/regional/{region}` | GET | Detail-Statistiken für eine Region |
| `/api/statistics/distributions/{metric}` | GET | Verteilungshistogramm (kwp, spez_ertrag, speicher_kwh, autarkie, neigung) |
| `/api/statistics/rankings/{category}` | GET | Rankings (spez_ertrag, autarkie, speicher_effizienz, jaz, eauto_pv_anteil) |
| **Components** |||
| `/api/components/speicher/by-class` | GET | Speicher nach Kapazitätsklasse |
| `/api/components/waermepumpe/by-region` | GET | Wärmepumpen-JAZ nach Region |
| `/api/components/eauto/by-usage` | GET | E-Auto nach Nutzungsintensität |
| **Trends** |||
| `/api/trends/{period}` | GET | Community-Trend (12_monate, 24_monate, gesamt) |
| `/api/trends/degradation` | GET | Degradation nach Anlagenalter |

## Frontend-Modi

1. **Community-Übersicht** (`/`)
   - Zeigt aggregierte Statistiken
   - Für Besucher ohne EEDC

2. **Personalisiertes Benchmark** (`/?anlage=HASH`)
   - Zeigt Basis-Ranking (PV-Performance)
   - Vereinfachte Ansicht für Web
   - **Detaillierte Analysen:** Im EEDC Add-on unter Auswertung → Community

## Bekannte Fallstricke

| Problem | Lösung |
|---------|--------|
| Frontend-Änderungen nicht sichtbar | `cd frontend && npm run build` ausführen |
| Container zeigt alte Version | Portainer: "Recreate" mit "Pull latest image" |
| Push rejected (workflow scope) | Workflow-Datei nicht ändern oder manuell auf GitHub |
| API-Route gibt HTML zurück | Catch-all Route wurde entfernt, sollte nicht mehr passieren |

## Verbundenes Repository: eedc-homeassistant

Dieses Projekt ist **eng gekoppelt** mit dem EEDC Add-on und wird gemeinsam entwickelt:

| Repository | Zweck | Technik |
| --- | --- | --- |
| **[eedc-homeassistant](https://github.com/supernova1963/eedc-homeassistant)** | PV-Analyse Add-on (Frontend + Backend) | FastAPI, React, SQLite |
| **eedc-community** (dieses) | Anonymer Community-Benchmark-Server | FastAPI, React, PostgreSQL |

**Lokaler Pfad eedc-homeassistant:** `/home/gernot/claude/eedc-homeassistant`

> **Beachte:** Änderungen am Datenmodell (z.B. neue Monatswert-Felder, Komponenten-KPIs)
> müssen in **beiden** Repositories synchron angepasst werden:
> Schemas in `eedc-community/backend/schemas.py` und Aufbereitung in
> `eedc-homeassistant/eedc/backend/services/community_service.py`.

### Datenfluss

Das EEDC Add-on (supernova1963/eedc-homeassistant) sendet Daten hierher:

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

**Architektur (seit v2.0.3):**
- **Web-Seite:** Vereinfachte Ansicht mit PV-Benchmark
- **EEDC Add-on:** Detaillierte Analyse mit Zeitraum-Auswahl und Komponenten-KPIs
- **Proxy-Endpoint:** EEDC ruft `/api/community/benchmark/{anlage_id}` auf,
  dieser proxied zu Community Server `/api/benchmark/anlage/{hash}`

**EEDC-Dateien:**
- `eedc/backend/services/community_service.py` - Datenaufbereitung
- `eedc/backend/api/routes/community.py` - API Routes + Benchmark-Proxy
- `eedc/frontend/src/pages/CommunityShare.tsx` - Upload UI
- `eedc/frontend/src/pages/CommunityVergleich.tsx` - Benchmark-Analyse (NEU v2.0.3)
- `eedc/frontend/src/api/community.ts` - API Client

## Feature-Verteilung

| Feature | Web (energy.raunet.eu) | EEDC Add-on |
|---------|------------------------|-------------|
| PV-Benchmark (kWh/kWp) | ✓ | ✓ |
| Zeitraum-Auswahl | - | ✓ |
| Komponenten-KPIs | - | ✓ (Speicher, WP, E-Auto) |
| Monatlicher Ertrag-Vergleich | - | ✓ (Chart) |
| Detailliertes Ranking | - | ✓ |

**Prinzip:** Die Web-Seite bietet einen schnellen Überblick, während das
EEDC Add-on umfassende Analysen ermöglicht (da dort alle Daten lokal vorliegen).

## Portainer/Docker Konfiguration

**Container:** eedc-community-api
**Image:** supernova1963/eedc-community:latest
**Port:** 8080 (intern)
**Netzwerk:** nginxproxymanager_default

**Umgebungsvariablen (in Portainer):**
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
