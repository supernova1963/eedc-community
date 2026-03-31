import { useState, useMemo, useEffect, useRef } from 'react'
import type { GesamtStatistik, CommunityGesamtwerte, TabId } from '../../types'
import { MONATE, REGION_NAMEN } from '../../constants'
import { fmtEnergy } from '../../utils'

// ── Hilfsfunktionen ──────────────────────────────────────────────────────────

function seasonEmoji(monat: number) {
  if (monat <= 2 || monat === 12) return '❄️'
  if (monat <= 5) return '🌱'
  if (monat <= 8) return '☀️'
  return '🍂'
}

const TABS: { id: TabId; label: string; cta?: boolean }[] = [
  { id: 'uebersicht',     label: 'Übersicht' },
  { id: 'monatsvergleich', label: 'Monatsvergleich' },
  { id: 'regionen',       label: 'Regionen' },
  { id: 'impact',         label: 'Impact' },
  { id: 'mitmachen',      label: 'Mitmachen', cta: true },
]

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 bg-orange-50 dark:bg-orange-900/30 border border-orange-200 dark:border-orange-800 text-orange-700 dark:text-orange-300 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap">
      {children}
    </span>
  )
}

function StatPill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap">
      {children}
    </span>
  )
}

function VDivider() {
  return <div className="w-px h-5 bg-gray-200 dark:bg-gray-600 shrink-0" />
}

// ── Haupt-Komponente ─────────────────────────────────────────────────────────

