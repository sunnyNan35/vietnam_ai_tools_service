import logging
from bs4 import BeautifulSoup
from scraper.base import BaseScraper, slugify

logger = logging.getLogger(__name__)

BASE_URL = "https://theresanaiforthat.com"
LIST_URL = f"{BASE_URL}/ais/?sort=latest&page="

CATEGORY_MAP = {
    "writing": "viet-van", "copywriting": "viet-van", "content": "viet-van",
    "image": "hinh-anh", "art": "hinh-anh", "photo": "hinh-anh", "design": "hinh-anh",
    "code": "lap-trinh", "coding": "lap-trinh", "developer": "lap-trinh",
    "video": "video",
    "music": "am-nhac", "audio": "am-nhac",
    "business": "kinh-doanh", "marketing": "kinh-doanh", "sales": "kinh-doanh",
    "education": "hoc-tap", "learning": "hoc-tap",
    "productivity": "tien-ich", "utility": "tien-ich",
}


def map_category(tags: list[str]) -> str:
    for tag in tags:
        lower = tag.lower()
        for keyword, slug in CATEGORY_MAP.items():
            if keyword in lower:
                return slug
    return "tien-ich"


def parse_pricing(text: str) -> str:
    lower = text.lower()
    if "free" in lower and ("paid" in lower or "premium" in lower):
        return "freemium"
    if "free" in lower:
        return "free"
    return "paid"


def scrape_page(scraper: BaseScraper, page: int) -> list[dict]:
    url = f"{LIST_URL}{page}"
    logger.info(f"Scraping theresanaiforthat.com page {page}")
    try:
        html = scraper.fetch_with_delay(url)
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    tools = []

    for card in soup.select("div.ai_box"):
        try:
            name_el = card.select_one("h2.ai_title, h3.ai_title, .ai-name")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name:
                continue

            link_el = card.select_one("a[href]")
            website_url = link_el["href"] if link_el else ""
            if not website_url.startswith("http"):
                website_url = BASE_URL + website_url

            desc_el = card.select_one(".ai_description, p.description")
            description_en = desc_el.get_text(strip=True) if desc_el else ""

            img_el = card.select_one("img")
            thumbnail_url = img_el.get("src", "") if img_el else ""

            tag_els = card.select(".tag, .category-tag, span.tag")
            tags = [t.get_text(strip=True) for t in tag_els if t.get_text(strip=True)]

            pricing_el = card.select_one(".pricing, .price-tag, span.pricing")
            pricing_text = pricing_el.get_text(strip=True) if pricing_el else "free"
            pricing = parse_pricing(pricing_text)

            tools.append({
                "name": name,
                "slug": slugify(name),
                "website_url": website_url,
                "description_en": description_en,
                "description_vi": None,
                "thumbnail_url": thumbnail_url,
                "pricing": pricing,
                "tags": tags,
                "featured": False,
                "status": "pending",
                "source": "theresanaiforthat.com",
                "category_slug": map_category(tags),
            })
        except Exception as e:
            logger.warning(f"Failed to parse tool card: {e}")
            continue

    return tools


def scrape(max_pages: int = 5) -> list[dict]:
    tools = []
    with BaseScraper() as scraper:
        for page in range(1, max_pages + 1):
            page_tools = scrape_page(scraper, page)
            if not page_tools:
                break
            tools.extend(page_tools)
    logger.info(f"theresanaiforthat.com: scraped {len(tools)} tools")
    return tools
