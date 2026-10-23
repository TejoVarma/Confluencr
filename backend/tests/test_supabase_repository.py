"""Checks the Supabase query building without a network, using a recording fake client."""

import datetime as dt
from typing import Any

from app.repositories.expense_repo import ExpenseFilters, SupabaseExpenseRepository


class FakeQuery:
    def __init__(self, calls: list[tuple], data: Any) -> None:
        self.calls = calls
        self.data = data

    def __getattr__(self, name: str):
        def method(*args: Any, **kwargs: Any) -> "FakeQuery":
            self.calls.append((name, args, kwargs))
            return self

        return method

    def execute(self) -> "FakeQuery":
        self.calls.append(("execute", (), {}))
        return self


class FakeClient:
    def __init__(self, data: Any = None) -> None:
        self.calls: list[tuple] = []
        self.data = data if data is not None else []

    def table(self, name: str) -> FakeQuery:
        self.calls.append(("table", (name,), {}))
        return FakeQuery(self.calls, self.data)

    def rpc(self, name: str, params: dict[str, Any]) -> FakeQuery:
        self.calls.append(("rpc", (name, params), {}))
        return FakeQuery(self.calls, self.data)


def make_repo(data: Any = None) -> tuple[SupabaseExpenseRepository, FakeClient]:
    client = FakeClient(data)
    return SupabaseExpenseRepository(lambda: client), client


def test_list_applies_filters_order_and_range():
    repo, client = make_repo([{"id": "1"}])
    filters = ExpenseFilters("food", dt.date(2025, 1, 1), dt.date(2025, 1, 31))

    assert repo.list(filters, offset=20, limit=10) == [{"id": "1"}]

    names = [(c[0], c[1], c[2]) for c in client.calls]
    assert ("table", ("expenses",), {}) in names
    assert ("eq", ("category", "food"), {}) in names
    assert ("gte", ("date", "2025-01-01"), {}) in names
    assert ("lte", ("date", "2025-01-31"), {}) in names
    assert ("order", ("date",), {"desc": True}) in names
    assert ("order", ("created_at",), {"desc": True}) in names
    assert ("range", (20, 29), {}) in names


def test_list_without_filters_skips_where_clauses():
    repo, client = make_repo()

    repo.list(ExpenseFilters(), offset=0, limit=10)

    assert not {"eq", "gte", "lte"} & {c[0] for c in client.calls}


def test_totals_calls_rpc_with_iso_params():
    repo, client = make_repo([{"total_count": 3, "total_amount": "12.50"}])

    assert repo.totals(ExpenseFilters(None, dt.date(2025, 2, 1), None)) == (3, 12.5)
    assert client.calls[0] == (
        "rpc",
        ("expense_totals", {"p_category": None, "p_from": "2025-02-01", "p_to": None}),
        {},
    )


def test_totals_handles_empty_rpc_result():
    repo, _ = make_repo([])

    assert repo.totals(ExpenseFilters()) == (0, 0.0)


def test_delete_reports_whether_a_row_was_removed():
    found, _ = make_repo([{"id": "x"}])
    missing, _ = make_repo([])

    assert found.delete("x") is True
    assert missing.delete("x") is False


def test_category_totals_maps_rows():
    repo, client = make_repo([{"category": "food", "total": "7.25"}, {"category": "bills", "total": 3}])

    assert repo.category_totals(dt.date(2025, 3, 1), dt.date(2025, 3, 31)) == {"food": 7.25, "bills": 3.0}
    assert client.calls[0][1] == ("expense_category_totals", {"p_from": "2025-03-01", "p_to": "2025-03-31"})


def test_create_returns_inserted_row():
    repo, client = make_repo([{"id": "new"}])

    assert repo.create({"title": "t"}) == {"id": "new"}
    assert ("insert", ({"title": "t"},), {}) in [(c[0], c[1], c[2]) for c in client.calls]
