from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

MOCK_TOOL = {
    "id": "tool-uuid-1",
    "slug": "chatgpt",
    "name": "ChatGPT",
    "category_id": "cat-uuid-1",
    "description_vi": "Trợ lý AI thông minh",
    "description_en": "AI assistant",
    "thumbnail_url": "https://example.com/img.png",
    "pricing": "freemium",
    "tags": ["chat", "ai"],
    "featured": True,
    "status": "published",
    "source": "manual",
    "click_count": 42,
    "created_at": datetime.now().isoformat(),
    "website_url": "https://chat.openai.com",
    "affiliate_url": "https://secret-affiliate-link.com",
}


def get_client():
    from main import app
    return TestClient(app)


def _mock_tools_query(mock_sb, data, count=None):
    q = MagicMock()
    mock_sb.return_value.table.return_value.select.return_value = q
    q.eq.return_value = q
    q.order.return_value = q
    q.range.return_value = q
    q.execute.return_value.data = data
    q.execute.return_value.count = count or len(data)
    return q


def test_list_tools_excludes_affiliate_url():
    with patch("routers.tools.get_supabase") as mock_sb:
        _mock_tools_query(mock_sb, [MOCK_TOOL])
        response = get_client().get("/api/tools")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert "affiliate_url" not in items[0]


def test_list_tools_pagination():
    with patch("routers.tools.get_supabase") as mock_sb:
        _mock_tools_query(mock_sb, [MOCK_TOOL], count=1)
        response = get_client().get("/api/tools?page=1&limit=12")
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["limit"] == 12


def test_get_tool_by_slug():
    with patch("routers.tools.get_supabase") as mock_sb:
        mock_sb.return_value.table.return_value.select.return_value.eq\
            .return_value.eq.return_value.single.return_value.execute\
            .return_value.data = MOCK_TOOL
        response = get_client().get("/api/tools/chatgpt")
    assert response.status_code == 200
    assert response.json()["slug"] == "chatgpt"
    assert "affiliate_url" not in response.json()


def test_click_returns_affiliate_url():
    with patch("routers.tools.get_supabase") as mock_sb:
        get_mock = MagicMock()
        get_mock.execute.return_value.data = {"affiliate_url": "https://secret.com", "click_count": 0}
        update_mock = MagicMock()
        update_mock.execute.return_value.data = {}
        mock_sb.return_value.table.return_value.select.return_value\
            .eq.return_value.single.return_value = get_mock
        mock_sb.return_value.table.return_value.update.return_value\
            .eq.return_value = update_mock
        response = get_client().post("/api/tools/tool-uuid-1/click")
    assert response.status_code == 200
    assert response.json()["affiliate_url"] == "https://secret.com"


def test_featured_tools():
    with patch("routers.tools.get_supabase") as mock_sb:
        q = MagicMock()
        mock_sb.return_value.table.return_value.select.return_value\
            .eq.return_value.eq.return_value.order.return_value\
            .execute.return_value.data = [MOCK_TOOL]
        response = get_client().get("/api/tools/featured")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
