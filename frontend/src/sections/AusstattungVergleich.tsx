import type { AnlageData, GesamtStatistik } from '../types'

export default function AusstattungVergleich({ anlage, stats }: { anlage: AnlageData; stats: GesamtStatistik }) {
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
