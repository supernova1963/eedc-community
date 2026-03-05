import { useState, useEffect } from 'react'
import type { MonatsVergleich, VerfuegbareMonate, MonatsKPI } from '../types'
import { MONATE } from '../constants'
import { REGION_NAMEN } from '../constants'

function KPIBlock({ label, kpi, unit, decimals = 1 }: { label: string; kpi: MonatsKPI; unit: string; decimals?: number }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      <div className="text-right">
        <span className="font-semibold text-gray-900 dark:text-white">
          {kpi.durchschnitt.toFixed(decimals)} {unit}
        </span>
        {kpi.anzahl_anlagen > 0 && (
          <span className="text-xs text-gray-400 ml-2">({kpi.anzahl_anlagen} Anl.)</span>
        )}
        {kpi.min !== null && kpi.max !== null && (
          <p className="text-xs text-gray-400">
            {kpi.min.toFixed(decimals)} – {kpi.max.toFixed(decimals)} {unit}
          </p>
        )}
      </div>
    </div>
  )
}

function KPISection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
      <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">{title}</h4>
      <div>{children}</div>
    </div>
  )
}

export default function MonatsvergleichTab() {
  const [verfuegbar, setVerfuegbar] = useState<VerfuegbareMonate | null>(null)
  const [daten, setDaten] = useState<MonatsVergleich | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingDaten, setLoadingDaten] = useState(false)
  const [selectedMonat, setSelectedMonat] = useState<string>('')

  // Verfügbare Monate laden
  useEffect(() => {
    fetch('/api/stats/verfuegbare-monate')
      .then(r => r.json())
      .then((data: VerfuegbareMonate) => {
        setVerfuegbar(data)
        if (data.monate.length > 0) {
          const neuester = data.monate[0]
          setSelectedMonat(`${neuester.jahr}-${neuester.monat}`)
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  // Monatsdaten laden wenn Auswahl sich ändert
  useEffect(() => {
    if (!selectedMonat) return
    const [jahr, monat] = selectedMonat.split('-').map(Number)
    setLoadingDaten(true)
    fetch(`/api/benchmark/monat/${jahr}/${monat}`)
      .then(r => {
        if (!r.ok) throw new Error('Keine Daten')
        return r.json()
      })
      .then((data: MonatsVergleich) => {
        setDaten(data)
        setLoadingDaten(false)
      })
      .catch(() => {
        setDaten(null)
        setLoadingDaten(false)
      })
  }, [selectedMonat])

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  if (!verfuegbar || verfuegbar.monate.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Noch keine Monatsdaten vorhanden.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Monats-Selektor */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 flex flex-wrap items-center gap-4">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Monat wählen:</label>
        <select
          value={selectedMonat}
          onChange={(e) => setSelectedMonat(e.target.value)}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
        >
          {verfuegbar.monate.map((m) => (
            <option key={`${m.jahr}-${m.monat}`} value={`${m.jahr}-${m.monat}`}>
              {MONATE[m.monat - 1]} {m.jahr} ({m.anzahl_anlagen} Anlagen)
            </option>
          ))}
        </select>
      </div>

      {loadingDaten && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-orange-500"></div>
        </div>
      )}

      {!loadingDaten && daten && (
        <>
          {/* Hero: Spez. Ertrag */}
          <div className="bg-gradient-to-r from-orange-500 to-amber-500 rounded-lg shadow-lg p-6 text-white text-center">
            <p className="text-orange-100 text-sm mb-1">
              Community-Durchschnitt {MONATE[daten.monat - 1]} {daten.jahr}
            </p>
            <p className="text-5xl font-bold">{daten.spez_ertrag.durchschnitt.toFixed(1)}</p>
            <p className="text-xl text-orange-100">kWh/kWp</p>
            <p className="text-orange-200 text-sm mt-2">
              Basierend auf {daten.anzahl_anlagen} Anlagen
              {daten.spez_ertrag.min !== null && daten.spez_ertrag.max !== null && (
                <> | Spanne: {daten.spez_ertrag.min.toFixed(1)} – {daten.spez_ertrag.max.toFixed(1)} kWh/kWp</>
              )}
            </p>
          </div>

          {/* PV-Kern-KPIs */}
          <KPISection title="PV-Ertrag">
            <KPIBlock label="Ertrag pro kWp" kpi={daten.spez_ertrag} unit="kWh/kWp" />
            {daten.autarkie && <KPIBlock label="Autarkie" kpi={daten.autarkie} unit="%" />}
            {daten.eigenverbrauch && <KPIBlock label="Eigenverbrauch" kpi={daten.eigenverbrauch} unit="%" />}
            {daten.einspeisung && <KPIBlock label="Einspeisung" kpi={daten.einspeisung} unit="kWh" decimals={0} />}
            {daten.netzbezug && <KPIBlock label="Netzbezug" kpi={daten.netzbezug} unit="kWh" decimals={0} />}
          </KPISection>

          {/* Komponenten-KPIs in Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {(daten.speicher_ladung || daten.speicher_entladung || daten.speicher_wirkungsgrad) && (
              <KPISection title="Speicher">
                {daten.speicher_ladung && <KPIBlock label="Ladung" kpi={daten.speicher_ladung} unit="kWh" decimals={0} />}
                {daten.speicher_entladung && <KPIBlock label="Entladung" kpi={daten.speicher_entladung} unit="kWh" decimals={0} />}
                {daten.speicher_wirkungsgrad && <KPIBlock label="Wirkungsgrad" kpi={daten.speicher_wirkungsgrad} unit="%" />}
              </KPISection>
            )}

            {(daten.wp_jaz || daten.wp_stromverbrauch || daten.wp_waerme) && (
              <KPISection title="Wärmepumpe">
                {daten.wp_jaz && <KPIBlock label="JAZ" kpi={daten.wp_jaz} unit="" decimals={2} />}
                {daten.wp_stromverbrauch && <KPIBlock label="Strom" kpi={daten.wp_stromverbrauch} unit="kWh" decimals={0} />}
                {daten.wp_waerme && <KPIBlock label="Wärme" kpi={daten.wp_waerme} unit="kWh" decimals={0} />}
              </KPISection>
            )}

            {(daten.eauto_ladung || daten.eauto_pv_anteil || daten.eauto_km) && (
              <KPISection title="E-Auto">
                {daten.eauto_ladung && <KPIBlock label="Ladung" kpi={daten.eauto_ladung} unit="kWh" decimals={0} />}
                {daten.eauto_pv_anteil && <KPIBlock label="PV-Anteil" kpi={daten.eauto_pv_anteil} unit="%" />}
                {daten.eauto_km && <KPIBlock label="Gefahren" kpi={daten.eauto_km} unit="km" decimals={0} />}
              </KPISection>
            )}

            {(daten.wallbox_ladung || daten.wallbox_pv_anteil) && (
              <KPISection title="Wallbox">
                {daten.wallbox_ladung && <KPIBlock label="Ladung" kpi={daten.wallbox_ladung} unit="kWh" decimals={0} />}
                {daten.wallbox_pv_anteil && <KPIBlock label="PV-Anteil" kpi={daten.wallbox_pv_anteil} unit="%" />}
              </KPISection>
            )}

            {daten.bkw_erzeugung && (
              <KPISection title="Balkonkraftwerk">
                <KPIBlock label="Erzeugung" kpi={daten.bkw_erzeugung} unit="kWh" decimals={0} />
              </KPISection>
            )}
          </div>

          {/* Regionale Aufschlüsselung */}
          {daten.regionen && daten.regionen.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
              <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                Regionale Aufschlüsselung
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-2 text-gray-500 dark:text-gray-400 font-medium">Region</th>
                      <th className="text-right py-2 text-gray-500 dark:text-gray-400 font-medium">Anlagen</th>
                      <th className="text-right py-2 text-gray-500 dark:text-gray-400 font-medium">kWh/kWp</th>
                      <th className="text-right py-2 text-gray-500 dark:text-gray-400 font-medium">Autarkie</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...daten.regionen]
                      .sort((a, b) => b.spez_ertrag - a.spez_ertrag)
                      .map((r) => (
                        <tr key={r.region} className="border-b border-gray-50 dark:border-gray-700/50">
                          <td className="py-2 text-gray-900 dark:text-white font-medium">
                            {REGION_NAMEN[r.region] || r.region}
                          </td>
                          <td className="py-2 text-right text-gray-600 dark:text-gray-400">{r.anzahl_anlagen}</td>
                          <td className="py-2 text-right font-semibold text-gray-900 dark:text-white">{r.spez_ertrag.toFixed(1)}</td>
                          <td className="py-2 text-right text-gray-600 dark:text-gray-400">
                            {r.autarkie !== null ? `${r.autarkie.toFixed(0)}%` : '–'}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
