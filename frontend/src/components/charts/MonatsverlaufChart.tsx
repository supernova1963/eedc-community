import {
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, Legend, ComposedChart,
} from 'recharts'
import type { MonatsStatistik } from '../../types'
import { MONATE } from '../../constants'

export default function MonatsverlaufChart({ monate }: { monate: MonatsStatistik[] }) {
  const data = [...monate].reverse().map(m => ({
    name: `${MONATE[m.monat - 1]} ${m.jahr.toString().slice(2)}`,
    durchschnitt: m.durchschnitt_spez_ertrag,
    min: m.min_spez_ertrag,
    max: m.max_spez_ertrag,
    anlagen: m.anzahl_anlagen,
  }))

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Community-Ertrag (kWh/kWp) - Letzte 12 Monate
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" tick={{ fill: '#9ca3af' }} />
          <YAxis domain={[0, 'auto']} tick={{ fill: '#9ca3af' }} />
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value.toFixed(1)} kWh/kWp`,
              name === 'durchschnitt' ? 'Ø Ertrag' : name === 'max' ? 'Maximum' : 'Minimum'
            ]}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
          <Bar dataKey="durchschnitt" fill="#f59e0b" name="Ø Ertrag" radius={[4, 4, 0, 0]} />
          <Line type="monotone" dataKey="max" stroke="#22c55e" strokeWidth={2} strokeDasharray="4 2" name="Maximum" dot={false} />
          <Line type="monotone" dataKey="min" stroke="#9ca3af" strokeWidth={2} strokeDasharray="4 2" name="Minimum" dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
