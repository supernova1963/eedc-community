import { useState } from 'react'
import type { GesamtStatistik, CommunityGesamtwerte, TabId } from '../types'
import HeroSection from '../components/layout/HeroSection'
import FadeIn from '../components/layout/FadeIn'
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
      <HeroSection stats={stats} totals={totals} isDark={isDark} toggleDark={toggleDark} />

      {/* Tabs */}
      <TabNavigation activeTab={activeTab} onChange={setActiveTab} />

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Tab: Übersicht */}
        {activeTab === 'uebersicht' && (
          <div className="space-y-8">
            {/* KPIs – gestaffelt von links/rechts/unten */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <FadeIn delay={0} from="left">
                <KPICard
                  title="Ø Jahresertrag"
                  value={Math.round(stats.durchschnitt_spez_ertrag_jahr)}
                  unit="kWh/kWp"
                  subtitle="Community-Durchschnitt"
                />
              </FadeIn>
              <FadeIn delay={100}>
                <KPICard
                  title="Ø Anlagengröße"
                  value={stats.durchschnitt_kwp.toFixed(1)}
                  unit="kWp"
                />
              </FadeIn>
              <FadeIn delay={200} from="right">
                <KPICard
                  title="Ø Speicher"
                  value={stats.durchschnitt_speicher_kwh?.toFixed(1) || '-'}
                  unit="kWh"
                  subtitle="bei Anlagen mit Speicher"
                />
              </FadeIn>
            </div>

            {/* Highlights */}
            <FadeIn>
              <CommunityHighlights stats={stats} />
            </FadeIn>

            {/* Trend und Top-Performer */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <FadeIn delay={0} from="left" className="lg:col-span-2">
                <TrendChart monate={stats.letzte_monate} />
              </FadeIn>
              <FadeIn delay={150} from="right">
                <TopPerformer regionen={stats.regionen} />
              </FadeIn>
            </div>

            {/* Ausstattung und Größen */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FadeIn delay={0} from="left">
                <AusstattungsVerteilung stats={stats} />
              </FadeIn>
              <FadeIn delay={150} from="right">
                <GroessenVerteilung stats={stats} />
              </FadeIn>
            </div>
          </div>
        )}

        {/* Tab: Monatsvergleich */}
        {activeTab === 'monatsvergleich' && (
          <FadeIn>
            <MonatsvergleichTab />
          </FadeIn>
        )}

        {/* Tab: Regionen */}
        {activeTab === 'regionen' && (
          <div className="space-y-8">
            <FadeIn from="left">
              <RegionenRanking regionen={stats.regionen} />
            </FadeIn>
            <FadeIn delay={100}>
              <MonatsverlaufChart monate={stats.letzte_monate} />
            </FadeIn>
          </div>
        )}

        {/* Tab: Impact */}
        {activeTab === 'impact' && totals && (
          <FadeIn>
            <CommunityImpact totals={totals} />
          </FadeIn>
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
