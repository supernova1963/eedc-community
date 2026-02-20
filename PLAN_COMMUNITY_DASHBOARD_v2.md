# Plan: Community-Dashboard v2 - Das Highlight

## Grundprinzipien

1. **Alle KPIs anzeigen** - So viele wie möglich, da andere Apps das nicht bieten
2. **Historische Trends** - Sowohl persönlich als auch Community-weit
3. **Zeitraum flexibel** - Letzte 12 Monate, Jahr, seit Installation, Custom
4. **Alle Komponenten gleichwertig** - PV, Speicher, WP, E-Auto, Wallbox, BKW, Sonstiges
5. **Datenschutz beachten** - Anonyme Aggregation, keine Einzeldaten identifizierbar

---

## Komponenten-KPIs (Vollständige Liste)

### ☀️ PV-Anlage
| KPI | Einheit | Beschreibung |
|-----|---------|--------------|
| Spezifischer Ertrag | kWh/kWp | Jahresertrag pro installierter Leistung |
| Eigenverbrauchsquote | % | Anteil selbst genutzter PV-Erzeugung |
| Autarkiegrad | % | Anteil Eigenstrom am Gesamtverbrauch |
| Performance Ratio | % | Ist vs. PVGIS-Prognose |
| Degradation | %/Jahr | Jährlicher Leistungsverlust (Trend) |

### 🔋 Speicher
| KPI | Einheit | Beschreibung |
|-----|---------|--------------|
| Kapazität | kWh | Nutzbare Speicherkapazität |
| Vollzyklen/Jahr | Anzahl | Äquivalente Vollzyklen |
| Nutzungsgrad | % | Entladung / (Kapazität × Tage) |
| Wirkungsgrad | % | Entladung / Ladung |
| Netz-Ladeanteil | % | Anteil Netzstrom bei Ladung |
| Eingesparter Netzbezug | kWh | Durch Speicher vermiedener Bezug |

### 🌡️ Wärmepumpe
| KPI | Einheit | Beschreibung |
|-----|---------|--------------|
| JAZ (Jahresarbeitszahl) | - | Wärme / Stromverbrauch |
| Stromverbrauch | kWh | Jährlicher WP-Stromverbrauch |
| Wärmeerzeugung | kWh | Erzeugte Heiz- + Warmwasserwärme |
| PV-Anteil Strom | % | Anteil PV am WP-Stromverbrauch |
| Heizwärme | kWh | Nur Heizung |
| Warmwasser | kWh | Nur Warmwasser |

### 🚗 E-Auto
| KPI | Einheit | Beschreibung |
|-----|---------|--------------|
| Ladung gesamt | kWh | Gesamte Lademenge |
| PV-Ladeanteil | % | Anteil PV-Strom an Ladung |
| Ladung zu Hause | kWh | Nur Heimladung |
| Ladung extern | kWh | Öffentlich/Arbeit |
| km gefahren | km | Jahreskilometer |
| Verbrauch | kWh/100km | Effizienz |
| V2H Entladung | kWh | Rückspeisung ins Haus |

### 🔌 Wallbox
| KPI | Einheit | Beschreibung |
|-----|---------|--------------|
| Ladung gesamt | kWh | Gesamte Lademenge über Wallbox |
| PV-Ladeanteil | % | Anteil PV-Strom |
| Ladevorgänge | Anzahl | Anzahl Ladevorgänge |
| Ø Lademenge | kWh | Durchschnitt pro Ladevorgang |

### 🏠 Balkonkraftwerk
| KPI | Einheit | Beschreibung |
|-----|---------|--------------|
| Erzeugung | kWh | Jahreserzeugung |
| Spezifischer Ertrag | kWh/kWp | Pro installierter Leistung |
| Eigenverbrauch | kWh | Selbst genutzter Anteil |
| Speicher-Ladung | kWh | Falls BKW-Speicher vorhanden |
| Speicher-Entladung | kWh | Falls BKW-Speicher vorhanden |

