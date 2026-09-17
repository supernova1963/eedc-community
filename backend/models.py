"""
EEDC Community - Datenbank-Modelle
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Anlage(Base):
    """
    Eine anonyme PV-Anlage.
    Der Hash wird aus Anlagendaten + Secret generiert und dient als eindeutige ID.
    """
    __tablename__ = "anlagen"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Eindeutiger Hash (SHA256 aus: kwp + install_datum + plz2 + secret)
    anlage_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # Standort (anonymisiert auf Bundesland)
    region: Mapped[str] = mapped_column(String(2))  # BY, NW, BW, etc.

    # Anlagendaten
    kwp: Mapped[float] = mapped_column(Float)
    ausrichtung: Mapped[str] = mapped_column(String(20))  # süd, ost, west, ost-west, gemischt
    neigung_grad: Mapped[int] = mapped_column(Integer)
    speicher_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    installation_jahr: Mapped[int] = mapped_column(Integer)

    # Ausstattung
    hat_waermepumpe: Mapped[bool] = mapped_column(Boolean, default=False)
    # luft_wasser · sole_wasser · grundwasser · luft_luft · brauchwasser
    wp_art: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # eedc W-14/SOLL §4.1: `keine` · `aktiv` · `passiv`. Eine Markierung, keine
    # Menge — passiv gekühlte Anlagen erreichen ein Vielfaches der Effizienz
    # aktiv gekühlter, ihr JAZ-Vergleich gegen sie wäre eine Falschaussage.
    # NULL = Altbestand oder älterer Client; dann wird wie bisher verglichen.
    kuehlung_art: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hat_eauto: Mapped[bool] = mapped_column(Boolean, default=False)
    hat_wallbox: Mapped[bool] = mapped_column(Boolean, default=False)
    hat_balkonkraftwerk: Mapped[bool] = mapped_column(Boolean, default=False)
    hat_sonstiges: Mapped[bool] = mapped_column(Boolean, default=False)

    # Komponenten-Details
    wallbox_kw: Mapped[float | None] = mapped_column(Float, nullable=True)  # Ladeleistung
    bkw_wp: Mapped[float | None] = mapped_column(Float, nullable=True)  # BKW Leistung in Wp
    sonstiges_bezeichnung: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # ⛔ Hier stand `wp_art` ein ZWEITES Mal (identische Spalte, kürzerer
    # Kommentar). In SQLAlchemy gewinnt die spätere Deklaration stillschweigend —
    # die Doppelung war folgenlos, aber sie hat die Definition zerteilt. Entfernt
    # 2026-08-26 beim Ergänzen von `kuehlung_art`; die eine Deklaration steht
    # oben bei der Ausstattung, wo sie hingehört.

    # Metadaten
    # Jahres-SOLL der aktiven PVGIS-Prognose (kWh), vom Client geliefert — der
    # Nenner der saisonalen Hochrechnung (eedc #387, Weg A; SoT
    # core/spez_ertrag.py, gebaut 17.09.2026). NULL = Altbestand, Client < v4.0.22
    # oder keine aktive Solarprognose: dann gibt es unter zwölf Monaten KEINEN
    # Jahreswert (`basis_grund = kein_massstab`) — bewusst keine Server-Kaskade,
    # Begründung im SoT-Docstring.
    soll_jahr_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    erstellt_am: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    aktualisiert_am: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Rate-Limit-Fenster (rollend 24h, statt Monatswechsel). Beim ersten
    # Submit oder wenn das Fenster älter als 24h ist, wird `update_window_start`
    # neu gesetzt und `update_count` auf 0. Sonst zählt jeder Submit hoch und
    # 429 greift bei settings.max_updates_per_24h. Issue #254 (kingcap1).
    update_count: Mapped[int] = mapped_column(Integer, default=0)
    update_window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Beziehungen
    monatswerte: Mapped[list["Monatswert"]] = relationship(back_populates="anlage", cascade="all, delete-orphan")


class Monatswert(Base):
    """
    Monatliche Ertragsdaten einer Anlage.
    """
    __tablename__ = "monatswerte"

    id: Mapped[int] = mapped_column(primary_key=True)
    anlage_id: Mapped[int] = mapped_column(ForeignKey("anlagen.id", ondelete="CASCADE"))

    # Zeitraum
    jahr: Mapped[int] = mapped_column(Integer)
    monat: Mapped[int] = mapped_column(Integer)

    # Energiewerte
    ertrag_kwh: Mapped[float] = mapped_column(Float)
    einspeisung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    netzbezug_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Berechnete Werte
    autarkie_prozent: Mapped[float | None] = mapped_column(Float, nullable=True)
    eigenverbrauch_prozent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Vom Client mitgelieferte Maßstäbe und Kanon-Größen (eedc #387/F-47, ab v4.0.22).
    # Der Server konstruiert davon NICHTS selbst — er hat die Rohdaten nie gesehen.
    # `soll_ertrag_kwh` ist die PVGIS-Erwartung genau dieses Monats, inklusive
    # tagesgenau gekürztem Anschaffungsmonat; `co2_vermieden_kg` und
    # `eigenverbrauch_kwh` lösen die beiden Stellen ab, an denen der Server bis
    # dahin nachgerechnet hat (F-47). NULL = Altbestand oder Client < v4.0.22.
    soll_ertrag_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    co2_vermieden_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    eigenverbrauch_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Speicher-KPIs
    speicher_ladung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    speicher_entladung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    speicher_ladung_netz_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Wärmepumpe-KPIs
    wp_stromverbrauch_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wp_heizwaerme_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wp_warmwasser_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    # eedc ADR-002/P12: Darf aus diesem Monatswert eine Arbeitszahl gebildet
    # werden? Eine Markierung, keine Menge — der Server rechnet damit nichts,
    # er nimmt den Monatswert aus den JAZ-Auswertungen (nicht aus den Mengen).
    # False = Zaehler und Nenner verschieden abgegrenzt. NULL = unbekannt und
    # **zaehlt mit** (wie `kuehlung_art`): unbekannt ist nicht unbelastbar.
    wp_jaz_belastbar: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # eedc W-14: der Anteil von `wp_stromverbrauch_kwh`, der ins **Kühlen** ging.
    # Eine **MENGE** — was der Monat gekühlt hat. **Teilmenge, kein Summand**
    # (nie addieren), und seit dem 13.09.2026 auch **kein Abzug mehr**: was vom
    # JAZ-Nenner abgezogen werden darf, steht in
    # `wp_strom_funktionsfremd_abzug_kwh` darunter. Dieses Feld hier wird nur
    # noch als **Fallback** abgezogen, wenn das andere NULL ist (älterer Client).
    # NULL = Altbestand oder älterer Client („unbekannt", nicht „null kWh").
    wp_strom_kuehlen_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    # eedc SOLL Wärme/Klima §4.1 („Ergänzung zu E7", Option A, 12.09.2026):
    # der Teil des funktionsfremden Stroms (Kühlen + Lüften + Entfeuchten), der
    # vom JAZ-Nenner abgezogen werden DARF — eine **Entscheidung des Clients**,
    # keine Menge. Er entscheidet sie je Gerät: Abgezogen wird nur, was im
    # Nenner auch drinsteht. Bei getrennter Strommessung (Heizen/Warmwasser als
    # eigene Zähler) ist ein aus dem Betriebsmodus **abgeleiteter** Kühlanteil
    # ein Ausschnitt genau dieser zwei Zähler — er kürzt sie nicht, und der
    # Client schickt hier 0.0. Der Server kann das nicht selbst bilden: Er hat
    # die Geräte nie gesehen.
    # NULL = Altbestand oder Client < WK-06b ⇒ Fallback auf `wp_strom_kuehlen_kwh`.
    # 0.0 = entschieden, es ist nichts abzuziehen. Der Unterschied ist Absicht.
    wp_strom_funktionsfremd_abzug_kwh: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # E-Auto-KPIs
    eauto_ladung_gesamt_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    eauto_ladung_pv_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    eauto_ladung_extern_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    eauto_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    eauto_v2h_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Wallbox-KPIs
    wallbox_ladung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wallbox_ladung_pv_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wallbox_ladevorgaenge: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Balkonkraftwerk-KPIs
    bkw_erzeugung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    bkw_eigenverbrauch_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    bkw_speicher_ladung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    bkw_speicher_entladung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Sonstiges-KPIs
    sonstiges_verbrauch_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Beziehung
    anlage: Mapped["Anlage"] = relationship(back_populates="monatswerte")

    # Eindeutigkeit: Pro Anlage nur ein Eintrag pro Monat
    __table_args__ = (
        Index("ix_monatswerte_anlage_zeit", "anlage_id", "jahr", "monat", unique=True),
    )


class RateLimit(Base):
    """
    Rate-Limiting Tracking pro IP.
    """
    __tablename__ = "rate_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(45), index=True)  # IPv6 max 45 chars
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_rate_limits_ip_time", "ip_address", "timestamp"),
    )
