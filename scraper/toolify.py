import logging
from bs4 import BeautifulSoup
from scraper.base import BaseScraper, slugify
from scraper.theresanaiforthat import map_category, parse_pricing

logger = logging.getLogger(__name__)

BASE_URL = "https://www.toolify.ai"
LIST_URL = f"{BASE_URL}/ai-tools"


def scrape_page(scraper: BaseScraper, page: int) -> list[dict]:
    url = f"{LIST_URL}?page={page}"
    logger.info(f"Scraping toolify.ai page {page}")
    try:
        html = scraper.fetch_with_delay(url)
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    tools = []

    for card in soup.select("div.tool-card, div.tool_item, article.tool"):
        try:
            name_el = card.select_one("h2, h3, .tool-name, .tool_name")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name:
                continue

            link_el = card.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            website_url = href if href.startswith("http") else BASE_URL + href

            desc_el = card.select_one("p, .description, .tool-desc")
            description_en = desc_el.get_text(strip=True) if desc_el else ""

            img_el = card.select_one("img")
            thumbnail_url = img_el.get("src", "") if img_el else ""

            tag_els = card.select(".tag, .category, span.tag")
            tags = [t.get_text(strip=True) for t in tag_els if t.get_text(strip=True)]

            pricing_el = card.select_one(".price, .pricing, .plan")
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
                "source": "toolify.ai",
                "category_slug": map_category(tags),
            })
        except Exception as e:
            logger.warning(f"Failed to parse toolify card: {e}")
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
    logger.info(f"toolify.ai: scraped {len(tools)} tools")
    return tools
