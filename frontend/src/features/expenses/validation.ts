// Mirrors backend/app/schemas/expense.py so users get the same messages before the request is sent.
import { todayISO } from '../../lib/format'
import { CATEGORIES, type Category, type NewExpense } from '../../types/expense'

export const TITLE_MAX_LENGTH = 100
const MAX_AMOUNT = 9_999_999_999.99
const NUMBER_RE = /^-?(\d+\.?\d*|\.\d+)$/
const TWO_DECIMALS_RE = /^-?\d*(\.\d{0,2})?$/
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/

export interface ExpenseFormValues {
  title: string
  amount: string
  category: Category | ''
  date: string
}

export type ExpenseFormErrors = Partial<Record<keyof ExpenseFormValues, string>>

function isRealDate(value: string): boolean {
  const [year, month, day] = value.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.getFullYear() === year && d.getMonth() === month - 1 && d.getDate() === day
}

export function validateExpense(values: ExpenseFormValues, today: string = todayISO()): ExpenseFormErrors {
  const errors: ExpenseFormErrors = {}

  const title = values.title.trim()
  if (!title) errors.title = 'title is required'
  else if (title.length > TITLE_MAX_LENGTH) errors.title = `title must be at most ${TITLE_MAX_LENGTH} characters`

  const amount = values.amount.trim()
  if (!amount) errors.amount = 'amount is required'
  else if (!NUMBER_RE.test(amount)) errors.amount = 'amount must be a number'
  else if (Number(amount) <= 0) errors.amount = 'amount must be greater than 0'
  else if (!TWO_DECIMALS_RE.test(amount)) errors.amount = 'amount must have at most 2 decimal places'
  else if (Number(amount) > MAX_AMOUNT) errors.amount = `amount must be at most ${MAX_AMOUNT}`

  if (!values.category) errors.category = 'category is required'
  else if (!CATEGORIES.includes(values.category)) errors.category = `category must be one of: ${CATEGORIES.join(', ')}`

  if (values.date) {
    if (!DATE_RE.test(values.date)) errors.date = 'date must be a date in YYYY-MM-DD format'
    else if (!isRealDate(values.date)) errors.date = 'date must be a valid date'
    else if (values.date > today) errors.date = 'date cannot be in the future'
  }

  return errors
}

/** Converts validated form values into the API payload (date omitted -> server defaults to today). */
export function toNewExpense(values: ExpenseFormValues): NewExpense {
  return {
    title: values.title.trim(),
    amount: Number(values.amount),
    category: values.category as Category,
    ...(values.date ? { date: values.date } : {}),
  }
}
