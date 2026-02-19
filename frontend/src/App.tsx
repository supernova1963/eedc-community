import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from 'recharts'

// Types
interface RegionStatistik {
  region: string
  anzahl_anlagen: number
  durchschnitt_kwp: number
  durchschnitt_spez_ertrag: number
  durchschnitt_autarkie: number | null
  anteil_mit_speicher: number
  anteil_mit_waermepumpe: number
  anteil_mit_eauto: number
}

interface MonatsStatistik {
  jahr: number
  monat: number
  anzahl_anlagen: number
  durchschnitt_ertrag_kwh: number
  durchschnitt_spez_ertrag: number
  median_spez_ertrag: number
  min_spez_ertrag: number
  max_spez_ertrag: number
}

interface GesamtStatistik {
  anzahl_anlagen: number
  anzahl_monatswerte: number
  durchschnitt_kwp: number
  durchschnitt_speicher_kwh: number | null
  durchschnitt_spez_ertrag_jahr: number
  regionen: RegionStatistik[]
  letzte_monate: MonatsStatistik[]
}

interface Monatswert {
  jahr: number
  monat: number
  ertrag_kwh: number
  einspeisung_kwh: number | null
  netzbezug_kwh: number | null
  autarkie_prozent: number | null
  eigenverbrauch_prozent: number | null
  spez_ertrag_kwh_kwp: number | null
}

interface AnlageData {
  anlage_hash: string
  region: string
  kwp: number
  ausrichtung: string
  neigung_grad: number
  speicher_kwh: number | null
  installation_jahr: number
  hat_waermepumpe: boolean
  hat_eauto: boolean
  hat_wallbox: boolean
  monatswerte: Monatswert[]
}

interface BenchmarkData {
  spez_ertrag_anlage: number
  spez_ertrag_durchschnitt: number
  spez_ertrag_region: number
  rang_gesamt: number
  anzahl_anlagen_gesamt: number
  rang_region: number
  anzahl_anlagen_region: number
}

interface AnlageBenchmark {
  anlage: AnlageData
  benchmark: BenchmarkData
  vergleichs_jahr: number
}

// Konstanten
const REGION_NAMEN: Record<string, string> = {
  BW: 'Baden-Württemberg',
  BY: 'Bayern',
  BE: 'Berlin',
  BB: 'Brandenburg',
  HB: 'Bremen',
  HH: 'Hamburg',
  HE: 'Hessen',
  MV: 'Mecklenburg-Vorpommern',
  NI: 'Niedersachsen',
  NW: 'Nordrhein-Westfalen',
  RP: 'Rheinland-Pfalz',
  SL: 'Saarland',
  SN: 'Sachsen',
  ST: 'Sachsen-Anhalt',
  SH: 'Schleswig-Holstein',
  TH: 'Thüringen',
  AT: 'Österreich',
  CH: 'Schweiz',
}

const MONATE = [
  'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
  'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'
]

// Helper: URL Parameter lesen
function getAnlageHash(): string | null {
  const params = new URLSearchParams(window.location.search)
  return params.get('anlage')
}

// Komponenten
function KPICard({ title, value, unit, subtitle, highlight, comparison }: {
  title: string
  value: string | number
  unit?: string
  subtitle?: string
  highlight?: boolean
  comparison?: { value: number; label: string }
}) {
  return (
    <div className={`rounded-lg shadow p-6 ${highlight ? 'bg-gradient-to-br from-orange-500 to-amber-500 text-white' : 'bg-white'}`}>
      <h3 className={`text-sm font-medium ${highlight ? 'text-orange-100' : 'text-gray-500'}`}>{title}</h3>
      <p className={`mt-2 text-3xl font-bold ${highlight ? 'text-white' : 'text-gray-900'}`}>
        {value}
        {unit && <span className={`text-lg font-normal ml-1 ${highlight ? 'text-orange-100' : 'text-gray-500'}`}>{unit}</span>}
      </p>
      {comparison && (
        <p className={`mt-1 text-sm font-medium ${comparison.value >= 0 ? 'text-green-400' : 'text-red-300'}`}>
          {comparison.value >= 0 ? '▲' : '▼'} {Math.abs(comparison.value).toFixed(0)}% {comparison.label}
        </p>
      )}
      {subtitle && <p className={`mt-1 text-sm ${highlight ? 'text-orange-100' : 'text-gray-500'}`}>{subtitle}</p>}
    </div>
  )
}

