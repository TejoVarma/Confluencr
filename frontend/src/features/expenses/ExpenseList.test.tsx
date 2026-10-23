import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import { emptySummary, jsonResponse, mockFetch, resetStore } from '../../test/utils'
import type { Expense } from '../../types/expense'
import { ExpenseList } from './ExpenseList'

const expense = (id: string, amount: number): Expense => ({
  id,
  title: `Expense ${id}`,
  amount,
  category: 'food',
  date: '2026-10-01',
})

describe('ExpenseList', () => {
  beforeEach(resetStore)

  it('shows the total from the API, not the sum of the visible page', async () => {
    mockFetch(() => jsonResponse({ items: [expense('a', 5)], total_count: 25, total_amount: 999.5 }))
    render(<ExpenseList />)

    expect(await screen.findByText('Expense a')).toBeInTheDocument()
    expect(screen.getByTestId('total-amount')).toHaveTextContent('999.50')
    expect(screen.getByTestId('total-count')).toHaveTextContent('25 expenses')
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument()
  })

  it('shows loading then empty state', async () => {
    mockFetch(() => jsonResponse({ items: [], total_count: 0, total_amount: 0 }))
    render(<ExpenseList />)

    expect(screen.getByText('Loading expenses…')).toBeInTheDocument()
    expect(await screen.findByText('No expenses yet. Add your first one!')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
  })

  it('shows an error state with retry', async () => {
    let fail = true
    mockFetch(() =>
      fail
        ? jsonResponse({ error: 'Database is not configured' }, 503)
        : jsonResponse({ items: [expense('a', 1)], total_count: 1, total_amount: 1 }),
    )
    render(<ExpenseList />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Database is not configured')
    fail = false
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('Expense a')).toBeInTheDocument()
  })

  it('pages with Next/Previous and filters by category', async () => {
    const fetch = mockFetch((url) => {
      const page = new URL(url, 'http://x').searchParams.get('page')
      return jsonResponse({ items: [expense(`p${page}`, 1)], total_count: 15, total_amount: 15 })
    })
    const user = userEvent.setup()
    render(<ExpenseList />)

    await screen.findByText('Expense p1')
    await user.click(screen.getByRole('button', { name: 'Next' }))
    expect(await screen.findByText('Expense p2')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()

    await user.click(screen.getByRole('button', { name: 'Previous' }))
    expect(await screen.findByText('Expense p1')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Filter by category'), 'travel')
    await screen.findByText('Expense p1')
    expect(fetch.mock.calls.at(-1)![0]).toBe('/api/expenses?page=1&limit=10&category=travel')
  })

  it('deletes only after confirmation', async () => {
    let items = [expense('a', 10)]
    const fetch = mockFetch((url, init) => {
      if (init?.method === 'DELETE') {
        items = []
        return jsonResponse(null, 204)
      }
      if (url.includes('/summary')) return jsonResponse(emptySummary)
      return jsonResponse({ items, total_count: items.length, total_amount: items.length ? 10 : 0 })
    })
    const user = userEvent.setup()
    render(<ExpenseList />)
    const row = (await screen.findByText('Expense a')).closest('li')!

    await user.click(within(row).getByRole('button', { name: 'Delete Expense a' }))
    await user.click(within(row).getByRole('button', { name: 'Cancel' }))
    expect(fetch.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false)

    await user.click(within(row).getByRole('button', { name: 'Delete Expense a' }))
    await user.click(within(row).getByRole('button', { name: 'Yes, delete' }))

    expect(await screen.findByText('No expenses yet. Add your first one!')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith('/api/expenses/a', expect.objectContaining({ method: 'DELETE' }))
  })
})
