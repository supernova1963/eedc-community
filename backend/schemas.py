"""
EEDC Community - Pydantic Schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Literal


# =============================================================================
# Eingabe-Schemas (für API-Requests)
# =============================================================================

class MonatswertInput(BaseModel):
    """Ein Monatswert für die Einreichung.

    **Bedeutung der Felder (Stand eedc S6, 2026-07-31).** Der Client rechnet den
    Payload; der Server hat die Rohdaten nie gesehen und kann nichts nachrechnen.
    Deshalb steht die Semantik hier — sie ist der Vertrag, an dem Auswertung und
    Anzeige hängen. Gegenstück: `eedc/backend/services/community_service.py`.

    Mit der eedc-Monats-Fakten-Schicht (ADR-002/P10) hat sich an dieser Struktur
    **nichts** geändert — kein Feld kam hinzu, keines fiel weg, keine Grenze hat
    sich verschoben. Was sich geändert hat, ist die *Auflösung* auf Client-Seite,
    und drei Feldgruppen tragen sie sichtbar:

    - ``ertrag_kwh`` — PV-Module **und** Balkonkraftwerk, aber **kein** sonstiger
      Erzeuger (BHKW/Mini-KWK). Das ist die Achse, aus der
      ``spez_ertrag_kwh_kwp`` gebildet wird; ein Brennstoff-Erzeuger darin würde
      jede betroffene Anlage im PV-Ranking nach oben schieben. Anlagen, die ihre
      Erzeugung als **ein** Anlagen-Aggregat statt je Modul pflegen, liefern hier
      seit S6 überhaupt erst Werte — vorher blieb ihre Monatsliste leer und der
      Submit scheiterte an ``min_length=1``.
    - ``autarkie_prozent`` / ``eigenverbrauch_prozent`` — die kanonische
      Haus-Bilanz: Bezugsgröße ist die **Erzeugung hinter dem Hauszähler**
      (also inkl. BHKW) plus Speicher-Entladung **und V2H**. Sie ist damit
      deckungsgleich mit dem, was der Anwender in eedc auf dem Bildschirm sieht,
      und **nicht** aus ``ertrag_kwh`` nachrechenbar, sobald ein weiterer
      Erzeuger hinter demselben Zähler sitzt.
    - ``speicher_ladung_kwh`` / ``speicher_entladung_kwh`` — gemessen an der
      Stelle, die zur **Kopplung** des Speichers passt: bei AC-Kopplung
      hausseitig hinter dem Batterie-Wechselrichter, bei DC-Kopplung am
      Batterie-Anschluss; **beide Werte von derselben Seite**. Ein einheitlicher
      AC-Vertrag wäre nicht erfüllbar — bei einem DC-gekoppelten Speicher gibt es
      zwischen Batterie und Hybrid-Wechselrichter keinen AC-Punkt. Folge für den
      Vergleich: der aus beiden gebildete Wirkungsgrad enthält bei AC-Kopplung
      **zwei Wandlungen**, bei DC-Kopplung keine — er ist also nur innerhalb
      derselben Kopplungsart vergleichbar. Der Server rechnet das **nicht** um;
      die Kopplung selbst wird bewusst nicht mitgeliefert (sie wäre ein weiteres
      Anlagenmerkmal in einem anonymen Datensatz). Bis zur Einführung des
      Kopplungs-Feldes in eedc (#351/N-60) nannte die Feldbeschreibung im Client
      die Messstelle nicht — ältere Datensätze können gemischte Seiten tragen.
    - ``eauto_*`` / ``wallbox_*`` — nur **privat** genutzte Fahrzeuge. Ein in
      eedc als *Dienstwagen* markiertes Auto ist von allen anlagenbezogenen
      Auswertungen ausgenommen und liefert deshalb weder km noch Ladung noch
      V2H. E-Auto und Wallbox bleiben getrennt gemeldet (sie messen denselben
      Fluss an zwei Punkten) — wer beide addiert, zählt doppelt.

    **Neu ab eedc v4.0.22 — drei Felder, die der Server NICHT selbst bilden darf**
    (eedc #387 und F-47):

    - ``soll_ertrag_kwh`` — die **PVGIS-Erwartung genau dieses Monats** in kWh,
      aus der *aktiven* Prognose der Anlage. Sie trägt, was nur der Client weiß:
      exakte Koordinaten samt Horizontprofil, je Modulgruppe eigene Ausrichtung
      und Neigung, AC-Kappung und Wechselrichtergrenze — und den
      **tagesgenau gekürzten Anschaffungsmonat**
      (``core/berechnungen/monatsfenster.py::monatsfenster_investition``). Genau
      deshalb sitzt die Rechnung im Client: ein serverseitiges PVGIS wäre eine
      zweite Konstruktionsstelle für dieselbe Größe. Anlagen ohne aktive
      PVGIS-Prognose senden ``None``.
    - ``co2_vermieden_kg`` — eedcs **einziger** CO₂-Kanon (ADR-001/DI-2:
      Eigenverbrauch × Strommix **plus Wärmepumpe und E-Mobilität**). Er ersetzt
      die serverseitige Rechnung ``Eigenverbrauch × 0,38``, die WP und E-Mob
      ganz ausließ und die Gemeinschaftssumme um gut 22 % zu niedrig auswies.
    - ``eigenverbrauch_kwh`` — der gemessene Eigenverbrauch in kWh. Der Server
      hat ihn bis dahin aus ``Erzeugung − Einspeisung`` rekonstruiert; das ist
      falsch, sobald ein weiterer Erzeuger hinter demselben Zähler sitzt oder
      der Speicher mitspielt.

    ⚠ **Alle drei sind optional und bleiben es.** Ältere Clients senden sie nicht;
    dort greifen die bisherigen Wege weiter. Eine Nachrechnung auf dem Server
    gibt es nicht — fehlt der Wert, fehlt die Aussage, sie wird nicht ersetzt.

    ⚑ **Angenommen ab jetzt, ausgewertet ab dem 01.09.2026.** Dieser Stand
    *speichert* die drei Felder nur; die Rangliste rechnet unverändert weiter wie
    bisher. Erst ein eigener Deploy am 01.09. stellt die Berechnung um — bewusst
    an *einem* Tag statt schleichend, und erst dann, wenn der Maßstab bei genug
    Anlagen angekommen ist.

    **Altbestand:** Datensätze, die vor S6 eingereicht wurden, tragen die alte
    Auflösung. Es gibt bewusst **keine** Markierung und keine Migration: der
    Submit ist ein Voll-Submit (``monate_vollstaendig``), also überschreibt jede
    Anlage ihren kompletten Verlauf beim nächsten manuellen oder automatischen
    Teilen. Bis dahin liegen zwei Rechenstände nebeneinander — betroffen sind nur
    Anlagen mit BHKW, V2H, Dienstwagen oder ohne Pro-Modul-Messung.
    """
    jahr: int = Field(..., ge=2010, le=2050)
    monat: int = Field(..., ge=1, le=12)
    ertrag_kwh: float = Field(..., ge=0)
    einspeisung_kwh: float | None = Field(None, ge=0)
    netzbezug_kwh: float | None = Field(None, ge=0)
    autarkie_prozent: float | None = Field(None, ge=0, le=100)
    eigenverbrauch_prozent: float | None = Field(None, ge=0, le=100)

    # Maßstab und Kanon-Größen (ab eedc v4.0.22) — siehe Vertrag im Docstring
    soll_ertrag_kwh: float | None = Field(None, ge=0)
    co2_vermieden_kg: float | None = Field(None, ge=0)
    eigenverbrauch_kwh: float | None = Field(None, ge=0)

    # Speicher-KPIs
    speicher_ladung_kwh: float | None = Field(None, ge=0)
    speicher_entladung_kwh: float | None = Field(None, ge=0)
    speicher_ladung_netz_kwh: float | None = Field(None, ge=0)

    # Wärmepumpe-KPIs
    wp_stromverbrauch_kwh: float | None = Field(None, ge=0)
    wp_heizwaerme_kwh: float | None = Field(None, ge=0)
    wp_warmwasser_kwh: float | None = Field(None, ge=0)
    # eedc W-14 (Client ab 2026-08-26): der Anteil von `wp_stromverbrauch_kwh`, der ins
    # **Kühlen** ging — eine **Teilmenge**, kein Summand. Er wird vom JAZ-Nenner
    # abgezogen: Kühlstrom erzeugt keine Wärme, seine Kältemenge steht in keinem
    # Zähler. Ohne ihn stand eine kühlende Anlage systematisch schlechter da als
    # eine, die nicht kühlt.
    # `None` = Altbestand oder älterer Client („unbekannt"); `0.0` = gemessen,
    # es gab keinen Kühlbetrieb. Der Unterschied ist Absicht.
    wp_strom_kuehlen_kwh: float | None = Field(None, ge=0)

    # E-Auto-KPIs
    eauto_ladung_gesamt_kwh: float | None = Field(None, ge=0)
    eauto_ladung_pv_kwh: float | None = Field(None, ge=0)
    eauto_ladung_extern_kwh: float | None = Field(None, ge=0)
    eauto_km: float | None = Field(None, ge=0)
    eauto_v2h_kwh: float | None = Field(None, ge=0)

    # Wallbox-KPIs
    wallbox_ladung_kwh: float | None = Field(None, ge=0)
    wallbox_ladung_pv_kwh: float | None = Field(None, ge=0)
    wallbox_ladevorgaenge: int | None = Field(None, ge=0)

    # Balkonkraftwerk-KPIs
    bkw_erzeugung_kwh: float | None = Field(None, ge=0)
    bkw_eigenverbrauch_kwh: float | None = Field(None, ge=0)
    bkw_speicher_ladung_kwh: float | None = Field(None, ge=0)
    bkw_speicher_entladung_kwh: float | None = Field(None, ge=0)

    # Sonstiges-KPIs
    sonstiges_verbrauch_kwh: float | None = Field(None, ge=0)

    @field_validator("ertrag_kwh")
    @classmethod
    def validate_ertrag(cls, v: float, info) -> float:
        # Max ~180 kWh/kWp/Monat ist realistisch (Sommer in DE)
        # Wir prüfen das später gegen kWp der Anlage
        if v > 50000:  # Absolute Obergrenze für sehr große Anlagen
            raise ValueError("Ertrag unrealistisch hoch")
        return v


class AnlageSubmitInput(BaseModel):
    """Eingabedaten für eine neue Anlage oder Update."""

    # Wird vom Backend generiert wenn nicht angegeben
    anlage_hash: str | None = None

    # Anlagendaten
    region: str = Field(..., min_length=2, max_length=2)  # Bundesland-Kürzel
    kwp: float = Field(..., gt=0, le=500)  # bis 500 kWp (größere Dachanlagen)
    ausrichtung: Literal["süd", "süd-ost", "süd-west", "ost", "west", "nord", "nord-ost", "nord-west", "ost-west", "gemischt", "unbekannt"] = "süd"
    neigung_grad: int = Field(..., ge=0, le=90)
    speicher_kwh: float | None = Field(None, ge=0, le=100)
    installation_jahr: int = Field(..., ge=2000, le=2050)

    # Jahres-SOLL der aktiven PVGIS-Prognose (kWh) — der Nenner der saisonalen
    # Hochrechnung (eedc #387, Weg A). Eine Zahl statt eines 12er-Arrays: die
    # Monatsform steckt bereits in `soll_ertrag_kwh` je Monatswert. `None`, wenn
    # die Anlage keine aktive Prognose hat. Wird ab dem 01.09.2026 ausgewertet.
    soll_jahr_kwh: float | None = Field(None, ge=0)

    # Ausstattung
    hat_waermepumpe: bool = False
    wp_art: Literal[
        "luft_wasser", "sole_wasser", "grundwasser", "luft_luft", "brauchwasser",
    ] | None = None
    # eedc W-14 / SOLL §4.1: Passiv gekühlte Anlagen (nur Umwälzpumpen) erreichen
    # ein Vielfaches der Effizienz aktiv gekühlter. Ihre eigene Kennzahl ist
    # korrekt — der **Vergleich** gegen aktiv gekühlte Anlagen wäre die
    # Falschaussage, deshalb nimmt der Benchmark sie aus dem JAZ-Ranking.
    kuehlung_art: Literal["keine", "aktiv", "passiv"] | None = None
    hat_eauto: bool = False
    hat_wallbox: bool = False
    hat_balkonkraftwerk: bool = False
    hat_sonstiges: bool = False

    # Komponenten-Details
    wallbox_kw: float | None = Field(None, ge=0, le=50)  # Ladeleistung in kW
    bkw_wp: float | None = Field(None, ge=0, le=2000)  # BKW Leistung in Wp
    sonstiges_bezeichnung: str | None = Field(None, max_length=100)
    # ⛔ Hier stand `wp_art` ein ZWEITES Mal, als `str | None`. In Pydantic
    # gewinnt die spätere Deklaration — der `Literal`-Constraint oben war damit
    # **wirkungslos**, jeder beliebige String bis 20 Zeichen ging durch. Entfernt
    # 2026-08-26 beim Ergänzen von `brauchwasser`; ab jetzt greift die Prüfung.

    # Monatswerte
    monatswerte: list[MonatswertInput] = Field(..., min_length=1)

    # N18-2: Client garantiert, dass `monatswerte` ALLE teilbaren Monate enthält —
    # serverseitig vorhandene Monate dieses Hashes, die im Payload fehlen, wurden
    # client-seitig entfernt und dürfen gelöscht werden (rückwirkendes Entfernen).
    # Alte Clients senden das Flag nicht → Verhalten unverändert (nur Upsert).
    monate_vollstaendig: bool = False

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        valid_regions = {
            "BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV",
            "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH",
            "AT", "CH", "IT",  # Österreich, Schweiz, Italien
            "XX",  # International / unbekannt — Fallback wenn PLZ/Land nicht auflösbar
        }
        v = v.upper()
        if v not in valid_regions:
            raise ValueError(f"Ungültige Region: {v}")
        return v

    @field_validator("monatswerte")
    @classmethod
    def validate_monatswerte(cls, v: list[MonatswertInput]) -> list[MonatswertInput]:
        # Keine Duplikate erlaubt
        seen = set()
        for mw in v:
            key = (mw.jahr, mw.monat)
            if key in seen:
                raise ValueError(f"Doppelter Monat: {mw.jahr}-{mw.monat:02d}")
            seen.add(key)
        return v


# =============================================================================
# Ausgabe-Schemas (für API-Responses)
# =============================================================================

class MonatswertOutput(BaseModel):
    """Monatswert in der Ausgabe."""
    jahr: int
    monat: int
    ertrag_kwh: float
    einspeisung_kwh: float | None
    netzbezug_kwh: float | None
    autarkie_prozent: float | None
    eigenverbrauch_prozent: float | None
    spez_ertrag_kwh_kwp: float | None = None  # Berechnet

    # Speicher-KPIs
    speicher_ladung_kwh: float | None = None
    speicher_entladung_kwh: float | None = None
    speicher_ladung_netz_kwh: float | None = None

    # Wärmepumpe-KPIs
    wp_stromverbrauch_kwh: float | None = None
    wp_heizwaerme_kwh: float | None = None
    wp_warmwasser_kwh: float | None = None

    # E-Auto-KPIs
    eauto_ladung_gesamt_kwh: float | None = None
    eauto_ladung_pv_kwh: float | None = None
    eauto_ladung_extern_kwh: float | None = None
    eauto_km: float | None = None
    eauto_v2h_kwh: float | None = None

    # Wallbox-KPIs
    wallbox_ladung_kwh: float | None = None
    wallbox_ladung_pv_kwh: float | None = None
    wallbox_ladevorgaenge: int | None = None

    # Balkonkraftwerk-KPIs
    bkw_erzeugung_kwh: float | None = None
    bkw_eigenverbrauch_kwh: float | None = None
    bkw_speicher_ladung_kwh: float | None = None
    bkw_speicher_entladung_kwh: float | None = None

    # Sonstiges-KPIs
    sonstiges_verbrauch_kwh: float | None = None


class AnlageOutput(BaseModel):
    """Anlage in der Ausgabe (ohne sensible Daten)."""
    anlage_hash: str
    region: str
    kwp: float
    ausrichtung: str
    neigung_grad: int
    speicher_kwh: float | None
    installation_jahr: int
    hat_waermepumpe: bool
    wp_art: str | None = None
    hat_eauto: bool
    hat_wallbox: bool
    hat_balkonkraftwerk: bool = False
    hat_sonstiges: bool = False
    wallbox_kw: float | None = None
    bkw_wp: float | None = None
    sonstiges_bezeichnung: str | None = None
    monatswerte: list[MonatswertOutput]

    class Config:
        from_attributes = True


class SubmitResponse(BaseModel):
    """Antwort nach erfolgreicher Einreichung."""
    success: bool
    message: str
    anlage_hash: str
    anzahl_monate: int
    # Vergleichsdaten
    benchmark: "BenchmarkData | None" = None


class BenchmarkData(BaseModel):
    """Vergleichsdaten für die eingereichte Anlage."""
    spez_ertrag_anlage: float  # kWh/kWp der Anlage (letztes Jahr)
    spez_ertrag_durchschnitt: float  # Durchschnitt aller Anlagen
    spez_ertrag_region: float  # Durchschnitt der Region
    rang_gesamt: int  # Platzierung gesamt
    anzahl_anlagen_gesamt: int
    rang_region: int  # Platzierung in Region
    anzahl_anlagen_region: int


class KPIVergleich(BaseModel):
    """Ein einzelner KPI-Vergleichswert."""
    wert: float
    community_avg: float | None = None
    rang: int | None = None
    von: int | None = None


class SpeicherBenchmark(BaseModel):
    """Benchmark-Daten für Speicher."""
    kapazitaet: KPIVergleich | None = None
    zyklen_jahr: KPIVergleich | None = None
    nutzungsgrad: KPIVergleich | None = None
    wirkungsgrad: KPIVergleich | None = None
    netz_anteil: KPIVergleich | None = None


class WaermepumpeBenchmark(BaseModel):
    """Benchmark-Daten für Wärmepumpe."""
    jaz: KPIVergleich | None = None
    jaz_typ: KPIVergleich | None = None  # JAZ-Vergleich nur mit gleicher WP-Art
    wp_art: str | None = None  # luft_wasser, sole_wasser, grundwasser, luft_luft
    stromverbrauch: KPIVergleich | None = None
    waermeerzeugung: KPIVergleich | None = None
    pv_anteil: KPIVergleich | None = None


class EAutoBenchmark(BaseModel):
    """Benchmark-Daten für E-Auto."""
    ladung_gesamt: KPIVergleich | None = None
    pv_anteil: KPIVergleich | None = None
    km: KPIVergleich | None = None
    verbrauch_100km: KPIVergleich | None = None
    v2h: KPIVergleich | None = None


class WallboxBenchmark(BaseModel):
    """Benchmark-Daten für Wallbox."""
    ladung: KPIVergleich | None = None
    pv_anteil: KPIVergleich | None = None
    ladevorgaenge: KPIVergleich | None = None


class BKWBenchmark(BaseModel):
    """Benchmark-Daten für Balkonkraftwerk."""
    erzeugung: KPIVergleich | None = None
    spez_ertrag: KPIVergleich | None = None
    eigenverbrauch: KPIVergleich | None = None


class PVBenchmark(BaseModel):
    """Benchmark-Daten für PV-Anlage."""
    spez_ertrag: KPIVergleich
    eigenverbrauch: KPIVergleich | None = None
    autarkie: KPIVergleich | None = None


class ErweiterteBenchmarkData(BaseModel):
    """Erweiterte Benchmark-Daten mit allen Komponenten."""
    pv: PVBenchmark
    speicher: SpeicherBenchmark | None = None
    waermepumpe: WaermepumpeBenchmark | None = None
    eauto: EAutoBenchmark | None = None
    wallbox: WallboxBenchmark | None = None
    balkonkraftwerk: BKWBenchmark | None = None


class DeleteResponse(BaseModel):
    """Antwort nach erfolgreicher Löschung."""
    success: bool
    message: str
    anzahl_geloeschte_monate: int


# =============================================================================
# Statistik-Schemas
# =============================================================================

class RegionStatistik(BaseModel):
    """Statistik für eine Region."""
    region: str
    anzahl_anlagen: int
    durchschnitt_kwp: float
    durchschnitt_spez_ertrag: float
    durchschnitt_autarkie: float | None
    anteil_mit_speicher: float
    anteil_mit_waermepumpe: float
    anteil_mit_eauto: float
    anteil_mit_wallbox: float = 0
    anteil_mit_balkonkraftwerk: float = 0
    # Performance-Durchschnitte (nur Anlagen mit dem jeweiligen Gerät)
    avg_speicher_ladung_kwh: float | None = None       # Ø Ladung pro Monat
    avg_speicher_entladung_kwh: float | None = None    # Ø Entladung pro Monat
    avg_wp_jaz: float | None = None                    # Ø berechnete JAZ (Σ Wärme / Σ Strom)
    avg_eauto_km: float | None = None                  # Ø km pro Monat
    avg_eauto_ladung_kwh: float | None = None          # Ø kWh zuhause geladen (gesamt − extern)
    avg_wallbox_kwh: float | None = None               # Ø kWh geladen pro Monat
    avg_wallbox_pv_anteil: float | None = None         # Ø PV-Anteil in % (nur wo messbar)
    avg_bkw_kwh: float | None = None                   # Ø BKW-Ertrag pro Monat


class MonatsStatistik(BaseModel):
    """Aggregierte Statistik für einen Monat."""
    jahr: int
    monat: int
    anzahl_anlagen: int
    durchschnitt_ertrag_kwh: float
    durchschnitt_spez_ertrag: float
    median_spez_ertrag: float
    min_spez_ertrag: float
    max_spez_ertrag: float


class SpeicherStatistik(BaseModel):
    """Speicher-Kennzahlen über die Anlagen mit `speicher_kwh > 0`.

    Mehrere KPIs nebeneinander, damit der reine Mittelwert nicht als
    "Ø über alle Anlagen" missverstanden wird (siehe Rainer-PN 2026-05-18).
    """
    anzahl_anlagen_mit_speicher: int
    durchschnitt_kwh: float | None
    median_kwh: float | None
    p25_kwh: float | None
    p75_kwh: float | None
    durchschnitt_kwh_pro_kwp: float | None


class GesamtStatistik(BaseModel):
    """Gesamtübersicht aller Daten."""
    anzahl_anlagen: int
    anzahl_monatswerte: int
    durchschnitt_kwp: float
    durchschnitt_speicher_kwh: float | None  # bestehend, = SpeicherStatistik.durchschnitt_kwh
    speicher_stats: SpeicherStatistik | None = None  # Median + IQR + kWh/kWp-Anker
    durchschnitt_spez_ertrag_jahr: float
    regionen: list[RegionStatistik]
    letzte_monate: list[MonatsStatistik]


# =============================================================================
# Erweiterte Statistik-Schemas (für eedc-homeassistant Community Feature)
# =============================================================================

class AusstattungsQuoten(BaseModel):
    """Prozentuale Ausstattungsquoten der Community."""
    speicher: float  # % mit Speicher
    waermepumpe: float  # % mit Wärmepumpe
    eauto: float  # % mit E-Auto
    wallbox: float  # % mit Wallbox
    balkonkraftwerk: float  # % mit BKW


class TypischeAnlage(BaseModel):
    """Die "typische" Community-Anlage (Median/Durchschnitt)."""
    kwp: float
    ausrichtung: str
    neigung_grad: int
    speicher_kwh: float | None


class GlobaleStatistik(BaseModel):
    """Erweiterte globale Community-Statistiken."""
    anzahl_anlagen: int
    anzahl_regionen: int
    durchschnitt: dict  # kwp, spez_ertrag, speicher_kwh, autarkie_prozent, eigenverbrauch_prozent
    ausstattungsquoten: AusstattungsQuoten
    typische_anlage: TypischeAnlage
    stand: str  # ISO Timestamp


class MonatsDurchschnitt(BaseModel):
    """Monatlicher Community-Durchschnitt."""
    jahr: int
    monat: int
    spez_ertrag_avg: float
    anzahl_anlagen: int


class MonatlicheDurchschnitte(BaseModel):
    """Monatliche Durchschnitte für Zeitraum."""
    monate: list[MonatsDurchschnitt]


class VerteilungsBin(BaseModel):
    """Ein Bin in der Verteilung."""
    von: float
    bis: float
    anzahl: int


class VerteilungsStatistik(BaseModel):
    """Statistische Kennzahlen einer Verteilung."""
    min: float
    max: float
    median: float
    durchschnitt: float
    stdabweichung: float


class Verteilung(BaseModel):
    """Verteilungsdaten für Histogramme."""
    metric: str
    einheit: str
    bins: list[VerteilungsBin]
    statistik: VerteilungsStatistik


class RankingEintrag(BaseModel):
    """Ein Eintrag in der Rangliste (anonym)."""
    rang: int
    wert: float
    region: str
    kwp: float


class Ranking(BaseModel):
    """Top-N Rangliste."""
    category: str
    label: str
    einheit: str
    zeitraum: str
    ranking: list[RankingEintrag]
    eigener_rang: int | None = None
    eigener_wert: float | None = None


# =============================================================================
# Trend-Schemas (Phase 4)
# =============================================================================

class TrendPunkt(BaseModel):
    """Ein Datenpunkt in einer Trend-Zeitreihe."""
    monat: str  # Format: "YYYY-MM"
    wert: float


class TrendDaten(BaseModel):
    """Zeitliche Entwicklung der Community-Daten."""
    period: str  # "12_monate", "24_monate", "gesamt"
    trends: dict[str, list[TrendPunkt]]


class AlterErtrag(BaseModel):
    """Spezifischer Ertrag nach Anlagenalter."""
    alter_jahre: int
    anzahl: int
    durchschnitt_spez_ertrag: float


class DegradationsAnalyse(BaseModel):
    """Ertrags-Analyse nach Anlagenalter."""
    nach_alter: list[AlterErtrag]
    durchschnittliche_degradation_prozent_jahr: float


# =============================================================================
# Gesamtwerte-Schemas (Community Impact)
# =============================================================================

class MonatsSumme(BaseModel):
    """Monatliche Summe über alle Anlagen."""
    jahr: int
    monat: int
    pv_erzeugung_kwh: float
    eigenverbrauch_kwh: float
    einspeisung_kwh: float
    anzahl_anlagen: int


class CommunityGesamtwerte(BaseModel):
    """Aufsummierte Gesamtwerte aller Community-Anlagen."""
    # Meta
    anzahl_anlagen: int
    anzahl_monate_total: int
    stand: str  # ISO Timestamp

    # Installierte Leistung
    gesamt_kwp: float
    gesamt_speicher_kwh: float

    # Energie-Gesamtwerte (kumuliert über alle Anlagen & Monate)
    pv_erzeugung_kwh: float
    pv_einspeisung_kwh: float
    pv_eigenverbrauch_kwh: float  # erzeugung - einspeisung
    netzbezug_kwh: float

    # Speicher
    speicher_anzahl: int
    speicher_ladung_kwh: float
    speicher_entladung_kwh: float

    # Wärmepumpe
    wp_anzahl: int
    wp_stromverbrauch_kwh: float
    wp_waerme_kwh: float  # heizwaerme + warmwasser

    # E-Mobilität
    eauto_anzahl: int
    wallbox_anzahl: int
    eauto_km: float
    eauto_ladung_kwh: float
    eauto_pv_kwh: float
    wallbox_ladung_kwh: float
    wallbox_pv_kwh: float

    # Balkonkraftwerke
    bkw_anzahl: int
    bkw_erzeugung_kwh: float

    # Impact
    co2_vermieden_kg: float  # eigenverbrauch × 0.38 kg/kWh

    # Monatliche Summen (letzte 12 Monate)
    monatliche_summen: list[MonatsSumme]


# =============================================================================
# Monatsvergleich-Schemas (Einzelmonat-Benchmark)
# =============================================================================

class MonatsKPI(BaseModel):
    """Community-Durchschnitt eines KPI für einen Monat."""
    durchschnitt: float
    median: float | None = None
    min: float | None = None
    max: float | None = None
    anzahl_anlagen: int


class MonatsVergleich(BaseModel):
    """Umfassender Community-Vergleich für einen Einzelmonat."""
    jahr: int
    monat: int
    anzahl_anlagen: int

    # PV-Kern-KPIs
    spez_ertrag: MonatsKPI  # kWh/kWp
    autarkie: MonatsKPI | None = None
    eigenverbrauch: MonatsKPI | None = None
    einspeisung: MonatsKPI | None = None
    netzbezug: MonatsKPI | None = None

    # Speicher
    speicher_ladung: MonatsKPI | None = None
    speicher_entladung: MonatsKPI | None = None
    speicher_wirkungsgrad: MonatsKPI | None = None  # entladung/ladung %

    # Wärmepumpe
    wp_stromverbrauch: MonatsKPI | None = None
    wp_waerme: MonatsKPI | None = None
    wp_jaz: MonatsKPI | None = None

    # E-Auto
    eauto_ladung: MonatsKPI | None = None
    eauto_pv_anteil: MonatsKPI | None = None
    eauto_km: MonatsKPI | None = None

    # Wallbox
    wallbox_ladung: MonatsKPI | None = None
    wallbox_pv_anteil: MonatsKPI | None = None

    # BKW
    bkw_erzeugung: MonatsKPI | None = None

    # Regionale Aufschlüsselung
    regionen: list["MonatsRegionVergleich"] | None = None


class MonatsRegionVergleich(BaseModel):
    """Regionale Durchschnitte für einen Monat."""
    region: str
    anzahl_anlagen: int
    spez_ertrag: float
    autarkie: float | None = None


class VerfuegbarerMonat(BaseModel):
    """Ein Monat mit Daten in der Community."""
    jahr: int
    monat: int
    anzahl_anlagen: int


class VerfuegbareMonate(BaseModel):
    """Liste aller verfügbaren Monate."""
    monate: list[VerfuegbarerMonat]
    aeltester: str | None = None  # "YYYY-MM"
    neuester: str | None = None  # "YYYY-MM"


# Forward reference auflösen
SubmitResponse.model_rebuild()
MonatsVergleich.model_rebuild()
