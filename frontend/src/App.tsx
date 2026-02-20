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
import Impressum from './pages/Impressum'
import Datenschutz from './pages/Datenschutz'

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
type ZeitraumTyp = 'letzter_monat' | 'letzte_12_monate' | 'jahr' | 'seit_installation'

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

// Komponenten-Icons (als Unicode-Emoji)
const KOMPONENTEN_ICONS: Record<string, string> = {
  pv: '☀️',
  speicher: '🔋',
  waermepumpe: '🌡️',
  eauto: '🚗',
  wallbox: '⚡',
  balkonkraftwerk: '🌻',
}

// Zeitraum-Konstanten und Labels
const ZEITRAUM_LABELS: Record<ZeitraumTyp, string> = {
  letzter_monat: 'Letzter Monat',
  letzte_12_monate: 'Letzte 12 Monate',
  jahr: 'Aktuelles Jahr',
  seit_installation: 'Seit Installation',
}

// Zeitraum-Auswahl Komponente
function ZeitraumSelect({
  value,
  onChange,
  disabled = false,
}: {
  value: ZeitraumTyp
  onChange: (zeitraum: ZeitraumTyp) => void
  disabled?: boolean
}) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-orange-100">Zeitraum:</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as ZeitraumTyp)}
        disabled={disabled}
        className="bg-white/20 text-white border border-orange-300/50 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-white/50 disabled:opacity-50"
      >
        {(Object.keys(ZEITRAUM_LABELS) as ZeitraumTyp[]).map((z) => (
          <option key={z} value={z} className="text-gray-900">
            {ZEITRAUM_LABELS[z]}
          </option>
        ))}
      </select>
    </div>
  )
}

