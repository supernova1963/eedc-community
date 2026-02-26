import type { GesamtStatistik, CommunityGesamtwerte } from '../types'
import DarkModeToggle from '../components/layout/DarkModeToggle'
import Footer from '../components/layout/Footer'
import KPICard from '../components/cards/KPICard'
import TrendChart from '../components/charts/TrendChart'
import MonatsverlaufChart from '../components/charts/MonatsverlaufChart'
import CommunityHighlights from '../sections/CommunityHighlights'
import CommunityImpact from '../sections/CommunityImpact'
import TopPerformer from '../sections/TopPerformer'
import AusstattungsVerteilung from '../sections/AusstattungsVerteilung'
import GroessenVerteilung from '../sections/GroessenVerteilung'
import RegionenRanking from '../sections/RegionenRanking'

export default function CommunityOverview({ stats, totals, isDark, toggleDark }: { stats: GesamtStatistik; totals: CommunityGesamtwerte | null; isDark: boolean; toggleDark: () => void }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-end mb-4">
            <DarkModeToggle isDark={isDark} toggle={toggleDark} />
          </div>
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-2">EEDC Community</h1>
            <p className="text-xl text-orange-100">
              {stats.anzahl_anlagen} PV-Anlagen teilen ihre Daten
            </p>
            <p className="text-orange-200 mt-2">
              Vergleiche deine Anlage anonym mit anderen aus der Community
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Hero KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <KPICard
            title="PV-Anlagen"
            value={stats.anzahl_anlagen}
            subtitle={`${stats.anzahl_monatswerte} Monatswerte`}
            highlight
          />
          <KPICard
            title="Ø Jahresertrag"
            value={Math.round(stats.durchschnitt_spez_ertrag_jahr)}
            unit="kWh/kWp"
            subtitle="Community-Durchschnitt"
          />
          <KPICard
            title="Ø Anlagengröße"
            value={stats.durchschnitt_kwp.toFixed(1)}
            unit="kWp"
          />
          <KPICard
            title="Ø Speicher"
            value={stats.durchschnitt_speicher_kwh?.toFixed(1) || '-'}
            unit="kWh"
            subtitle="bei Anlagen mit Speicher"
          />
        </div>

        {/* Community Impact - Gesamtwerte */}
        {totals && (
          <div className="mb-8">
            <CommunityImpact totals={totals} />
          </div>
        )}

        {/* Highlights */}
        <div className="mb-8">
          <CommunityHighlights stats={stats} />
        </div>

        {/* Trend und Top-Performer */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <TrendChart monate={stats.letzte_monate} />
          </div>
          <TopPerformer regionen={stats.regionen} />
        </div>

        {/* Verteilungen und Regionen */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <AusstattungsVerteilung stats={stats} />
          <GroessenVerteilung stats={stats} />
          <RegionenRanking regionen={stats.regionen} />
        </div>

        {/* Monatsverlauf (volle Breite) */}
        <div className="mb-8">
          <MonatsverlaufChart monate={stats.letzte_monate} />
        </div>

        {/* Call to Action */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Wie schneidet deine Anlage ab?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Mit dem EEDC Add-on für Home Assistant kannst du deine PV-Anlage anonym
            mit der Community vergleichen und sehen, wo du im Ranking stehst.
          </p>
          <a
            href="https://github.com/supernova1963/eedc-homeassistant"
            className="inline-block bg-gradient-to-r from-orange-500 to-amber-500 text-white font-semibold px-8 py-3 rounded-lg hover:from-orange-600 hover:to-amber-600 transition-all"
            target="_blank"
            rel="noopener noreferrer"
          >
            EEDC Add-on installieren
          </a>
        </div>

        {/* Footer */}
        <Footer />
      </main>
    </div>
  )
}
