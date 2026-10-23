import { useState, type ChangeEvent, type FormEvent } from 'react'
import { errorMessage } from '../../api/client'
import { capitalize, todayISO } from '../../lib/format'
import { useExpenseStore } from '../../store/expenseStore'
import { CATEGORIES } from '../../types/expense'
import {
  TITLE_MAX_LENGTH,
  toNewExpense,
  validateExpense,
  type ExpenseFormErrors,
  type ExpenseFormValues,
} from './validation'

const EMPTY_FORM: ExpenseFormValues = { title: '', amount: '', category: '', date: '' }

export function ExpenseForm() {
  const addExpense = useExpenseStore((s) => s.addExpense)
  const [values, setValues] = useState<ExpenseFormValues>(EMPTY_FORM)
  const [errors, setErrors] = useState<ExpenseFormErrors>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const onChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const field = e.target.name as keyof ExpenseFormValues
    setValues((v) => ({ ...v, [field]: e.target.value }))
    setErrors((errs) => ({ ...errs, [field]: undefined }))
    setSaved(false)
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (saving) return
    const validation = validateExpense(values)
    setErrors(validation)
    setServerError(null)
    setSaved(false)
    if (Object.keys(validation).length > 0) return

    setSaving(true)
    try {
      await addExpense(toNewExpense(values))
      setValues(EMPTY_FORM)
      setSaved(true)
    } catch (error) {
      setServerError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const fieldProps = (name: keyof ExpenseFormValues) => ({
    id: `expense-${name}`,
    name,
    value: values[name],
    onChange,
    disabled: saving,
    className: 'input',
    'aria-invalid': Boolean(errors[name]),
    'aria-describedby': errors[name] ? `expense-${name}-error` : undefined,
  })

  const fieldError = (name: keyof ExpenseFormValues) =>
    errors[name] ? (
      <p id={`expense-${name}-error`} className="field-error">
        {errors[name]}
      </p>
    ) : null

  return (
    <form className="card space-y-4" onSubmit={onSubmit} noValidate aria-label="Add expense">
      <h2 className="text-lg font-semibold">Add expense</h2>

      <div className="space-y-1.5">
        <label className="label block" htmlFor="expense-title">Title</label>
        <input {...fieldProps('title')} type="text" maxLength={TITLE_MAX_LENGTH + 20} placeholder="e.g. Groceries" />
        {fieldError('title')}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="label block" htmlFor="expense-amount">Amount</label>
          <input {...fieldProps('amount')} type="text" inputMode="decimal" placeholder="0.00" />
          {fieldError('amount')}
        </div>

        <div className="space-y-1.5">
          <label className="label block" htmlFor="expense-category">Category</label>
          <select {...fieldProps('category')}>
            <option value="">Select…</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {capitalize(c)}
              </option>
            ))}
          </select>
          {fieldError('category')}
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="label block" htmlFor="expense-date">
          Date <span className="font-normal text-slate-400">(optional, defaults to today)</span>
        </label>
        <input {...fieldProps('date')} type="date" max={todayISO()} />
        {fieldError('date')}
      </div>

      {serverError && (
        <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {serverError}
        </p>
      )}
      {saved && (
        <p role="status" className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          Expense added.
        </p>
      )}

      <button type="submit" className="btn btn-primary w-full" disabled={saving}>
        {saving ? 'Saving…' : 'Add expense'}
      </button>
    </form>
  )
}
