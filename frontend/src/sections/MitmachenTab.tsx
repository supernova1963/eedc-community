import { useState } from 'react'
import FadeIn from '../components/layout/FadeIn'

const HA_STEPS = [
  {
    nr: '1',
    title: 'Repository hinzufügen',
    text: 'In Home Assistant → Einstellungen → Add-ons → Add-on-Store → ⋮ → Repositories → URL eintragen.',
    code: 'https://github.com/supernova1963/eedc-homeassistant',
  },
  {
    nr: '2',
    title: 'Add-on installieren & starten',
    text: 'EEDC im Store suchen, installieren, Watchdog aktivieren, starten. Die Web-UI öffnet sich automatisch per Ingress.',
    code: null,
  },
  {
    nr: '3',
    title: 'Anlage einrichten',
    text: 'Anlage-Wizard starten: Stammdaten, Investitionen, Sensor-Mapping (HA-Sensoren → EEDC-Felder). Fertig.',
    code: null,
  },
]

const STANDALONE_STEPS = [
  {
    nr: '1',
    title: 'docker-compose.yml herunterladen',
    text: 'Die Compose-Datei aus dem Repository holen und in ein lokales Verzeichnis legen.',
    code: 'curl -O https://raw.githubusercontent.com/supernova1963/eedc/main/docker-compose.yml',
  },
  {
    nr: '2',
    title: 'Container starten',
    text: 'EEDC läuft auf Port 8099. Beim ersten Start wird die Datenbank automatisch initialisiert.',
    code: 'docker compose up -d',
  },
  {
    nr: '3',
    title: 'Anlage einrichten & Daten verbinden',
    text: 'Anlage-Wizard im Browser öffnen. Für Live-Daten MQTT-Inbound oder MQTT-Gateway konfigurieren.',
    code: 'http://localhost:8099',
  },
]

const FEATURES = [
  {
    icon: '📊',
    title: '8 Analyse-Dashboards',
    text: 'PV, Speicher, E-Auto, Wärmepumpe, Wallbox, Bilanz, Finanzen, CO₂ – alles auf einen Blick.',
  },
  {
    icon: '🔮',
    title: 'Ertragsprognose',
    text: 'GTI-basierte Kurzfristprognose (7 Tage) und PVGIS-Langzeitprognose mit SOLL/IST-Vergleich.',
  },
  {
    icon: '⚡',
    title: 'Live Dashboard',
    text: 'Echtzeit-Energiefluss, animiertes Flussdiagramm, Tagesverlauf. Via HA-Sensoren, MQTT-Inbound oder Geräte-Connector.',
  },
  {
    icon: '☁️',
    title: 'Portal-Import',
    text: 'Historische Daten direkt aus SMA, Fronius, Huawei, Growatt, Deye/Solarman und EcoFlow importieren.',
  },
  {
    icon: '🔌',
    title: 'MQTT-Inbound & Gateway',
    text: 'Universelle Datenschnittstelle für Home Assistant, ioBroker, Node-RED, openHAB und FHEM.',
  },
  {
    icon: '🏆',
    title: 'Community-Vergleich',
    text: 'Anonymer Benchmark: Rang bundesweit und regional, Komponenten-Vergleich, Trends.',
  },
]

const HA_EXTRAS = [
  { icon: '🔗', text: 'Sensor-Mapping Wizard – HA-Sensoren direkt auf EEDC-Felder abbilden' },
  { icon: '📥', text: 'HA Statistik-Import – Monatsdaten direkt aus dem Recorder (SQLite & MariaDB)' },
  { icon: '🔧', text: 'Geräte-Connectors – direkte HTTP-Integration für SMA, Fronius, Kostal, go-e, Shelly u.a.' },
  { icon: '📡', text: 'MQTT Auto-Publish – EEDC-KPIs als HA-Entitäten via MQTT Discovery' },
  { icon: '📤', text: 'REST-Sensor-Export – 50+ KPIs per REST für HA-Templates und Dashboards' },
]

function Step({ nr, title, text, code }: { nr: string; title: string; text: string; code: string | null }) {
  return (
    <div className="flex gap-4">
      <div className="shrink-0 w-8 h-8 rounded-full bg-orange-500 text-white text-sm font-bold flex items-center justify-center">
        {nr}
      </div>
      <div className="flex-1 pb-6">
        <p className="font-semibold text-gray-900 dark:text-white mb-1">{title}</p>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{text}</p>
        {code && (
          <code className="block text-xs bg-gray-900 dark:bg-gray-950 text-green-400 rounded-lg px-4 py-2.5 font-mono overflow-x-auto">
            {code}
          </code>
        )}
      </div>
    </div>
  )
}

