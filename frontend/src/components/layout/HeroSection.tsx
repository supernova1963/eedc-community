import type { ReactNode } from 'react'
import type { GesamtStatistik, CommunityGesamtwerte } from '../../types'
import DarkModeToggle from './DarkModeToggle'
import { useCountUp } from '../../hooks/useCountUp'
import { useScrolled } from '../../hooks/useScrolled'

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
  const scrolled = useScrolled(60)

  return (
    <header className={`relative flex flex-col bg-gradient-to-br from-orange-600 via-orange-500 to-amber-400 text-white overflow-hidden transition-all duration-700 ease-in-out ${scrolled ? 'min-h-[38.2vh]' : 'min-h-[61.8vh]'}`}>
      {/* Decorative sun glows */}
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-amber-300 rounded-full blur-3xl opacity-20 pointer-events-none" />
      <div className="absolute -bottom-12 -left-12 w-56 h-56 bg-orange-700 rounded-full blur-3xl opacity-20 pointer-events-none" />

      <div className="relative flex-1 flex flex-col max-w-6xl mx-auto px-4 w-full pt-4 pb-8">
        {/* Dark mode toggle */}
        <div className="flex justify-end mb-4">
          <DarkModeToggle isDark={isDark} toggle={toggleDark} />
        </div>

        {/* Goldener Schnitt: oberer Block (61,8%) = Titel zentriert, unterer Block (38,2%) = Stats + CTA */}
        <div className="flex-1 flex flex-col">

          {/* Oberer Block – Titel schwebt vertikal zentriert */}
          <div className="flex-[1.618] flex flex-col items-center justify-center text-center py-4">
            {/* Emoji + Tagline: ausgeblendet wenn gescrollt */}
            <div className={`transition-all duration-500 overflow-hidden ${scrolled ? 'max-h-0 opacity-0 mb-0' : 'max-h-24 opacity-100 mb-4'}`}>
              <div className="text-5xl select-none">☀️</div>
            </div>
            <h1 className={`font-bold tracking-tight transition-all duration-500 ${scrolled ? 'text-2xl md:text-3xl mb-1' : 'text-4xl md:text-5xl mb-3'}`}>
              EEDC Community
            </h1>
            <div className={`transition-all duration-500 overflow-hidden ${scrolled ? 'max-h-0 opacity-0' : 'max-h-16 opacity-100'}`}>
              <p className="text-lg md:text-xl text-orange-100 max-w-lg mx-auto leading-relaxed">
                Echte Daten echter PV-Anlagen.<br />
                Anonym. Transparent. Vergleichbar.
              </p>
            </div>
          </div>

          {/* Unterer Block – Stat-Boxen und CTA */}
          <div className="flex-1">
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

        </div>
      </div>
    </header>
  )
}
