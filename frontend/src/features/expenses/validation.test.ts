import { describe, expect, it } from 'vitest'
import { toNewExpense, validateExpense, type ExpenseFormValues } from './validation'

const TODAY = '2026-10-23'
const valid: ExpenseFormValues = { title: 'Lunch', amount: '12.50', category: 'food', date: '' }
const check = (overrides: Partial<ExpenseFormValues>) => validateExpense({ ...valid, ...overrides }, TODAY)

describe('validateExpense', () => {
  it('accepts valid input', () => {
    expect(check({})).toEqual({})
    expect(check({ date: TODAY })).toEqual({})
    expect(check({ title: 'x'.repeat(100), amount: '7' })).toEqual({})
  })

  it.each([
    [{ title: '' }, 'title', 'title is required'],
    [{ title: '   ' }, 'title', 'title is required'],
    [{ title: 'x'.repeat(101) }, 'title', 'title must be at most 100 characters'],
    [{ amount: '' }, 'amount', 'amount is required'],
    [{ amount: 'abc' }, 'amount', 'amount must be a number'],
    [{ amount: '0' }, 'amount', 'amount must be greater than 0'],
    [{ amount: '-3' }, 'amount', 'amount must be greater than 0'],
    [{ amount: '1.234' }, 'amount', 'amount must have at most 2 decimal places'],
    [{ category: '' }, 'category', 'category is required'],
    [{ date: '2026-10-24' }, 'date', 'date cannot be in the future'],
    [{ date: '2026-02-30' }, 'date', 'date must be a valid date'],
  ] as const)('%o -> %s error', (overrides, field, message) => {
    expect(check(overrides)[field]).toBe(message)
  })
})

describe('toNewExpense', () => {
  it('trims, converts amount, and omits empty date', () => {
    expect(toNewExpense({ ...valid, title: ' Lunch ' })).toEqual({ title: 'Lunch', amount: 12.5, category: 'food' })
    expect(toNewExpense({ ...valid, date: '2026-10-01' }).date).toBe('2026-10-01')
  })
})
