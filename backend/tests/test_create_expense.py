import datetime as dt

import pytest

from app.core.clock import today


def test_create_returns_201_and_defaults_date_to_today(client):
    response = client.post("/api/expenses", json={"title": "  Coffee ", "amount": 4.5, "category": "food"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Coffee"
    assert body["amount"] == 4.5
    assert body["category"] == "food"
    assert body["date"] == today().isoformat()
    assert body["id"]


def test_create_accepts_explicit_past_date(client):
    response = client.post(
        "/api/expenses", json={"title": "Train", "amount": 120, "category": "travel", "date": "2025-01-31"}
    )

    assert response.status_code == 201
    assert response.json()["date"] == "2025-01-31"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"title": ""}, "title is required"),
        ({"title": "   "}, "title is required"),
        ({"title": "x" * 101}, "title must be at most 100 characters"),
        ({"title": 123}, "title must be a string"),
        ({"amount": 0}, "amount must be greater than 0"),
        ({"amount": -5}, "amount must be greater than 0"),
        ({"amount": 1.234}, "amount must have at most 2 decimal places"),
        ({"amount": "10"}, "amount must be a number"),
        ({"amount": True}, "amount must be a number"),
        ({"category": "fun"}, "category must be one of: food, travel, bills, other"),
        ({"date": "2025-13-01"}, "date must be a valid date"),
        ({"date": "01-01-2025"}, "date must be a date in YYYY-MM-DD format"),
    ],
)
def test_create_rejects_invalid_input(client, overrides, message):
    body = {"title": "Lunch", "amount": 10, "category": "food", **overrides}

    response = client.post("/api/expenses", json=body)

    assert response.status_code == 400
    assert response.json() == {"error": message}


def test_create_rejects_future_date(client):
    tomorrow = (today() + dt.timedelta(days=1)).isoformat()

    response = client.post(
        "/api/expenses", json={"title": "Later", "amount": 1, "category": "other", "date": tomorrow}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "date cannot be in the future"}


def test_create_accepts_title_of_exactly_100_chars(client):
    response = client.post("/api/expenses", json={"title": "x" * 100, "amount": 1, "category": "bills"})

    assert response.status_code == 201


@pytest.mark.parametrize("field", ["title", "amount", "category"])
def test_create_requires_fields(client, field):
    body = {"title": "Lunch", "amount": 10, "category": "food"}
    del body[field]

    response = client.post("/api/expenses", json=body)

    assert response.status_code == 400
    assert response.json() == {"error": f"{field} is required"}


def test_create_rejects_malformed_json(client):
    response = client.post(
        "/api/expenses", content="{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Request body must be valid JSON"}


def test_validation_runs_before_database_config(monkeypatch):
    """Bad input must be a 400 even when the database isn't configured."""
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.main import app

    monkeypatch.setattr(get_settings(), "supabase_url", "")
    with TestClient(app) as raw_client:
        response = raw_client.post("/api/expenses", json={"title": "", "amount": 1, "category": "food"})
        unconfigured = raw_client.get("/api/expenses")

    assert response.status_code == 400
    assert unconfigured.status_code == 503
    assert unconfigured.json() == {"error": "Database is not configured"}
