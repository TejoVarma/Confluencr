import { create } from 'zustand'
import * as api from '../api/expenses'
import { errorMessage } from '../api/client'
import { currentMonth } from '../lib/format'
import type { Category, Expense, MonthlySummary, NewExpense } from '../types/expense'

export type LoadStatus = 'idle' | 'loading' | 'success' | 'error'

interface ExpenseState {
  items: Expense[]
  totalCount: number
  totalAmount: number
  category: Category | ''
  page: number
  limit: number
  status: LoadStatus
  error: string | null

  summaryMonth: string
  summary: MonthlySummary | null
  summaryStatus: LoadStatus
  summaryError: string | null

  fetchExpenses: () => Promise<void>
  setCategory: (category: Category | '') => void
  goToPage: (page: number) => void
  addExpense: (expense: NewExpense) => Promise<void>
  removeExpense: (id: string) => Promise<void>
  fetchSummary: () => Promise<void>
  setSummaryMonth: (month: string) => void
}

export const PAGE_SIZE = 10

// Lets us drop responses from requests that were superseded (e.g. fast paging/filtering).
let listRequestId = 0
let summaryRequestId = 0

export const initialExpenseState = {
  items: [],
  totalCount: 0,
  totalAmount: 0,
  category: '' as const,
  page: 1,
  limit: PAGE_SIZE,
  status: 'idle' as const,
  error: null,
  summaryMonth: currentMonth(),
  summary: null,
  summaryStatus: 'idle' as const,
  summaryError: null,
}

export const useExpenseStore = create<ExpenseState>()((set, get) => ({
  ...initialExpenseState,

  fetchExpenses: async () => {
    const requestId = ++listRequestId
    const { category, page, limit } = get()
    set({ status: 'loading', error: null })
    try {
      const data = await api.listExpenses({ category, page, limit })
      if (requestId !== listRequestId) return
      // If the current page emptied out (e.g. after a delete), step back to the last real page.
      const lastPage = Math.max(1, Math.ceil(data.total_count / limit))
      if (data.items.length === 0 && page > lastPage) {
        set({ page: lastPage })
        return get().fetchExpenses()
      }
      set({
        items: data.items,
        totalCount: data.total_count,
        totalAmount: data.total_amount,
        status: 'success',
      })
    } catch (error) {
      if (requestId !== listRequestId) return
      set({ status: 'error', error: errorMessage(error) })
    }
  },

  setCategory: (category) => {
    set({ category, page: 1 })
    void get().fetchExpenses()
  },

  goToPage: (page) => {
    set({ page: Math.max(1, page) })
    void get().fetchExpenses()
  },

  // Errors propagate to the caller so the form can show the server message.
  addExpense: async (expense) => {
    await api.createExpense(expense)
    set({ page: 1 })
    await Promise.all([get().fetchExpenses(), get().fetchSummary()])
  },

  removeExpense: async (id) => {
    await api.deleteExpense(id)
    await Promise.all([get().fetchExpenses(), get().fetchSummary()])
  },

  fetchSummary: async () => {
    const requestId = ++summaryRequestId
    set({ summaryStatus: 'loading', summaryError: null })
    try {
      const summary = await api.getMonthlySummary(get().summaryMonth)
      if (requestId !== summaryRequestId) return
      set({ summary, summaryStatus: 'success' })
    } catch (error) {
      if (requestId !== summaryRequestId) return
      set({ summaryStatus: 'error', summaryError: errorMessage(error) })
    }
  },

  setSummaryMonth: (month) => {
    set({ summaryMonth: month })
    void get().fetchSummary()
  },
}))