export default function StickyHeader({
  stats,
  totals,
  activeTab,
  onChange,
  onHomeClick,
}: {
  stats: GesamtStatistik
  totals: CommunityGesamtwerte | null
  activeTab: TabId
  onChange: (tab: TabId) => void
  onHomeClick: () => void
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Menü bei Klick außerhalb schließen
  useEffect(() => {
    if (!menuOpen) return
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [menuOpen])

  // Letzten abgeschlossenen Monat berechnen
  const monthly = useMemo(() => {
    if (stats.letzte_monate.length === 0) return null
    const now = new Date()
    const abgeschlossen = stats.letzte_monate.filter(m =>
      m.jahr < now.getFullYear() ||
      (m.jahr === now.getFullYear() && m.monat < now.getMonth() + 1),
    )
    const basis = abgeschlossen.length > 0 ? abgeschlossen : stats.letzte_monate
    const sorted = [...basis].sort((a, b) =>
      a.jahr !== b.jahr ? a.jahr - b.jahr : a.monat - b.monat,
    )
    const latest = sorted[sorted.length - 1]
    const prev = sorted.length > 1 ? sorted[sorted.length - 2] : null
    const trendPct = prev
      ? ((latest.durchschnitt_spez_ertrag - prev.durchschnitt_spez_ertrag) /
          prev.durchschnitt_spez_ertrag) * 100
      : null
    const topRegion = stats.regionen.length > 0
      ? [...stats.regionen].sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)[0]
      : null
    return { latest, trendPct, topRegion }
  }, [stats.letzte_monate, stats.regionen])

  // Community-Gesamtstatistik
  const energy = totals ? fmtEnergy(totals.pv_erzeugung_kwh) : null
  const co2t   = totals ? (totals.co2_vermieden_kg / 1000).toFixed(1) : null
  const hh     = totals ? Math.round(totals.pv_erzeugung_kwh / 5000) : null

  const activeLabel = TABS.find(t => t.id === activeTab)?.label ?? ''

  return (
    <div ref={menuRef} className="sticky top-0 z-20">

      {/* ── Haupt-Bar ── */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-6xl mx-auto px-4 h-11 flex items-center gap-2">

          {/* Brand */}
          <button
            type="button"
            onClick={onHomeClick}
            className="font-bold text-orange-600 dark:text-orange-400 hover:text-orange-500 transition-colors shrink-0 flex items-center gap-1.5"
          >
            ☀️ <span>eedc</span>
          </button>

          <VDivider />

          {/* Desktop: Monats-Pills + Community-Stats */}
          <div className="hidden md:flex items-center gap-2 flex-1 overflow-x-auto min-w-0">
            {monthly && (
              <>
                <Pill>{seasonEmoji(monthly.latest.monat)} {MONATE[monthly.latest.monat - 1]} {monthly.latest.jahr}</Pill>
                <Pill>Ø {monthly.latest.durchschnitt_spez_ertrag.toFixed(1)} kWh/kWp</Pill>
                {monthly.trendPct !== null && (
                  <Pill>{monthly.trendPct >= 0 ? '▲' : '▼'} {Math.abs(monthly.trendPct).toFixed(0)}%</Pill>
                )}
                {monthly.topRegion && (
                  <Pill>🏆 {REGION_NAMEN[monthly.topRegion.region] || monthly.topRegion.region}</Pill>
                )}
                <VDivider />
              </>
            )}
            <StatPill>⚡ {stats.anzahl_anlagen} Anlagen</StatPill>
            {energy && <StatPill>☀️ {energy.value} {energy.unit}</StatPill>}
            {co2t  && <StatPill>🌿 {co2t} t CO₂</StatPill>}
            {hh    && <StatPill>🏠 {hh} Haushalte</StatPill>}
          </div>

          {/* Mobile: kompakte Zusammenfassung */}
          <div className="flex md:hidden items-center gap-1.5 flex-1 min-w-0 text-xs text-gray-600 dark:text-gray-400 overflow-hidden">
            <span className="font-medium text-gray-800 dark:text-gray-200 shrink-0">⚡ {stats.anzahl_anlagen}</span>
            {monthly && (
              <>
                <span className="text-gray-300 dark:text-gray-600">·</span>
                <span className="shrink-0">{seasonEmoji(monthly.latest.monat)} {MONATE[monthly.latest.monat - 1]}</span>
                <span className="text-gray-300 dark:text-gray-600">·</span>
                <span className="shrink-0 font-medium text-gray-800 dark:text-gray-200">
                  {monthly.latest.durchschnitt_spez_ertrag.toFixed(1)} kWh/kWp
                </span>
              </>
            )}
          </div>

          {/* Mobile: Hamburger + aktiver Tab-Name */}
          <div className="flex md:hidden items-center gap-2 shrink-0">
            <span className="text-xs text-gray-500 dark:text-gray-400 max-w-[80px] truncate">{activeLabel}</span>
            <button
              type="button"
              onClick={() => setMenuOpen(o => !o)}
              className="p-1.5 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Menü öffnen"
            >
              {menuOpen
                ? <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                : <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
              }
            </button>
          </div>
        </div>
      </div>

      {/* ── Desktop Tab-Leiste ── */}
      <div className="hidden md:block bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center">
            <nav className="flex gap-1 -mb-px flex-1">
              {TABS.filter(t => !t.cta).map(tab => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => onChange(tab.id)}
                  className={`whitespace-nowrap py-3 px-4 text-sm font-medium border-b-2 transition-colors shrink-0 ${
                    activeTab === tab.id
                      ? 'border-orange-500 text-orange-600 dark:text-orange-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
            <div className="shrink-0 pl-2 py-2">
              <button
                type="button"
                onClick={() => onChange('mitmachen')}
                className={`whitespace-nowrap px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${
                  activeTab === 'mitmachen'
                    ? 'bg-orange-600 text-white shadow-md'
                    : 'bg-orange-500 text-white hover:bg-orange-600 shadow-sm'
                }`}
              >
                Mitmachen
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Mobile Dropdown-Menü ── */}
      {menuOpen && (
        <div className="md:hidden bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-xl">
          {TABS.filter(t => !t.cta).map(tab => (
            <button
              key={tab.id}
              type="button"
              onClick={() => { onChange(tab.id); setMenuOpen(false) }}
              className={`w-full text-left px-5 py-3.5 text-sm font-medium border-l-4 transition-colors ${
                activeTab === tab.id
                  ? 'border-orange-500 text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20'
                  : 'border-transparent text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
          <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-700">
            <button
              type="button"
              onClick={() => { onChange('mitmachen'); setMenuOpen(false) }}
              className="w-full py-2.5 rounded-lg text-sm font-semibold bg-orange-500 text-white hover:bg-orange-600 transition-colors"
            >
              Mitmachen
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
