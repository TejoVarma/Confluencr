"""Live tests against the real Supabase database, through the real app (no repository override).

Opt-in: RUN_INTEGRATION=1 with SUPABASE_URL/SUPABASE_KEY set (backend/.env locally, secrets in CI).
Each session writes into one random month in the distant past so it never mixes with real data,
and deletes everything it created afterwards.
"""

import os
import random
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def live_client() -> Iterator[TestClient]:
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("set RUN_INTEGRATION=1 to run live Supabase tests")
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        pytest.skip("SUPABASE_URL / SUPABASE_KEY not configured")
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def month(live_client: TestClient) -> str:
    """A random month in 1900-1989 that has no data yet."""
    for _ in range(5):
        candidate = f"{random.randint(1900, 1989)}-{random.randint(1, 12):02d}"
        body = live_client.get("/api/expenses", params=window(candidate)).json()
        if body["total_count"] == 0:
            return candidate
    pytest.fail("could not find an empty month for isolated integration tests")


def window(month: str) -> dict[str, str]:
    return {"from": f"{month}-01", "to": f"{month}-28"}


@pytest.fixture
def create(live_client: TestClient, month: str) -> Iterator[Any]:
    created: list[str] = []

    def _create(day: int = 1, **overrides: Any) -> dict[str, Any]:
        body = {
            "title": "it-expense",
            "amount": 1,
            "category": "other",
            "date": f"{month}-{day:02d}",
            **overrides,
        }
        response = live_client.post("/api/expenses", json=body)
        assert response.status_code == 201, response.text
        created.append(response.json()["id"])
        return response.json()

    yield _create

    for expense_id in created:
        live_client.delete(f"/api/expenses/{expense_id}")
