import { capitalize } from '../../lib/format'
import type { Category } from '../../types/expense'

const COLORS: Record<Category, string> = {
  food: 'bg-orange-100 text-orange-700',
  travel: 'bg-sky-100 text-sky-700',
  bills: 'bg-violet-100 text-violet-700',
  other: 'bg-slate-200 text-slate-700',
}

export function CategoryBadge({ category }: { category: Category }) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${COLORS[category]}`}>
      {capitalize(category)}
    </span>
  )
}
