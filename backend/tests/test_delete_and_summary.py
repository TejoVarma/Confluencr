import uuid


def test_delete_removes_expense(client, add_expense):
    expense = add_expense()

    response = client.delete(f"/api/expenses/{expense['id']}")

    assert response.status_code == 204
    assert client.get("/api/expenses").json()["total_count"] == 0


def test_delete_missing_returns_404(client):
    response = client.delete(f"/api/expenses/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"error": "Expense not found"}


def test_delete_invalid_id_returns_400(client):
    response = client.delete("/api/expenses/not-a-uuid")

    assert response.status_code == 400
    assert response.json() == {"error": "id must be a valid UUID"}


def test_summary_totals_per_category_for_month(client, add_expense):
    add_expense(category="food", amount=10.5, date="2025-10-01")
    add_expense(category="food", amount=4.25, date="2025-10-31")
    add_expense(category="bills", amount=100, date="2025-10-15")
    add_expense(category="travel", amount=999, date="2025-09-30")
    add_expense(category="travel", amount=999, date="2025-11-01")

    response = client.get("/api/expenses/summary", params={"month": "2025-10"})

    assert response.status_code == 200
    assert response.json() == {
        "month": "2025-10",
        "totals": {"food": 14.75, "travel": 0, "bills": 100, "other": 0},
        "total": 114.75,
    }


def test_summary_requires_valid_month(client):
    missing = client.get("/api/expenses/summary")
    bad = client.get("/api/expenses/summary", params={"month": "2025-13"})

    assert missing.status_code == 400
    assert missing.json() == {"error": "month is required (YYYY-MM)"}
    assert bad.status_code == 400
    assert bad.json() == {"error": "month must be in YYYY-MM format"}


def test_unknown_route_uses_error_shape(client):
    response = client.get("/api/nope")

    assert response.status_code == 404
    assert response.json() == {"error": "Not Found"}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
