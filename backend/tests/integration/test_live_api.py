import uuid

from .conftest import window


def test_create_persists_all_fields(live_client, create, month):
    created = create(day=3, title="Dinner", amount=42.75, category="food")

    items = live_client.get("/api/expenses", params=window(month)).json()["items"]

    assert items == [created]
    assert created["title"] == "Dinner"
    assert created["amount"] == 42.75
    assert created["category"] == "food"
    assert created["date"] == f"{month}-03"
    uuid.UUID(created["id"])


def test_newest_first_pagination_and_totals_cover_all_pages(live_client, create, month):
    for day in (5, 20, 10, 15, 1):
        create(day=day, title=f"day-{day}", amount=1.1)

    page1 = live_client.get("/api/expenses", params={**window(month), "limit": 2}).json()
    page2 = live_client.get("/api/expenses", params={**window(month), "limit": 2, "page": 2}).json()
    page3 = live_client.get("/api/expenses", params={**window(month), "limit": 2, "page": 3}).json()

    titles = [i["title"] for p in (page1, page2, page3) for i in p["items"]]
    assert titles == ["day-20", "day-15", "day-10", "day-5", "day-1"]
    for page in (page1, page2, page3):
        assert page["total_count"] == 5
        assert page["total_amount"] == 5.5


def test_same_day_orders_by_creation_time(live_client, create, month):
    create(day=7, title="first")
    create(day=7, title="second")

    titles = [i["title"] for i in live_client.get("/api/expenses", params=window(month)).json()["items"]]

    assert titles == ["second", "first"]


def test_filters_by_category_and_date_range(live_client, create, month):
    create(day=2, category="food", amount=3)
    create(day=12, category="food", amount=4)
    create(day=12, category="travel", amount=50)
    create(day=25, category="food", amount=5)

    body = live_client.get(
        "/api/expenses", params={"category": "food", "from": f"{month}-10", "to": f"{month}-25"}
    ).json()

    assert body["total_count"] == 2
    assert body["total_amount"] == 9
    assert {i["category"] for i in body["items"]} == {"food"}


def test_decimal_amounts_sum_exactly(live_client, create, month):
    create(amount=0.1)
    create(amount=0.2)

    assert live_client.get("/api/expenses", params=window(month)).json()["total_amount"] == 0.3


def test_monthly_summary(live_client, create, month):
    create(day=1, category="food", amount=10.5)
    create(day=28, category="food", amount=4.25)
    create(day=15, category="bills", amount=100)

    body = live_client.get("/api/expenses/summary", params={"month": month}).json()

    assert body == {
        "month": month,
        "totals": {"food": 14.75, "travel": 0, "bills": 100, "other": 0},
        "total": 114.75,
    }


def test_delete_then_404(live_client, create, month):
    expense = create()

    first = live_client.delete(f"/api/expenses/{expense['id']}")
    second = live_client.delete(f"/api/expenses/{expense['id']}")

    assert first.status_code == 204
    assert second.status_code == 404
    assert second.json() == {"error": "Expense not found"}
    assert live_client.get("/api/expenses", params=window(month)).json()["total_count"] == 0


def test_invalid_input_is_rejected_before_reaching_the_database(live_client, month):
    response = live_client.post(
        "/api/expenses", json={"title": "x", "amount": 1.234, "category": "food", "date": f"{month}-01"}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "amount must have at most 2 decimal places"}
    assert live_client.get("/api/expenses", params=window(month)).json()["total_count"] == 0
