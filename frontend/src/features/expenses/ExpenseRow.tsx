import { useState } from 'react'
import { errorMessage } from '../../api/client'
import { formatAmount, formatDate } from '../../lib/format'
import { useExpenseStore } from '../../store/expenseStore'
import type { Expense } from '../../types/expense'
import { CategoryBadge } from './CategoryBadge'

export function ExpenseRow({ expense }: { expense: Expense }) {
  const removeExpense = useExpenseStore((s) => s.removeExpense)
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onConfirm = async () => {
    setDeleting(true)
    setError(null)
    try {
      await removeExpense(expense.id)
    } catch (err) {
      setError(errorMessage(err))
      setDeleting(false)
      setConfirming(false)
    }
  }

  return (
    <li className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-2 py-3 sm:grid-cols-[1fr_auto_auto]">
      <div className="min-w-0 space-y-1">
        <p className="break-words font-medium text-slate-900">{expense.title}</p>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <CategoryBadge category={expense.category} />
          <time dateTime={expense.date}>{formatDate(expense.date)}</time>
        </div>
        {error && (
          <p role="alert" className="field-error">
            {error}
          </p>
        )}
      </div>

      <span className="font-semibold tabular-nums text-slate-900">{formatAmount(expense.amount)}</span>

      <div className="col-span-2 flex items-center justify-end gap-2 sm:col-span-1">
        {confirming ? (
          <>
            <span className="text-sm text-slate-500">Delete?</span>
            <button type="button" className="btn btn-danger" onClick={onConfirm} disabled={deleting}>
              {deleting ? 'Deleting…' : 'Yes, delete'}
            </button>
            <button type="button" className="btn" onClick={() => setConfirming(false)} disabled={deleting}>
              Cancel
            </button>
          </>
        ) : (
          <button
            type="button"
            className="btn border-transparent text-slate-500 hover:bg-rose-50 hover:text-rose-600"
            onClick={() => setConfirming(true)}
            aria-label={`Delete ${expense.title}`}
          >
            Delete
          </button>
        )}
      </div>
    </li>
  )
}
