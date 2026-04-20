import pytest
from unittest.mock import patch, MagicMock
import httpx


def test_base_scraper_fetch_returns_text():
    from scraper.base import BaseScraper
    scraper = BaseScraper()
    mock_response = MagicMock()
    mock_response.text = "<html>hello</html>"
    mock_response.raise_for_status = MagicMock()
    with patch.object(scraper.client, "get", return_value=mock_response) as mock_get:
        result = scraper.fetch("https://example.com")
    assert result == "<html>hello</html>"
    mock_get.assert_called_once_with("https://example.com")


def test_base_scraper_fetch_raises_on_http_error():
    from scraper.base import BaseScraper
    scraper = BaseScraper()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=MagicMock()
    )
    with patch.object(scraper.client, "get", return_value=mock_response):
        with pytest.raises(httpx.HTTPStatusError):
            scraper.fetch("https://example.com/404")


def test_slugify():
    from scraper.base import slugify
    assert slugify("ChatGPT") == "chatgpt"
    assert slugify("Midjourney AI") == "midjourney-ai"
    assert slugify("GPT-4o") == "gpt-4o"
    assert slugify("  spaces  ") == "spaces"
