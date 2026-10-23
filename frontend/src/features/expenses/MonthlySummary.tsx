import { useEffect } from 'react'
import { useShallow } from 'zustand/react/shallow'
import { formatAmount } from '../../lib/format'
import { useExpenseStore } from '../../store/expenseStore'
import { CATEGORIES } from '../../types/expense'
import { CategoryBadge } from './CategoryBadge'

export function MonthlySummary() {
  const { summaryMonth, summary, summaryStatus, summaryError, fetchSummary, setSummaryMonth } = useExpenseStore(
    useShallow((s) => ({
      summaryMonth: s.summaryMonth,
      summary: s.summary,
      summaryStatus: s.summaryStatus,
      summaryError: s.summaryError,
      fetchSummary: s.fetchSummary,
      setSummaryMonth: s.setSummaryMonth,
    })),
  )

  useEffect(() => {
    void fetchSummary()
  }, [fetchSummary])

  return (
    <section className="card" aria-label="Monthly summary">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Monthly summary</h2>
        <input
          type="month"
          aria-label="Summary month"
          className="input w-auto"
          value={summaryMonth}
          onChange={(e) => e.target.value && setSummaryMonth(e.target.value)}
        />
      </header>

      {summaryStatus === 'error' ? (
        <div role="alert" className="flex flex-col items-center gap-3 py-6 text-center text-rose-600">
          <p>{summaryError}</p>
          <button type="button" className="btn" onClick={() => void fetchSummary()}>
            Retry
          </button>
        </div>
      ) : !summary ? (
        <p className="py-6 text-center text-slate-500">Loading summary…</p>
      ) : (
        <dl className={`space-y-2 text-sm transition-opacity ${summaryStatus === 'loading' ? 'opacity-50' : ''}`}>
          {CATEGORIES.map((c) => (
            <div key={c} className="flex items-center justify-between">
              <dt>
                <CategoryBadge category={c} />
              </dt>
              <dd className="tabular-nums">{formatAmount(summary.totals[c] ?? 0)}</dd>
            </div>
          ))}
          <div className="flex items-center justify-between border-t border-slate-200 pt-2 font-semibold">
            <dt>Total</dt>
            <dd className="tabular-nums">{formatAmount(summary.total)}</dd>
          </div>
        </dl>
      )}
    </section>
  )
}
