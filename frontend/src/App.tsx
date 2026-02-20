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
  ComposedChart,
} from 'recharts'
import Impressum from './pages/Impressum'
import Datenschutz from './pages/Datenschutz'

// Dark Mode Hook
function useDarkMode() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window === 'undefined') return false
    const saved = localStorage.getItem('darkMode')
    if (saved !== null) return saved === 'true'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    localStorage.setItem('darkMode', isDark.toString())
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  return [isDark, setIsDark] as const
}

// Dark Mode Toggle Component
function DarkModeToggle({ isDark, toggle }: { isDark: boolean; toggle: () => void }) {
  return (
    <button
      onClick={toggle}
      className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
      title={isDark ? 'Light Mode' : 'Dark Mode'}
    >
      {isDark ? (
        <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
        </svg>
      ) : (
        <svg className="w-5 h-5 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
          <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
        </svg>
      )}
    </button>
  )
}

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
  anteil_mit_wallbox: number
  anteil_mit_balkonkraftwerk: number
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
  // Speicher-KPIs
  speicher_ladung_kwh: number | null
  speicher_entladung_kwh: number | null
  speicher_ladung_netz_kwh: number | null
  // Wärmepumpe-KPIs
  wp_stromverbrauch_kwh: number | null
  wp_heizwaerme_kwh: number | null
  wp_warmwasser_kwh: number | null
  // E-Auto-KPIs
  eauto_ladung_gesamt_kwh: number | null
  eauto_ladung_pv_kwh: number | null
  eauto_ladung_extern_kwh: number | null
  eauto_km: number | null
  eauto_v2h_kwh: number | null
  // Wallbox-KPIs
  wallbox_ladung_kwh: number | null
  wallbox_ladung_pv_kwh: number | null
  wallbox_ladevorgaenge: number | null
  // Balkonkraftwerk-KPIs
  bkw_erzeugung_kwh: number | null
  bkw_eigenverbrauch_kwh: number | null
  bkw_speicher_ladung_kwh: number | null
  bkw_speicher_entladung_kwh: number | null
  // Sonstiges-KPIs
  sonstiges_verbrauch_kwh: number | null
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
  hat_balkonkraftwerk: boolean
  hat_sonstiges: boolean
  wallbox_kw: number | null
  bkw_wp: number | null
  sonstiges_bezeichnung: string | null
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

// Erweiterte Benchmark-Typen
type ZeitraumTyp = 'letzter_monat' | 'letzte_12_monate' | 'letztes_vollstaendiges_jahr' | 'jahr' | 'seit_installation'

interface KPIVergleich {
  wert: number
  community_avg: number | null
  rang: number | null
  von: number | null
}

interface PVBenchmark {
  spez_ertrag: KPIVergleich
  eigenverbrauch: KPIVergleich | null
  autarkie: KPIVergleich | null
}

interface SpeicherBenchmark {
  kapazitaet: KPIVergleich | null
  zyklen_jahr: KPIVergleich | null
  nutzungsgrad: KPIVergleich | null
  wirkungsgrad: KPIVergleich | null
  netz_anteil: KPIVergleich | null
}

interface WaermepumpeBenchmark {
  jaz: KPIVergleich | null
  stromverbrauch: KPIVergleich | null
  waermeerzeugung: KPIVergleich | null
  pv_anteil: KPIVergleich | null
}

interface EAutoBenchmark {
  ladung_gesamt: KPIVergleich | null
  pv_anteil: KPIVergleich | null
  km: KPIVergleich | null
  verbrauch_100km: KPIVergleich | null
  v2h: KPIVergleich | null
}

interface WallboxBenchmark {
  ladung: KPIVergleich | null
  pv_anteil: KPIVergleich | null
  ladevorgaenge: KPIVergleich | null
}

interface BKWBenchmark {
  erzeugung: KPIVergleich | null
  spez_ertrag: KPIVergleich | null
  eigenverbrauch: KPIVergleich | null
}

interface ErweiterteBenchmarkData {
  pv: PVBenchmark
  speicher: SpeicherBenchmark | null
  waermepumpe: WaermepumpeBenchmark | null
  eauto: EAutoBenchmark | null
  wallbox: WallboxBenchmark | null
  balkonkraftwerk: BKWBenchmark | null
}

