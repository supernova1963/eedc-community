import { useMemo } from 'react'
import type { MonatsStatistik, RegionStatistik } from '../../types'
import { MONATE, REGION_NAMEN } from '../../constants'

function seasonEmoji(monat: number) {
  if (monat <= 2 || monat === 12) return '❄️'
  if (monat <= 5) return '🌱'
  if (monat <= 8) return '☀️'
  return '🍂'
}

export default function StickyBar({
  monate,
  regionen,
}: {
  monate: MonatsStatistik[]
  regionen: RegionStatistik[]
}) {
  const monthly = useMemo(() => {
    if (monate.length === 0) return null
    const sorted = [...monate].sort((a, b) =>
      a.jahr !== b.jahr ? a.jahr - b.jahr : a.monat - b.monat,
    )
    const latest = sorted[sorted.length - 1]
    const prev = sorted.length > 1 ? sorted[sorted.length - 2] : null
    const trendPct = prev
      ? ((latest.durchschnitt_spez_ertrag - prev.durchschnitt_spez_ertrag) /
          prev.durchschnitt_spez_ertrag) * 100
      : null
    const topRegion = regionen.length > 0
      ? [...regionen].sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)[0]
      : null
    return { latest, trendPct, topRegion }
  }, [monate, regionen])

  return (
    <div className="bg-gradient-to-r from-orange-600 to-amber-500 text-white px-4 py-2 flex items-center gap-3 min-h-[44px]">
      {/* Brand-Link nach Home */}
      <a
        href="/"
        className="flex items-center gap-1.5 font-bold text-white hover:text-orange-100 transition-colors shrink-0"
        aria-label="EEDC Community – Startseite"
      >
        ☀️ <span className="text-base">eedc</span>
      </a>

      {/* Trennlinie */}
      <div className="w-px h-5 bg-white/30 shrink-0" />

      {/* Monats-Pills – horizontal scrollbar auf Mobile, kein Wrap */}
      {monthly && (
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-none min-w-0">
          <span className="inline-flex items-center gap-1 bg-white/15 border border-white/20 rounded-full px-3 py-0.5 text-xs font-medium whitespace-nowrap">
            {seasonEmoji(monthly.latest.monat)}{' '}
            {MONATE[monthly.latest.monat - 1]} {monthly.latest.jahr}
          </span>
          <span className="inline-flex items-center bg-white/15 border border-white/20 rounded-full px-3 py-0.5 text-xs font-medium whitespace-nowrap">
            Ø {monthly.latest.durchschnitt_spez_ertrag.toFixed(1)} kWh/kWp
          </span>
          {monthly.trendPct !== null && (
            <span className="inline-flex items-center bg-white/15 border border-white/20 rounded-full px-3 py-0.5 text-xs font-medium whitespace-nowrap">
              {monthly.trendPct >= 0 ? '▲' : '▼'} {Math.abs(monthly.trendPct).toFixed(0)}%
            </span>
          )}
          {monthly.topRegion && (
            <span className="inline-flex items-center bg-white/15 border border-white/20 rounded-full px-3 py-0.5 text-xs font-medium whitespace-nowrap">
              🏆 {REGION_NAMEN[monthly.topRegion.region] || monthly.topRegion.region}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