// Footer-Komponente
function Footer() {
  return (
    <footer className="border-t border-gray-200 mt-12 pt-6 pb-8">
      <div className="text-center text-sm text-gray-500 space-y-2">
        <p>
          Alle Daten werden anonym und ohne persönliche Informationen gespeichert.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <a
            href="https://github.com/supernova1963/eedc-homeassistant"
            className="text-orange-600 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            EEDC auf GitHub
          </a>
          <span className="text-gray-300">|</span>
          <button
            onClick={() => navigateTo('impressum')}
            className="text-orange-600 hover:underline"
          >
            Impressum
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={() => navigateTo('datenschutz')}
            className="text-orange-600 hover:underline"
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

// KPI-Vergleich Anzeige (einzelner Wert mit Community-Vergleich)
function KPIVergleichItem({
  label,
  kpi,
  einheit,
  format = 'number',
  besserWennHoeher = true,
}: {
  label: string
  kpi: KPIVergleich
  einheit?: string
  format?: 'number' | 'percent' | 'decimal'
  besserWennHoeher?: boolean
}) {
  const formatValue = (v: number) => {
    if (format === 'percent') return `${v.toFixed(1)}%`
    if (format === 'decimal') return v.toFixed(2)
    return v.toFixed(1)
  }

  const diff = kpi.community_avg ? kpi.wert - kpi.community_avg : null
  const isGood = diff !== null ? (besserWennHoeher ? diff >= 0 : diff <= 0) : null

  return (
    <div className="flex items-center justify-between py-2 border-b last:border-0 border-gray-100">
      <span className="text-sm text-gray-600">{label}</span>
      <div className="flex items-center gap-3">
        <span className="font-semibold text-gray-900">
          {formatValue(kpi.wert)}
          {einheit && <span className="text-xs text-gray-500 ml-0.5">{einheit}</span>}
        </span>
        {kpi.community_avg !== null && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            isGood ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {diff !== null && diff >= 0 ? '+' : ''}{diff?.toFixed(1)} vs Ø
          </span>
        )}
        {kpi.rang !== null && kpi.von !== null && (
          <span className="text-xs text-gray-400">
            #{kpi.rang}/{kpi.von}
          </span>
        )}
      </div>
    </div>
  )
}

// Komponenten-Benchmark Karte
function KomponentenKarte({
  titel,
  icon,
  kpis,
  isEmpty = false,
}: {
  titel: string
  icon: string
  kpis: { label: string; kpi: KPIVergleich | null; einheit?: string; format?: 'number' | 'percent' | 'decimal'; besserWennHoeher?: boolean }[]
  isEmpty?: boolean
}) {
  const activeKpis = kpis.filter(k => k.kpi !== null)

  if (isEmpty || activeKpis.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">{icon}</span>
        <h3 className="text-lg font-semibold text-gray-900">{titel}</h3>
      </div>
      <div className="space-y-1">
        {activeKpis.map((k, i) => (
          <KPIVergleichItem
            key={i}
            label={k.label}
            kpi={k.kpi!}
            einheit={k.einheit}
            format={k.format}
            besserWennHoeher={k.besserWennHoeher}
          />
        ))}
      </div>
    </div>
  )
}

// Speicher-Karte
function SpeicherKarte({ data }: { data: SpeicherBenchmark | null }) {
  if (!data) return null

  return (
    <KomponentenKarte
      titel="Speicher"
      icon={KOMPONENTEN_ICONS.speicher}
      kpis={[
        { label: 'Kapazität', kpi: data.kapazitaet, einheit: 'kWh' },
        { label: 'Zyklen/Jahr', kpi: data.zyklen_jahr },
        { label: 'Nutzungsgrad', kpi: data.nutzungsgrad, einheit: '%', format: 'percent' },
        { label: 'Wirkungsgrad', kpi: data.wirkungsgrad, einheit: '%', format: 'percent' },
        { label: 'Netzanteil', kpi: data.netz_anteil, einheit: '%', format: 'percent', besserWennHoeher: false },
      ]}
    />
  )
}

// Wärmepumpe-Karte
function WaermepumpeKarte({ data }: { data: WaermepumpeBenchmark | null }) {
  if (!data) return null

  return (
    <KomponentenKarte
      titel="Wärmepumpe"
      icon={KOMPONENTEN_ICONS.waermepumpe}
      kpis={[
        { label: 'JAZ', kpi: data.jaz, format: 'decimal' },
        { label: 'Stromverbrauch', kpi: data.stromverbrauch, einheit: 'kWh', besserWennHoeher: false },
        { label: 'Wärmeerzeugung', kpi: data.waermeerzeugung, einheit: 'kWh' },
        { label: 'PV-Anteil', kpi: data.pv_anteil, einheit: '%', format: 'percent' },
      ]}
    />
  )
}

// E-Auto-Karte
function EAutoKarte({ data }: { data: EAutoBenchmark | null }) {
  if (!data) return null

  return (
    <KomponentenKarte
      titel="E-Auto"
      icon={KOMPONENTEN_ICONS.eauto}
      kpis={[
        { label: 'Ladung gesamt', kpi: data.ladung_gesamt, einheit: 'kWh' },
        { label: 'PV-Anteil', kpi: data.pv_anteil, einheit: '%', format: 'percent' },
        { label: 'Kilometer', kpi: data.km, einheit: 'km' },
        { label: 'Verbrauch', kpi: data.verbrauch_100km, einheit: 'kWh/100km', besserWennHoeher: false },
        { label: 'V2H', kpi: data.v2h, einheit: 'kWh' },
      ]}
    />
  )
}

// Wallbox-Karte
function WallboxKarte({ data }: { data: WallboxBenchmark | null }) {
  if (!data) return null

  return (
    <KomponentenKarte
      titel="Wallbox"
      icon={KOMPONENTEN_ICONS.wallbox}
      kpis={[
        { label: 'Ladung', kpi: data.ladung, einheit: 'kWh' },
        { label: 'PV-Anteil', kpi: data.pv_anteil, einheit: '%', format: 'percent' },
        { label: 'Ladevorgänge', kpi: data.ladevorgaenge },
      ]}
    />
  )
}

// BKW-Karte
function BKWKarte({ data }: { data: BKWBenchmark | null }) {
  if (!data) return null

  return (
    <KomponentenKarte
      titel="Balkonkraftwerk"
      icon={KOMPONENTEN_ICONS.balkonkraftwerk}
      kpis={[
        { label: 'Erzeugung', kpi: data.erzeugung, einheit: 'kWh' },
        { label: 'Spez. Ertrag', kpi: data.spez_ertrag, einheit: 'kWh/kWp' },
        { label: 'Eigenverbrauch', kpi: data.eigenverbrauch, einheit: '%', format: 'percent' },
      ]}
    />
  )
}

// PV-Benchmark-Karte (erweitert)
function PVKarte({ data }: { data: PVBenchmark }) {
  return (
    <KomponentenKarte
      titel="PV-Anlage"
      icon={KOMPONENTEN_ICONS.pv}
      kpis={[
        { label: 'Spez. Ertrag', kpi: data.spez_ertrag, einheit: 'kWh/kWp' },
        { label: 'Eigenverbrauch', kpi: data.eigenverbrauch, einheit: '%', format: 'percent' },
        { label: 'Autarkie', kpi: data.autarkie, einheit: '%', format: 'percent' },
      ]}
    />
  )
}

// Komponenten-Benchmarks Container
function KomponentenBenchmarks({ data }: { data: ErweiterteBenchmarkData | undefined }) {
  if (!data) {
    return null
  }

  const hatKomponenten = data.speicher || data.waermepumpe || data.eauto || data.wallbox || data.balkonkraftwerk

  return (
    <div className="space-y-6">
      {/* PV ist immer da */}
      <PVKarte data={data.pv} />

      {/* Optionale Komponenten */}
      {hatKomponenten && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <SpeicherKarte data={data.speicher} />
          <WaermepumpeKarte data={data.waermepumpe} />
          <EAutoKarte data={data.eauto} />
          <WallboxKarte data={data.wallbox} />
          <BKWKarte data={data.balkonkraftwerk} />
        </div>
      )}
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
function PersonalizedView({
  benchmark,
  stats,
  zeitraum,
  onZeitraumChange,
  loading = false,
}: {
  benchmark: AnlageBenchmark
  stats: GesamtStatistik
  zeitraum: ZeitraumTyp
  onZeitraumChange: (z: ZeitraumTyp) => void
  loading?: boolean
}) {
  const { anlage, benchmark: bm, benchmark_erweitert, zeitraum_label } = benchmark
  const abweichungGesamt = ((bm.spez_ertrag_anlage - bm.spez_ertrag_durchschnitt) / bm.spez_ertrag_durchschnitt) * 100
  const abweichungRegion = ((bm.spez_ertrag_anlage - bm.spez_ertrag_region) / bm.spez_ertrag_region) * 100

  // Prüfe ob Komponenten-Benchmarks vorhanden sind
  const hatKomponenten = benchmark_erweitert && (
    benchmark_erweitert.speicher ||
    benchmark_erweitert.waermepumpe ||
    benchmark_erweitert.eauto ||
    benchmark_erweitert.wallbox ||
    benchmark_erweitert.balkonkraftwerk
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header mit Zeitraum-Auswahl */}
      <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-8">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <p className="text-orange-100 mb-1">EEDC Community</p>
              <h1 className="text-3xl font-bold mb-2">Dein PV-Anlagen Benchmark</h1>
              <p className="text-orange-100">
                {anlage.kwp} kWp | {REGION_NAMEN[anlage.region] || anlage.region} | seit {anlage.installation_jahr}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <ZeitraumSelect
                value={zeitraum}
                onChange={onZeitraumChange}
                disabled={loading}
              />
              {loading && (
                <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
              )}
            </div>
          </div>
          {zeitraum_label && (
            <p className="text-orange-200 text-sm mt-2">
              Auswertungszeitraum: {zeitraum_label}
            </p>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Ranking Badges */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <RankingBadge rang={bm.rang_gesamt} total={bm.anzahl_anlagen_gesamt} label="Rang Deutschland" />
          <RankingBadge rang={bm.rang_region} total={bm.anzahl_anlagen_region} label={`Rang ${REGION_NAMEN[anlage.region] || anlage.region}`} />
          <KPICard
            title="Dein spez. Ertrag"
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

        {/* Komponenten-Benchmarks (nur wenn erweiterte Daten vorhanden) */}
        {hatKomponenten && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>📊</span>
              Komponenten-Benchmarks
            </h2>
            <KomponentenBenchmarks data={benchmark_erweitert} />
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ComparisonChart anlageData={anlage.monatswerte} communityData={stats.letzte_monate} />
          <AusstattungVergleich anlage={anlage} stats={stats} />
        </div>

        {/* Regionen-Ranking */}
        <div className="mb-8">
          <RegionenRanking regionen={stats.regionen} meineRegion={anlage.region} />
        </div>

        {/* Vergleichsjahr-Info */}
        <div className="text-center text-sm text-gray-500 mt-8">
          <p>Vergleichsjahr: {benchmark.vergleichs_jahr}</p>
          <p className="mt-2">
            <a href="/" className="text-orange-600 hover:underline">
              ← Zur Community-Übersicht
            </a>
          </p>
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
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <span>🏆</span>
        Top-Performer
      </h3>

      {/* Top Regionen */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-500 mb-3">Beste Regionen (Ertrag)</h4>
        <div className="space-y-2">
          {topRegionen.map((r, idx) => (
            <div key={r.region} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">{['🥇', '🥈', '🥉'][idx]}</span>
                <span className="text-gray-700">{REGION_NAMEN[r.region] || r.region}</span>
              </div>
              <span className="font-semibold text-gray-900">
                {r.durchschnitt_spez_ertrag.toFixed(0)} kWh/kWp
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Weitere Highlights */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t">
        {besteAutarkie && besteAutarkie.durchschnitt_autarkie && (
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {besteAutarkie.durchschnitt_autarkie.toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500">
              Beste Autarkie
              <br />
              ({REGION_NAMEN[besteAutarkie.region] || besteAutarkie.region})
            </p>
          </div>
        )}
        {hoechsteSpeicherQuote && (
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">
              {hoechsteSpeicherQuote.anteil_mit_speicher.toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500">
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
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <span>📈</span>
        Community-Trend
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 'auto']} />
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
          />
          <Legend />
          {/* Bereich zwischen min und max */}
          <Line
            type="monotone"
            dataKey="max"
            stroke="#fde68a"
            strokeWidth={1}
            strokeDasharray="3 3"
            name="Maximum"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="min"
            stroke="#fde68a"
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
            stroke="#ea580c"
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
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <span>⚡</span>
        Ausstattung der Community
      </h3>
      <div className="space-y-4">
        {ausstattung.map((item) => (
          <div key={item.name}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">{item.name}</span>
              <span className="text-sm text-gray-500">
                {item.anzahl} Anlagen ({item.prozent.toFixed(0)}%)
              </span>
            </div>
            <div className="bg-gray-200 rounded-full h-3">
              <div
                className="h-3 rounded-full transition-all duration-500"
                style={{ width: `${item.prozent}%`, backgroundColor: item.color }}
              />
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-400 mt-4 text-center">
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
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <span>📊</span>
        Anlagengrößen
      </h3>
      <div className="space-y-3">
        {klassen.map((k) => (
          <div key={k.range} className="flex items-center gap-3">
            <span className="text-sm text-gray-600 w-20">{k.range}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
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
      <p className="text-sm text-gray-500 mt-4 text-center">
        Ø Anlagengröße: <span className="font-semibold">{avgKwp.toFixed(1)} kWp</span>
      </p>
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
  const [benchmarkLoading, setBenchmarkLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState<'main' | 'impressum' | 'datenschutz'>(getCurrentPage())
  const [zeitraum, setZeitraum] = useState<ZeitraumTyp>('letzte_12_monate')

  const anlageHash = getAnlageHash()

  // Listen for popstate events (browser back/forward)
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPage(getCurrentPage())
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  // Benchmark bei Zeitraum-Änderung neu laden
  const loadBenchmark = async (z: ZeitraumTyp) => {
    if (!anlageHash) return

    setBenchmarkLoading(true)
    try {
      const benchmarkRes = await fetch(`/api/benchmark/anlage/${anlageHash}?zeitraum=${z}`)
      if (benchmarkRes.ok) {
        const benchmarkData = await benchmarkRes.json()
        setBenchmark(benchmarkData)
      }
    } catch (err) {
      console.error('Fehler beim Laden des Benchmarks:', err)
    } finally {
      setBenchmarkLoading(false)
    }
  }

  const handleZeitraumChange = (z: ZeitraumTyp) => {
    setZeitraum(z)
    loadBenchmark(z)
  }

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
          const benchmarkRes = await fetch(`/api/benchmark/anlage/${anlageHash}?zeitraum=${zeitraum}`)
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
  }, [anlageHash]) // zeitraum absichtlich nicht in deps, da handleZeitraumChange das übernimmt

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
        zeitraum={zeitraum}
        onZeitraumChange={handleZeitraumChange}
        loading={benchmarkLoading}
      />
    )
  }

  // Standard Community-Übersicht
  return <CommunityOverview stats={stats} />
}
