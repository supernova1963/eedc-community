"""
EEDC Community - Daten einreichen
"""

import hashlib
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings, get_db
from models import Anlage, Monatswert, RateLimit
from schemas import AnlageSubmitInput, MonatswertInput, SubmitResponse, BenchmarkData, DeleteResponse

logger = logging.getLogger(__name__)
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


def validate_monatswerte_plausibility(
    data: AnlageSubmitInput,
) -> tuple[list[MonatswertInput], list[str]]:
    """Prüft die Monatswerte und trennt sie in angenommene und übersprungene.

    **Bis zum 19.09.2026 warf ein einziger unplausibler Monat den GANZEN Submit
    mit 400 ab** (eedc N-523). Im Proxy-Log stand das als tägliche 400 einer
    aktuellen 4.0.47-Installation, die damit seit Wochen keinen Datensatz mehr
    in der Community hatte — der Anwender sah nur „Unrealistischer Ertrag in
    YYYY-MM" und verlor alle anderen Monate mit.

    Jetzt gilt: der unplausible Monat wird **übersprungen und im Hinweis
    genannt**, die übrigen Monate werden angenommen. Erst wenn KEIN Monat übrig
    bleibt, antwortet der Server mit 400 und allen Gründen. Ein übersprungener
    Monat wird weder gespeichert noch gelöscht — hat der Server für ihn schon
    einen früher plausiblen Wert, bleibt der stehen (auch beim Voll-Submit mit
    `monate_vollstaendig`: der Client hat den Monat ja gesendet).

    Die Schwellen sind unverändert: Zukunftsmonat, Ertrag ≤ 0, spezifischer
    Ertrag über 180 kWh/kWp (ein Sommer-Maßstab; das am 19.08.2026 entschiedene
    relative Band am SOLL ist davon unabhängig und nicht Teil dieser Änderung).

    Returns:
        (angenommene Monatswerte, Hinweise) — Hinweise sind Klartext je Monat,
        übersprungene beginnen mit ``YYYY-MM übersprungen:``.
    """
    hinweise: list[str] = []
    angenommen: list[MonatswertInput] = []
    now = datetime.utcnow()

    for mw in data.monatswerte:
        label = f"{mw.jahr}-{mw.monat:02d}"

        # Keine Zukunftsmonate
        if mw.jahr > now.year or (mw.jahr == now.year and mw.monat > now.month):
            hinweise.append(f"{label} übersprungen: Zukunftsmonat")
            continue

        # Kein 0-Ertrag
        if mw.ertrag_kwh <= 0:
            hinweise.append(f"{label} übersprungen: Ertrag 0 oder negativ")
            continue

        # Spezifischer Ertrag pro kWp
        spez_ertrag = mw.ertrag_kwh / data.kwp

        # Max ~180 kWh/kWp/Monat ist extrem (Juni in Süddeutschland)
        if spez_ertrag > 180:
            hinweise.append(
                f"{label} übersprungen: unrealistischer Ertrag ({spez_ertrag:.0f} kWh/kWp)"
            )
            continue

        # Warnung bei sehr hohen Werten
        if spez_ertrag > 150:
            hinweise.append(f"{label}: Sehr hoher Ertrag ({spez_ertrag:.0f} kWh/kWp)")

        angenommen.append(mw)

    if not angenommen:
        raise HTTPException(
            status_code=400,
            detail="Kein plausibler Monat im Submit: " + "; ".join(hinweise),
        )

    return angenommen, hinweise