export default function MitmachenTab() {
  const [variant, setVariant] = useState<'ha' | 'standalone'>('ha')

  return (
    <div className="space-y-10 max-w-4xl mx-auto">

      {/* Entscheidungsfrage */}
      <FadeIn>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Deine Anlage in der Community
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            Wähle dein Setup – beide Varianten sind kostenlos und Open Source.
          </p>

          <div className="inline-flex rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-1 shadow-sm">
            <button
              onClick={() => setVariant('ha')}
              className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                variant === 'ha'
                  ? 'bg-orange-500 text-white shadow'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              🏠 Mit Home Assistant
            </button>
            <button
              onClick={() => setVariant('standalone')}
              className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                variant === 'standalone'
                  ? 'bg-orange-500 text-white shadow'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              🐳 Standalone (Docker)
            </button>
          </div>
        </div>
      </FadeIn>

      {/* Varianten-Box */}
      <FadeIn delay={100}>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-orange-500 to-amber-400 px-6 py-4 text-white">
            {variant === 'ha' ? (
              <div>
                <h3 className="text-lg font-bold">EEDC als Home Assistant Add-on</h3>
                <p className="text-orange-100 text-sm mt-0.5">
                  Empfohlen · Sensor-Mapping, HA Statistik-Import, Geräte-Connectors
                </p>
              </div>
            ) : (
              <div>
                <h3 className="text-lg font-bold">EEDC Standalone</h3>
                <p className="text-orange-100 text-sm mt-0.5">
                  Unabhängig von Home Assistant · läuft mit Docker auf jedem System
                </p>
              </div>
            )}
          </div>

          {/* Voraussetzungen */}
          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/40 border-b border-gray-100 dark:border-gray-700 flex flex-wrap gap-3">
            {variant === 'ha' ? (
              <>
                <span className="text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full font-medium">Home Assistant OS oder Supervised</span>
                <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1 rounded-full font-medium">MQTT optional (für Live-Daten)</span>
              </>
            ) : (
              <>
                <span className="text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full font-medium">Docker &amp; docker compose</span>
                <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1 rounded-full font-medium">Linux · macOS · Windows</span>
                <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-3 py-1 rounded-full font-medium">MQTT optional (für Live-Daten)</span>
              </>
            )}
          </div>

          {/* Installation Steps */}
          <div className="px-6 pt-6 pb-2">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">Installation</p>
            {(variant === 'ha' ? HA_STEPS : STANDALONE_STEPS).map(s => (
              <Step key={s.nr} {...s} />
            ))}
          </div>

          {/* HA Extras */}
          {variant === 'ha' && (
            <div className="px-6 pb-6">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Zusätzlich mit Home Assistant</p>
              <div className="space-y-2">
                {HA_EXTRAS.map(e => (
                  <div key={e.text} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="shrink-0 mt-0.5">{e.icon}</span>
                    <span>{e.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Standalone MQTT Hinweis */}
          {variant === 'standalone' && (
            <div className="mx-6 mb-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
              <strong>Live-Daten ohne Home Assistant:</strong> MQTT-Inbound oder MQTT-Gateway konfigurieren.
              Kompatibel mit ioBroker, Node-RED, openHAB, FHEM und jedem System das MQTT spricht.
            </div>
          )}

          {/* CTA Button */}
          <div className="px-6 pb-6">
            <a
              href={
                variant === 'ha'
                  ? 'https://github.com/supernova1963/eedc-homeassistant'
                  : 'https://github.com/supernova1963/eedc'
              }
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block w-full text-center bg-gradient-to-r from-orange-500 to-amber-500 text-white font-semibold px-6 py-3 rounded-lg hover:from-orange-600 hover:to-amber-600 transition-all shadow-sm"
            >
              {variant === 'ha' ? '→ Zum HA Add-on Repository' : '→ Zum Standalone Repository'}
            </a>
          </div>
        </div>
      </FadeIn>

      {/* Feature Highlights */}
      <FadeIn delay={150}>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 text-center">
            Was dich erwartet
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map(f => (
              <div
                key={f.title}
                className="bg-white dark:bg-gray-800 rounded-xl shadow p-4 flex gap-3"
              >
                <span className="text-2xl shrink-0 mt-0.5">{f.icon}</span>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white text-sm mb-1">{f.title}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">{f.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </FadeIn>

      {/* Footer-Hinweis */}
      <FadeIn delay={200}>
        <div className="text-center text-sm text-gray-400 dark:text-gray-500 pb-4">
          <p>
            Open Source · MIT-Lizenz ·{' '}
            <a
              href="https://supernova1963.github.io/eedc-homeassistant/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-orange-500 hover:underline"
            >
              Dokumentation
            </a>
          </p>
        </div>
      </FadeIn>
    </div>
  )
}
