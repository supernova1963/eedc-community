export default function KPICard({ title, value, unit, subtitle, highlight, comparison }: {
  title: string
  value: string | number
  unit?: string
  subtitle?: string
  highlight?: boolean
  comparison?: { value: number; label: string }
}) {
  return (
    <div className={`rounded-lg shadow p-6 ${highlight ? 'bg-gradient-to-br from-orange-500 to-amber-500 text-white' : 'bg-white dark:bg-gray-800'}`}>
      <h3 className={`text-sm font-medium ${highlight ? 'text-orange-100' : 'text-gray-500 dark:text-gray-400'}`}>{title}</h3>
      <p className={`mt-2 text-3xl font-bold ${highlight ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
        {value}
        {unit && <span className={`text-lg font-normal ml-1 ${highlight ? 'text-orange-100' : 'text-gray-500 dark:text-gray-400'}`}>{unit}</span>}
      </p>
      {comparison && (
        <p className={`mt-1 text-sm font-medium ${comparison.value >= 0 ? 'text-green-400' : 'text-red-300'}`}>
          {comparison.value >= 0 ? '▲' : '▼'} {Math.abs(comparison.value).toFixed(0)}% {comparison.label}
        </p>
      )}
      {subtitle && <p className={`mt-1 text-sm ${highlight ? 'text-orange-100' : 'text-gray-500 dark:text-gray-400'}`}>{subtitle}</p>}
    </div>
  )
}
