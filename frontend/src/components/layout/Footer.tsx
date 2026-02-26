import { navigateTo } from '../../utils'

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 dark:border-gray-700 mt-12 pt-6 pb-8">
      <div className="text-center text-sm text-gray-500 dark:text-gray-400 space-y-2">
        <p>
          Alle Daten werden anonym und ohne persönliche Informationen gespeichert.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <a
            href="https://github.com/supernova1963/eedc-homeassistant"
            className="text-orange-600 dark:text-orange-400 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            EEDC auf GitHub
          </a>
          <span className="text-gray-300 dark:text-gray-600">|</span>
          <button
            onClick={() => navigateTo('impressum')}
            className="text-orange-600 dark:text-orange-400 hover:underline"
          >
            Impressum
          </button>
          <span className="text-gray-300 dark:text-gray-600">|</span>
          <button
            onClick={() => navigateTo('datenschutz')}
            className="text-orange-600 dark:text-orange-400 hover:underline"
          >
            Datenschutz
          </button>
        </div>
      </div>
    </footer>
  )
}
