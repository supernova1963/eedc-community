# Plan: Community-Dashboard zum Highlight machen

## Aktuelle Probleme

1. **Ausstattungs-Vergleich inkonsistent**
   - Speicher zeigt "10.0 kWh | Ø 100% haben" - sollte "10.0 kWh | Ø 12.7 kWh" sein
   - Nur ja/nein für WP, E-Auto - keine KPIs

2. **Fehlende Komponenten**
   - Balkonkraftwerk nicht erfasst
   - Wallbox nicht erfasst
   - Sonstiges nicht erfasst

3. **Fehlende interessante KPIs**
   - Wärmepumpe: JAZ (Jahresarbeitszahl)
   - E-Auto: % PV-Strom Anteil
   - Wallbox: % PV-Strom Anteil
   - Speicher: Zyklen, Nutzungsgrad

4. **Zeitraum-Problem**
   - Nicht jeder tippt nur das letzte Jahr ein
   - Manche haben Daten ab Installation (z.B. 2020)
   - Vergleich sollte flexibler sein

---

## Phase 1: Backend - Erweiterte Datenerfassung

### 1.1 Datenmodell erweitern (models.py)

```python
class Anlage(Base):
    # Bestehende Felder...

    # NEU: Erweiterte Komponenten
    hat_balkonkraftwerk: bool
    balkonkraftwerk_wp: float | None  # Leistung in Wp

    # Wallbox Details
    wallbox_kw: float | None  # Ladeleistung

class Monatswert(Base):
    # Bestehende Felder...

    # NEU: Komponenten-KPIs
    # Speicher
    speicher_zyklen: float | None
    speicher_ladung_kwh: float | None
    speicher_entladung_kwh: float | None

    # Wärmepumpe
    wp_stromverbrauch_kwh: float | None
    wp_waerme_kwh: float | None  # Erzeugte Wärme
    wp_jaz: float | None  # Berechnete JAZ

    # E-Auto
    eauto_ladung_gesamt_kwh: float | None
    eauto_ladung_pv_kwh: float | None
    eauto_pv_anteil_prozent: float | None

    # Wallbox
    wallbox_ladung_gesamt_kwh: float | None
    wallbox_ladung_pv_kwh: float | None
    wallbox_pv_anteil_prozent: float | None

    # Balkonkraftwerk
    bkw_erzeugung_kwh: float | None
```

### 1.2 EEDC Submit-API erweitern

Die `community_service.py` muss erweitert werden, um diese Daten aus `InvestitionMonatsdaten.verbrauch_daten` zu extrahieren:

```python
# Aus InvestitionMonatsdaten.verbrauch_daten extrahieren:
# Speicher: ladung_kwh, entladung_kwh
# E-Auto: ladung_pv_kwh, ladung_netz_kwh
# WP: stromverbrauch_kwh, heizenergie_kwh, warmwasser_kwh
# Wallbox: ladung_kwh (mit PV-Anteil berechnen)
# BKW: pv_erzeugung_kwh
```

---

## Phase 2: Neue Benchmark-Metriken

### 2.1 Speicher-Benchmark
- **Ø Zyklen/Jahr**: Wie oft wird der Speicher geladen?
- **Nutzungsgrad**: Entladung / Kapazität / Tage
- **Speicher-ROI**: Eingesparter Netzbezug durch Speicher

### 2.2 Wärmepumpe-Benchmark
- **Ø JAZ Community**: Vergleich der Jahresarbeitszahl
- **Dein JAZ vs. Ø**: Bist du effizienter?
- **kWh Wärme/m²**: Wenn Wohnfläche bekannt

### 2.3 E-Auto-Benchmark
- **% PV-Ladung**: Wie viel wurde mit eigenem Strom geladen?
- **Ø km/kWh**: Effizienz (wenn km erfasst)
- **Community-Vergleich**: Dein PV-Anteil vs. Ø

### 2.4 Wallbox-Benchmark
- **PV-Anteil Ladung**: Wieviel % der Ladungen sind PV?
- **Ø Ladeleistung genutzt**: Auslastung der Wallbox

### 2.5 Balkonkraftwerk-Benchmark
- **Spez. Ertrag**: kWh/kWp wie bei großer Anlage
- **Ø Eigenverbrauch**: Wie viel wird selbst genutzt?

---

## Phase 3: Frontend - Personalisiertes Dashboard

### 3.1 Komponenten-Karten (statt einfacher Liste)

