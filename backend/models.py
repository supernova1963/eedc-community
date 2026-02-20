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
    hat_eauto: Mapped[bool] = mapped_column(Boolean, default=False)
    hat_wallbox: Mapped[bool] = mapped_column(Boolean, default=False)
    hat_balkonkraftwerk: Mapped[bool] = mapped_column(Boolean, default=False)
    hat_sonstiges: Mapped[bool] = mapped_column(Boolean, default=False)

    # Komponenten-Details
    wallbox_kw: Mapped[float | None] = mapped_column(Float, nullable=True)  # Ladeleistung
    bkw_wp: Mapped[float | None] = mapped_column(Float, nullable=True)  # BKW Leistung in Wp
    sonstiges_bezeichnung: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Metadaten
    erstellt_am: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    aktualisiert_am: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    update_count: Mapped[int] = mapped_column(Integer, default=0)

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

    # Speicher-KPIs
    speicher_ladung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    speicher_entladung_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    speicher_ladung_netz_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Wärmepumpe-KPIs
    wp_stromverbrauch_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wp_heizwaerme_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wp_warmwasser_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)

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
