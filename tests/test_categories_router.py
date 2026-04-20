from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def get_app():
    from main import app
    return app


def test_get_categories_returns_list():
    mock_data = [
        {"id": "uuid-1", "slug": "viet-van", "name_vi": "Viết văn",
         "name_en": "Writing", "icon": "✍️", "sort_order": 1}
    ]
    with patch("routers.categories.get_supabase") as mock_sb:
        mock_sb.return_value.table.return_value.select.return_value\
            .order.return_value.execute.return_value.data = mock_data
        client = TestClient(get_app())
        response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "viet-van"


def test_get_categories_empty():
    with patch("routers.categories.get_supabase") as mock_sb:
        mock_sb.return_value.table.return_value.select.return_value\
            .order.return_value.execute.return_value.data = []
        client = TestClient(get_app())
        response = client.get("/api/categories")
    assert response.status_code == 200
    assert response.json() == []
