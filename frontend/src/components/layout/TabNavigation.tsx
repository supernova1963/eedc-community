import type { TabId } from '../../types'

const TABS: { id: TabId; label: string }[] = [
  { id: 'uebersicht', label: 'Übersicht' },
  { id: 'monatsvergleich', label: 'Monatsvergleich' },
  { id: 'regionen', label: 'Regionen' },
  { id: 'impact', label: 'Impact' },
  { id: 'mitmachen', label: '🚀 Mitmachen' },
]

export default function TabNavigation({
  activeTab,
  onChange,
}: {
  activeTab: TabId
  onChange: (tab: TabId) => void
}) {
  return (
    <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div className="max-w-6xl mx-auto px-4">
        <nav className="flex gap-1 -mb-px overflow-x-auto" aria-label="Tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChange(tab.id)}
              className={`
                whitespace-nowrap py-3 px-4 text-sm font-medium border-b-2 transition-colors shrink-0
                ${activeTab === tab.id
                  ? 'border-orange-500 text-orange-600 dark:text-orange-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
    </div>
  )
}
