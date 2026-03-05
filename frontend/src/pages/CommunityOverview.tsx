import { useState } from 'react'
import type { GesamtStatistik, CommunityGesamtwerte, TabId } from '../types'
import DarkModeToggle from '../components/layout/DarkModeToggle'
import Footer from '../components/layout/Footer'
import TabNavigation from '../components/layout/TabNavigation'
import KPICard from '../components/cards/KPICard'
import TrendChart from '../components/charts/TrendChart'
import TopPerformer from '../sections/TopPerformer'
import CommunityHighlights from '../sections/CommunityHighlights'
import CommunityImpact from '../sections/CommunityImpact'
import AusstattungsVerteilung from '../sections/AusstattungsVerteilung'
import GroessenVerteilung from '../sections/GroessenVerteilung'
import RegionenRanking from '../sections/RegionenRanking'
import MonatsverlaufChart from '../components/charts/MonatsverlaufChart'
import MonatsvergleichTab from '../sections/MonatsvergleichTab'

export default function CommunityOverview({ stats, totals, isDark, toggleDark }: { stats: GesamtStatistik; totals: CommunityGesamtwerte | null; isDark: boolean; toggleDark: () => void }) {
  const [activeTab, setActiveTab] = useState<TabId>('uebersicht')

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-8">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-end mb-3">
            <DarkModeToggle isDark={isDark} toggle={toggleDark} />
          </div>
          <div className="text-center">
            <h1 className="text-3xl font-bold mb-1">EEDC Community</h1>
            <p className="text-lg text-orange-100">
              {stats.anzahl_anlagen} PV-Anlagen teilen ihre Daten
            </p>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <TabNavigation activeTab={activeTab} onChange={setActiveTab} />

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Tab: Übersicht */}
        {activeTab === 'uebersicht' && (
          <div className="space-y-8">
            {/* Hero KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
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

            {/* Highlights */}
            <CommunityHighlights stats={stats} />

            {/* Trend und Top-Performer */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <TrendChart monate={stats.letzte_monate} />
              </div>
              <TopPerformer regionen={stats.regionen} />
            </div>

            {/* Ausstattung und Größen */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AusstattungsVerteilung stats={stats} />
              <GroessenVerteilung stats={stats} />
            </div>

            {/* Call to Action */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Wie schneidet deine Anlage ab?
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Mit dem EEDC Add-on für Home Assistant kannst du deine PV-Anlage anonym
                mit der Community vergleichen.
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
          </div>
        )}

        {/* Tab: Monatsvergleich */}
        {activeTab === 'monatsvergleich' && (
          <MonatsvergleichTab />
        )}

        {/* Tab: Regionen */}
        {activeTab === 'regionen' && (
          <div className="space-y-8">
            <RegionenRanking regionen={stats.regionen} />
            <MonatsverlaufChart monate={stats.letzte_monate} />
          </div>
        )}

        {/* Tab: Impact */}
        {activeTab === 'impact' && totals && (
          <CommunityImpact totals={totals} />
        )}
        {activeTab === 'impact' && !totals && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
            <p className="text-gray-500 dark:text-gray-400">Impact-Daten werden geladen...</p>
          </div>
        )}

        {/* Footer */}
        <Footer />
      </main>
    </div>
  )
}
