"""Boundary cases on top of the per-endpoint tests."""

from app.core.clock import today


def test_create_accepts_today_and_smallest_amount(client):
    response = client.post(
        "/api/expenses",
        json={"title": "Gum", "amount": 0.01, "category": "other", "date": today().isoformat()},
    )

    assert response.status_code == 201
    assert response.json()["amount"] == 0.01


def test_create_accepts_max_amount_and_rejects_above(client):
    ok = client.post("/api/expenses", json={"title": "Big", "amount": 9999999999.99, "category": "bills"})
    too_big = client.post(
        "/api/expenses", json={"title": "Too big", "amount": 10000000000, "category": "bills"}
    )

    assert ok.status_code == 201
    assert too_big.status_code == 400
    assert too_big.json() == {"error": "amount must be at most 9999999999.99"}


def test_create_reports_every_invalid_field(client):
    response = client.post("/api/expenses", json={"title": "", "amount": 0, "category": "fun"})

    assert response.status_code == 400
    assert response.json()["error"] == (
        "title is required; amount must be greater than 0; "
        "category must be one of: food, travel, bills, other"
    )


def test_create_rejects_non_object_body(client):
    response = client.post("/api/expenses", json=["not", "an", "object"])

    assert response.status_code == 400
    assert "error" in response.json()


def test_create_ignores_unknown_fields(client):
    response = client.post(
        "/api/expenses", json={"title": "Tea", "amount": 2, "category": "food", "id": "hacked"}
    )

    assert response.status_code == 201
    assert response.json()["id"] != "hacked"


def test_page_past_the_end_is_empty_but_keeps_totals(client, add_expense):
    add_expense(amount=3)
    add_expense(amount=4)

    body = client.get("/api/expenses", params={"page": 5}).json()

    assert body == {"items": [], "total_count": 2, "total_amount": 7}


def test_same_from_and_to_is_a_single_day(client, add_expense):
    add_expense(title="in", date="2025-05-05")
    add_expense(title="out", date="2025-05-06")

    body = client.get("/api/expenses", params={"from": "2025-05-05", "to": "2025-05-05"}).json()

    assert [i["title"] for i in body["items"]] == ["in"]


def test_empty_filters_are_ignored(client, add_expense):
    add_expense()

    body = client.get(
        "/api/expenses", params={"category": "", "from": "", "to": "", "page": "", "limit": ""}
    ).json()

    assert body["total_count"] == 1


def test_summary_handles_leap_year_february(client, add_expense):
    add_expense(category="travel", amount=20, date="2024-02-29")
    add_expense(category="travel", amount=99, date="2024-03-01")

    body = client.get("/api/expenses/summary", params={"month": "2024-02"}).json()

    assert body["totals"]["travel"] == 20
    assert body["total"] == 20


def test_summary_for_empty_month_returns_zeros(client):
    body = client.get("/api/expenses/summary", params={"month": "2020-01"}).json()

    assert body == {
        "month": "2020-01",
        "totals": {"food": 0, "travel": 0, "bills": 0, "other": 0},
        "total": 0,
    }


def test_method_not_allowed_uses_error_shape(client):
    response = client.put("/api/expenses")

    assert response.status_code == 405
    assert response.json() == {"error": "Method Not Allowed"}
