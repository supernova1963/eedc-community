import type { TabId } from '../../types'

const CONTENT_TABS: { id: TabId; label: string }[] = [
  { id: 'uebersicht', label: 'Übersicht' },
  { id: 'monatsvergleich', label: 'Monatsvergleich' },
  { id: 'regionen', label: 'Regionen' },
  { id: 'impact', label: 'Impact' },
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
        <div className="flex items-center">
          {/* Content-Tabs */}
          <nav className="flex gap-1 -mb-px overflow-x-auto flex-1" aria-label="Tabs">
            {CONTENT_TABS.map((tab) => (
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

          {/* Mitmachen – Orange CTA-Button rechtsbündig */}
          <div className="shrink-0 pl-2 py-2">
            <button
              type="button"
              onClick={() => onChange('mitmachen')}
              className={`
                whitespace-nowrap px-4 py-1.5 rounded-full text-sm font-semibold transition-all
                ${activeTab === 'mitmachen'
                  ? 'bg-orange-600 text-white shadow-md'
                  : 'bg-orange-500 text-white hover:bg-orange-600 shadow-sm hover:shadow-md'
                }
              `}
            >
              Mitmachen
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
