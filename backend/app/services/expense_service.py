import calendar
import datetime as dt
from typing import Any

from app.core.clock import today
from app.core.errors import AppError
from app.repositories.expense_repo import ExpenseFilters, ExpenseRepository
from app.schemas.expense import CATEGORIES, ExpenseCreate, ExpenseListQuery


class ExpenseService:
    def __init__(self, repo: ExpenseRepository) -> None:
        self.repo = repo

    def create(self, payload: ExpenseCreate) -> dict[str, Any]:
        return self.repo.create(
            {
                "title": payload.title,
                "amount": str(payload.amount),  # string keeps exact decimal precision
                "category": payload.category,
                "date": (payload.date or today()).isoformat(),
            }
        )

    def list(self, query: ExpenseListQuery) -> dict[str, Any]:
        filters = ExpenseFilters(query.category, query.date_from, query.date_to)
        offset = (query.page - 1) * query.limit
        items = self.repo.list(filters, offset, query.limit)
        total_count, total_amount = self.repo.totals(filters)
        return {
            "items": items,
            "total_count": total_count,
            "total_amount": round(total_amount, 2),
        }

    def delete(self, expense_id: str) -> None:
        if not self.repo.delete(expense_id):
            raise AppError("Expense not found", 404)

    def monthly_summary(self, month: str) -> dict[str, Any]:
        year, month_num = (int(part) for part in month.split("-"))
        start = dt.date(year, month_num, 1)
        end = dt.date(year, month_num, calendar.monthrange(year, month_num)[1])
        raw = self.repo.category_totals(start, end)
        totals = {category: round(raw.get(category, 0.0), 2) for category in CATEGORIES}
        return {"month": month, "totals": totals, "total": round(sum(totals.values()), 2)}
