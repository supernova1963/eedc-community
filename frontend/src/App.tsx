import { useState, useEffect } from 'react'
import Impressum from './pages/Impressum'
import Datenschutz from './pages/Datenschutz'
import CommunityOverview from './pages/CommunityOverview'
import PersonalizedView from './pages/PersonalizedView'
import { useDarkMode } from './hooks/useDarkMode'
import { getAnlageHash, getCurrentPage, navigateTo } from './utils'
import type { GesamtStatistik, CommunityGesamtwerte, AnlageBenchmark } from './types'

export default function App() {
  const [stats, setStats] = useState<GesamtStatistik | null>(null)
  const [totals, setTotals] = useState<CommunityGesamtwerte | null>(null)
  const [benchmark, setBenchmark] = useState<AnlageBenchmark | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState<'main' | 'impressum' | 'datenschutz'>(getCurrentPage())
  const [isDark, setIsDark] = useDarkMode()

  const anlageHash = getAnlageHash()
  const toggleDark = () => setIsDark(!isDark)

  // Listen for popstate events (browser back/forward)
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPage(getCurrentPage())
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  useEffect(() => {
    const loadData = async () => {
      try {
        // Stats und Totals parallel laden
        const [statsRes, totalsRes] = await Promise.all([
          fetch('/api/stats'),
          fetch('/api/statistics/global/totals'),
        ])
        if (!statsRes.ok) throw new Error('Fehler beim Laden der Statistiken')
        const statsData = await statsRes.json()
        setStats(statsData)

        if (totalsRes.ok) {
          const totalsData = await totalsRes.json()
          setTotals(totalsData)
        }

        // Wenn anlage Parameter vorhanden, Benchmark laden (immer Jahresertrag)
        if (anlageHash) {
          const benchmarkRes = await fetch(`/api/benchmark/anlage/${anlageHash}`)
          if (benchmarkRes.ok) {
            const benchmarkData = await benchmarkRes.json()
            setBenchmark(benchmarkData)
          }
          // Wenn Anlage nicht gefunden, zeigen wir einfach die Übersicht
        }

        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unbekannter Fehler')
        setLoading(false)
      }
    }

    loadData()
  }, [anlageHash])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Lade Community-Daten...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Fehler</h1>
          <p className="text-gray-600 dark:text-gray-400">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
          >
            Erneut versuchen
          </button>
        </div>
      </div>
    )
  }

  if (!stats || stats.anzahl_anlagen === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-orange-100 to-white dark:from-gray-800 dark:to-gray-900">
        <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-12">
          <div className="max-w-6xl mx-auto px-4 text-center">
            <h1 className="text-4xl font-bold mb-2">EEDC Community</h1>
            <p className="text-orange-100">Anonyme PV-Anlagen Statistiken</p>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-12">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Noch keine Daten vorhanden</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Sei der Erste, der seine PV-Anlagendaten teilt!
            </p>
            <a
              href="https://github.com/supernova1963/eedc-homeassistant"
              className="inline-block bg-gradient-to-r from-orange-500 to-amber-500 text-white font-semibold px-6 py-3 rounded-lg hover:from-orange-600 hover:to-amber-600"
              target="_blank"
              rel="noopener noreferrer"
            >
              EEDC Add-on installieren
            </a>
          </div>
        </main>
      </div>
    )
  }

  // Routing: Impressum
  if (currentPage === 'impressum') {
    return <Impressum onBack={() => navigateTo('main')} />
  }

  // Routing: Datenschutz
  if (currentPage === 'datenschutz') {
    return <Datenschutz onBack={() => navigateTo('main')} />
  }

  // Personalisierte Ansicht wenn Benchmark vorhanden
  if (benchmark) {
    return (
      <PersonalizedView
        benchmark={benchmark}
        stats={stats}
        isDark={isDark}
        toggleDark={toggleDark}
      />
    )
  }

  // Standard Community-Übersicht
  return <CommunityOverview stats={stats} totals={totals} isDark={isDark} toggleDark={toggleDark} />
}