### 📦 Sonstiges (Heizstab, Klimaanlage, etc.)
| KPI | Einheit | Beschreibung |
|-----|---------|--------------|
| Stromverbrauch | kWh | Verbrauch der Komponente |
| PV-Anteil | % | Anteil PV-Strom |

---

## E-Auto vs. Wallbox - Unterscheidung

**Problem:** 2× "PV-Ladeanteil" ist verwirrend

**Lösung:**
- **E-Auto** = Fahrzeug-zentriert (inkl. externe Ladung, km, Verbrauch)
- **Wallbox** = Ladeinfrastruktur-zentriert (nur was durch die Wallbox geht)

Ein Haushalt kann:
- E-Auto OHNE Wallbox haben (nur extern laden)
- Wallbox OHNE E-Auto haben (für Besucher/Firmenwagen)
- Beides haben (Normalfall)

**Anzeige:**
```
🚗 E-AUTO
├── Gesamt geladen: 2.400 kWh (davon 68% PV)
├── Zu Hause: 1.800 kWh | Extern: 600 kWh
├── Gefahren: 15.000 km | Verbrauch: 16 kWh/100km
└── V2H Rückspeisung: 120 kWh

🔌 WALLBOX
├── Ladung: 1.800 kWh (davon 72% PV)
├── Ladevorgänge: 156 | Ø 11,5 kWh
└── Ladeleistung: 11 kW
```

---

## Datenstruktur Community-Server

### Erweiterte Monatswert-Felder

```python
class Monatswert(Base):
    # Basis (bereits vorhanden)
    ertrag_kwh: float
    einspeisung_kwh: float | None
    netzbezug_kwh: float | None
    autarkie_prozent: float | None
    eigenverbrauch_prozent: float | None

    # NEU: Speicher
    speicher_ladung_kwh: float | None
    speicher_entladung_kwh: float | None
    speicher_ladung_netz_kwh: float | None  # Anteil Netzstrom

    # NEU: Wärmepumpe
    wp_stromverbrauch_kwh: float | None
    wp_heizwaerme_kwh: float | None
    wp_warmwasser_kwh: float | None

    # NEU: E-Auto
    eauto_ladung_gesamt_kwh: float | None
    eauto_ladung_pv_kwh: float | None
    eauto_ladung_extern_kwh: float | None
    eauto_km: float | None
    eauto_v2h_kwh: float | None

    # NEU: Wallbox
    wallbox_ladung_kwh: float | None
    wallbox_ladung_pv_kwh: float | None
    wallbox_ladevorgaenge: int | None

    # NEU: Balkonkraftwerk
    bkw_erzeugung_kwh: float | None
    bkw_eigenverbrauch_kwh: float | None
    bkw_speicher_ladung_kwh: float | None
    bkw_speicher_entladung_kwh: float | None

    # NEU: Sonstiges
    sonstiges_verbrauch_kwh: float | None
```

### Erweiterte Anlage-Felder

```python
class Anlage(Base):
    # Basis (bereits vorhanden)
    kwp: float
    speicher_kwh: float | None
    hat_waermepumpe: bool
    hat_eauto: bool
    hat_wallbox: bool

    # NEU: Details
    wallbox_kw: float | None  # Ladeleistung
    hat_balkonkraftwerk: bool
    bkw_wp: float | None  # Leistung in Wp
    hat_sonstiges: bool
    sonstiges_bezeichnung: str | None  # z.B. "Heizstab, Klimaanlage"
```

---

## API-Endpoints

