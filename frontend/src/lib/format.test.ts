import { describe, expect, it } from 'vitest'
import { capitalize, currentMonth, todayISO } from './format'

describe('todayISO', () => {
  it('uses the local calendar date, zero-padded', () => {
    expect(todayISO(new Date(2026, 0, 5))).toBe('2026-01-05')
  })

  it('does not shift to UTC late in the local day', () => {
    // 23:30 local time must stay on the same local date regardless of timezone offset.
    expect(todayISO(new Date(2026, 9, 23, 23, 30))).toBe('2026-10-23')
    expect(todayISO(new Date(2026, 9, 23, 0, 15))).toBe('2026-10-23')
  })
})

describe('currentMonth', () => {
  it('returns YYYY-MM for the local date', () => {
    expect(currentMonth(new Date(2026, 11, 31, 23, 59))).toBe('2026-12')
  })
})

describe('capitalize', () => {
  it('uppercases the first letter', () => {
    expect(capitalize('food')).toBe('Food')
  })
})