async def calculate_benchmark(db: AsyncSession, anlage: Anlage) -> BenchmarkData:
    """Berechnet Vergleichsdaten für eine Anlage.

    Dieselbe Konstruktionsstelle wie das Dashboard
    (`benchmark.py::baue_benchmark_data`, SoT `core/spez_ertrag.py`, #387):
    Bestätigung und Dashboard nennen dieselbe Zahl und dieselbe Grundgesamtheit.
    Bis zum 17.09.2026 zählte „von N" hier ALLE Anlagen, im Dashboard nur die
    mit Wert. Eine Anlage ohne Jahreswert bekommt kein `None` mehr, sondern die
    Felder samt Grund — der Client sagt dann, warum.
    """
    from .benchmark import baue_benchmark_data

    return await baue_benchmark_data(db, anlage)


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
    # Hash generieren falls nicht angegeben
    anlage_hash = data.anlage_hash or generate_anlage_hash(data)

    # Bestehende Anlage suchen
    result = await db.execute(
        select(Anlage).where(Anlage.anlage_hash == anlage_hash)
    )
    anlage = result.scalar_one_or_none()

    # Plausibilität prüfen — unplausible Monate werden übersprungen, nicht der Submit
    angenommen, warnings = validate_monatswerte_plausibility(data)
    uebersprungen = [w for w in warnings if " übersprungen: " in w]
    if uebersprungen:
        # Im Container-Log sichtbar: bis zum 19.09.2026 stand im Proxy-Log nur
        # „400, 59 Bytes" — der Grund war von außen nicht unterscheidbar.
        logger.warning(
            "submit: %d von %d Monat(en) uebersprungen hash=%s: %s",
            len(uebersprungen), len(data.monatswerte), anlage_hash[:12],
            "; ".join(uebersprungen),
        )

    if anlage:
        # Update: Rate-Limit-Fenster rollend 24h prüfen. Wenn das letzte Fenster
        # leer (Neuanlage / Migration aus Monatszähler-Logik) oder älter als 24h
        # ist, frisches Fenster starten. Damit sind Reparatur-/Nachpflege-
        # Sessions möglich, ohne den Spam-Schutz pro Hash aufzugeben.
        # Issue #254 (kingcap1).
        now = datetime.utcnow()
        window_start = anlage.update_window_start
        if window_start is None or (now - window_start) > timedelta(hours=24):
            anlage.update_window_start = now
            anlage.update_count = 0

        if anlage.update_count >= settings.max_updates_per_24h:
            logger.warning(
                "submit 429 Anlagen-Limit hash=%s update_count=%s window_start=%s",
                anlage_hash[:12], anlage.update_count, anlage.update_window_start,
            )
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Maximale Anzahl Updates ({settings.max_updates_per_24h}) "
                    f"im 24-Stunden-Fenster erreicht. Bitte später erneut versuchen."
                ),
            )

        # Anlagendaten aktualisieren (alle Felder, nicht nur Komponenten)
        anlage.region = data.region
        anlage.kwp = data.kwp
        anlage.ausrichtung = data.ausrichtung
        anlage.neigung_grad = data.neigung_grad
        anlage.speicher_kwh = data.speicher_kwh
        anlage.installation_jahr = data.installation_jahr
        anlage.soll_jahr_kwh = data.soll_jahr_kwh
        anlage.hat_waermepumpe = data.hat_waermepumpe
        anlage.wp_art = data.wp_art
        anlage.kuehlung_art = data.kuehlung_art
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
            soll_jahr_kwh=data.soll_jahr_kwh,
            hat_waermepumpe=data.hat_waermepumpe,
            wp_art=data.wp_art,
            kuehlung_art=data.kuehlung_art,
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

    # Monatswerte einfügen/aktualisieren — nur die angenommenen (s. o.)
    for mw in angenommen:
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
            # Maßstab + Kanon-Größen (ab eedc v4.0.22, #387/F-47). Bewusst auch
            # dann gesetzt, wenn der Client None schickt: der Submit ist ein
            # Voll-Submit — der Client sagt, was gilt. Ein alter Client räumt das
            # SOLL damit ab; das ist heilbar, ein stehengebliebener falscher
            # Maßstab wäre es nicht.
            existing.soll_ertrag_kwh = mw.soll_ertrag_kwh
            existing.co2_vermieden_kg = mw.co2_vermieden_kg
            existing.eigenverbrauch_kwh = mw.eigenverbrauch_kwh
            # Speicher
            existing.speicher_ladung_kwh = mw.speicher_ladung_kwh
            existing.speicher_entladung_kwh = mw.speicher_entladung_kwh
            existing.speicher_ladung_netz_kwh = mw.speicher_ladung_netz_kwh
            # Wärmepumpe
            existing.wp_stromverbrauch_kwh = mw.wp_stromverbrauch_kwh
            existing.wp_heizwaerme_kwh = mw.wp_heizwaerme_kwh
            existing.wp_warmwasser_kwh = mw.wp_warmwasser_kwh
            # eedc W-14: Teilmenge des WP-Stroms, die ins Kühlen ging (MENGE).
            existing.wp_strom_kuehlen_kwh = mw.wp_strom_kuehlen_kwh
            # eedc WK-06b: wieviel davon vom JAZ-Nenner abgezogen werden darf
            # (ENTSCHEIDUNG, s. `MonatswertInput`). Auch `None` wird gesetzt —
            # Voll-Submit, der Client sagt, was gilt; ein alter Client schaltet
            # die Zeile damit auf den Fallback zurück, und das ist richtig so.
            existing.wp_strom_funktionsfremd_abzug_kwh = (
                mw.wp_strom_funktionsfremd_abzug_kwh
            )
            existing.wp_jaz_belastbar = mw.wp_jaz_belastbar
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
                # Maßstab + Kanon-Größen vom Client (ab eedc v4.0.22, #387/F-47).
                # Werden ab dem 01.09.2026 ausgewertet; bis dahin nur gespeichert.
                soll_ertrag_kwh=mw.soll_ertrag_kwh,
                co2_vermieden_kg=mw.co2_vermieden_kg,
                eigenverbrauch_kwh=mw.eigenverbrauch_kwh,
                # Speicher
                speicher_ladung_kwh=mw.speicher_ladung_kwh,
                speicher_entladung_kwh=mw.speicher_entladung_kwh,
                speicher_ladung_netz_kwh=mw.speicher_ladung_netz_kwh,
                # Wärmepumpe
                wp_stromverbrauch_kwh=mw.wp_stromverbrauch_kwh,
                wp_heizwaerme_kwh=mw.wp_heizwaerme_kwh,
                wp_warmwasser_kwh=mw.wp_warmwasser_kwh,
                wp_strom_kuehlen_kwh=mw.wp_strom_kuehlen_kwh,
                # eedc WK-06b — die Entscheidung neben der Menge (s. o.).
                wp_strom_funktionsfremd_abzug_kwh=(
                    mw.wp_strom_funktionsfremd_abzug_kwh
                ),
                wp_jaz_belastbar=mw.wp_jaz_belastbar,
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

    # N18-2: Vollständigkeits-Submit — Monate dieses Hashes, die im Payload fehlen,
    # wurden client-seitig entfernt (Datensatz gelöscht oder Korrektur filtert ihn
    # raus) und werden hier gelöscht. Nur mit explizitem Flag; alte Clients ohne
    # `monate_vollstaendig` behalten das reine Upsert-Verhalten.
    geloescht = 0
    if data.monate_vollstaendig:
        gesendet = {(mw.jahr, mw.monat) for mw in data.monatswerte}
        result = await db.execute(
            select(Monatswert).where(Monatswert.anlage_id == anlage.id)
        )
        for vorhandenen_monat in result.scalars():
            if (vorhandenen_monat.jahr, vorhandenen_monat.monat) not in gesendet:
                await db.delete(vorhandenen_monat)
                geloescht += 1
    if geloescht:
        warnings.append(f"{geloescht} rückwirkend entfernte(r) Monat(e) gelöscht")

    await db.commit()
    await db.refresh(anlage)

    # Benchmark berechnen
    benchmark = await calculate_benchmark(db, anlage)

    return SubmitResponse(
        success=True,
        message=message + (f" (Hinweise: {', '.join(warnings)})" if warnings else ""),
        anlage_hash=anlage_hash,
        anzahl_monate=len(angenommen),
        hinweise=warnings,
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
