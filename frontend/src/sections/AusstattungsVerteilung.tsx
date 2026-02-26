import type { GesamtStatistik } from '../types'

export default function AusstattungsVerteilung({ stats }: { stats: GesamtStatistik }) {
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
  const mitWallbox = stats.regionen.reduce(
    (sum, r) => sum + (r.anteil_mit_wallbox / 100) * r.anzahl_anlagen, 0
  )
  const mitBKW = stats.regionen.reduce(
    (sum, r) => sum + (r.anteil_mit_balkonkraftwerk / 100) * r.anzahl_anlagen, 0
  )

  const ausstattung = [
    { name: 'Speicher', anzahl: Math.round(mitSpeicher), prozent: (mitSpeicher / totalAnlagen) * 100, color: '#3b82f6' },
    { name: 'Wärmepumpe', anzahl: Math.round(mitWP), prozent: (mitWP / totalAnlagen) * 100, color: '#ef4444' },
    { name: 'E-Auto', anzahl: Math.round(mitEAuto), prozent: (mitEAuto / totalAnlagen) * 100, color: '#22c55e' },
    { name: 'Wallbox', anzahl: Math.round(mitWallbox), prozent: (mitWallbox / totalAnlagen) * 100, color: '#8b5cf6' },
    { name: 'Balkonkraftwerk', anzahl: Math.round(mitBKW), prozent: (mitBKW / totalAnlagen) * 100, color: '#f59e0b' },
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
