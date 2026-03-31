import type { ReactNode } from 'react'
import type { GesamtStatistik, CommunityGesamtwerte } from '../../types'
import DarkModeToggle from './DarkModeToggle'
import { useCountUp } from '../../hooks/useCountUp'

function StatBox({ icon, label, children }: { icon: string; label: string; children: ReactNode }) {
  return (
    <div className="bg-white/15 backdrop-blur-sm rounded-xl border border-white/20 p-2 md:p-4 text-center">
      <div className="text-base md:text-2xl mb-0.5 md:mb-1 select-none">{icon}</div>
      <div className="text-sm md:text-2xl lg:text-3xl font-bold leading-tight">{children}</div>
      <div className="text-xs text-orange-100 mt-0.5 md:mt-1">{label}</div>
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

export default function HeroSection({
  stats,
  totals,
  isDark,
  toggleDark,
  onMitmachen,
}: {
  stats: GesamtStatistik
  totals: CommunityGesamtwerte | null
  isDark: boolean
  toggleDark: () => void
  onMitmachen?: () => void
}) {
  const haushalte = totals ? Math.round(totals.pv_erzeugung_kwh / 5000) : 0

  return (
    <header className="relative min-h-[38.2vh] flex flex-col bg-gradient-to-br from-orange-600 via-orange-500 to-amber-400 text-white overflow-hidden">
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-amber-300 rounded-full blur-3xl opacity-20 pointer-events-none" />
      <div className="absolute -bottom-12 -left-12 w-56 h-56 bg-orange-700 rounded-full blur-3xl opacity-20 pointer-events-none" />

      <div className="relative flex-1 flex flex-col max-w-6xl mx-auto px-4 w-full pt-2 md:pt-4 pb-4 md:pb-8">
        {/* Dark-Mode-Toggle */}
        <div className="flex justify-end mb-1 md:mb-4">
          <DarkModeToggle isDark={isDark} toggle={toggleDark} />
        </div>

        {/* Titel */}
        <div className="flex-1 flex flex-col items-center justify-center text-center py-1 md:py-4">
          <div className="text-3xl md:text-5xl mb-1 md:mb-4 select-none">☀️</div>
          <h1 className="text-2xl md:text-4xl lg:text-5xl font-bold mb-1 md:mb-3 tracking-tight">
            EEDC Community
          </h1>
          <p className="text-xs md:text-lg lg:text-xl text-orange-100 max-w-lg mx-auto leading-relaxed">
            Echte Daten echter PV-Anlagen.
            <span className="hidden sm:inline"><br /></span>
            <span className="sm:hidden"> </span>
            Anonym. Transparent. Vergleichbar.
          </p>
        </div>

        {/* Stat-Boxen – auf Mobile kompakter (ca. halbe Höhe) */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4 mb-2 md:mb-6">
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
          <p className="text-orange-100 text-xs md:text-sm mb-1.5 md:mb-3 hidden sm:block">
            Nutzt du EEDC? Vergleiche deine Anlage anonym mit der Community.
          </p>
          <button
            type="button"
            onClick={onMitmachen}
            className="bg-white text-orange-600 font-semibold px-4 md:px-6 py-1.5 md:py-2.5 text-sm md:text-base rounded-lg hover:bg-orange-50 transition-colors shadow-md"
          >
            Mitmachen →
          </button>
        </div>
      </div>
    </header>
  )
}
