import type { MonatsStatistik, RegionStatistik } from '../types'
import { MONATE, REGION_NAMEN } from '../constants'

function seasonEmoji(monat: number): string {
  if (monat <= 2 || monat === 12) return '❄️'
  if (monat <= 5) return '🌱'
  if (monat <= 8) return '☀️'
  return '🍂'
}

function trendLabel(pct: number): { text: string; color: string } {
  if (pct >= 20) return { text: `+${pct.toFixed(0)}% vs. Vormonat`, color: 'text-green-600 dark:text-green-400' }
  if (pct >= 5)  return { text: `+${pct.toFixed(0)}% vs. Vormonat`, color: 'text-green-500 dark:text-green-400' }
  if (pct >= -5) return { text: `${pct.toFixed(0)}% vs. Vormonat`, color: 'text-gray-500 dark:text-gray-400' }
  return { text: `${pct.toFixed(0)}% vs. Vormonat`, color: 'text-red-500 dark:text-red-400' }
}

export default function MonthlyHighlightBanner({
  monate,
  regionen,
}: {
  monate: MonatsStatistik[]
  regionen: RegionStatistik[]
}) {
  if (monate.length === 0) return null

  const sorted = [...monate].sort((a, b) =>
    a.jahr !== b.jahr ? a.jahr - b.jahr : a.monat - b.monat,
  )
  const latest = sorted[sorted.length - 1]
  const prev = sorted.length > 1 ? sorted[sorted.length - 2] : null

  const trendPct = prev
    ? ((latest.durchschnitt_spez_ertrag - prev.durchschnitt_spez_ertrag) /
        prev.durchschnitt_spez_ertrag) *
      100
    : null

  const topRegion = regionen.length > 0
    ? [...regionen].sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)[0]
    : null

  const emoji = seasonEmoji(latest.monat)
  const monatName = `${MONATE[latest.monat - 1]} ${latest.jahr}`
  const trend = trendPct !== null ? trendLabel(trendPct) : null

  return (
    <div className="rounded-lg bg-white dark:bg-gray-800 shadow border-l-4 border-amber-500 px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
      {/* Label + Monat */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-xl select-none">{emoji}</span>
        <div>
          <p className="text-xs font-medium text-amber-600 dark:text-amber-400 uppercase tracking-wide leading-none mb-0.5">
            Monats-Highlight
          </p>
          <p className="text-base font-bold text-gray-900 dark:text-white leading-none">
            {monatName}
          </p>
        </div>
      </div>

      <div className="hidden sm:block w-px h-10 bg-gray-200 dark:bg-gray-700 shrink-0" />

      {/* Stats */}
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <span className="text-gray-700 dark:text-gray-300">
          <span className="font-semibold text-gray-900 dark:text-white">
            {latest.durchschnitt_spez_ertrag.toFixed(1)}
          </span>{' '}
          <span className="text-gray-500 dark:text-gray-400">kWh/kWp Ø</span>
        </span>

        <span className="text-gray-700 dark:text-gray-300">
          <span className="font-semibold text-gray-900 dark:text-white">
            {latest.anzahl_anlagen}
          </span>{' '}
          <span className="text-gray-500 dark:text-gray-400">Anlagen</span>
        </span>

        {topRegion && (
          <span className="text-gray-700 dark:text-gray-300">
            <span className="text-gray-500 dark:text-gray-400">Top: </span>
            <span className="font-semibold text-gray-900 dark:text-white">
              {REGION_NAMEN[topRegion.region] || topRegion.region}
            </span>{' '}
            <span className="text-gray-500 dark:text-gray-400">
              ({topRegion.durchschnitt_spez_ertrag.toFixed(0)} kWh/kWp)
            </span>
          </span>
        )}

        {trend && (
          <span className={`font-medium ${trend.color}`}>
            {trendPct! >= 0 ? '▲' : '▼'} {trend.text}
          </span>
        )}
      </div>
    </div>
  )
}
