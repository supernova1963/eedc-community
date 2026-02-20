"""
EEDC Community - Daten einreichen
"""

import hashlib
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings, get_db
from models import Anlage, Monatswert, RateLimit
from schemas import AnlageSubmitInput, SubmitResponse, BenchmarkData, DeleteResponse

router = APIRouter(prefix="/submit", tags=["Einreichen"])


def generate_anlage_hash(data: AnlageSubmitInput) -> str:
    """
    Generiert einen eindeutigen Hash für eine Anlage.
    Basiert auf: kWp + Installationsjahr + Region + Secret
    """
    raw = f"{data.kwp:.1f}:{data.installation_jahr}:{data.region}:{settings.secret_key}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def check_rate_limit(db: AsyncSession, ip: str) -> bool:
    """Prüft ob die IP das Rate-Limit überschritten hat."""
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    # Alte Einträge löschen
    await db.execute(
        delete(RateLimit).where(RateLimit.timestamp < one_hour_ago)
    )

    # Anzahl der Requests in der letzten Stunde
    result = await db.execute(
        select(func.count(RateLimit.id))
        .where(RateLimit.ip_address == ip)
        .where(RateLimit.timestamp >= one_hour_ago)
    )
    count = result.scalar() or 0

    return count < settings.rate_limit_per_hour


async def record_request(db: AsyncSession, ip: str):
    """Speichert einen Request für Rate-Limiting."""
    db.add(RateLimit(ip_address=ip))
    await db.commit()


def validate_monatswerte_plausibility(data: AnlageSubmitInput) -> list[str]:
    """
    Prüft Plausibilität der Monatswerte.
    Gibt Liste von Warnungen zurück (leere Liste = alles OK).
    """
    warnings = []
    now = datetime.utcnow()

    for mw in data.monatswerte:
        # Keine Zukunftsmonate
        if mw.jahr > now.year or (mw.jahr == now.year and mw.monat > now.month):
            raise HTTPException(
                status_code=400,
                detail=f"Zukunftsmonat nicht erlaubt: {mw.jahr}-{mw.monat:02d}"
            )

        # Spezifischer Ertrag pro kWp
        spez_ertrag = mw.ertrag_kwh / data.kwp

        # Max ~180 kWh/kWp/Monat ist extrem (Juni in Süddeutschland)
        if spez_ertrag > 180:
            raise HTTPException(
                status_code=400,
                detail=f"Unrealistischer Ertrag in {mw.jahr}-{mw.monat:02d}: {spez_ertrag:.0f} kWh/kWp"
            )

        # Warnung bei sehr hohen Werten
        if spez_ertrag > 150:
            warnings.append(f"{mw.jahr}-{mw.monat:02d}: Sehr hoher Ertrag ({spez_ertrag:.0f} kWh/kWp)")

    return warnings


