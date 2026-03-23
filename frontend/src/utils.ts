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

/**
 * Fetch JSON with detailed error reporting.
 * Shows status code, content-type and response snippet on failure.
 */
export async function fetchJson<T>(url: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(url)
  } catch (err) {
    throw new Error(`Netzwerkfehler bei ${url}: ${err instanceof Error ? err.message : String(err)}`)
  }

  const contentType = res.headers.get('content-type') || 'unbekannt'

  if (!res.ok) {
    let body = ''
    try { body = (await res.text()).slice(0, 200) } catch { /* ignore */ }
    throw new Error(
      `HTTP ${res.status} bei ${url} (Content-Type: ${contentType})${body ? ` — ${body}` : ''}`
    )
  }

  const text = await res.text()

  try {
    return JSON.parse(text) as T
  } catch (err) {
    // Show first 200 chars of the response that failed to parse
    const snippet = text.slice(0, 200)
    throw new Error(
      `JSON-Parse-Fehler bei ${url} (Content-Type: ${contentType}, ${text.length} Bytes): ${snippet}`
    )
  }
}
