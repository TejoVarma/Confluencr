# Expense Tracker — Frontend

Vite 6 + React 19 + TypeScript + Zustand + Tailwind CSS 3. Node 18.18+.

## Structure

```
src/
  api/client.ts                 fetch wrapper on "/api"; parses {"error"} into ApiError
  api/expenses.ts               typed endpoint functions
  store/expenseStore.ts         zustand: list, filter, paging, totals, summary, loading/error
  features/expenses/
    ExpenseForm.tsx             add form (client validation + server errors, disabled while saving)
    ExpenseList.tsx             category filter, totals from API, Prev/Next, loading/empty/error
    ExpenseRow.tsx              row with delete + confirm step
    MonthlySummary.tsx          per-category totals for a month
    validation.ts               same rules as the backend
  lib/format.ts                 number/date helpers
  types/expense.ts
```

## Run

```bash
npm install
npm run dev        # http://localhost:5173, /api proxied to http://localhost:8000
npm test           # vitest
npm run lint       # eslint
npm run check      # lint + typecheck + tests (same as CI)
npm run build      # typecheck + production build to dist/
```

## CI

`.github/workflows/frontend.yml` runs lint, typecheck, tests and build on every PR touching `frontend/`.

## Deploy (AWS Amplify)

`amplify.yml` at the repo root builds this folder (`appRoot: frontend`), runs the tests, and publishes `dist/`.

Add the rewrites from `amplify-rewrites.json` under **Hosting → Rewrites and redirects** (edit JSON),
replacing `YOUR-BACKEND-HOST` with the Beanstalk/CloudFront host. The `/api/<*>` rule must stay **above**
the SPA fallback. Use an HTTPS backend URL (e.g. CloudFront in front of Beanstalk).
