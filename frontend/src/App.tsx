import { ExpenseForm } from './features/expenses/ExpenseForm'
import { ExpenseList } from './features/expenses/ExpenseList'
import { MonthlySummary } from './features/expenses/MonthlySummary'

export default function App() {
  return (
    <div className="mx-auto max-w-6xl px-4 pb-12 pt-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Expense Tracker</h1>
      </header>
      <main className="grid items-start gap-5 lg:grid-cols-[minmax(300px,380px)_1fr]">
        <div className="grid gap-5">
          <ExpenseForm />
          <MonthlySummary />
        </div>
        <ExpenseList />
      </main>
    </div>
  )
}
