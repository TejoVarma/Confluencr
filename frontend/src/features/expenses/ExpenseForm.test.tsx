import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import { emptySummary, jsonResponse, mockFetch, resetStore } from '../../test/utils'
import { ExpenseForm } from './ExpenseForm'

async function fillValidForm() {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText('Title'), 'Groceries')
  await user.type(screen.getByLabelText('Amount'), '25.40')
  await user.selectOptions(screen.getByLabelText('Category'), 'food')
  return user
}

describe('ExpenseForm', () => {
  beforeEach(resetStore)

  it('shows validation errors and does not call the API', async () => {
    const fetch = mockFetch(() => jsonResponse({}))
    render(<ExpenseForm />)

    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))

    expect(screen.getByText('title is required')).toBeInTheDocument()
    expect(screen.getByText('amount is required')).toBeInTheDocument()
    expect(screen.getByText('category is required')).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalled()
  })

  it('disables submit while saving, then posts and resets', async () => {
    let resolvePost!: (r: Response) => void
    const fetch = mockFetch((url, init) => {
      if (init?.method === 'POST') return new Promise<Response>((r) => (resolvePost = r))
      if (url.includes('/summary')) return jsonResponse(emptySummary)
      return jsonResponse({ items: [], total_count: 0, total_amount: 0 })
    })
    render(<ExpenseForm />)
    const user = await fillValidForm()

    await user.click(screen.getByRole('button', { name: 'Add expense' }))

    const button = screen.getByRole('button', { name: 'Saving…' })
    expect(button).toBeDisabled()
    const [, init] = fetch.mock.calls[0]
    expect(fetch.mock.calls[0][0]).toBe('/api/expenses')
    expect(JSON.parse(init!.body as string)).toEqual({ title: 'Groceries', amount: 25.4, category: 'food' })

    resolvePost(jsonResponse({ id: '1' }, 201))

    expect(await screen.findByText('Expense added.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add expense' })).toBeEnabled()
    expect(screen.getByLabelText('Title')).toHaveValue('')
  })

  it('shows the server error message', async () => {
    mockFetch(() => jsonResponse({ error: 'date cannot be in the future' }, 400))
    render(<ExpenseForm />)
    const user = await fillValidForm()

    await user.click(screen.getByRole('button', { name: 'Add expense' }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('date cannot be in the future'))
    expect(screen.getByLabelText('Title')).toHaveValue('Groceries')
  })
})
