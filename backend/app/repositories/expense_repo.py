"""Data access for expenses.

The service depends on the ExpenseRepository protocol so tests can swap in a fake.
"""

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from supabase import Client

TABLE = "expenses"
COLUMNS = "id,title,amount,category,date,created_at"


@dataclass(frozen=True)
class ExpenseFilters:
    category: str | None = None
    date_from: dt.date | None = None
    date_to: dt.date | None = None


class ExpenseRepository(Protocol):
    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...

    def list(self, filters: ExpenseFilters, offset: int, limit: int) -> list[dict[str, Any]]: ...

    def totals(self, filters: ExpenseFilters) -> tuple[int, float]: ...

    def delete(self, expense_id: str) -> bool: ...

    def category_totals(self, start: dt.date, end: dt.date) -> dict[str, float]: ...


class SupabaseExpenseRepository:
    def __init__(self, client_factory: Callable[[], Client]) -> None:
        # Resolved lazily so request validation (400) runs before any DB/config error.
        self._client_factory = client_factory

    @property
    def client(self) -> Client:
        return self._client_factory()

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self.client.table(TABLE).insert(data).execute()
        return result.data[0]

    def list(self, filters: ExpenseFilters, offset: int, limit: int) -> list[dict[str, Any]]:
        query = self.client.table(TABLE).select(COLUMNS)
        if filters.category:
            query = query.eq("category", filters.category)
        if filters.date_from:
            query = query.gte("date", filters.date_from.isoformat())
        if filters.date_to:
            query = query.lte("date", filters.date_to.isoformat())
        result = (
            query.order("date", desc=True)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data

    def totals(self, filters: ExpenseFilters) -> tuple[int, float]:
        # Aggregated in Postgres so total_amount covers every matching row, not just one page.
        result = self.client.rpc(
            "expense_totals",
            {
                "p_category": filters.category,
                "p_from": filters.date_from.isoformat() if filters.date_from else None,
                "p_to": filters.date_to.isoformat() if filters.date_to else None,
            },
        ).execute()
        row = result.data[0] if result.data else {"total_count": 0, "total_amount": 0}
        return int(row["total_count"]), float(row["total_amount"])

    def delete(self, expense_id: str) -> bool:
        result = self.client.table(TABLE).delete().eq("id", expense_id).execute()
        return bool(result.data)

    def category_totals(self, start: dt.date, end: dt.date) -> dict[str, float]:
        result = self.client.rpc(
            "expense_category_totals",
            {"p_from": start.isoformat(), "p_to": end.isoformat()},
        ).execute()
        return {row["category"]: float(row["total"]) for row in result.data}
