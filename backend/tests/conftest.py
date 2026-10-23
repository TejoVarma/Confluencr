import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_expense_repository
from app.main import app
from app.repositories.expense_repo import ExpenseFilters


class FakeExpenseRepository:
    """In-memory stand-in for SupabaseExpenseRepository."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self._seq = 0

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        self._seq += 1
        row = {
            **data,
            "id": str(uuid.uuid4()),
            "amount": float(Decimal(data["amount"])),
            "created_at": f"2000-01-01T00:00:{self._seq:02d}+00:00",
        }
        self.rows.append(row)
        return row

    def _matching(self, filters: ExpenseFilters) -> list[dict[str, Any]]:
        return [
            r
            for r in self.rows
            if (not filters.category or r["category"] == filters.category)
            and (not filters.date_from or r["date"] >= filters.date_from.isoformat())
            and (not filters.date_to or r["date"] <= filters.date_to.isoformat())
        ]

    def list(self, filters: ExpenseFilters, offset: int, limit: int) -> list[dict[str, Any]]:
        rows = sorted(self._matching(filters), key=lambda r: (r["date"], r["created_at"]), reverse=True)
        return rows[offset : offset + limit]

    def totals(self, filters: ExpenseFilters) -> tuple[int, float]:
        rows = self._matching(filters)
        return len(rows), float(sum(Decimal(str(r["amount"])) for r in rows))

    def delete(self, expense_id: str) -> bool:
        before = len(self.rows)
        self.rows = [r for r in self.rows if r["id"] != expense_id]
        return len(self.rows) < before

    def category_totals(self, start: dt.date, end: dt.date) -> dict[str, float]:
        totals: dict[str, Decimal] = {}
        for r in self.rows:
            if start.isoformat() <= r["date"] <= end.isoformat():
                totals[r["category"]] = totals.get(r["category"], Decimal(0)) + Decimal(str(r["amount"]))
        return {k: float(v) for k, v in totals.items()}


@pytest.fixture
def repo() -> FakeExpenseRepository:
    return FakeExpenseRepository()


@pytest.fixture
def client(repo: FakeExpenseRepository):
    app.dependency_overrides[get_expense_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def add_expense(client: TestClient):
    def _add(**overrides: Any) -> dict[str, Any]:
        body = {"title": "Lunch", "amount": 10, "category": "food", **overrides}
        response = client.post("/api/expenses", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _add
