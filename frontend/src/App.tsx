import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
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

const COLORS = ['#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ef4444', '#ec4899']

// Komponenten
function KPICard({ title, value, unit, subtitle }: {
  title: string
  value: string | number
  unit?: string
  subtitle?: string
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      <p className="mt-2 text-3xl font-bold text-gray-900">
        {value}
        {unit && <span className="text-lg font-normal text-gray-500 ml-1">{unit}</span>}
      </p>
      {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
    </div>
  )
}

function RegionenChart({ regionen }: { regionen: RegionStatistik[] }) {
  const data = regionen.slice(0, 8).map(r => ({
    name: r.region,
    fullName: REGION_NAMEN[r.region] || r.region,
    anlagen: r.anzahl_anlagen,
    spezErtrag: r.durchschnitt_spez_ertrag,
  }))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Anlagen nach Region</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="name" type="category" width={40} />
          <Tooltip
            formatter={(value: number, name: string) => [
              name === 'anlagen' ? value : `${value} kWh/kWp`,
              name === 'anlagen' ? 'Anlagen' : 'Ø Ertrag'
            ]}
            labelFormatter={(label) => REGION_NAMEN[label] || label}
          />
          <Bar dataKey="anlagen" fill="#f59e0b" name="Anlagen" />
        </BarChart>
      </ResponsiveContainer>
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
      <h3 className="text-lg font-semibold mb-4">Spezifischer Ertrag (kWh/kWp) - Letzte 12 Monate</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 'auto']} />
          <Tooltip
            formatter={(value: number) => [`${value.toFixed(1)} kWh/kWp`]}
            labelFormatter={(label) => label}
          />
          <Bar dataKey="durchschnitt" fill="#f59e0b" name="Ø Ertrag" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function AusstattungChart({ regionen }: { regionen: RegionStatistik[] }) {
  // Durchschnitt über alle Regionen
  const total = regionen.reduce((acc, r) => ({
    speicher: acc.speicher + r.anteil_mit_speicher * r.anzahl_anlagen,
    wp: acc.wp + r.anteil_mit_waermepumpe * r.anzahl_anlagen,
    eauto: acc.eauto + r.anteil_mit_eauto * r.anzahl_anlagen,
    count: acc.count + r.anzahl_anlagen,
  }), { speicher: 0, wp: 0, eauto: 0, count: 0 })

  const data = [
    { name: 'Speicher', value: Math.round(total.speicher / total.count) || 0 },
    { name: 'Wärmepumpe', value: Math.round(total.wp / total.count) || 0 },
    { name: 'E-Auto', value: Math.round(total.eauto / total.count) || 0 },
  ]

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Ausstattung der Anlagen</h3>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            label={({ name, value }) => `${name}: ${value}%`}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

// Hauptkomponente
export default function App() {
  const [stats, setStats] = useState<GesamtStatistik | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/stats')
      .then(res => {
        if (!res.ok) throw new Error('Fehler beim Laden der Daten')
        return res.json()
      })
      .then(data => {
        setStats(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-solar-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Fehler</h1>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  if (!stats || stats.anzahl_anlagen === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-solar-100 to-white">
        <header className="bg-solar-500 text-white py-12">
          <div className="max-w-6xl mx-auto px-4 text-center">
            <h1 className="text-4xl font-bold mb-2">☀️ EEDC Community</h1>
            <p className="text-solar-100">Anonyme PV-Anlagen Statistiken</p>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-12">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Noch keine Daten vorhanden</h2>
            <p className="text-gray-600 mb-6">
              Sei der Erste, der seine PV-Anlagendaten teilt!
            </p>
            <p className="text-sm text-gray-500">
              Nutze EEDC (Home Assistant Add-on) und aktiviere die Community-Funktion,
              um deine anonymisierten Daten beizutragen.
            </p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-solar-500 to-solar-600 text-white py-8">
        <div className="max-w-6xl mx-auto px-4">
          <h1 className="text-3xl font-bold mb-2">☀️ EEDC Community</h1>
          <p className="text-solar-100">
            Anonyme Statistiken von {stats.anzahl_anlagen} PV-Anlagen
          </p>
        </div>
      </header>

      {/* KPI Cards */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <KPICard
            title="Anlagen"
            value={stats.anzahl_anlagen}
            subtitle={`${stats.anzahl_monatswerte} Monatswerte`}
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
            subtitle="nur Anlagen mit Speicher"
          />
          <KPICard
            title="Ø Jahresertrag"
            value={Math.round(stats.durchschnitt_spez_ertrag_jahr)}
            unit="kWh/kWp"
            subtitle="spezifischer Ertrag"
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <MonatsverlaufChart monate={stats.letzte_monate} />
          <RegionenChart regionen={stats.regionen} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <AusstattungChart regionen={stats.regionen} />

          {/* Regionen-Tabelle */}
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
            <h3 className="text-lg font-semibold mb-4">Regionen-Details</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Region</th>
                    <th className="text-right py-2">Anlagen</th>
                    <th className="text-right py-2">Ø kWp</th>
                    <th className="text-right py-2">Ø kWh/kWp</th>
                    <th className="text-right py-2">Ø Autarkie</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.regionen.map(r => (
                    <tr key={r.region} className="border-b hover:bg-gray-50">
                      <td className="py-2">{REGION_NAMEN[r.region] || r.region}</td>
                      <td className="text-right py-2">{r.anzahl_anlagen}</td>
                      <td className="text-right py-2">{r.durchschnitt_kwp.toFixed(1)}</td>
                      <td className="text-right py-2">{r.durchschnitt_spez_ertrag.toFixed(0)}</td>
                      <td className="text-right py-2">
                        {r.durchschnitt_autarkie ? `${r.durchschnitt_autarkie.toFixed(0)}%` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-gray-500">
          <p>
            Daten werden anonym und ohne persönliche Informationen gespeichert.
          </p>
          <p className="mt-2">
            <a
              href="https://github.com/supernova1963/eedc-homeassistant"
              className="text-solar-600 hover:underline"
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
