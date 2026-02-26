import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend,
} from 'recharts'
import type { MonatsStatistik } from '../../types'
import { MONATE } from '../../constants'

export default function TrendChart({ monate }: { monate: MonatsStatistik[] }) {
  const data = [...monate].reverse().map((m, idx, arr) => {
    const startIdx = Math.max(0, idx - 2)
    const slice = arr.slice(startIdx, idx + 1)
    const avg3m = slice.reduce((s, x) => s + x.durchschnitt_spez_ertrag, 0) / slice.length

    return {
      name: `${MONATE[m.monat - 1]} ${m.jahr.toString().slice(2)}`,
      ertrag: m.durchschnitt_spez_ertrag,
      trend: avg3m,
      anlagen: m.anzahl_anlagen,
      min: m.min_spez_ertrag,
      max: m.max_spez_ertrag,
    }
  })

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <span>📈</span>
        Community-Trend
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" tick={{ fill: '#9ca3af' }} />
          <YAxis domain={[0, 'auto']} tick={{ fill: '#9ca3af' }} />
          <Tooltip
            formatter={(value: number, name: string) => {
              const labels: Record<string, string> = {
                ertrag: 'Monatswert',
                trend: '3-Monats-Trend',
                min: 'Minimum',
                max: 'Maximum',
              }
              return [`${value.toFixed(1)} kWh/kWp`, labels[name] || name]
            }}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
          <Line type="monotone" dataKey="max" stroke="#9ca3af" strokeWidth={1} strokeDasharray="3 3" name="Maximum" dot={false} />
          <Line type="monotone" dataKey="min" stroke="#9ca3af" strokeWidth={1} strokeDasharray="3 3" name="Minimum" dot={false} />
          <Line type="monotone" dataKey="ertrag" stroke="#f59e0b" strokeWidth={2} name="Monatswert" dot={{ fill: '#f59e0b', r: 3 }} />
          <Line type="monotone" dataKey="trend" stroke="#dc2626" strokeWidth={3} name="3-Monats-Trend" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
