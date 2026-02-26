import type { AnlageBenchmark, GesamtStatistik } from '../types'
import { REGION_NAMEN } from '../constants'
import DarkModeToggle from '../components/layout/DarkModeToggle'
import Footer from '../components/layout/Footer'
import KPICard from '../components/cards/KPICard'
import RankingBadge from '../components/cards/RankingBadge'
import ComparisonChart from '../components/charts/ComparisonChart'
import AusstattungVergleich from '../sections/AusstattungVergleich'
import RegionenRanking from '../sections/RegionenRanking'

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
  const { anlage, benchmark: bm } = benchmark
  const abweichungGesamt = ((bm.spez_ertrag_anlage - bm.spez_ertrag_durchschnitt) / bm.spez_ertrag_durchschnitt) * 100
  const abweichungRegion = ((bm.spez_ertrag_anlage - bm.spez_ertrag_region) / bm.spez_ertrag_region) * 100

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-8">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-orange-100 mb-1">EEDC Community</p>
              <h1 className="text-3xl font-bold mb-2">Dein Anlagen-Benchmark</h1>
              <p className="text-orange-100">
                {anlage.kwp} kWp | {REGION_NAMEN[anlage.region] || anlage.region} | seit {anlage.installation_jahr}
              </p>
              <p className="text-orange-200 text-sm mt-2">
                Vergleichszeitraum: Jahresertrag {benchmark.vergleichs_jahr}
              </p>
            </div>
            <DarkModeToggle isDark={isDark} toggle={toggleDark} />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Ranking Badges */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
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

        {/* Dein Monatsverlauf vs. Community */}
        <div className="mb-8">
          <ComparisonChart anlageData={anlage.monatswerte} communityData={stats.letzte_monate} />
        </div>

        {/* Ausstattung und Regionen */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <AusstattungVergleich anlage={anlage} stats={stats} />
          <RegionenRanking regionen={stats.regionen} meineRegion={anlage.region} />
        </div>

        {/* Hinweis auf Details im Add-on */}
        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-6 text-center mb-8">
          <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-2">
            Detaillierte Analysen im EEDC Add-on
          </h3>
          <p className="text-blue-700 dark:text-blue-400 text-sm">
            Für zeitraumbezogene Auswertungen, Komponenten-Benchmarks (Speicher, Wärmepumpe, E-Auto)
            und weitere Details nutze den Community-Vergleich in deiner lokalen EEDC-Installation.
          </p>
        </div>

        {/* Link zurück */}
        <div className="text-center text-sm text-gray-500 dark:text-gray-400">
          <a href="/" className="text-orange-600 dark:text-orange-400 hover:underline">
            ← Zur Community-Übersicht
          </a>
        </div>

        {/* Footer */}
        <Footer />
      </main>
    </div>
  )
}
