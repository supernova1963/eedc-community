-- Migration: v0.2.0 - Erweiterte KPIs für Komponenten
-- Datum: 2026-02-20
-- Beschreibung: Fügt neue Felder für Speicher, WP, E-Auto, Wallbox, BKW hinzu

-- ============================================================================
-- Anlage: Neue Felder
-- ============================================================================

ALTER TABLE anlagen ADD COLUMN IF NOT EXISTS hat_balkonkraftwerk BOOLEAN DEFAULT FALSE;
ALTER TABLE anlagen ADD COLUMN IF NOT EXISTS hat_sonstiges BOOLEAN DEFAULT FALSE;
ALTER TABLE anlagen ADD COLUMN IF NOT EXISTS wallbox_kw FLOAT;
ALTER TABLE anlagen ADD COLUMN IF NOT EXISTS bkw_wp FLOAT;
ALTER TABLE anlagen ADD COLUMN IF NOT EXISTS sonstiges_bezeichnung VARCHAR(100);

-- ============================================================================
-- Monatswerte: Speicher-KPIs
-- ============================================================================

ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS speicher_ladung_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS speicher_entladung_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS speicher_ladung_netz_kwh FLOAT;

-- ============================================================================
-- Monatswerte: Wärmepumpe-KPIs
-- ============================================================================

ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS wp_stromverbrauch_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS wp_heizwaerme_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS wp_warmwasser_kwh FLOAT;

-- ============================================================================
-- Monatswerte: E-Auto-KPIs
-- ============================================================================

ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS eauto_ladung_gesamt_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS eauto_ladung_pv_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS eauto_ladung_extern_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS eauto_km FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS eauto_v2h_kwh FLOAT;

-- ============================================================================
-- Monatswerte: Wallbox-KPIs
-- ============================================================================

ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS wallbox_ladung_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS wallbox_ladung_pv_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS wallbox_ladevorgaenge INTEGER;

-- ============================================================================
-- Monatswerte: Balkonkraftwerk-KPIs
-- ============================================================================

ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS bkw_erzeugung_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS bkw_eigenverbrauch_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS bkw_speicher_ladung_kwh FLOAT;
ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS bkw_speicher_entladung_kwh FLOAT;

-- ============================================================================
-- Monatswerte: Sonstiges-KPIs
-- ============================================================================

ALTER TABLE monatswerte ADD COLUMN IF NOT EXISTS sonstiges_verbrauch_kwh FLOAT;

-- ============================================================================
-- Verification
-- ============================================================================

-- Prüfe ob alle Spalten hinzugefügt wurden:
-- \d anlagen
-- \d monatswerte
