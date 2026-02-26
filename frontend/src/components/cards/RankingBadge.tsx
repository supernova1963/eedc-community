export default function RankingBadge({ rang, total, label }: { rang: number; total: number; label: string }) {
  const prozent = ((total - rang + 1) / total) * 100
  const medalColor = rang === 1 ? 'text-yellow-500' : rang === 2 ? 'text-gray-400' : rang === 3 ? 'text-amber-600' : 'text-gray-600 dark:text-gray-400'
  const medal = rang <= 3 ? ['🥇', '🥈', '🥉'][rang - 1] : `#${rang}`

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{label}</p>
      <p className={`text-4xl font-bold ${medalColor}`}>{medal}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">von {total} Anlagen</p>
      <div className="mt-3 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className="bg-gradient-to-r from-orange-500 to-amber-500 h-2 rounded-full"
          style={{ width: `${prozent}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Top {(100 - prozent + 1).toFixed(0)}%</p>
    </div>
  )
}
