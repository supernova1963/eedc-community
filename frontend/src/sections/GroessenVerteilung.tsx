import type { GesamtStatistik, Verteilung } from '../types'

export default function GroessenVerteilung({ stats, verteilung }: { stats: GesamtStatistik; verteilung: Verteilung | null }) {
  // Größenklassen aus GET /api/statistics/distributions/kwp (N-741):
  // Anteil je Klasse = anzahl / Σ anzahl, leere Klassen entfallen.
  const avgKwp = stats.durchschnitt_kwp
  const bins = verteilung?.bins ?? []
  const n = bins.reduce((sum, b) => sum + b.anzahl, 0)

  const klassen = bins
    .filter(b => b.anzahl > 0)
    .map(b => ({ range: `${b.von}–${b.bis} kWp`, anzahl: b.anzahl, anteil: (b.anzahl / n) * 100 }))

  const maxAnteil = Math.max(...klassen.map(k => k.anteil))

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <span>📊</span>
        Anlagengrößen
      </h3>
      {verteilung === null ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
          Die Größenverteilung ist gerade nicht verfügbar.
        </p>
      ) : n === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
          Noch keine Anlagengrößen vorhanden.
        </p>
      ) : (
        <div className="space-y-3">
          {klassen.map((k) => (
            <div key={k.range} className="flex items-center gap-3">
              <span className="text-sm text-gray-600 dark:text-gray-400 w-24">{k.range}</span>
              <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-6 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-orange-400 to-amber-500 rounded-full flex items-center justify-end pr-2"
                  style={{ width: `${(k.anteil / maxAnteil) * 100}%` }}
                  title={`${k.anzahl} Anlagen`}
                >
                  <span className="text-xs text-white font-medium">{k.anteil.toFixed(0)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-4 text-center">
        Ø Anlagengröße: <span className="font-semibold">{avgKwp.toFixed(1)} kWp</span>
      </p>
      {n > 0 && (
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 text-center">
          Basis: {n} Anlagen in der Community
        </p>
      )}
    </div>
  )
}
