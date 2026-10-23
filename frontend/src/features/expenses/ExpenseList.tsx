import { useEffect } from 'react'
import { useShallow } from 'zustand/react/shallow'
import { capitalize, formatAmount } from '../../lib/format'
import { useExpenseStore } from '../../store/expenseStore'
import { CATEGORIES, type Category } from '../../types/expense'
import { ExpenseRow } from './ExpenseRow'

export function ExpenseList() {
  const { items, totalCount, totalAmount, category, page, limit, status, error, fetchExpenses, setCategory, goToPage } =
    useExpenseStore(
      useShallow((s) => ({
        items: s.items,
        totalCount: s.totalCount,
        totalAmount: s.totalAmount,
        category: s.category,
        page: s.page,
        limit: s.limit,
        status: s.status,
        error: s.error,
        fetchExpenses: s.fetchExpenses,
        setCategory: s.setCategory,
        goToPage: s.goToPage,
      })),
    )

  useEffect(() => {
    void fetchExpenses()
  }, [fetchExpenses])

  const totalPages = Math.max(1, Math.ceil(totalCount / limit))
  const loading = status === 'loading' || status === 'idle'

  return (
    <section className="card" aria-label="Expenses">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Expenses</h2>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          Category
          <select
            aria-label="Filter by category"
            className="input w-auto"
            value={category}
            onChange={(e) => setCategory(e.target.value as Category | '')}
          >
            <option value="">All</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {capitalize(c)}
              </option>
            ))}
          </select>
        </label>
      </header>

      {/* Total comes from the API (all matching expenses), not a sum of the visible page. */}
      <div className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-600" aria-live="polite">
        <span data-testid="total-count">
          {totalCount} {totalCount === 1 ? 'expense' : 'expenses'}
        </span>
        <span>
          Total:{' '}
          <strong data-testid="total-amount" className="text-base text-slate-900 tabular-nums">
            {formatAmount(totalAmount)}
          </strong>
        </span>
      </div>

      {status === 'error' ? (
        <div role="alert" className="flex flex-col items-center gap-3 py-10 text-center text-rose-600">
          <p>{error}</p>
          <button type="button" className="btn" onClick={() => void fetchExpenses()}>
            Retry
          </button>
        </div>
      ) : loading && items.length === 0 ? (
        <p role="status" className="py-10 text-center text-slate-500">
          Loading expenses…
        </p>
      ) : items.length === 0 ? (
        <p className="py-10 text-center text-slate-500">
          {category ? `No ${category} expenses yet.` : 'No expenses yet. Add your first one!'}
        </p>
      ) : (
        <ul
          className={`mt-2 divide-y divide-slate-100 transition-opacity ${loading ? 'opacity-50' : ''}`}
          aria-busy={loading}
        >
          {items.map((expense) => (
            <ExpenseRow key={expense.id} expense={expense} />
          ))}
        </ul>
      )}

      <nav className="mt-4 flex items-center justify-between text-sm text-slate-500" aria-label="Pagination">
        <button type="button" className="btn" onClick={() => goToPage(page - 1)} disabled={loading || page <= 1}>
          Previous
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          className="btn"
          onClick={() => goToPage(page + 1)}
          disabled={loading || page >= totalPages}
        >
          Next
        </button>
      </nav>
    </section>
  )
}
