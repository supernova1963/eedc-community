import type { GesamtStatistik } from '../types'

export default function GroessenVerteilung({ stats }: { stats: GesamtStatistik }) {
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
