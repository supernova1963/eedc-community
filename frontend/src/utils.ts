export function fmtEnergy(kwh: number): { value: string; unit: string } {
  if (kwh >= 1_000_000) return { value: (kwh / 1_000_000).toFixed(1), unit: 'GWh' }
  if (kwh >= 10_000) return { value: (kwh / 1_000).toFixed(1), unit: 'MWh' }
  if (kwh >= 1_000) return { value: (kwh / 1_000).toFixed(2), unit: 'MWh' }
  return { value: kwh.toFixed(0), unit: 'kWh' }
}

export function fmtEnergyStr(kwh: number): string {
  const { value, unit } = fmtEnergy(kwh)
  return `${value} ${unit}`
}

export function getAnlageHash(): string | null {
  const params = new URLSearchParams(window.location.search)
  return params.get('anlage')
}

export function getCurrentPage(): 'main' | 'impressum' | 'datenschutz' {
  const path = window.location.pathname.toLowerCase()
  if (path === '/impressum' || path === '/impressum/') return 'impressum'
  if (path === '/datenschutz' || path === '/datenschutz/') return 'datenschutz'
  return 'main'
}

export function navigateTo(page: 'main' | 'impressum' | 'datenschutz') {
  const path = page === 'main' ? '/' : `/${page}`
  window.history.pushState({}, '', path)
  window.dispatchEvent(new PopStateEvent('popstate'))
}
