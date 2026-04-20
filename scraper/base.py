import httpx
import re
import time
import random
import logging

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


class BaseScraper:
    def __init__(self, rate_limit_seconds: float = 2.5):
        self.rate_limit = rate_limit_seconds
        self.client = httpx.Client(
            headers={"User-Agent": random.choice(USER_AGENTS)},
            timeout=15.0,
            follow_redirects=True,
        )

    def fetch(self, url: str) -> str:
        response = self.client.get(url)
        response.raise_for_status()
        return response.text

    def fetch_with_delay(self, url: str) -> str:
        time.sleep(self.rate_limit + random.uniform(0, 1))
        return self.fetch(url)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
