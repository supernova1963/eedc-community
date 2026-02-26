import type { RegionStatistik } from '../types'
import { REGION_NAMEN } from '../constants'

export default function RegionenRanking({ regionen, meineRegion }: { regionen: RegionStatistik[]; meineRegion?: string }) {
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