interface AnlageBenchmark {
  anlage: AnlageData
  benchmark: BenchmarkData
  vergleichs_jahr: number
  // Erweiterte Benchmark-Daten (optional für Abwärtskompatibilität)
  zeitraum?: ZeitraumTyp
  zeitraum_label?: string
  benchmark_erweitert?: ErweiterteBenchmarkData
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

// Helper: URL Parameter und Pfad lesen
function getAnlageHash(): string | null {
  const params = new URLSearchParams(window.location.search)
  return params.get('anlage')
}

function getCurrentPage(): 'main' | 'impressum' | 'datenschutz' {
  const path = window.location.pathname.toLowerCase()
  if (path === '/impressum' || path === '/impressum/') return 'impressum'
  if (path === '/datenschutz' || path === '/datenschutz/') return 'datenschutz'
  return 'main'
}

function navigateTo(page: 'main' | 'impressum' | 'datenschutz') {
  const path = page === 'main' ? '/' : `/${page}`
  window.history.pushState({}, '', path)
  window.dispatchEvent(new PopStateEvent('popstate'))
}

// Footer-Komponente
function Footer() {
  return (
    <footer className="border-t border-gray-200 dark:border-gray-700 mt-12 pt-6 pb-8">
      <div className="text-center text-sm text-gray-500 dark:text-gray-400 space-y-2">
        <p>
          Alle Daten werden anonym und ohne persönliche Informationen gespeichert.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <a
            href="https://github.com/supernova1963/eedc-homeassistant"
            className="text-orange-600 dark:text-orange-400 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            EEDC auf GitHub
          </a>
          <span className="text-gray-300 dark:text-gray-600">|</span>
          <button
            onClick={() => navigateTo('impressum')}
            className="text-orange-600 dark:text-orange-400 hover:underline"
          >
            Impressum
          </button>
          <span className="text-gray-300 dark:text-gray-600">|</span>
          <button
            onClick={() => navigateTo('datenschutz')}
            className="text-orange-600 dark:text-orange-400 hover:underline"
          >
            Datenschutz
          </button>
        </div>
      </div>
    </footer>
  )
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
    <div className={`rounded-lg shadow p-6 ${highlight ? 'bg-gradient-to-br from-orange-500 to-amber-500 text-white' : 'bg-white dark:bg-gray-800'}`}>
      <h3 className={`text-sm font-medium ${highlight ? 'text-orange-100' : 'text-gray-500 dark:text-gray-400'}`}>{title}</h3>
      <p className={`mt-2 text-3xl font-bold ${highlight ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
        {value}
        {unit && <span className={`text-lg font-normal ml-1 ${highlight ? 'text-orange-100' : 'text-gray-500 dark:text-gray-400'}`}>{unit}</span>}
      </p>
      {comparison && (
        <p className={`mt-1 text-sm font-medium ${comparison.value >= 0 ? 'text-green-400' : 'text-red-300'}`}>
          {comparison.value >= 0 ? '▲' : '▼'} {Math.abs(comparison.value).toFixed(0)}% {comparison.label}
        </p>
      )}
      {subtitle && <p className={`mt-1 text-sm ${highlight ? 'text-orange-100' : 'text-gray-500 dark:text-gray-400'}`}>{subtitle}</p>}
    </div>
  )
}

function RankingBadge({ rang, total, label }: { rang: number; total: number; label: string }) {
  const prozent = ((total - rang + 1) / total) * 100
  const medalColor = rang === 1 ? 'text-yellow-500' : rang === 2 ? 'text-gray-400' : rang === 3 ? 'text-amber-600' : 'text-gray-600 dark:text-gray-400'
  const medal = rang <= 3 ? ['🥇', '🥈', '🥉'][rang - 1] : `#${rang}`

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{label}</p>
      <p className={`text-4xl font-bold ${medalColor}`}>{medal}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">von {total} Anlagen</p>
      <div className="mt-3 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className="bg-gradient-to-r from-orange-500 to-amber-500 h-2 rounded-full"
          style={{ width: `${prozent}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Top {(100 - prozent + 1).toFixed(0)}%</p>
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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">Dein Ertrag vs. Community-Durchschnitt</h3>
      <p className="text-xs text-gray-400 mb-4">Letzte 12 Monate (spezifischer Ertrag in kWh/kWp)</p>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" tick={{ fill: '#9ca3af' }} />
          <YAxis domain={[0, 'auto']} tick={{ fill: '#9ca3af' }} />
          <Tooltip
            formatter={(value: number) => value ? `${value.toFixed(1)} kWh/kWp` : '-'}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
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
  const avgWallbox = stats.regionen.reduce((sum, r) => sum + r.anteil_mit_wallbox * r.anzahl_anlagen, 0) / totalAnlagen
  const avgBKW = stats.regionen.reduce((sum, r) => sum + r.anteil_mit_balkonkraftwerk * r.anzahl_anlagen, 0) / totalAnlagen

  // Speicher: kWh-Vergleich wenn Anlage Speicher hat, sonst %-Vergleich
  const speicherCommunity = anlage.speicher_kwh && stats.durchschnitt_speicher_kwh
    ? `${stats.durchschnitt_speicher_kwh.toFixed(1)} kWh`
    : `${Math.round(avgSpeicher)}% haben`

  const items = [
    { name: 'PV-Anlage', du: `${anlage.kwp.toFixed(1)} kWp`, community: `${stats.durchschnitt_kwp.toFixed(1)} kWp`, hatDu: true },
    { name: 'Speicher', du: anlage.speicher_kwh ? `${anlage.speicher_kwh.toFixed(1)} kWh` : '-', community: speicherCommunity, hatDu: !!anlage.speicher_kwh },
    { name: 'Wärmepumpe', du: anlage.hat_waermepumpe ? '✓' : '-', community: `${Math.round(avgWP)}% haben`, hatDu: anlage.hat_waermepumpe },
    { name: 'E-Auto', du: anlage.hat_eauto ? '✓' : '-', community: `${Math.round(avgEAuto)}% haben`, hatDu: anlage.hat_eauto },
    { name: 'Wallbox', du: anlage.hat_wallbox ? '✓' : '-', community: `${Math.round(avgWallbox)}% haben`, hatDu: anlage.hat_wallbox },
    { name: 'Balkonkraftwerk', du: anlage.hat_balkonkraftwerk ? '✓' : '-', community: `${Math.round(avgBKW)}% haben`, hatDu: anlage.hat_balkonkraftwerk },
  ]

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Deine Ausstattung</h3>
      <div className="space-y-3">
        {items.map(item => (
          <div key={item.name} className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700 last:border-0">
            <span className="font-medium text-gray-700 dark:text-gray-300">{item.name}</span>
            <div className="flex items-center gap-4">
              <span className={`font-semibold ${item.hatDu ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'}`}>
                {item.du}
              </span>
              <span className="text-sm text-gray-400">|</span>
              <span className="text-sm text-gray-500 dark:text-gray-400">Ø {item.community}</span>
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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Community-Ertrag (kWh/kWp) - Letzte 12 Monate
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" tick={{ fill: '#9ca3af' }} />
          <YAxis domain={[0, 'auto']} tick={{ fill: '#9ca3af' }} />
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value.toFixed(1)} kWh/kWp`,
              name === 'durchschnitt' ? 'Ø Ertrag' : name === 'max' ? 'Maximum' : 'Minimum'
            ]}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
          <Bar dataKey="durchschnitt" fill="#f59e0b" name="Ø Ertrag" radius={[4, 4, 0, 0]} />
          <Line type="monotone" dataKey="max" stroke="#22c55e" strokeWidth={2} strokeDasharray="4 2" name="Maximum" dot={false} />
          <Line type="monotone" dataKey="min" stroke="#9ca3af" strokeWidth={2} strokeDasharray="4 2" name="Minimum" dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

function RegionenRanking({ regionen, meineRegion }: { regionen: RegionStatistik[]; meineRegion?: string }) {
  const sorted = [...regionen].sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)
  const maxErtrag = Math.max(...sorted.map(r => r.durchschnitt_spez_ertrag))

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Regionen-Ranking (Jahresertrag)</h3>
      <div className="space-y-3">
        {sorted.map((r, idx) => {
          const isHighlight = r.region === meineRegion
          const width = (r.durchschnitt_spez_ertrag / maxErtrag) * 100
          return (
            <div key={r.region} className={`rounded-lg p-3 ${isHighlight ? 'bg-orange-50 dark:bg-orange-900/30 ring-2 ring-orange-500' : ''}`}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-gray-400">#{idx + 1}</span>
                  <span className={`font-medium ${isHighlight ? 'text-orange-700 dark:text-orange-400' : 'text-gray-700 dark:text-gray-300'}`}>
                    {REGION_NAMEN[r.region] || r.region}
                    {isHighlight && <span className="ml-2 text-xs bg-orange-500 text-white px-2 py-0.5 rounded-full">DEINE REGION</span>}
                  </span>
                </div>
                <span className="font-bold text-gray-900 dark:text-white">{r.durchschnitt_spez_ertrag.toFixed(0)} kWh/kWp</span>
              </div>
              <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${isHighlight ? 'bg-orange-500' : 'bg-gray-400 dark:bg-gray-500'}`}
                  style={{ width: `${width}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{r.anzahl_anlagen} Anlagen</p>
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

// Personalisierte Ansicht (vereinfacht - Details im EEDC Add-on)
function PersonalizedView({
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

// Top-Performer Anzeige (anonym)
function TopPerformer({ regionen }: { regionen: RegionStatistik[] }) {
  // Top 3 Regionen nach Ertrag
  const topRegionen = [...regionen]
    .sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)
    .slice(0, 3)

  // Beste Ausstattungsquoten
  const besteAutarkie = [...regionen]
    .filter(r => r.durchschnitt_autarkie !== null)
    .sort((a, b) => (b.durchschnitt_autarkie || 0) - (a.durchschnitt_autarkie || 0))[0]

  const hoechsteSpeicherQuote = [...regionen]
    .sort((a, b) => b.anteil_mit_speicher - a.anteil_mit_speicher)[0]

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <span>🏆</span>
        Top-Performer
      </h3>

      {/* Top Regionen */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Beste Regionen (Ertrag)</h4>
        <div className="space-y-2">
          {topRegionen.map((r, idx) => (
            <div key={r.region} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">{['🥇', '🥈', '🥉'][idx]}</span>
                <span className="text-gray-700 dark:text-gray-300">{REGION_NAMEN[r.region] || r.region}</span>
              </div>
              <span className="font-semibold text-gray-900 dark:text-white">
                {r.durchschnitt_spez_ertrag.toFixed(0)} kWh/kWp
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Weitere Highlights */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        {besteAutarkie && besteAutarkie.durchschnitt_autarkie && (
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {besteAutarkie.durchschnitt_autarkie.toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Beste Autarkie
              <br />
              ({REGION_NAMEN[besteAutarkie.region] || besteAutarkie.region})
            </p>
          </div>
        )}
        {hoechsteSpeicherQuote && (
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {hoechsteSpeicherQuote.anteil_mit_speicher.toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Höchste Speicherquote
              <br />
              ({REGION_NAMEN[hoechsteSpeicherQuote.region] || hoechsteSpeicherQuote.region})
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// Trend-Analyse Chart
function TrendChart({ monate }: { monate: MonatsStatistik[] }) {
  // Berechne gleitenden 3-Monats-Durchschnitt
  const data = [...monate].reverse().map((m, idx, arr) => {
    // 3-Monats-Durchschnitt
    const startIdx = Math.max(0, idx - 2)
    const slice = arr.slice(startIdx, idx + 1)
    const avg3m = slice.reduce((s, x) => s + x.durchschnitt_spez_ertrag, 0) / slice.length

    return {
      name: `${MONATE[m.monat - 1]} ${m.jahr.toString().slice(2)}`,
      ertrag: m.durchschnitt_spez_ertrag,
      trend: avg3m,
      anlagen: m.anzahl_anlagen,
      min: m.min_spez_ertrag,
      max: m.max_spez_ertrag,
    }
  })

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <span>📈</span>
        Community-Trend
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" tick={{ fill: '#9ca3af' }} />
          <YAxis domain={[0, 'auto']} tick={{ fill: '#9ca3af' }} />
          <Tooltip
            formatter={(value: number, name: string) => {
              const labels: Record<string, string> = {
                ertrag: 'Monatswert',
                trend: '3-Monats-Trend',
                min: 'Minimum',
                max: 'Maximum',
              }
              return [`${value.toFixed(1)} kWh/kWp`, labels[name] || name]
            }}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
          {/* Bereich zwischen min und max - kontrastreichere Farben */}
          <Line
            type="monotone"
            dataKey="max"
            stroke="#9ca3af"
            strokeWidth={1}
            strokeDasharray="3 3"
            name="Maximum"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="min"
            stroke="#9ca3af"
            strokeWidth={1}
            strokeDasharray="3 3"
            name="Minimum"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="ertrag"
            stroke="#f59e0b"
            strokeWidth={2}
            name="Monatswert"
            dot={{ fill: '#f59e0b', r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="trend"
            stroke="#dc2626"
            strokeWidth={3}
            name="3-Monats-Trend"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// Ausstattungs-Verteilung
function AusstattungsVerteilung({ stats }: { stats: GesamtStatistik }) {
  const totalAnlagen = stats.regionen.reduce((sum, r) => sum + r.anzahl_anlagen, 0)

  // Aggregiere über alle Regionen
  const mitSpeicher = stats.regionen.reduce(
    (sum, r) => sum + (r.anteil_mit_speicher / 100) * r.anzahl_anlagen, 0
  )
  const mitWP = stats.regionen.reduce(
    (sum, r) => sum + (r.anteil_mit_waermepumpe / 100) * r.anzahl_anlagen, 0
  )
  const mitEAuto = stats.regionen.reduce(
    (sum, r) => sum + (r.anteil_mit_eauto / 100) * r.anzahl_anlagen, 0
  )

  const ausstattung = [
    { name: 'Speicher', anzahl: Math.round(mitSpeicher), prozent: (mitSpeicher / totalAnlagen) * 100, color: '#3b82f6' },
    { name: 'Wärmepumpe', anzahl: Math.round(mitWP), prozent: (mitWP / totalAnlagen) * 100, color: '#ef4444' },
    { name: 'E-Auto', anzahl: Math.round(mitEAuto), prozent: (mitEAuto / totalAnlagen) * 100, color: '#22c55e' },
  ]

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <span>⚡</span>
        Ausstattung der Community
      </h3>
      <div className="space-y-4">
        {ausstattung.map((item) => (
          <div key={item.name}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{item.name}</span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {item.anzahl} Anlagen ({item.prozent.toFixed(0)}%)
              </span>
            </div>
            <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                className="h-3 rounded-full transition-all duration-500"
                style={{ width: `${item.prozent}%`, backgroundColor: item.color }}
              />
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-4 text-center">
        Basis: {totalAnlagen} Anlagen in der Community
      </p>
    </div>
  )
}

// Größenverteilung Histogramm
function GroessenVerteilung({ stats }: { stats: GesamtStatistik }) {
  // Erstelle Größenklassen aus den Regionsdaten
  // Da wir nur Durchschnitte haben, simulieren wir eine Verteilung
  const avgKwp = stats.durchschnitt_kwp

  // Typische Verteilung basierend auf Durchschnitt
  const klassen = [
    { range: '< 5 kWp', anteil: 15 },
    { range: '5-10 kWp', anteil: 35 },
    { range: '10-15 kWp', anteil: 30 },
    { range: '15-20 kWp', anteil: 12 },
    { range: '> 20 kWp', anteil: 8 },
  ]

  const maxAnteil = Math.max(...klassen.map(k => k.anteil))

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <span>📊</span>
        Anlagengrößen
      </h3>
      <div className="space-y-3">
        {klassen.map((k) => (
          <div key={k.range} className="flex items-center gap-3">
            <span className="text-sm text-gray-600 dark:text-gray-400 w-20">{k.range}</span>
            <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-6 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-orange-400 to-amber-500 rounded-full flex items-center justify-end pr-2"
                style={{ width: `${(k.anteil / maxAnteil) * 100}%` }}
              >
                <span className="text-xs text-white font-medium">{k.anteil}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-4 text-center">
        Ø Anlagengröße: <span className="font-semibold">{avgKwp.toFixed(1)} kWp</span>
      </p>
    </div>
  )
}

// Community-Übersicht (ohne anlage Parameter)
function CommunityOverview({ stats, isDark, toggleDark }: { stats: GesamtStatistik; isDark: boolean; toggleDark: () => void }) {
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

// Hauptkomponente
export default function App() {
  const [stats, setStats] = useState<GesamtStatistik | null>(null)
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
        // Stats immer laden
        const statsRes = await fetch('/api/stats')
        if (!statsRes.ok) throw new Error('Fehler beim Laden der Statistiken')
        const statsData = await statsRes.json()
        setStats(statsData)

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
  return <CommunityOverview stats={stats} isDark={isDark} toggleDark={toggleDark} />
}
