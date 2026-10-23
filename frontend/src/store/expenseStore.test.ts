import { beforeEach, describe, expect, it } from 'vitest'
import { emptySummary, jsonResponse, mockFetch, resetStore } from '../test/utils'
import type { Expense } from '../types/expense'
import { useExpenseStore } from './expenseStore'

const expense = (id: string): Expense => ({ id, title: id, amount: 1, category: 'food', date: '2026-10-01' })
const listCalls = (fetch: ReturnType<typeof mockFetch>) =>
  fetch.mock.calls.map(([url]) => String(url)).filter((url) => url.startsWith('/api/expenses?'))
const store = () => useExpenseStore.getState()

describe('expenseStore', () => {
  beforeEach(resetStore)

  it('fetchExpenses stores items and totals from the API', async () => {
    mockFetch(() => jsonResponse({ items: [expense('a')], total_count: 42, total_amount: 1234.56 }))

    await store().fetchExpenses()

    expect(store()).toMatchObject({ status: 'success', totalCount: 42, totalAmount: 1234.56, error: null })
    expect(store().items).toHaveLength(1)
  })

  it('fetchExpenses records the error message on failure', async () => {
    mockFetch(() => jsonResponse({ error: 'Database is not configured' }, 503))

    await store().fetchExpenses()

    expect(store()).toMatchObject({ status: 'error', error: 'Database is not configured' })
  })

  it('setCategory resets to page 1 and sends the category', async () => {
    const fetch = mockFetch(() => jsonResponse({ items: [expense('a')], total_count: 30, total_amount: 30 }))
    useExpenseStore.setState({ page: 3 })

    store().setCategory('travel')

    expect(store().page).toBe(1)
    await expect.poll(() => store().status).toBe('success')
    expect(listCalls(fetch).at(-1)).toBe('/api/expenses?page=1&limit=10&category=travel')
  })

  it('ignores a stale response that resolves after a newer request', async () => {
    const pending: Record<string, (r: Response) => void> = {}
    mockFetch((url) => new Promise<Response>((resolve) => (pending[new URL(url, 'http://x').searchParams.get('page')!] = resolve)))

    store().goToPage(1)
    store().goToPage(2)
    pending['2'](jsonResponse({ items: [expense('page2')], total_count: 20, total_amount: 20 }))
    await expect.poll(() => store().status).toBe('success')
    pending['1'](jsonResponse({ items: [expense('page1')], total_count: 20, total_amount: 20 }))
    await new Promise((r) => setTimeout(r, 0))

    expect(store().page).toBe(2)
    expect(store().items.map((e) => e.id)).toEqual(['page2'])
  })

  it('steps back a page when deleting the last item on the last page', async () => {
    let total = 11
    const fetch = mockFetch((url, init) => {
      if (init?.method === 'DELETE') {
        total = 10
        return jsonResponse(null, 204)
      }
      if (url.includes('/summary')) return jsonResponse(emptySummary)
      const page = Number(new URL(url, 'http://x').searchParams.get('page'))
      const items = page === 1 ? Array.from({ length: Math.min(total, 10) }, (_, i) => expense(`e${i}`)) : total > 10 ? [expense('e10')] : []
      return jsonResponse({ items, total_count: total, total_amount: total })
    })
    useExpenseStore.setState({ page: 2 })

    await store().removeExpense('e10')

    expect(store().page).toBe(1)
    expect(store().items).toHaveLength(10)
    expect(store().totalCount).toBe(10)
    expect(listCalls(fetch)).toEqual(['/api/expenses?page=2&limit=10', '/api/expenses?page=1&limit=10'])
  })

  it('addExpense resets to page 1 and refreshes the list and summary', async () => {
    const fetch = mockFetch((url, init) => {
      if (init?.method === 'POST') return jsonResponse(expense('new'), 201)
      if (url.includes('/summary')) return jsonResponse({ ...emptySummary, totals: { ...emptySummary.totals, food: 1 }, total: 1 })
      return jsonResponse({ items: [expense('new')], total_count: 1, total_amount: 1 })
    })
    useExpenseStore.setState({ page: 4 })

    await store().addExpense({ title: 'new', amount: 1, category: 'food' })

    expect(store().page).toBe(1)
    expect(store().summary?.total).toBe(1)
    const urls = fetch.mock.calls.map(([url]) => String(url))
    expect(urls).toContain('/api/expenses?page=1&limit=10')
    expect(urls).toContain('/api/expenses/summary?month=2026-10')
  })

  it('addExpense propagates server errors and does not refetch', async () => {
    const fetch = mockFetch(() => jsonResponse({ error: 'date cannot be in the future' }, 400))

    await expect(store().addExpense({ title: 'x', amount: 1, category: 'food' })).rejects.toThrow(
      'date cannot be in the future',
    )
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('fetchSummary sets the error state on failure', async () => {
    mockFetch(() => jsonResponse({ error: 'month must be in YYYY-MM format' }, 400))

    await store().fetchSummary()

    expect(store()).toMatchObject({ summaryStatus: 'error', summaryError: 'month must be in YYYY-MM format' })
  })

  it('setSummaryMonth fetches that month', async () => {
    const fetch = mockFetch(() => jsonResponse({ ...emptySummary, month: '2026-09' }))

    store().setSummaryMonth('2026-09')

    await expect.poll(() => store().summaryStatus).toBe('success')
    expect(fetch.mock.calls[0][0]).toBe('/api/expenses/summary?month=2026-09')
    expect(store().summary?.month).toBe('2026-09')
  })
})
