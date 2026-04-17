import { useState, useMemo } from 'react'
import { ComposableMap, Geographies, Geography } from 'react-simple-maps'
import type { RegionStatistik } from '../../types'
import { REGION_NAMEN } from '../../constants'

const GEO_URL = '/deutschland-bundeslaender.geo.json'

const DE_CODES = new Set([
  'BW', 'BY', 'BE', 'BB', 'HB', 'HH', 'HE', 'MV',
  'NI', 'NW', 'RP', 'SL', 'SN', 'ST', 'SH', 'TH',
])

function interpolateColor(value: number, min: number, max: number): string {
  if (max === min) return '#fbbf24'
  const t = Math.max(0, Math.min(1, (value - min) / (max - min)))
  // hellblau (niedrig) → amber (hoch) — passend zum orange/amber Branding
  const r = Math.round(219 + (251 - 219) * t)
  const g = Math.round(234 + (191 - 234) * t)
  const b = Math.round(254 + (36 - 254) * t)
  return `rgb(${r},${g},${b})`
}

interface TooltipData {
  name: string
  region: RegionStatistik
  x: number
  y: number
}

export default function GermanyHeatmap({ regionen }: { regionen: RegionStatistik[] }) {
  const [tooltip, setTooltip] = useState<TooltipData | null>(null)

  const regionMap = useMemo(() => {
    const m: Record<string, RegionStatistik> = {}
    regionen.forEach(r => { m[r.region] = r })
    return m
  }, [regionen])

  const deRegionen = useMemo(() => regionen.filter(r => DE_CODES.has(r.region)), [regionen])
  const auslandRegionen = useMemo(() => regionen.filter(r => !DE_CODES.has(r.region)), [regionen])

  const { min, max } = useMemo(() => {
    const vals = deRegionen.map(r => r.durchschnitt_spez_ertrag).filter(v => v > 0)
    if (vals.length === 0) return { min: 0, max: 0 }
    return { min: Math.min(...vals), max: Math.max(...vals) }
  }, [deRegionen])

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        ☀️ Spezifischer Ertrag nach Bundesland
      </h3>

      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Karte */}
        <div className="relative w-full lg:w-1/2">
          <ComposableMap
            projection="geoMercator"
            projectionConfig={{ center: [10.45, 51.2], scale: 2800 }}
            width={500}
            height={560}
            style={{ width: '100%', height: 'auto' }}
          >
            <Geographies geography={GEO_URL}>
              {({ geographies }: { geographies: { rsmKey: string; properties: Record<string, unknown> }[] }) =>
                geographies.map(geo => {
                  const code = (geo.properties.id as string).replace('DE-', '')
                  const r = regionMap[code]
                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={r ? interpolateColor(r.durchschnitt_spez_ertrag, min, max) : '#e5e7eb'}
                      stroke="#fff"
                      strokeWidth={0.8}
                      style={{
                        default: { outline: 'none' },
                        hover: { outline: 'none', opacity: 0.8, cursor: r ? 'pointer' : 'default' },
                        pressed: { outline: 'none' },
                      }}
                      onMouseEnter={(e: React.MouseEvent) => {
                        if (r) setTooltip({ name: geo.properties.name as string, region: r, x: e.clientX, y: e.clientY })
                      }}
                      onMouseMove={(e: React.MouseEvent) => {
                        if (tooltip) setTooltip(prev => prev ? { ...prev, x: e.clientX, y: e.clientY } : null)
                      }}
                      onMouseLeave={() => setTooltip(null)}
                    />
                  )
                })
              }
            </Geographies>
          </ComposableMap>

          {/* Legende */}
          <div className="flex items-center gap-2 justify-center mt-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">{min.toFixed(0)}</span>
            <div
              className="h-3 w-32 rounded"
              style={{ background: `linear-gradient(to right, ${interpolateColor(min, min, max)}, ${interpolateColor(max, min, max)})` }}
            />
            <span className="text-xs text-gray-500 dark:text-gray-400">{max.toFixed(0)} kWh/kWp</span>
          </div>
        </div>

        {/* Rangliste */}
        <div className="w-full lg:w-1/2 space-y-2">
          {[...deRegionen]
            .sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)
            .map((r, idx) => {
              const width = max > min ? ((r.durchschnitt_spez_ertrag - min) / (max - min)) * 100 : 50
              return (
                <div key={r.region} className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 w-5 text-right shrink-0">#{idx + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-gray-700 dark:text-gray-300 truncate">
                        {REGION_NAMEN[r.region] || r.region}
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white ml-2 shrink-0">
                        {r.durchschnitt_spez_ertrag.toFixed(0)}
                      </span>
                    </div>
                    <div className="bg-gray-100 dark:bg-gray-700 rounded-full h-1.5">
                      <div
                        className="h-1.5 rounded-full"
                        style={{
                          width: `${width}%`,
                          backgroundColor: interpolateColor(r.durchschnitt_spez_ertrag, min, max),
                        }}
                      />
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">{r.anzahl_anlagen} Anlage{r.anzahl_anlagen !== 1 ? 'n' : ''}</p>
                  </div>
                </div>
              )
            })}
          <p className="text-xs text-gray-400 dark:text-gray-500 text-right pt-1">kWh/kWp</p>
        </div>
      </div>

      {/* Ausland */}
      {auslandRegionen.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
            Ausland
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[...auslandRegionen]
              .sort((a, b) => b.durchschnitt_spez_ertrag - a.durchschnitt_spez_ertrag)
              .map(r => (
                <div key={r.region} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700/50 rounded-lg px-4 py-2">
                  <div>
                    <span className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                      {REGION_NAMEN[r.region] || r.region}
                    </span>
                    <p className="text-xs text-gray-400">{r.anzahl_anlagen} Anlage{r.anzahl_anlagen !== 1 ? 'n' : ''}</p>
                  </div>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    {r.durchschnitt_spez_ertrag.toFixed(0)} kWh/kWp
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Tooltip (fixed position) */}
      {tooltip && (
        <div
          className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 shadow-lg pointer-events-none text-sm"
          style={{ left: tooltip.x + 14, top: tooltip.y - 44 }}
        >
          <p className="font-semibold text-gray-900 dark:text-white">{tooltip.name}</p>
          <p className="text-amber-600 dark:text-amber-400 font-medium">
            {tooltip.region.durchschnitt_spez_ertrag.toFixed(0)} kWh/kWp
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {tooltip.region.anzahl_anlagen} Anlage{tooltip.region.anzahl_anlagen !== 1 ? 'n' : ''}
            {' · '}Ø {tooltip.region.durchschnitt_kwp.toFixed(1)} kWp
          </p>
        </div>
      )}
    </div>
  )
}
