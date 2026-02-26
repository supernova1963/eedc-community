import {
  Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import type { CommunityGesamtwerte } from '../types'
import { MONATE } from '../constants'
import { fmtEnergy, fmtEnergyStr } from '../utils'

export default function CommunityImpact({ totals }: { totals: CommunityGesamtwerte }) {
  const pv = fmtEnergy(totals.pv_erzeugung_kwh)
  const eigen = fmtEnergy(totals.pv_eigenverbrauch_kwh)
  const einsp = fmtEnergy(totals.pv_einspeisung_kwh)
  const eigenProzent = totals.pv_erzeugung_kwh > 0
    ? ((totals.pv_eigenverbrauch_kwh / totals.pv_erzeugung_kwh) * 100).toFixed(0)
    : '0'

  // Äquivalente
  const haushalte = Math.round(totals.pv_erzeugung_kwh / 5000) // Ø 5.000 kWh/Jahr
  const baeume = Math.round(totals.co2_vermieden_kg / 20) // 1 Baum ≈ 20 kg CO2/Jahr
  const erdumrundungen = (totals.eauto_km / 40_075).toFixed(1) // Erdumfang 40.075 km
  const gasM3 = Math.round(totals.wp_waerme_kwh / 10) // 1 m³ Erdgas ≈ 10 kWh

  // Monatsdaten für Chart (chronologisch sortieren)
  const chartData = [...totals.monatliche_summen]
    .sort((a, b) => a.jahr !== b.jahr ? a.jahr - b.jahr : a.monat - b.monat)
    .map(m => ({
      name: `${MONATE[m.monat - 1]} ${m.jahr.toString().slice(2)}`,
      eigenverbrauch: Math.round(m.eigenverbrauch_kwh),
      einspeisung: Math.round(m.einspeisung_kwh),
      anlagen: m.anzahl_anlagen,
    }))

  return (
    <div className="space-y-6">
      {/* Impact Banner */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-500 rounded-lg shadow-lg p-8 text-white">
        <h2 className="text-xl font-bold mb-1 text-center">Gemeinsam für die Energiewende</h2>
        <p className="text-emerald-100 text-sm mb-6 text-center">
          Was unsere {totals.anzahl_anlagen} Anlagen zusammen erreicht haben
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
          <div className="text-center">
            <p className="text-3xl font-bold">{pv.value}</p>
            <p className="text-lg text-emerald-100">{pv.unit}</p>
            <p className="text-sm text-emerald-200 mt-1">PV erzeugt</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold">{eigen.value}</p>
            <p className="text-lg text-emerald-100">{eigen.unit}</p>
            <p className="text-sm text-emerald-200 mt-1">selbst verbraucht</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold">{einsp.value}</p>
            <p className="text-lg text-emerald-100">{einsp.unit}</p>
            <p className="text-sm text-emerald-200 mt-1">eingespeist</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold">{(totals.co2_vermieden_kg / 1000).toFixed(1)}</p>
            <p className="text-lg text-emerald-100">t CO₂</p>
            <p className="text-sm text-emerald-200 mt-1">vermieden</p>
          </div>
        </div>
        <p className="text-center text-emerald-100 text-sm italic">
          Gemeinsam haben wir so viel Strom erzeugt wie {haushalte} Haushalte in einem Jahr verbrauchen.
        </p>
      </div>

      {/* Energie-Bilanz */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Energie-Bilanz</h3>
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600 dark:text-gray-400">
              Eigenverbrauch: {fmtEnergyStr(totals.pv_eigenverbrauch_kwh)} ({eigenProzent}%)
            </span>
            <span className="text-gray-600 dark:text-gray-400">
              Einspeisung: {fmtEnergyStr(totals.pv_einspeisung_kwh)} ({100 - Number(eigenProzent)}%)
            </span>
          </div>
          <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-4 flex overflow-hidden">
            <div
              className="bg-orange-500 h-full transition-all"
              style={{ width: `${eigenProzent}%` }}
            />
            <div
              className="bg-amber-300 dark:bg-amber-400 h-full transition-all"
              style={{ width: `${100 - Number(eigenProzent)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>Eigenverbrauch</span>
            <span>Einspeisung</span>
          </div>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Installierte Leistung: <span className="font-semibold">{totals.gesamt_kwp.toFixed(1)} kWp</span>
          {totals.gesamt_speicher_kwh > 0 && (
            <> | Speicherkapazität: <span className="font-semibold">{totals.gesamt_speicher_kwh.toFixed(1)} kWh</span></>
          )}
        </p>
      </div>

      {/* Komponenten-Impact */}
      {(totals.speicher_anzahl > 0 || totals.wp_anzahl > 0 || totals.eauto_anzahl > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {totals.speicher_anzahl > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">🔋</span>
                <h4 className="font-semibold text-gray-900 dark:text-white">Speicher</h4>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">{totals.speicher_anzahl} Anlagen</p>
              <div className="mt-3 space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Kapazität gesamt</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{totals.gesamt_speicher_kwh.toFixed(0)} kWh</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Umgesetzt</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{fmtEnergyStr(totals.speicher_entladung_kwh)}</span>
                </div>
              </div>
            </div>
          )}
          {totals.wp_anzahl > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">♨️</span>
                <h4 className="font-semibold text-gray-900 dark:text-white">Wärmepumpe</h4>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">{totals.wp_anzahl} Anlagen</p>
              <div className="mt-3 space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Wärme erzeugt</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{fmtEnergyStr(totals.wp_waerme_kwh)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Strom eingesetzt</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{fmtEnergyStr(totals.wp_stromverbrauch_kwh)}</span>
                </div>
                {totals.wp_stromverbrauch_kwh > 0 && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Ø JAZ</span>
                    <span className="font-semibold text-gray-900 dark:text-white">{(totals.wp_waerme_kwh / totals.wp_stromverbrauch_kwh).toFixed(1)}</span>
                  </div>
                )}
              </div>
            </div>
          )}
          {(totals.eauto_anzahl > 0 || totals.wallbox_anzahl > 0) && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">🚗</span>
                <h4 className="font-semibold text-gray-900 dark:text-white">E-Mobilität</h4>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {totals.eauto_anzahl > 0 && `${totals.eauto_anzahl} E-Autos`}
                {totals.eauto_anzahl > 0 && totals.wallbox_anzahl > 0 && ' · '}
                {totals.wallbox_anzahl > 0 && `${totals.wallbox_anzahl} Wallboxen`}
              </p>
              <div className="mt-3 space-y-2">
                {totals.eauto_km > 0 && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Gefahren</span>
                    <span className="font-semibold text-gray-900 dark:text-white">{totals.eauto_km.toLocaleString('de-DE')} km</span>
                  </div>
                )}
                {totals.eauto_ladung_kwh > 0 && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Geladen</span>
                    <span className="font-semibold text-gray-900 dark:text-white">{fmtEnergyStr(totals.eauto_ladung_kwh)}</span>
                  </div>
                )}
                {totals.eauto_pv_kwh > 0 && totals.eauto_ladung_kwh > 0 && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">PV-Anteil</span>
                    <span className="font-semibold text-green-600 dark:text-green-400">
                      {((totals.eauto_pv_kwh / totals.eauto_ladung_kwh) * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* BKW-Zeile */}
      {totals.bkw_anzahl > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">🪟</span>
              <span className="font-semibold text-gray-900 dark:text-white">Balkonkraftwerke</span>
              <span className="text-sm text-gray-500 dark:text-gray-400">({totals.bkw_anzahl} Anlagen)</span>
            </div>
            <span className="font-semibold text-gray-900 dark:text-white">{fmtEnergyStr(totals.bkw_erzeugung_kwh)} erzeugt</span>
          </div>
        </div>
      )}

      {/* Monatlicher Verlauf */}
      {chartData.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Monatliche Erzeugung der Community
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" tick={{ fill: '#9ca3af' }} />
              <YAxis tick={{ fill: '#9ca3af' }} tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}`} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  const labels: Record<string, string> = {
                    eigenverbrauch: 'Eigenverbrauch',
                    einspeisung: 'Einspeisung',
                  }
                  return [`${(value / 1000).toFixed(1)} MWh`, labels[name] || name]
                }}
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#f3f4f6' }}
              />
              <Legend wrapperStyle={{ color: '#9ca3af' }} />
              <Area
                type="monotone"
                dataKey="eigenverbrauch"
                stackId="1"
                fill="#f59e0b"
                stroke="#f59e0b"
                name="Eigenverbrauch"
              />
              <Area
                type="monotone"
                dataKey="einspeisung"
                stackId="1"
                fill="#fcd34d"
                stroke="#fbbf24"
                name="Einspeisung"
              />
            </AreaChart>
          </ResponsiveContainer>
          <p className="text-xs text-gray-400 text-center mt-2">Y-Achse in MWh</p>
        </div>
      )}

      {/* Äquivalente */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Das entspricht...</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {totals.co2_vermieden_kg > 0 && (
            <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <span className="text-2xl">🌳</span>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white">{baeume.toLocaleString('de-DE')} Bäume</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">binden gleich viel CO₂ pro Jahr</p>
              </div>
            </div>
          )}
          {haushalte > 0 && (
            <div className="flex items-center gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <span className="text-2xl">🏠</span>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white">{haushalte} Haushalte</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">ein Jahr lang mit Strom versorgt</p>
              </div>
            </div>
          )}
          {totals.eauto_km > 0 && (
            <div className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <span className="text-2xl">🌍</span>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white">{erdumrundungen}× um die Erde</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{totals.eauto_km.toLocaleString('de-DE')} km elektrisch gefahren</p>
              </div>
            </div>
          )}
          {totals.wp_waerme_kwh > 0 && (
            <div className="flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <span className="text-2xl">🔥</span>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white">{gasM3.toLocaleString('de-DE')} m³ Erdgas</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">durch Wärmepumpen eingespart</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