function RankingBadge({ rang, total, label }: { rang: number; total: number; label: string }) {
  const prozent = ((total - rang + 1) / total) * 100
  const medalColor = rang === 1 ? 'text-yellow-500' : rang === 2 ? 'text-gray-400' : rang === 3 ? 'text-amber-600' : 'text-gray-600'
  const medal = rang <= 3 ? ['🥇', '🥈', '🥉'][rang - 1] : `#${rang}`

  return (
    <div className="bg-white rounded-lg shadow p-6 text-center">
      <p className="text-sm text-gray-500 mb-2">{label}</p>
      <p className={`text-4xl font-bold ${medalColor}`}>{medal}</p>
      <p className="text-sm text-gray-500 mt-2">von {total} Anlagen</p>
      <div className="mt-3 bg-gray-200 rounded-full h-2">
        <div
          className="bg-gradient-to-r from-orange-500 to-amber-500 h-2 rounded-full"
          style={{ width: `${prozent}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">Top {(100 - prozent + 1).toFixed(0)}%</p>
    </div>
  )
}

function ComparisonChart({ anlageData, communityData }: {
  anlageData: Monatswert[]
  communityData: MonatsStatistik[]
}) {
  // Kombiniere Daten für Chart
  const data = communityData.slice().reverse().map(cm => {
    const anlageMonat = anlageData.find(a => a.jahr === cm.jahr && a.monat === cm.monat)
    return {
      name: `${MONATE[cm.monat - 1]} ${cm.jahr.toString().slice(2)}`,
      community: cm.durchschnitt_spez_ertrag,
      anlage: anlageMonat?.spez_ertrag_kwh_kwp || null,
    }
  })

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Dein Ertrag vs. Community-Durchschnitt</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 'auto']} />
          <Tooltip formatter={(value: number) => value ? `${value.toFixed(1)} kWh/kWp` : '-'} />
          <Legend />
          <Line
            type="monotone"
            dataKey="anlage"
            stroke="#f59e0b"
            strokeWidth={3}
            name="Deine Anlage"
            dot={{ fill: '#f59e0b' }}
          />
          <Line
            type="monotone"
            dataKey="community"
            stroke="#9ca3af"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Community Ø"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function AusstattungVergleich({ anlage, stats }: { anlage: AnlageData; stats: GesamtStatistik }) {
  // Community-Durchschnitte berechnen
  const totalAnlagen = stats.regionen.reduce((sum, r) => sum + r.anzahl_anlagen, 0)
  const avgSpeicher = stats.regionen.reduce((sum, r) => sum + r.anteil_mit_speicher * r.anzahl_anlagen, 0) / totalAnlagen
  const avgWP = stats.regionen.reduce((sum, r) => sum + r.anteil_mit_waermepumpe * r.anzahl_anlagen, 0) / totalAnlagen
  const avgEAuto = stats.regionen.reduce((sum, r) => sum + r.anteil_mit_eauto * r.anzahl_anlagen, 0) / totalAnlagen

  const items = [
    { name: 'PV-Anlage', du: `${anlage.kwp.toFixed(1)} kWp`, community: `${stats.durchschnitt_kwp.toFixed(1)} kWp`, hatDu: true },
    { name: 'Speicher', du: anlage.speicher_kwh ? `${anlage.speicher_kwh.toFixed(1)} kWh` : '-', community: `${Math.round(avgSpeicher)}% haben`, hatDu: !!anlage.speicher_kwh },
    { name: 'Wärmepumpe', du: anlage.hat_waermepumpe ? '✓' : '-', community: `${Math.round(avgWP)}% haben`, hatDu: anlage.hat_waermepumpe },
    { name: 'E-Auto', du: anlage.hat_eauto ? '✓' : '-', community: `${Math.round(avgEAuto)}% haben`, hatDu: anlage.hat_eauto },
    { name: 'Wallbox', du: anlage.hat_wallbox ? '✓' : '-', community: '-', hatDu: anlage.hat_wallbox },
  ]

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Deine Ausstattung</h3>
      <div className="space-y-3">
        {items.map(item => (
          <div key={item.name} className="flex items-center justify-between py-2 border-b last:border-0">
            <span className="font-medium text-gray-700">{item.name}</span>
            <div className="flex items-center gap-4">
              <span className={`font-semibold ${item.hatDu ? 'text-green-600' : 'text-gray-400'}`}>
                {item.du}
              </span>
              <span className="text-sm text-gray-400">|</span>
              <span className="text-sm text-gray-500">Ø {item.community}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function MonatsverlaufChart({ monate }: { monate: MonatsStatistik[] }) {
  const data = [...monate].reverse().map(m => ({
    name: `${MONATE[m.monat - 1]} ${m.jahr.toString().slice(2)}`,
    durchschnitt: m.durchschnitt_spez_ertrag,
    min: m.min_spez_ertrag,
    max: m.max_spez_ertrag,
    anlagen: m.anzahl_anlagen,
  }))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">
        Community-Ertrag (kWh/kWp) - Letzte 12 Monate
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 'auto']} />
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value.toFixed(1)} kWh/kWp`,
              name === 'durchschnitt' ? 'Ø Ertrag' : name === 'max' ? 'Maximum' : 'Minimum'
            ]}
          />
          <Bar dataKey="durchschnitt" fill="#f59e0b" name="Ø Ertrag" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function RegionenRanking({ regionen, meineRegion }: { regionen: RegionStatistik[]; meineRegion?: string }) {
  const sorted = [...regionen].sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)
  const maxErtrag = Math.max(...sorted.map(r => r.durchschnitt_spez_ertrag))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Regionen-Ranking (Jahresertrag)</h3>
      <div className="space-y-3">
        {sorted.map((r, idx) => {
          const isHighlight = r.region === meineRegion
          const width = (r.durchschnitt_spez_ertrag / maxErtrag) * 100
          return (
            <div key={r.region} className={`rounded-lg p-3 ${isHighlight ? 'bg-orange-50 ring-2 ring-orange-500' : ''}`}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-gray-400">#{idx + 1}</span>
                  <span className={`font-medium ${isHighlight ? 'text-orange-700' : 'text-gray-700'}`}>
                    {REGION_NAMEN[r.region] || r.region}
                    {isHighlight && <span className="ml-2 text-xs bg-orange-500 text-white px-2 py-0.5 rounded-full">DEINE REGION</span>}
                  </span>
                </div>
                <span className="font-bold text-gray-900">{r.durchschnitt_spez_ertrag.toFixed(0)} kWh/kWp</span>
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${isHighlight ? 'bg-orange-500' : 'bg-gray-400'}`}
                  style={{ width: `${width}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{r.anzahl_anlagen} Anlagen</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function CommunityHighlights({ stats }: { stats: GesamtStatistik }) {
  const totalSpeicher = stats.regionen.reduce((sum, r) => sum + (r.anteil_mit_speicher / 100) * r.anzahl_anlagen, 0)
  const totalWP = stats.regionen.reduce((sum, r) => sum + (r.anteil_mit_waermepumpe / 100) * r.anzahl_anlagen, 0)
  const totalEAuto = stats.regionen.reduce((sum, r) => sum + (r.anteil_mit_eauto / 100) * r.anzahl_anlagen, 0)
  const topRegion = [...stats.regionen].sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)[0]

  return (
    <div className="bg-gradient-to-r from-orange-500 to-amber-500 rounded-lg shadow p-6 text-white">
      <h3 className="text-lg font-semibold mb-4">Community Highlights</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-3xl font-bold">{Math.round(totalSpeicher)}</p>
          <p className="text-sm text-orange-100">mit Speicher</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold">{Math.round(totalWP)}</p>
          <p className="text-sm text-orange-100">mit Wärmepumpe</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold">{Math.round(totalEAuto)}</p>
          <p className="text-sm text-orange-100">mit E-Auto</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold">{topRegion?.region || '-'}</p>
          <p className="text-sm text-orange-100">Top Region</p>
        </div>
      </div>
    </div>
  )
}

// Personalisierte Ansicht
function PersonalizedView({ benchmark, stats }: { benchmark: AnlageBenchmark; stats: GesamtStatistik }) {
  const { anlage, benchmark: bm } = benchmark
  const abweichungGesamt = ((bm.spez_ertrag_anlage - bm.spez_ertrag_durchschnitt) / bm.spez_ertrag_durchschnitt) * 100
  const abweichungRegion = ((bm.spez_ertrag_anlage - bm.spez_ertrag_region) / bm.spez_ertrag_region) * 100

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-8">
        <div className="max-w-6xl mx-auto px-4">
          <p className="text-orange-100 mb-1">EEDC Community</p>
          <h1 className="text-3xl font-bold mb-2">Dein PV-Anlagen Benchmark</h1>
          <p className="text-orange-100">
            {anlage.kwp} kWp | {REGION_NAMEN[anlage.region] || anlage.region} | seit {anlage.installation_jahr}
          </p>
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

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ComparisonChart anlageData={anlage.monatswerte} communityData={stats.letzte_monate} />
          <AusstattungVergleich anlage={anlage} stats={stats} />
        </div>

        {/* Regionen-Ranking */}
        <div className="mb-8">
          <RegionenRanking regionen={stats.regionen} meineRegion={anlage.region} />
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-gray-500">
          <p>Vergleichsjahr: {benchmark.vergleichs_jahr}</p>
          <p className="mt-2">
            <a href="/" className="text-orange-600 hover:underline">
              ← Zur Community-Übersicht
            </a>
            {' | '}
            <a
              href="https://github.com/supernova1963/eedc-homeassistant"
              className="text-orange-600 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              EEDC auf GitHub
            </a>
          </p>
        </footer>
      </main>
    </div>
  )
}

// Community-Übersicht (ohne anlage Parameter)
function CommunityOverview({ stats }: { stats: GesamtStatistik }) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-12">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <h1 className="text-4xl font-bold mb-2">EEDC Community</h1>
          <p className="text-xl text-orange-100">
            {stats.anzahl_anlagen} PV-Anlagen teilen ihre Daten
          </p>
          <p className="text-orange-200 mt-2">
            Vergleiche deine Anlage anonym mit anderen aus der Community
          </p>
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

        {/* Highlights */}
        <div className="mb-8">
          <CommunityHighlights stats={stats} />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <MonatsverlaufChart monate={stats.letzte_monate} />
          <RegionenRanking regionen={stats.regionen} />
        </div>

        {/* Call to Action */}
        <div className="bg-white rounded-lg shadow-lg p-8 text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Wie schneidet deine Anlage ab?
          </h2>
          <p className="text-gray-600 mb-6">
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
        <footer className="text-center text-sm text-gray-500">
          <p>
            Alle Daten werden anonym und ohne persönliche Informationen gespeichert.
          </p>
          <p className="mt-2">
            <a
              href="https://github.com/supernova1963/eedc-homeassistant"
              className="text-orange-600 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              EEDC auf GitHub
            </a>
          </p>
        </footer>
      </main>
    </div>
  )
}

// Hauptkomponente
export default function App() {
  const [stats, setStats] = useState<GesamtStatistik | null>(null)
  const [benchmark, setBenchmark] = useState<AnlageBenchmark | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const anlageHash = getAnlageHash()

  useEffect(() => {
    const loadData = async () => {
      try {
        // Stats immer laden
        const statsRes = await fetch('/api/stats')
        if (!statsRes.ok) throw new Error('Fehler beim Laden der Statistiken')
        const statsData = await statsRes.json()
        setStats(statsData)

        // Wenn anlage Parameter vorhanden, Benchmark laden
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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Lade Community-Daten...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Fehler</h1>
          <p className="text-gray-600">{error}</p>
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
      <div className="min-h-screen bg-gradient-to-b from-orange-100 to-white">
        <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-12">
          <div className="max-w-6xl mx-auto px-4 text-center">
            <h1 className="text-4xl font-bold mb-2">EEDC Community</h1>
            <p className="text-orange-100">Anonyme PV-Anlagen Statistiken</p>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-12">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Noch keine Daten vorhanden</h2>
            <p className="text-gray-600 mb-6">
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

  // Personalisierte Ansicht wenn Benchmark vorhanden
  if (benchmark) {
    return <PersonalizedView benchmark={benchmark} stats={stats} />
  }

  // Standard Community-Übersicht
  return <CommunityOverview stats={stats} />
}
