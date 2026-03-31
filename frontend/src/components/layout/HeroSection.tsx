import type { ReactNode } from 'react'
import { useMemo } from 'react'
import type { GesamtStatistik, CommunityGesamtwerte } from '../../types'
import { MONATE, REGION_NAMEN } from '../../constants'
import DarkModeToggle from './DarkModeToggle'
import { useCountUp } from '../../hooks/useCountUp'

// ── Sub-Komponenten ──────────────────────────────────────────────────────────

function StatBox({ icon, label, children }: { icon: string; label: string; children: ReactNode }) {
  return (
    <div className="bg-white/15 backdrop-blur-sm rounded-xl border border-white/20 p-4 text-center">
      <div className="text-2xl mb-1 select-none">{icon}</div>
      <div className="text-2xl md:text-3xl font-bold leading-tight">{children}</div>
      <div className="text-sm text-orange-100 mt-1">{label}</div>
    </div>
  )
}

function EnergyCounter({ kwh }: { kwh: number }) {
  const isGWh = kwh >= 1_000_000
  const isMWh = kwh >= 10_000
  const divisor = isGWh ? 1_000_000 : isMWh ? 1_000 : 1
  const unit = isGWh ? 'GWh' : isMWh ? 'MWh' : 'kWh'
  const count = useCountUp(Math.round((kwh / divisor) * 10))
  return <>{(count / 10).toFixed(1)} {unit}</>
}

function CO2Counter({ kg }: { kg: number }) {
  const count = useCountUp(Math.round(kg / 100))
  return <>{(count / 10).toFixed(1)} t</>
}

function IntCounter({ value }: { value: number }) {
  const count = useCountUp(value)
  return <>{count.toLocaleString('de-DE')}</>
}

function Pill({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 bg-white/15 backdrop-blur-sm border border-white/20 rounded-full px-3 py-1 text-xs sm:text-sm font-medium whitespace-nowrap">
      {children}
    </span>
  )
}

function seasonEmoji(monat: number) {
  if (monat <= 2 || monat === 12) return '❄️'
  if (monat <= 5) return '🌱'
  if (monat <= 8) return '☀️'
  return '🍂'
}

// ── Haupt-Komponente ─────────────────────────────────────────────────────────

export default function HeroSection({
  stats,
  totals,
  isDark,
  toggleDark,
}: {
  stats: GesamtStatistik
  totals: CommunityGesamtwerte | null
  isDark: boolean
  toggleDark: () => void
}) {
  const haushalte = totals ? Math.round(totals.pv_erzeugung_kwh / 5000) : 0

  const monthly = useMemo(() => {
    if (stats.letzte_monate.length === 0) return null
    const sorted = [...stats.letzte_monate].sort((a, b) =>
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

  return (
    <header className="relative min-h-[38.2vh] flex flex-col bg-gradient-to-br from-orange-600 via-orange-500 to-amber-400 text-white overflow-hidden">
      {/* Dekorative Sonnen-Glows */}
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-amber-300 rounded-full blur-3xl opacity-20 pointer-events-none" />
      <div className="absolute -bottom-12 -left-12 w-56 h-56 bg-orange-700 rounded-full blur-3xl opacity-20 pointer-events-none" />

      <div className="relative flex-1 flex flex-col max-w-6xl mx-auto px-4 w-full pt-4 pb-8">
        {/* Dark-Mode-Toggle */}
        <div className="flex justify-end mb-4">
          <DarkModeToggle isDark={isDark} toggle={toggleDark} />
        </div>

        {/* Titel – füllt den verfügbaren Raum (oberer goldener Block) */}
        <div className="flex-1 flex flex-col items-center justify-center text-center py-4">
          <div className="text-5xl mb-4 select-none">☀️</div>
          <h1 className="text-4xl md:text-5xl font-bold mb-3 tracking-tight">
            EEDC Community
          </h1>
          <p className="text-lg md:text-xl text-orange-100 max-w-lg mx-auto leading-relaxed">
            Echte Daten echter PV-Anlagen.<br />
            Anonym. Transparent. Vergleichbar.
          </p>
        </div>

        {/* Monats-Highlights – immer sichtbar, flex-wrap für Mobile */}
        {monthly && (
          <div className="flex flex-wrap justify-center gap-2 mb-6">
            <Pill>
              {seasonEmoji(monthly.latest.monat)}{' '}
              {MONATE[monthly.latest.monat - 1]} {monthly.latest.jahr}
            </Pill>
            <Pill>
              Ø {monthly.latest.durchschnitt_spez_ertrag.toFixed(1)} kWh/kWp
            </Pill>
            {monthly.trendPct !== null && (
              <Pill>
                {monthly.trendPct >= 0 ? '▲' : '▼'} {Math.abs(monthly.trendPct).toFixed(0)}%
              </Pill>
            )}
            {monthly.topRegion && (
              <Pill>
                🏆 {REGION_NAMEN[monthly.topRegion.region] || monthly.topRegion.region}
              </Pill>
            )}
          </div>
        )}

        {/* Stat-Boxen – unterer goldener Block */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-6">
          <StatBox icon="⚡" label="PV-Anlagen">
            <IntCounter value={stats.anzahl_anlagen} />
          </StatBox>
          <StatBox icon="☀️" label="erzeugte Energie">
            {totals ? <EnergyCounter kwh={totals.pv_erzeugung_kwh} /> : '–'}
          </StatBox>
          <StatBox icon="🌿" label="CO₂ vermieden">
            {totals ? <CO2Counter kg={totals.co2_vermieden_kg} /> : '–'}
          </StatBox>
          <StatBox icon="🏠" label="Haushalte versorgt">
            {totals ? <IntCounter value={haushalte} /> : '–'}
          </StatBox>
        </div>

        {/* CTA */}
        <div className="text-center">
          <p className="text-orange-100 text-sm mb-3">
            Nutzt du EEDC? Vergleiche deine Anlage anonym mit der Community.
          </p>
          <a
            href="https://github.com/supernova1963/eedc-homeassistant"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-white text-orange-600 font-semibold px-6 py-2.5 rounded-lg hover:bg-orange-50 transition-colors shadow-md"
          >
            EEDC Add-on installieren →
          </a>
        </div>
      </div>
    </header>
  )
}
