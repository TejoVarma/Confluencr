import type {
  Expense,
  ExpenseListParams,
  ExpenseListResponse,
  MonthlySummary,
  NewExpense,
} from '../types/expense'
import { request } from './client'

export function listExpenses(params: ExpenseListParams): Promise<ExpenseListResponse> {
  const query = new URLSearchParams({ page: String(params.page), limit: String(params.limit) })
  if (params.category) query.set('category', params.category)
  if (params.from) query.set('from', params.from)
  if (params.to) query.set('to', params.to)
  return request(`/expenses?${query}`)
}

export function createExpense(expense: NewExpense): Promise<Expense> {
  return request('/expenses', { method: 'POST', body: JSON.stringify(expense) })
}

export function deleteExpense(id: string): Promise<void> {
  return request(`/expenses/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function getMonthlySummary(month: string): Promise<MonthlySummary> {
  return request(`/expenses/summary?${new URLSearchParams({ month })}`)
}
