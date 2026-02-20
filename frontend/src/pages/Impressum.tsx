/**
 * Impressum gemäß TMG §5 / DDG §5
 */

interface ImpressumProps {
  onBack: () => void
}

export default function Impressum({ onBack }: ImpressumProps) {
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
          <h1 className="text-3xl font-bold">Impressum</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-8 space-y-6">
          {/* Angaben gemäß § 5 TMG / § 5 DDG */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              Angaben gemäß § 5 TMG / § 5 DDG
            </h2>
            <div className="text-gray-700 space-y-1">
              <p className="font-medium">Gernot Rau</p>
              <p>Am Sträßchen 3</p>
              <p>51588 Nümbrecht</p>
              <p>Deutschland</p>
            </div>
          </section>

          {/* Kontakt */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Kontakt</h2>
            <div className="text-gray-700">
              <p>
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

          {/* Verantwortlich für den Inhalt */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              Verantwortlich für den Inhalt gemäß § 18 Abs. 2 MStV
            </h2>
            <div className="text-gray-700 space-y-1">
              <p className="font-medium">Gernot Rau</p>
              <p>Am Sträßchen 3</p>
              <p>51588 Nümbrecht</p>
            </div>
          </section>

          {/* Haftungsausschluss */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              Haftungsausschluss
            </h2>

            <h3 className="text-lg font-medium text-gray-800 mt-4 mb-2">
              Haftung für Inhalte
            </h3>
            <p className="text-gray-700">
              Die Inhalte dieser Seite wurden mit größter Sorgfalt erstellt. Für die
              Richtigkeit, Vollständigkeit und Aktualität der Inhalte kann jedoch keine
              Gewähr übernommen werden. Als Diensteanbieter bin ich gemäß § 7 Abs. 1 TMG
              für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen
              verantwortlich. Nach §§ 8 bis 10 TMG bin ich als Diensteanbieter jedoch
              nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu
              überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige
              Tätigkeit hinweisen.
            </p>

            <h3 className="text-lg font-medium text-gray-800 mt-4 mb-2">
              Haftung für Links
            </h3>
            <p className="text-gray-700">
              Diese Seite enthält Links zu externen Webseiten Dritter, auf deren Inhalte
              ich keinen Einfluss habe. Deshalb kann ich für diese fremden Inhalte auch
              keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets
              der jeweilige Anbieter oder Betreiber der Seiten verantwortlich.
            </p>
          </section>

          {/* Urheberrecht */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Urheberrecht</h2>
            <p className="text-gray-700">
              Die durch den Seitenbetreiber erstellten Inhalte und Werke auf diesen
              Seiten unterliegen dem deutschen Urheberrecht. Die Software (EEDC) ist
              unter der MIT-Lizenz veröffentlicht und Open Source verfügbar auf{' '}
              <a
                href="https://github.com/supernova1963/eedc-homeassistant"
                target="_blank"
                rel="noopener noreferrer"
                className="text-orange-600 hover:underline"
              >
                GitHub
              </a>
              .
            </p>
          </section>

          {/* Projektbezug */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              Über dieses Projekt
            </h2>
            <p className="text-gray-700">
              EEDC Community ist Teil des EEDC-Projekts (Energie Effizienz Data Center)
              – einem Open-Source-Tool zur Analyse von PV-Anlagen. Die Community-Plattform
              ermöglicht den anonymen Vergleich von PV-Anlagendaten zur gegenseitigen
              Unterstützung und Optimierung. Das Projekt wird privat und ohne kommerzielle
              Absichten betrieben.
            </p>
          </section>
        </div>
      </main>
    </div>
  )
}
