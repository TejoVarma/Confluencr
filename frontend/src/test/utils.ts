import { vi } from 'vitest'
import { initialExpenseState, useExpenseStore } from '../store/expenseStore'

export function resetStore() {
  useExpenseStore.setState({ ...initialExpenseState, summaryMonth: '2026-10' })
}

export function jsonResponse(body: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response
}

/** Stubs global fetch; `handler` gets (url, init) and returns a Response (or a promise of one). */
export function mockFetch(handler: (url: string, init?: RequestInit) => Response | Promise<Response>) {
  const fn = vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))
  vi.stubGlobal('fetch', fn)
  return fn
}

export const emptySummary = {
  month: '2026-10',
  totals: { food: 0, travel: 0, bills: 0, other: 0 },
  total: 0,
}
