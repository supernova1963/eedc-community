import type { TabId } from '../../types'
import { useScrolled } from '../../hooks/useScrolled'

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
  // Hero ist ~61,8vh hoch – ab 300px ist er weitgehend weggescrollt
  const heroGone = useScrolled(300)

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 sticky top-0 z-20">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center">
          {/* Kompakter Brand – erscheint erst wenn Hero weg */}
          <div
            className={`shrink-0 overflow-hidden transition-all duration-300 ${
              heroGone ? 'max-w-[120px] opacity-100 mr-3' : 'max-w-0 opacity-0 mr-0'
            }`}
          >
            <span className="text-sm font-bold text-orange-600 dark:text-orange-400 whitespace-nowrap">
              ☀️ EEDC
            </span>
          </div>

          {/* Tab-Buttons */}
          <nav className="flex gap-1 -mb-px overflow-x-auto flex-1" aria-label="Tabs">
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
    </div>
  )
}
