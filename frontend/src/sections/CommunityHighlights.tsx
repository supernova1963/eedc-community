import type { GesamtStatistik } from '../types'

export default function CommunityHighlights({ stats }: { stats: GesamtStatistik }) {
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
