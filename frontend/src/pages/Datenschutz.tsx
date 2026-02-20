/**
 * Datenschutzerklärung gemäß DSGVO Art. 13/14
 */

interface DatenschutzProps {
  onBack: () => void
}

export default function Datenschutz({ onBack }: DatenschutzProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 to-amber-500 text-white py-8">
        <div className="max-w-4xl mx-auto px-4">
          <button
            onClick={onBack}
            className="text-orange-100 hover:text-white mb-4 inline-flex items-center gap-1"
          >
            ← Zurück
          </button>
          <h1 className="text-3xl font-bold">Datenschutzerklärung</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-8 space-y-8">
          {/* Einleitung */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              1. Datenschutz auf einen Blick
            </h2>
            <p className="text-gray-700 mb-4">
              Der Schutz Ihrer Daten ist uns wichtig. Diese Datenschutzerklärung
              informiert Sie darüber, welche Daten wir erheben und wie wir diese
              verwenden.
            </p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-medium text-green-800 mb-2">
                Zusammenfassung: Anonymität hat Priorität
              </h3>
              <ul className="text-green-700 text-sm space-y-1">
                <li>✓ Keine persönlichen Daten (Name, Adresse, E-Mail) werden gespeichert</li>
                <li>✓ PLZ wird auf Bundesland reduziert (z.B. 51588 → NW)</li>
                <li>✓ Anlagen-Hash ist nicht rückführbar</li>
                <li>✓ Sie können Ihre Daten jederzeit löschen</li>
                <li>✓ Keine Cookies, kein Tracking, keine Werbung</li>
              </ul>
            </div>
          </section>

          {/* Verantwortlicher */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              2. Verantwortlicher
            </h2>
            <div className="text-gray-700 space-y-1">
              <p className="font-medium">Gernot Rau</p>
              <p>Am Sträßchen 3</p>
              <p>51588 Nümbrecht</p>
              <p>Deutschland</p>
              <p className="mt-2">
                E-Mail:{' '}
                <a
                  href="mailto:gernot.rau@icloud.com"
                  className="text-orange-600 hover:underline"
                >
                  gernot.rau@icloud.com
                </a>
              </p>
            </div>
          </section>

          {/* Welche Daten */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              3. Welche Daten werden erhoben?
            </h2>

            <h3 className="text-lg font-medium text-gray-800 mt-4 mb-2">
              3.1 Anlagendaten (bei freiwilliger Teilnahme)
            </h3>
            <p className="text-gray-700 mb-3">
              Wenn Sie Ihre PV-Anlagendaten mit der Community teilen, werden folgende
              <strong> anonymisierten</strong> Daten gespeichert:
            </p>
            <table className="w-full text-sm border-collapse mb-4">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 px-3 py-2 text-left">Datum</th>
                  <th className="border border-gray-300 px-3 py-2 text-left">Zweck</th>
                  <th className="border border-gray-300 px-3 py-2 text-left">Anonymisierung</th>
                </tr>
              </thead>
              <tbody className="text-gray-700">
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Region (Bundesland)</td>
                  <td className="border border-gray-300 px-3 py-2">Regionaler Vergleich</td>
                  <td className="border border-gray-300 px-3 py-2">PLZ → 2-Buchstaben-Code</td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Anlagenleistung (kWp)</td>
                  <td className="border border-gray-300 px-3 py-2">Spez. Ertrag berechnen</td>
                  <td className="border border-gray-300 px-3 py-2">Gerundet auf 0,1 kWp</td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Ausrichtung/Neigung</td>
                  <td className="border border-gray-300 px-3 py-2">Vergleich ähnlicher Anlagen</td>
                  <td className="border border-gray-300 px-3 py-2">Kategorisiert</td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Monatserträge (kWh)</td>
                  <td className="border border-gray-300 px-3 py-2">Benchmark-Berechnung</td>
                  <td className="border border-gray-300 px-3 py-2">Gerundet</td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Ausstattung</td>
                  <td className="border border-gray-300 px-3 py-2">Statistik (% mit Speicher, etc.)</td>
                  <td className="border border-gray-300 px-3 py-2">Nur Ja/Nein</td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Komponenten-Daten</td>
                  <td className="border border-gray-300 px-3 py-2">Benchmark (Speicher, WP, E-Auto, Wallbox, BKW)</td>
                  <td className="border border-gray-300 px-3 py-2">Nur aggregierte Werte (kWh/Monat)</td>
                </tr>
              </tbody>
            </table>
            <p className="text-gray-700">
              <strong>Nicht gespeichert werden:</strong> Name, E-Mail-Adresse, exakte
              Adresse, IP-Adresse (dauerhaft), Seriennummern oder andere identifizierende
              Merkmale.
            </p>

            <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">
              3.2 Anlage-Hash (Pseudonymisierung)
            </h3>
            <p className="text-gray-700">
              Für Updates und Löschungen wird ein kryptografischer Hash (SHA-256)
              generiert. Dieser Hash wird aus Anlagendaten und einem serverseitigen
              Geheimnis berechnet und kann <strong>nicht rückwärts</strong> aufgelöst
              werden. Er dient ausschließlich dazu, Ihre Anlage wiederzuerkennen, wenn
              Sie Daten aktualisieren oder löschen möchten.
            </p>

            <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">
              3.3 Server-Logs (temporär)
            </h3>
            <p className="text-gray-700">
              Beim Zugriff auf diese Website werden standardmäßig folgende Daten
              temporär in Server-Logs gespeichert:
            </p>
            <ul className="list-disc list-inside text-gray-700 mt-2">
              <li>IP-Adresse (für Rate-Limiting, max. 1 Stunde)</li>
              <li>Zeitpunkt des Zugriffs</li>
              <li>Aufgerufene Seite</li>
            </ul>
            <p className="text-gray-700 mt-2">
              Diese Daten werden nach spätestens 24 Stunden automatisch gelöscht und
              dienen ausschließlich dem Schutz vor Missbrauch.
            </p>
          </section>

          {/* Rechtsgrundlage */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              4. Rechtsgrundlage
            </h2>
            <p className="text-gray-700">
              Die Verarbeitung der Anlagendaten erfolgt auf Grundlage Ihrer{' '}
              <strong>Einwilligung</strong> (Art. 6 Abs. 1 lit. a DSGVO). Sie erteilen
              diese Einwilligung aktiv, wenn Sie im EEDC Add-on auf "Mit Community
              teilen" klicken. Die Verarbeitung der Server-Logs erfolgt auf Grundlage
              unseres <strong>berechtigten Interesses</strong> (Art. 6 Abs. 1 lit. f
              DSGVO) am sicheren Betrieb der Website.
            </p>
          </section>

          {/* Zweck */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              5. Zweck der Datenverarbeitung
            </h2>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>
                <strong>Benchmark:</strong> Vergleich Ihrer PV-Anlage mit ähnlichen
                Anlagen in der Community
              </li>
              <li>
                <strong>Statistik:</strong> Aggregierte Auswertungen (Durchschnittswerte,
                regionale Vergleiche)
              </li>
              <li>
                <strong>Optimierung:</strong> Erkennung von Verbesserungspotenzial durch
                Vergleich
              </li>
            </ul>
            <p className="text-gray-700 mt-3">
              Es erfolgt <strong>keine</strong> Weitergabe an Dritte, keine Nutzung für
              Werbung und kein Verkauf von Daten.
            </p>
          </section>

          {/* Speicherdauer */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              6. Speicherdauer
            </h2>
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 px-3 py-2 text-left">Datenart</th>
                  <th className="border border-gray-300 px-3 py-2 text-left">Speicherdauer</th>
                </tr>
              </thead>
              <tbody className="text-gray-700">
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Anlagendaten</td>
                  <td className="border border-gray-300 px-3 py-2">
                    Bis Sie diese löschen oder widerrufen
                  </td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Rate-Limit-Daten (IP)</td>
                  <td className="border border-gray-300 px-3 py-2">Maximal 1 Stunde</td>
                </tr>
                <tr>
                  <td className="border border-gray-300 px-3 py-2">Server-Logs</td>
                  <td className="border border-gray-300 px-3 py-2">Maximal 24 Stunden</td>
                </tr>
              </tbody>
            </table>
          </section>

          {/* Ihre Rechte */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              7. Ihre Rechte
            </h2>
            <p className="text-gray-700 mb-3">
              Sie haben folgende Rechte bezüglich Ihrer Daten:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              <li>
                <strong>Auskunft (Art. 15 DSGVO):</strong> Sie können erfragen, welche
                Daten über Sie gespeichert sind.
              </li>
              <li>
                <strong>Löschung (Art. 17 DSGVO):</strong> Sie können Ihre Daten
                jederzeit über das EEDC Add-on oder durch Kontakt löschen lassen.
              </li>
              <li>
                <strong>Widerruf (Art. 7 Abs. 3 DSGVO):</strong> Sie können Ihre
                Einwilligung jederzeit widerrufen (durch Löschen der Daten).
              </li>
              <li>
                <strong>Beschwerde:</strong> Sie haben das Recht, sich bei einer
                Aufsichtsbehörde zu beschweren.
              </li>
            </ul>
          </section>

          {/* Cookies */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              8. Cookies und Tracking
            </h2>
            <p className="text-gray-700">
              Diese Website verwendet <strong>keine Cookies</strong> und kein Tracking.
              Es werden keine Analyse-Tools (wie Google Analytics) oder Social-Media-Plugins
              eingesetzt.
            </p>
          </section>

          {/* Hosting */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              9. Hosting
            </h2>
            <p className="text-gray-700">
              Diese Website wird auf eigener Infrastruktur des Betreibers gehostet.
              Die Server befinden sich in Deutschland.
            </p>
          </section>

          {/* Datensicherheit */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              10. Datensicherheit
            </h2>
            <p className="text-gray-700">
              Die Übertragung erfolgt ausschließlich verschlüsselt über HTTPS
              (TLS 1.2/1.3). Die Datenbank ist durch Zugriffskontrollen geschützt
              und nur vom Betreiber erreichbar.
            </p>
          </section>

          {/* Änderungen */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              11. Änderungen dieser Datenschutzerklärung
            </h2>
            <p className="text-gray-700">
              Diese Datenschutzerklärung kann bei Bedarf angepasst werden. Die aktuelle
              Version ist immer auf dieser Seite verfügbar.
            </p>
            <p className="text-gray-500 text-sm mt-2">
              Stand: Februar 2026
            </p>
          </section>
        </div>
      </main>
    </div>
  )
}
