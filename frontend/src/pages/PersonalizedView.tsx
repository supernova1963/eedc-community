import { useState } from 'react'
import type { AnlageBenchmark, GesamtStatistik, TabId } from '../types'
import { REGION_NAMEN } from '../constants'
import DarkModeToggle from '../components/layout/DarkModeToggle'
import Footer from '../components/layout/Footer'
import TabNavigation from '../components/layout/TabNavigation'
import KPICard from '../components/cards/KPICard'
import RankingBadge from '../components/cards/RankingBadge'
import ComparisonChart from '../components/charts/ComparisonChart'
import AusstattungVergleich from '../sections/AusstattungVergleich'
import RegionenRanking from '../sections/RegionenRanking'
import MonatsvergleichTab from '../sections/MonatsvergleichTab'

export default function PersonalizedView({
  benchmark,
  stats,
  isDark,
  toggleDark,
}: {
  benchmark: AnlageBenchmark
  stats: GesamtStatistik
  isDark: boolean
  toggleDark: () => void
}) {
  const [activeTab, setActiveTab] = useState<TabId>('uebersicht')
  const { anlage, benchmark: bm } = benchmark
  const abweichungGesamt = ((bm.spez_ertrag_anlage - bm.spez_ertrag_durchschnitt) / bm.spez_ertrag_durchschnitt) * 100
  const abweichungRegion = ((bm.spez_ertrag_anlage - bm.spez_ertrag_region) / bm.spez_ertrag_region) * 100

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-6">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-orange-100 mb-1">EEDC Community</p>
              <h1 className="text-2xl font-bold mb-1">Dein Anlagen-Benchmark</h1>
              <p className="text-orange-100 text-sm">
                {anlage.kwp} kWp | {REGION_NAMEN[anlage.region] || anlage.region} | seit {anlage.installation_jahr}
              </p>
            </div>
            <DarkModeToggle isDark={isDark} toggle={toggleDark} />
          </div>
        </div>
      </header>

      {/* Tabs */}
      <TabNavigation activeTab={activeTab} onChange={setActiveTab} />

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Tab: Übersicht (Benchmark) */}
        {activeTab === 'uebersicht' && (
          <div className="space-y-8">
            {/* Ranking Badges */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <RankingBadge rang={bm.rang_gesamt} total={bm.anzahl_anlagen_gesamt} label="Rang Deutschland" />
              <RankingBadge rang={bm.rang_region} total={bm.anzahl_anlagen_region} label={`Rang ${REGION_NAMEN[anlage.region] || anlage.region}`} />
              <KPICard
                title="Dein Jahresertrag"
                value={bm.spez_ertrag_anlage.toFixed(0)}
                unit="kWh/kWp"
                highlight
                comparison={{ value: abweichungGesamt, label: 'vs. Ø' }}
              />
            </div>

            {/* Vergleichs-KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <KPICard
                title="Community Durchschnitt"
                value={bm.spez_ertrag_durchschnitt.toFixed(0)}
                unit="kWh/kWp"
                subtitle={`${bm.anzahl_anlagen_gesamt} Anlagen`}
              />
              <KPICard
                title={`Ø ${REGION_NAMEN[anlage.region] || anlage.region}`}
                value={bm.spez_ertrag_region.toFixed(0)}
                unit="kWh/kWp"
                subtitle={`${bm.anzahl_anlagen_region} Anlagen`}
              />
              <KPICard
                title="Dein Vorteil Region"
                value={abweichungRegion >= 0 ? `+${abweichungRegion.toFixed(0)}` : abweichungRegion.toFixed(0)}
                unit="%"
                subtitle={abweichungRegion >= 0 ? 'über dem Durchschnitt' : 'unter dem Durchschnitt'}
              />
            </div>

            {/* Monatsverlauf vs. Community */}
            <ComparisonChart anlageData={anlage.monatswerte} communityData={stats.letzte_monate} />

            {/* Ausstattung und Regionen */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AusstattungVergleich anlage={anlage} stats={stats} />
              <RegionenRanking regionen={stats.regionen} meineRegion={anlage.region} />
            </div>

            {/* Hinweis auf Details im Add-on */}
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-6 text-center">
              <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-2">
                Detaillierte Analysen im EEDC Add-on
              </h3>
              <p className="text-blue-700 dark:text-blue-400 text-sm">
                Für zeitraumbezogene Auswertungen, Komponenten-Benchmarks (Speicher, Wärmepumpe, E-Auto)
                und weitere Details nutze den Community-Vergleich in deiner lokalen EEDC-Installation.
              </p>
            </div>
          </div>
        )}

        {/* Tab: Monatsvergleich */}
        {activeTab === 'monatsvergleich' && (
          <MonatsvergleichTab />
        )}

        {/* Tab: Regionen */}
        {activeTab === 'regionen' && (
          <RegionenRanking regionen={stats.regionen} meineRegion={anlage.region} />
        )}

        {/* Tab: Impact */}
        {activeTab === 'impact' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
            <p className="text-gray-500 dark:text-gray-400">
              Die Community-Impact-Daten findest du in der{' '}
              <a href="/" className="text-orange-600 dark:text-orange-400 hover:underline">
                Community-Übersicht
              </a>.
            </p>
          </div>
        )}

        {/* Link zurück */}
        <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-8">
          <a href="/" className="text-orange-600 dark:text-orange-400 hover:underline">
            Zur Community-Übersicht
          </a>
        </div>

        <Footer />
      </main>
    </div>
  )
}