### Persönliches Dashboard
```
GET /api/benchmark/anlage/{hash}
```
Response:
```json
{
  "anlage": { ... },
  "benchmark": {
    "pv": {
      "spez_ertrag": { "wert": 1023, "community_avg": 945, "rang": 3, "von": 47 },
      "eigenverbrauch": { "wert": 42, "community_avg": 38 },
      "autarkie": { "wert": 68, "community_avg": 52 },
      "trend_12m": { "spez_ertrag": +2.1, "eigenverbrauch": -1.5 }
    },
    "speicher": {
      "kapazitaet": { "wert": 10.2, "community_avg": 12.7 },
      "zyklen_jahr": { "wert": 285, "community_avg": 310 },
      "nutzungsgrad": { "wert": 78, "community_avg": 72 },
      "wirkungsgrad": { "wert": 92, "community_avg": 89 }
    },
    "waermepumpe": {
      "jaz": { "wert": 4.2, "community_avg": 3.8, "rang": 5, "von": 23 },
      "stromverbrauch": { "wert": 4500 },
      "waermeerzeugung": { "wert": 18900 },
      "pv_anteil": { "wert": 42, "community_avg": 35 }
    },
    "eauto": {
      "ladung_gesamt": { "wert": 2400 },
      "pv_anteil": { "wert": 68, "community_avg": 52 },
      "km": { "wert": 15000 },
      "verbrauch_100km": { "wert": 16, "community_avg": 18 }
    },
    "wallbox": {
      "ladung": { "wert": 1800 },
      "pv_anteil": { "wert": 72, "community_avg": 58 },
      "ladevorgaenge": { "wert": 156 }
    },
    "balkonkraftwerk": {
      "erzeugung": { "wert": 650 },
      "spez_ertrag": { "wert": 812, "community_avg": 780 }
    }
  },
  "zeitraum": "letzte_12_monate"
}
```

### Community-Übersicht (anonym)
```
GET /api/stats/extended
```
Response:
```json
{
  "anlagen": 47,
  "zeitraum": "letzte_12_monate",
  "pv": {
    "avg_spez_ertrag": 945,
    "min": 720, "max": 1180,
    "trend_jahr": +3.2
  },
  "speicher": {
    "verbreitung_prozent": 78,
    "avg_kapazitaet": 12.7,
    "avg_zyklen": 310,
    "avg_wirkungsgrad": 89
  },
  "waermepumpe": {
    "verbreitung_prozent": 45,
    "avg_jaz": 3.8,
    "top_jaz": 4.8,
    "trend_jaz_jahr": +0.3
  },
  "eauto": {
    "verbreitung_prozent": 72,
    "avg_pv_anteil": 52,
    "top_pv_anteil": 89,
    "avg_verbrauch_100km": 18
  },
  "wallbox": {
    "verbreitung_prozent": 68,
    "avg_pv_anteil": 58
  },
  "balkonkraftwerk": {
    "verbreitung_prozent": 12,
    "avg_spez_ertrag": 780
  },
  "top_performer": {
    "pv": { "region": "BW", "wert": 1180 },
    "jaz": { "region": "BY", "wert": 4.8 },
    "eauto_pv": { "region": "NW", "wert": 89 }
  },
  "regionen": [ ... ]
}
```

### Zeitraum-Parameter
```
GET /api/benchmark/anlage/{hash}?zeitraum=letzte_12_monate
GET /api/benchmark/anlage/{hash}?zeitraum=jahr_2025
GET /api/benchmark/anlage/{hash}?zeitraum=seit_installation
GET /api/benchmark/anlage/{hash}?zeitraum=custom&von=2024-01&bis=2025-06
```

---

## Frontend-Layout