```
┌─────────────────────────────────────────────────────────────┐
│ 🔋 SPEICHER                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Kapazität: 10.2 kWh                    Ø Community: 12.7 kWh│
│                                                             │
│ Jahres-Zyklen     Nutzungsgrad      Eingesparter Netzbezug │
│    ▼ 285            ▲ 78%              ▲ 1.240 kWh         │
│  Ø 310 (-8%)      Ø 72% (+6%)         Ø 1.100 kWh (+13%)   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🌡️ WÄRMEPUMPE                                               │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Deine JAZ: 4.2                         Ø Community: 3.8     │
│ ▲ +11% effizienter als Durchschnitt                        │
│                                                             │
│ Stromverbrauch     Wärme erzeugt      PV-Anteil Strom      │
│   4.500 kWh         18.900 kWh           ▲ 42%             │
│                                         Ø 35%              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🚗 E-AUTO                                                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ PV-Ladeanteil: 68%                     Ø Community: 52%     │
│ ▲ Du lädst mehr mit Sonne als andere!                       │
│                                                             │
│ Geladen gesamt    Davon PV-Strom       Ersparnis           │
│   2.400 kWh         1.632 kWh          ~490 €/Jahr         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Zeitraum-Auswahl

```
┌──────────────────────────────────────┐
│ Vergleichszeitraum:                  │
│ ○ Letztes Jahr (2025)                │
│ ● Letzte 12 Monate                   │
│ ○ Seit Installation (2022)           │
│ ○ Benutzerdefiniert: [____] - [____] │
└──────────────────────────────────────┘
```

### 3.3 Trend-Anzeige

Nicht nur aktueller Stand, sondern auch Entwicklung:
- JAZ verbessert sich? ▲
- PV-Anteil E-Auto steigt? ▲
- Speicher-Nutzung sinkt? ▼

---

## Phase 4: Allgemeine Community-Übersicht (ohne Login)

### 4.1 Interessante Statistiken für Besucher

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 COMMUNITY INSIGHTS                                       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ 🏆 Top-Performer                                            │
│    Beste Anlage: 1.245 kWh/kWp (Bayern, Süd-Ausrichtung)   │
│    Beste JAZ: 4.8 (Luftwärmepumpe, Fußbodenheizung)        │
│    Höchster PV-Anteil E-Auto: 89%                          │
│                                                             │
│ 📈 Trends                                                   │
│    Ø JAZ steigt: 3.4 (2023) → 3.8 (2025)                   │
│    Speicher werden größer: 8 kWh (2023) → 12 kWh (2025)    │
│    E-Auto Verbreitung: 45% (2023) → 72% (2025)             │
│                                                             │
│ 🗺️ Regionen-Vergleich                                       │
│    Höchster Ertrag: Baden-Württemberg (1.050 kWh/kWp)      │
│    Meiste WP: Bayern (78% der Anlagen)                     │
│    Meiste E-Autos: NRW (82% der Anlagen)                   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Interaktive Filter

- Nach Region filtern
- Nach Anlagengröße filtern
- Nach Ausstattung filtern (nur mit Speicher, nur mit WP, etc.)

---

## Implementierungs-Reihenfolge

### Schritt 1: Backend erweitern (1-2h)
1. models.py: Neue Felder hinzufügen
2. Migration erstellen
3. schemas.py: Input/Output erweitern
4. submit.py: Erweiterte Daten akzeptieren

### Schritt 2: EEDC community_service.py (1h)
1. InvestitionMonatsdaten auslesen
2. KPIs berechnen (JAZ, PV-Anteil, etc.)
3. An Community-Server senden

### Schritt 3: Benchmark-API erweitern (1h)
1. Komponenten-spezifische Benchmarks
2. Zeitraum-Parameter
3. Trend-Berechnung

### Schritt 4: Frontend überarbeiten (2h)
1. Komponenten-Karten mit KPIs
2. Zeitraum-Auswahl
3. Verbesserte Visualisierung

### Schritt 5: Community-Übersicht (1h)
1. Top-Performer Anzeige
2. Trends über Zeit
3. Interaktive Filter

---

## Fragen zur Klärung

1. **Welche KPIs sind am wichtigsten?**
   - JAZ?
   - PV-Anteil E-Auto?
   - Speicher-Nutzung?

2. **Sollen historische Trends angezeigt werden?**
   - z.B. "Deine JAZ hat sich um 5% verbessert"

3. **Anonymitäts-Level?**
   - Sollen Top-Performer gezeigt werden (anonym)?
   - Regionale Details?

4. **Zeitraum-Flexibilität?**
   - Nur letzte 12 Monate?
   - Oder auch "seit Installation"?

5. **Priorität der Komponenten?**
   - Alle gleichwertig?
   - Oder Fokus auf PV + Speicher?
