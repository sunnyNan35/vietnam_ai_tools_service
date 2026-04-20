from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

MOCK_TOOL = {
    "id": "tool-uuid-1", "slug": "chatgpt", "name": "ChatGPT",
    "category_id": "cat-1", "description_vi": "Trợ lý AI",
    "description_en": "AI assistant", "thumbnail_url": None,
    "pricing": "freemium", "tags": [], "featured": False,
    "status": "published", "source": "manual", "click_count": 0,
    "created_at": datetime.now().isoformat(), "website_url": "https://chat.openai.com",
}


def test_search_returns_results():
    with patch("routers.search.get_supabase") as mock_sb:
        q = MagicMock()
        mock_sb.return_value.table.return_value.select.return_value = q
        q.eq.return_value = q
        q.ilike.return_value = q
        q.execute.return_value.data = [MOCK_TOOL]
        from main import app
        response = TestClient(app).get("/api/search?q=chat")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_empty_query_returns_400():
    from main import app
    response = TestClient(app).get("/api/search?q=")
    assert response.status_code == 400
