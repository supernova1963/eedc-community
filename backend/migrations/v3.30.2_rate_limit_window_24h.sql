-- Migration: v3.30.2 - Rate-Limit rollend 24h statt Monatswechsel
-- Datum: 2026-05-15
-- Beschreibung: Issue #254 (kingcap1). Submit-Limit wechselt von
--   "max 30 Updates pro Anlage/Kalendermonat" zu
--   "max 50 Updates pro Anlage in rollendem 24h-Fenster".
--
-- Die App-Migration in `backend/core/database.py:run_migrations` führt das
-- ALTER TABLE automatisch beim Server-Start aus. Diese SQL-Datei dient
-- nur der Dokumentation für manuelle DB-Audits oder Restore-Vorgänge.

-- Neue Spalte: Startzeit des aktuellen 24h-Fensters pro Anlage.
-- NULL bei Bestandsanlagen → erste Submit startet frisches Fenster
-- und setzt update_count auf 0. Damit sind alle Anlagen, die am alten
-- Monats-Limit hingen, nach Deploy automatisch entsperrt.
ALTER TABLE anlagen ADD COLUMN IF NOT EXISTS update_window_start TIMESTAMP;