### Persönliches Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│ EEDC Community - Dein PV-Anlagen Benchmark                         │
│ 12.3 kWp | NRW | seit 2022                                         │
├─────────────────────────────────────────────────────────────────────┤
│ Zeitraum: [Letzte 12 Monate ▼]                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🏆 DEIN RANKING                                                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────────────────────────┐ │
│  │ #3      │  │ #1      │  │ 1.023 kWh/kWp                       │ │
│  │ von 47  │  │ von 8   │  │ ▲ +8% vs. Ø Community               │ │
│  │ DE      │  │ NRW     │  │ Dein Jahresertrag                   │ │
│  └─────────┘  └─────────┘  └─────────────────────────────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ☀️ PV-ANLAGE                                                       │
│  ┌───────────────┬───────────────┬───────────────┬───────────────┐ │
│  │ Spez. Ertrag  │ Eigenverbr.   │ Autarkie      │ Performance   │ │
│  │ 1.023 kWh/kWp │ 42%           │ 68%           │ 98%           │ │
│  │ Ø 945 ▲+8%    │ Ø 38% ▲+4%    │ Ø 52% ▲+16%   │ Ø 95% ▲+3%    │ │
│  └───────────────┴───────────────┴───────────────┴───────────────┘ │
│  📈 Trend: Ertrag +2.1% | Eigenverbr. -1.5%                        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔋 SPEICHER (10.2 kWh)                                             │
│  ┌───────────────┬───────────────┬───────────────┬───────────────┐ │
│  │ Vollzyklen    │ Nutzungsgrad  │ Wirkungsgrad  │ Netz-Anteil   │ │
│  │ 285/Jahr      │ 78%           │ 92%           │ 12%           │ │
│  │ Ø 310 ▼-8%    │ Ø 72% ▲+6%    │ Ø 89% ▲+3%    │ Ø 18% ▲besser │ │
│  └───────────────┴───────────────┴───────────────┴───────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🌡️ WÄRMEPUMPE                                        🏆 #5 von 23  │
│  ┌───────────────┬───────────────┬───────────────┬───────────────┐ │
│  │ JAZ           │ Stromverbr.   │ Wärme         │ PV-Anteil     │ │
│  │ 4.2           │ 4.500 kWh     │ 18.900 kWh    │ 42%           │ │
│  │ Ø 3.8 ▲+11%   │               │               │ Ø 35% ▲+7%    │ │
│  └───────────────┴───────────────┴───────────────┴───────────────┘ │
│  📈 Trend: JAZ +0.2 seit letztem Jahr                               │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🚗 E-AUTO                                                          │
│  ┌───────────────┬───────────────┬───────────────┬───────────────┐ │
│  │ PV-Ladeanteil │ Geladen       │ Gefahren      │ Verbrauch     │ │
│  │ 68%           │ 2.400 kWh     │ 15.000 km     │ 16 kWh/100km  │ │
│  │ Ø 52% ▲+16%   │ (Haus: 1.800) │               │ Ø 18 ▲besser  │ │
│  └───────────────┴───────────────┴───────────────┴───────────────┘ │
│  V2H Rückspeisung: 120 kWh                                          │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔌 WALLBOX (11 kW)                                                 │
│  ┌───────────────┬───────────────┬───────────────┐                 │
│  │ PV-Ladeanteil │ Ladung        │ Ladevorgänge  │                 │
│  │ 72%           │ 1.800 kWh     │ 156           │                 │
│  │ Ø 58% ▲+14%   │               │ Ø 11,5 kWh    │                 │
│  └───────────────┴───────────────┴───────────────┘                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🏠 BALKONKRAFTWERK (800 Wp)                                        │
│  ┌───────────────┬───────────────┬───────────────┐                 │
│  │ Erzeugung     │ Spez. Ertrag  │ Eigenverbr.   │                 │
│  │ 650 kWh       │ 812 kWh/kWp   │ 620 kWh (95%) │                 │
│  │               │ Ø 780 ▲+4%    │               │                 │
│  └───────────────┴───────────────┴───────────────┘                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📊 DEIN ERTRAG VS. COMMUNITY                                       │
│  [Chart: Linie eigene Anlage vs. Community-Durchschnitt]           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Community-Übersicht (ohne Anmeldung)

