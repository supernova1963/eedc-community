export interface RegionStatistik {
  region: string
  anzahl_anlagen: number
  durchschnitt_kwp: number
  durchschnitt_spez_ertrag: number
  durchschnitt_autarkie: number | null
  anteil_mit_speicher: number
  anteil_mit_waermepumpe: number
  anteil_mit_eauto: number
  anteil_mit_wallbox: number
  anteil_mit_balkonkraftwerk: number
}

export interface MonatsStatistik {
  jahr: number
  monat: number
  anzahl_anlagen: number
  durchschnitt_ertrag_kwh: number
  durchschnitt_spez_ertrag: number
  median_spez_ertrag: number
  min_spez_ertrag: number
  max_spez_ertrag: number
}

export interface GesamtStatistik {
  anzahl_anlagen: number
  anzahl_monatswerte: number
  durchschnitt_kwp: number
  durchschnitt_speicher_kwh: number | null
  durchschnitt_spez_ertrag_jahr: number
  regionen: RegionStatistik[]
  letzte_monate: MonatsStatistik[]
}

export interface Monatswert {
  jahr: number
  monat: number
  ertrag_kwh: number
  einspeisung_kwh: number | null
  netzbezug_kwh: number | null
  autarkie_prozent: number | null
  eigenverbrauch_prozent: number | null
  spez_ertrag_kwh_kwp: number | null
  // Speicher-KPIs
  speicher_ladung_kwh: number | null
  speicher_entladung_kwh: number | null
  speicher_ladung_netz_kwh: number | null
  // Wärmepumpe-KPIs
  wp_stromverbrauch_kwh: number | null
  wp_heizwaerme_kwh: number | null
  wp_warmwasser_kwh: number | null
  // E-Auto-KPIs
  eauto_ladung_gesamt_kwh: number | null
  eauto_ladung_pv_kwh: number | null
  eauto_ladung_extern_kwh: number | null
  eauto_km: number | null
  eauto_v2h_kwh: number | null
  // Wallbox-KPIs
  wallbox_ladung_kwh: number | null
  wallbox_ladung_pv_kwh: number | null
  wallbox_ladevorgaenge: number | null
  // Balkonkraftwerk-KPIs
  bkw_erzeugung_kwh: number | null
  bkw_eigenverbrauch_kwh: number | null
  bkw_speicher_ladung_kwh: number | null
  bkw_speicher_entladung_kwh: number | null
  // Sonstiges-KPIs
  sonstiges_verbrauch_kwh: number | null
}

export interface AnlageData {
  anlage_hash: string
  region: string
  kwp: number
  ausrichtung: string
  neigung_grad: number
  speicher_kwh: number | null
  installation_jahr: number
  hat_waermepumpe: boolean
  hat_eauto: boolean
  hat_wallbox: boolean
  hat_balkonkraftwerk: boolean
  hat_sonstiges: boolean
  wallbox_kw: number | null
  bkw_wp: number | null
  sonstiges_bezeichnung: string | null
  monatswerte: Monatswert[]
}

export interface BenchmarkData {
  spez_ertrag_anlage: number
  spez_ertrag_durchschnitt: number
  spez_ertrag_region: number
  rang_gesamt: number
  anzahl_anlagen_gesamt: number
  rang_region: number
  anzahl_anlagen_region: number
}

// Erweiterte Benchmark-Typen
export type ZeitraumTyp = 'letzter_monat' | 'letzte_12_monate' | 'letztes_vollstaendiges_jahr' | 'jahr' | 'seit_installation'

export interface KPIVergleich {
  wert: number
  community_avg: number | null
  rang: number | null
  von: number | null
}

export interface PVBenchmark {
  spez_ertrag: KPIVergleich
  eigenverbrauch: KPIVergleich | null
  autarkie: KPIVergleich | null
}

export interface SpeicherBenchmark {
  kapazitaet: KPIVergleich | null
  zyklen_jahr: KPIVergleich | null
  nutzungsgrad: KPIVergleich | null
  wirkungsgrad: KPIVergleich | null
  netz_anteil: KPIVergleich | null
}

export interface WaermepumpeBenchmark {
  jaz: KPIVergleich | null
  stromverbrauch: KPIVergleich | null
  waermeerzeugung: KPIVergleich | null
  pv_anteil: KPIVergleich | null
}

export interface EAutoBenchmark {
  ladung_gesamt: KPIVergleich | null
  pv_anteil: KPIVergleich | null
  km: KPIVergleich | null
  verbrauch_100km: KPIVergleich | null
  v2h: KPIVergleich | null
}

export interface WallboxBenchmark {
  ladung: KPIVergleich | null
  pv_anteil: KPIVergleich | null
  ladevorgaenge: KPIVergleich | null
}

export interface BKWBenchmark {
  erzeugung: KPIVergleich | null
  spez_ertrag: KPIVergleich | null
  eigenverbrauch: KPIVergleich | null
}

export interface ErweiterteBenchmarkData {
  pv: PVBenchmark
  speicher: SpeicherBenchmark | null
  waermepumpe: WaermepumpeBenchmark | null
  eauto: EAutoBenchmark | null
  wallbox: WallboxBenchmark | null
  balkonkraftwerk: BKWBenchmark | null
}

export interface AnlageBenchmark {
  anlage: AnlageData
  benchmark: BenchmarkData
  vergleichs_jahr: number
  zeitraum?: ZeitraumTyp
  zeitraum_label?: string
  benchmark_erweitert?: ErweiterteBenchmarkData
}

export interface MonatsSumme {
  jahr: number
  monat: number
  pv_erzeugung_kwh: number
  eigenverbrauch_kwh: number
  einspeisung_kwh: number
  anzahl_anlagen: number
}

export interface CommunityGesamtwerte {
  anzahl_anlagen: number
  anzahl_monate_total: number
  stand: string
  gesamt_kwp: number
  gesamt_speicher_kwh: number
  pv_erzeugung_kwh: number
  pv_einspeisung_kwh: number
  pv_eigenverbrauch_kwh: number
  netzbezug_kwh: number
  speicher_anzahl: number
  speicher_ladung_kwh: number
  speicher_entladung_kwh: number
  wp_anzahl: number
  wp_stromverbrauch_kwh: number
  wp_waerme_kwh: number
  eauto_anzahl: number
  wallbox_anzahl: number
  eauto_km: number
  eauto_ladung_kwh: number
  eauto_pv_kwh: number
  wallbox_ladung_kwh: number
  wallbox_pv_kwh: number
  bkw_anzahl: number
  bkw_erzeugung_kwh: number
  co2_vermieden_kg: number
  monatliche_summen: MonatsSumme[]
}
