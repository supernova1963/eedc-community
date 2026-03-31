import type { ReactNode } from 'react'
import type { GesamtStatistik, CommunityGesamtwerte } from '../../types'
import DarkModeToggle from './DarkModeToggle'
import { useCountUp } from '../../hooks/useCountUp'

function StatBox({ icon, label, children }: { icon: string; label: string; children: ReactNode }) {
  return (
    <div className="bg-white/15 backdrop-blur-sm rounded-xl border border-white/20 p-4 text-center">
      <div className="text-2xl mb-1 select-none">{icon}</div>
      <div className="text-2xl md:text-3xl font-bold leading-tight">{children}</div>
      <div className="text-sm text-orange-100 mt-1">{label}</div>
    </div>
  )
}

/** Counts up to `kwh`, keeps unit stable throughout the animation */
function EnergyCounter({ kwh }: { kwh: number }) {
  const isGWh = kwh >= 1_000_000
  const isMWh = kwh >= 10_000
  const divisor = isGWh ? 1_000_000 : isMWh ? 1_000 : 1
  const unit = isGWh ? 'GWh' : isMWh ? 'MWh' : 'kWh'
  // Count in tenths for one decimal of precision
  const scaledTarget = Math.round((kwh / divisor) * 10)
  const count = useCountUp(scaledTarget)
  return <>{(count / 10).toFixed(1)} {unit}</>
}

/** Counts up CO₂ in kg, displays as tons with one decimal */
function CO2Counter({ kg }: { kg: number }) {
  const scaledTarget = Math.round(kg / 100) // tenths of a ton
  const count = useCountUp(scaledTarget)
  return <>{(count / 10).toFixed(1)} t</>
}

/** Simple integer count-up with German locale */
function IntCounter({ value }: { value: number }) {
  const count = useCountUp(value)
  return <>{count.toLocaleString('de-DE')}</>
}

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

  return (
    <header className="relative bg-gradient-to-br from-orange-600 via-orange-500 to-amber-400 text-white overflow-hidden">
      {/* Decorative sun glows */}
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-amber-300 rounded-full blur-3xl opacity-20 pointer-events-none" />
      <div className="absolute -bottom-12 -left-12 w-56 h-56 bg-orange-700 rounded-full blur-3xl opacity-20 pointer-events-none" />

      <div className="relative max-w-6xl mx-auto px-4 pt-5 pb-12">
        {/* Dark mode toggle */}
        <div className="flex justify-end mb-6">
          <DarkModeToggle isDark={isDark} toggle={toggleDark} />
        </div>

        {/* Title block */}
        <div className="text-center mb-10">
          <div className="text-5xl mb-4 select-none">☀️</div>
          <h1 className="text-4xl md:text-5xl font-bold mb-3 tracking-tight">
            EEDC Community
          </h1>
          <p className="text-lg md:text-xl text-orange-100 max-w-lg mx-auto leading-relaxed">
            Echte Daten echter PV-Anlagen.<br />
            Anonym. Transparent. Vergleichbar.
          </p>
        </div>

        {/* Animated stat boxes */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-10">
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