async def calculate_benchmark(db: AsyncSession, anlage: Anlage) -> BenchmarkData | None:
    """Berechnet Vergleichsdaten für eine Anlage."""
    # Aktuelles Jahr oder letztes vollständiges Jahr
    current_year = datetime.utcnow().year
    target_year = current_year if datetime.utcnow().month > 6 else current_year - 1

    # Spez. Ertrag der Anlage im Zieljahr
    result = await db.execute(
        select(func.sum(Monatswert.ertrag_kwh))
        .where(Monatswert.anlage_id == anlage.id)
        .where(Monatswert.jahr == target_year)
    )
    anlage_ertrag = result.scalar() or 0
    spez_ertrag_anlage = anlage_ertrag / anlage.kwp if anlage.kwp > 0 else 0

    if spez_ertrag_anlage == 0:
        return None

    # Durchschnitt aller Anlagen
    result = await db.execute(
        select(
            func.sum(Monatswert.ertrag_kwh),
            func.sum(Anlage.kwp)
        )
        .join(Anlage)
        .where(Monatswert.jahr == target_year)
    )
    row = result.first()
    gesamt_ertrag = row[0] or 0
    gesamt_kwp = row[1] or 1
    spez_ertrag_durchschnitt = gesamt_ertrag / gesamt_kwp

    # Durchschnitt der Region
    result = await db.execute(
        select(
            func.sum(Monatswert.ertrag_kwh),
            func.sum(Anlage.kwp)
        )
        .join(Anlage)
        .where(Monatswert.jahr == target_year)
        .where(Anlage.region == anlage.region)
    )
    row = result.first()
    region_ertrag = row[0] or 0
    region_kwp = row[1] or 1
    spez_ertrag_region = region_ertrag / region_kwp

    # Rang gesamt (Anlagen mit höherem spez. Ertrag)
    # Vereinfachte Berechnung - in Produktion optimieren
    result = await db.execute(select(func.count(Anlage.id)))
    anzahl_gesamt = result.scalar() or 1

    result = await db.execute(
        select(func.count(Anlage.id)).where(Anlage.region == anlage.region)
    )
    anzahl_region = result.scalar() or 1

    # Platzierung basierend auf Perzentil (vereinfacht)
    if spez_ertrag_anlage >= spez_ertrag_durchschnitt:
        rang_gesamt = int(anzahl_gesamt * 0.3)  # Top 30%
    else:
        rang_gesamt = int(anzahl_gesamt * 0.6)  # Untere 60%

    rang_region = int(rang_gesamt * anzahl_region / anzahl_gesamt)

    return BenchmarkData(
        spez_ertrag_anlage=round(spez_ertrag_anlage, 1),
        spez_ertrag_durchschnitt=round(spez_ertrag_durchschnitt, 1),
        spez_ertrag_region=round(spez_ertrag_region, 1),
        rang_gesamt=max(1, rang_gesamt),
        anzahl_anlagen_gesamt=anzahl_gesamt,
        rang_region=max(1, rang_region),
        anzahl_anlagen_region=anzahl_region,
    )


