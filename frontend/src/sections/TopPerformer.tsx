import type { RegionStatistik } from '../types'
import { REGION_NAMEN } from '../constants'

export default function TopPerformer({ regionen }: { regionen: RegionStatistik[] }) {
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
