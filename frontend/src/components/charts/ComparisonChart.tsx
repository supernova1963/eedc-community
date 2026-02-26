import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend,
} from 'recharts'
import type { Monatswert, MonatsStatistik } from '../../types'
import { MONATE } from '../../constants'

export default function ComparisonChart({ anlageData, communityData }: {
  anlageData: Monatswert[]
  communityData: MonatsStatistik[]
}) {
  const data = communityData.slice().reverse().map(cm => {
    const anlageMonat = anlageData.find(a => a.jahr === cm.jahr && a.monat === cm.monat)
    return {
      name: `${MONATE[cm.monat - 1]} ${cm.jahr.toString().slice(2)}`,
      community: cm.durchschnitt_spez_ertrag,
      anlage: anlageMonat?.spez_ertrag_kwh_kwp || null,
    }
  })

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">Dein Ertrag vs. Community-Durchschnitt</h3>
      <p className="text-xs text-gray-400 mb-4">Letzte 12 Monate (spezifischer Ertrag in kWh/kWp)</p>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" tick={{ fill: '#9ca3af' }} />
          <YAxis domain={[0, 'auto']} tick={{ fill: '#9ca3af' }} />
          <Tooltip
            formatter={(value: number) => value ? `${value.toFixed(1)} kWh/kWp` : '-'}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
          <Line type="monotone" dataKey="anlage" stroke="#f59e0b" strokeWidth={3} name="Deine Anlage" dot={{ fill: '#f59e0b' }} />
          <Line type="monotone" dataKey="community" stroke="#9ca3af" strokeWidth={2} strokeDasharray="5 5" name="Community Ø" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