@router.post("", response_model=SubmitResponse)
async def submit_anlage(
    data: AnlageSubmitInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Reicht Anlagendaten ein oder aktualisiert bestehende.

    - Neue Anlage: Wird erstellt mit generiertem Hash
    - Bestehende Anlage (gleicher Hash): Monatswerte werden ergänzt/aktualisiert
    """
    # Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    if not await check_rate_limit(db, client_ip):
        raise HTTPException(
            status_code=429,
            detail="Zu viele Anfragen. Bitte warte eine Stunde."
        )

    # Plausibilität prüfen
    warnings = validate_monatswerte_plausibility(data)

    # Hash generieren falls nicht angegeben
    anlage_hash = data.anlage_hash or generate_anlage_hash(data)

    # Bestehende Anlage suchen
    result = await db.execute(
        select(Anlage).where(Anlage.anlage_hash == anlage_hash)
    )
    anlage = result.scalar_one_or_none()

    if anlage:
        # Update: Prüfen ob zu viele Updates
        if anlage.update_count >= settings.max_updates_per_month:
            raise HTTPException(
                status_code=429,
                detail="Maximale Anzahl Updates pro Monat erreicht."
            )

        # Anlagendaten aktualisieren
        anlage.speicher_kwh = data.speicher_kwh
        anlage.hat_waermepumpe = data.hat_waermepumpe
        anlage.hat_eauto = data.hat_eauto
        anlage.hat_wallbox = data.hat_wallbox
        anlage.hat_balkonkraftwerk = data.hat_balkonkraftwerk
        anlage.hat_sonstiges = data.hat_sonstiges
        anlage.wallbox_kw = data.wallbox_kw
        anlage.bkw_wp = data.bkw_wp
        anlage.sonstiges_bezeichnung = data.sonstiges_bezeichnung
        anlage.update_count += 1
        message = "Anlage aktualisiert"
    else:
        # Neue Anlage erstellen
        anlage = Anlage(
            anlage_hash=anlage_hash,
            region=data.region,
            kwp=data.kwp,
            ausrichtung=data.ausrichtung,
            neigung_grad=data.neigung_grad,
            speicher_kwh=data.speicher_kwh,
            installation_jahr=data.installation_jahr,
            hat_waermepumpe=data.hat_waermepumpe,
            hat_eauto=data.hat_eauto,
            hat_wallbox=data.hat_wallbox,
            hat_balkonkraftwerk=data.hat_balkonkraftwerk,
            hat_sonstiges=data.hat_sonstiges,
            wallbox_kw=data.wallbox_kw,
            bkw_wp=data.bkw_wp,
            sonstiges_bezeichnung=data.sonstiges_bezeichnung,
        )
        db.add(anlage)
        await db.flush()  # ID generieren
        message = "Anlage erstellt"

    # Monatswerte einfügen/aktualisieren
    for mw in data.monatswerte:
        # Bestehenden Monatswert suchen
        result = await db.execute(
            select(Monatswert)
            .where(Monatswert.anlage_id == anlage.id)
            .where(Monatswert.jahr == mw.jahr)
            .where(Monatswert.monat == mw.monat)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Aktualisieren - Basis
            existing.ertrag_kwh = mw.ertrag_kwh
            existing.einspeisung_kwh = mw.einspeisung_kwh
            existing.netzbezug_kwh = mw.netzbezug_kwh
            existing.autarkie_prozent = mw.autarkie_prozent
            existing.eigenverbrauch_prozent = mw.eigenverbrauch_prozent
            # Speicher
            existing.speicher_ladung_kwh = mw.speicher_ladung_kwh
            existing.speicher_entladung_kwh = mw.speicher_entladung_kwh
            existing.speicher_ladung_netz_kwh = mw.speicher_ladung_netz_kwh
            # Wärmepumpe
            existing.wp_stromverbrauch_kwh = mw.wp_stromverbrauch_kwh
            existing.wp_heizwaerme_kwh = mw.wp_heizwaerme_kwh
            existing.wp_warmwasser_kwh = mw.wp_warmwasser_kwh
            # E-Auto
            existing.eauto_ladung_gesamt_kwh = mw.eauto_ladung_gesamt_kwh
            existing.eauto_ladung_pv_kwh = mw.eauto_ladung_pv_kwh
            existing.eauto_ladung_extern_kwh = mw.eauto_ladung_extern_kwh
            existing.eauto_km = mw.eauto_km
            existing.eauto_v2h_kwh = mw.eauto_v2h_kwh
            # Wallbox
            existing.wallbox_ladung_kwh = mw.wallbox_ladung_kwh
            existing.wallbox_ladung_pv_kwh = mw.wallbox_ladung_pv_kwh
            existing.wallbox_ladevorgaenge = mw.wallbox_ladevorgaenge
            # Balkonkraftwerk
            existing.bkw_erzeugung_kwh = mw.bkw_erzeugung_kwh
            existing.bkw_eigenverbrauch_kwh = mw.bkw_eigenverbrauch_kwh
            existing.bkw_speicher_ladung_kwh = mw.bkw_speicher_ladung_kwh
            existing.bkw_speicher_entladung_kwh = mw.bkw_speicher_entladung_kwh
            # Sonstiges
            existing.sonstiges_verbrauch_kwh = mw.sonstiges_verbrauch_kwh
        else:
            # Neu erstellen
            db.add(Monatswert(
                anlage_id=anlage.id,
                jahr=mw.jahr,
                monat=mw.monat,
                ertrag_kwh=mw.ertrag_kwh,
                einspeisung_kwh=mw.einspeisung_kwh,
                netzbezug_kwh=mw.netzbezug_kwh,
                autarkie_prozent=mw.autarkie_prozent,
                eigenverbrauch_prozent=mw.eigenverbrauch_prozent,
                # Speicher
                speicher_ladung_kwh=mw.speicher_ladung_kwh,
                speicher_entladung_kwh=mw.speicher_entladung_kwh,
                speicher_ladung_netz_kwh=mw.speicher_ladung_netz_kwh,
                # Wärmepumpe
                wp_stromverbrauch_kwh=mw.wp_stromverbrauch_kwh,
                wp_heizwaerme_kwh=mw.wp_heizwaerme_kwh,
                wp_warmwasser_kwh=mw.wp_warmwasser_kwh,
                # E-Auto
                eauto_ladung_gesamt_kwh=mw.eauto_ladung_gesamt_kwh,
                eauto_ladung_pv_kwh=mw.eauto_ladung_pv_kwh,
                eauto_ladung_extern_kwh=mw.eauto_ladung_extern_kwh,
                eauto_km=mw.eauto_km,
                eauto_v2h_kwh=mw.eauto_v2h_kwh,
                # Wallbox
                wallbox_ladung_kwh=mw.wallbox_ladung_kwh,
                wallbox_ladung_pv_kwh=mw.wallbox_ladung_pv_kwh,
                wallbox_ladevorgaenge=mw.wallbox_ladevorgaenge,
                # Balkonkraftwerk
                bkw_erzeugung_kwh=mw.bkw_erzeugung_kwh,
                bkw_eigenverbrauch_kwh=mw.bkw_eigenverbrauch_kwh,
                bkw_speicher_ladung_kwh=mw.bkw_speicher_ladung_kwh,
                bkw_speicher_entladung_kwh=mw.bkw_speicher_entladung_kwh,
                # Sonstiges
                sonstiges_verbrauch_kwh=mw.sonstiges_verbrauch_kwh,
            ))

    # Request für Rate-Limiting speichern
    await record_request(db, client_ip)

    await db.commit()
    await db.refresh(anlage)

    # Benchmark berechnen
    benchmark = await calculate_benchmark(db, anlage)

    return SubmitResponse(
        success=True,
        message=message + (f" (Hinweise: {', '.join(warnings)})" if warnings else ""),
        anlage_hash=anlage_hash,
        anzahl_monate=len(data.monatswerte),
        benchmark=benchmark,
    )


@router.delete("/{anlage_hash}", response_model=DeleteResponse)
async def delete_anlage(
    anlage_hash: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Löscht eine Anlage und alle zugehörigen Monatswerte.

    Der Anlage-Hash dient als Authentifizierung - nur wer den Hash kennt,
    kann die Daten löschen. Der Hash wird nur beim Teilen zurückgegeben.
    """
    # Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    if not await check_rate_limit(db, client_ip):
        raise HTTPException(
            status_code=429,
            detail="Zu viele Anfragen. Bitte warte eine Stunde."
        )

    # Anlage suchen
    result = await db.execute(
        select(Anlage).where(Anlage.anlage_hash == anlage_hash)
    )
    anlage = result.scalar_one_or_none()

    if not anlage:
        raise HTTPException(
            status_code=404,
            detail="Anlage nicht gefunden. Ungültiger Hash oder bereits gelöscht."
        )

    # Anzahl der Monatswerte für Rückmeldung
    result = await db.execute(
        select(func.count(Monatswert.id)).where(Monatswert.anlage_id == anlage.id)
    )
    anzahl_monate = result.scalar() or 0

    # Monatswerte löschen (CASCADE sollte das auch machen, aber explizit ist sicherer)
    await db.execute(
        delete(Monatswert).where(Monatswert.anlage_id == anlage.id)
    )

    # Anlage löschen
    await db.delete(anlage)

    # Request für Rate-Limiting speichern
    await record_request(db, client_ip)

    await db.commit()

    return DeleteResponse(
        success=True,
        message="Deine Anlage und alle Monatswerte wurden vollständig gelöscht.",
        anzahl_geloeschte_monate=anzahl_monate,
    )
