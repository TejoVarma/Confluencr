export const CATEGORIES = ['food', 'travel', 'bills', 'other'] as const
export type Category = (typeof CATEGORIES)[number]

export interface Expense {
  id: string
  title: string
  amount: number
  category: Category
  date: string
  created_at?: string | null
}

export interface NewExpense {
  title: string
  amount: number
  category: Category
  date?: string
}

export interface ExpenseListParams {
  category?: Category | ''
  from?: string
  to?: string
  page: number
  limit: number
}

export interface ExpenseListResponse {
  items: Expense[]
  total_count: number
  total_amount: number
}

export interface MonthlySummary {
  month: string
  totals: Record<Category, number>
  total: number
}
