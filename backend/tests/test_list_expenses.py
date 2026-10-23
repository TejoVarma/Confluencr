import pytest


def test_list_empty(client):
    response = client.get("/api/expenses")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total_count": 0, "total_amount": 0}


def test_list_is_newest_first(client, add_expense):
    add_expense(title="old", date="2025-01-01")
    add_expense(title="new", date="2025-03-01")
    add_expense(title="mid", date="2025-02-01")
    add_expense(title="new-later", date="2025-03-01")

    titles = [item["title"] for item in client.get("/api/expenses").json()["items"]]

    assert titles == ["new-later", "new", "mid", "old"]


def test_pagination_defaults_to_10_and_totals_cover_all_pages(client, add_expense):
    for i in range(12):
        add_expense(title=f"e{i}", amount=1.25, date=f"2025-01-{i + 1:02d}")

    page1 = client.get("/api/expenses").json()
    page2 = client.get("/api/expenses", params={"page": 2}).json()

    assert len(page1["items"]) == 10
    assert len(page2["items"]) == 2
    for page in (page1, page2):
        assert page["total_count"] == 12
        assert page["total_amount"] == 15.0
    assert page2["items"][-1]["title"] == "e0"


def test_custom_limit(client, add_expense):
    for i in range(5):
        add_expense(title=f"e{i}")

    body = client.get("/api/expenses", params={"limit": 2, "page": 3}).json()

    assert len(body["items"]) == 1
    assert body["total_count"] == 5


def test_filters_by_category_and_date_range(client, add_expense):
    add_expense(title="a", category="food", amount=5, date="2025-01-10")
    add_expense(title="b", category="food", amount=7, date="2025-02-10")
    add_expense(title="c", category="travel", amount=100, date="2025-02-11")
    add_expense(title="d", category="food", amount=9, date="2025-03-10")

    body = client.get(
        "/api/expenses", params={"category": "food", "from": "2025-02-01", "to": "2025-03-10"}
    ).json()

    assert [i["title"] for i in body["items"]] == ["d", "b"]
    assert body["total_count"] == 2
    assert body["total_amount"] == 16.0


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"category": "fun"}, "category must be one of: food, travel, bills, other"),
        ({"from": "2025/01/01"}, "from must be a date in YYYY-MM-DD format"),
        ({"to": "2025-02-30"}, "to must be a valid date"),
        ({"from": "2025-02-01", "to": "2025-01-01"}, "from must be on or before to"),
        ({"page": "0"}, "page must be a positive integer"),
        ({"page": "abc"}, "page must be a positive integer"),
        ({"limit": "0"}, "limit must be an integer between 1 and 100"),
        ({"limit": "101"}, "limit must be an integer between 1 and 100"),
    ],
)
def test_list_rejects_bad_query(client, params, message):
    response = client.get("/api/expenses", params=params)

    assert response.status_code == 400
    assert response.json() == {"error": message}