```
┌─────────────────────────────────────────────────────────────────────┐
│ EEDC Community                                                      │
│ 47 PV-Anlagen teilen ihre Daten                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Zeitraum: [Letzte 12 Monate ▼]                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🏆 TOP-PERFORMER (anonym)                                          │
│  ┌───────────────┬───────────────┬───────────────┐                 │
│  │ Bester Ertrag │ Beste JAZ     │ Höchster PV-  │                 │
│  │ 1.180 kWh/kWp │ 4.8           │ Anteil E-Auto │                 │
│  │ (BW, Süd 35°) │ (BY, LWWP)    │ 89% (NW)      │                 │
│  └───────────────┴───────────────┴───────────────┘                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📈 TRENDS (Vergleich zum Vorjahr)                                  │
│  ┌───────────────┬───────────────┬───────────────┬───────────────┐ │
│  │ Ø JAZ         │ Ø Speicher    │ E-Auto Quote  │ WP Quote      │ │
│  │ 3.8 ▲+8%      │ 12.7 kWh ▲+20%│ 72% ▲+12%     │ 45% ▲+15%     │ │
│  │ (war 3.5)     │ (war 10.6)    │ (war 60%)     │ (war 30%)     │ │
│  └───────────────┴───────────────┴───────────────┴───────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ☀️ PV-ANLAGEN STATISTIK                                            │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ Ø Ertrag: 945 kWh/kWp | Min: 720 | Max: 1.180                  ││
│  │ Ø Größe: 14.2 kWp | Ø Eigenverbrauch: 38% | Ø Autarkie: 52%   ││
│  │ [Histogramm: Verteilung der spez. Erträge]                     ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔋 SPEICHER        │  🌡️ WÄRMEPUMPE     │  🚗 E-AUTO              │
│  78% haben einen    │  45% haben eine    │  72% haben eins        │
│  Ø 12.7 kWh         │  Ø JAZ: 3.8        │  Ø PV-Anteil: 52%      │
│  Ø 310 Zyklen/Jahr  │  Top JAZ: 4.8      │  Top: 89%              │
│  Ø Wirkungsgrad: 89%│                    │  Ø 18 kWh/100km        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🗺️ REGIONEN-VERGLEICH                                              │
│  #1 BW: 1.050 kWh/kWp | #2 BY: 1.020 | #3 RP: 980 | ...           │
│  [Karte oder Balkendiagramm]                                        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔍 FILTER                                                          │
│  Region: [Alle ▼]  Größe: [Alle ▼]  Mit Speicher: [x]  Mit WP: [ ] │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  💡 MITMACHEN                                                       │
│  Vergleiche deine Anlage mit der Community!                         │
│  [EEDC Add-on installieren]                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementierungs-Schritte

### Phase 1: Backend Datenmodell (Community-Server)
1. models.py erweitern (neue Felder)
2. Migration erstellen
3. schemas.py anpassen

### Phase 2: EEDC Daten-Extraktion
1. community_service.py erweitern
2. Daten aus InvestitionMonatsdaten.verbrauch_daten extrahieren
3. KPIs berechnen (JAZ, PV-Anteile, etc.)

### Phase 3: Backend APIs
1. /api/stats/extended - Erweiterte Community-Statistik
2. /api/benchmark/anlage/{hash} - Erweiterte Benchmark-Daten
3. Zeitraum-Parameter implementieren
4. Trend-Berechnungen

### Phase 4: Frontend Persönlich
1. Komponenten-Karten mit allen KPIs
2. Zeitraum-Auswahl
3. Trend-Anzeigen
4. Vergleichs-Charts

### Phase 5: Frontend Community
1. Top-Performer Anzeige
2. Trends über Zeit
3. Interaktive Filter
4. Histogramme/Verteilungen

---

## Offene Fragen

1. **Welche Daten hat EEDC bereits?**
   - Prüfen: InvestitionMonatsdaten.verbrauch_daten Struktur
   - Was fehlt komplett?

2. **Datenschutz bei Top-Performern:**
   - Nur Region + Wert zeigen?
   - Oder auch Ausrichtung/Neigung?

3. **Performance:**
   - Bei vielen Anlagen: Caching?
   - Trend-Berechnung vorberechnen?
