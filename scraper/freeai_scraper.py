"""
Scrapes all tools from freeai.run and generates INSERT SQL statements.
Usage: python -m scraper.freeai_scraper
"""
import httpx
import re
import time
import random
import json
import uuid
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

CATEGORY_MAP = {
    "writing": "viet-van",
    "copywriting": "viet-van",
    "content": "viet-van",
    "image": "hinh-anh",
    "photo": "hinh-anh",
    "design": "hinh-anh",
    "art": "hinh-anh",
    "coding": "lap-trinh",
    "developer": "lap-trinh",
    "code": "lap-trinh",
    "programming": "lap-trinh",
    "video": "video",
    "music": "am-nhac",
    "audio": "am-nhac",
    "voice": "am-nhac",
    "business": "kinh-doanh",
    "marketing": "kinh-doanh",
    "seo": "kinh-doanh",
    "education": "hoc-tap",
    "learning": "hoc-tap",
    "research": "hoc-tap",
    "productivity": "tien-ich",
    "tool": "tien-ich",
    "assistant": "tien-ich",
    "chat": "tien-ich",
    "artificial intelligence": "tien-ich",
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def map_category(category_text: str) -> str:
    text = category_text.lower()
    for keyword, slug in CATEGORY_MAP.items():
        if keyword in text:
            return slug
    return "tien-ich"


def parse_pricing(text: str) -> str:
    text = text.lower()
    if "freemium" in text:
        return "freemium"
    if "paid" in text or "premium" in text or "pro" in text or "subscription" in text:
        return "paid"
    return "free"


def get_all_product_urls(client: httpx.Client) -> list[str]:
    r = client.get("https://www.freeai.run/sitemap.xml")
    r.raise_for_status()
    urls = re.findall(r"<loc>(https://www\.freeai\.run/product/[^<]+)</loc>", r.text)
    logger.info(f"Found {len(urls)} product URLs in sitemap")
    return urls


def scrape_product_page(client: httpx.Client, url: str) -> dict | None:
    try:
        r = client.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Tool name from h1
        h1 = soup.find("h1")
        name = h1.get_text(strip=True) if h1 else url.split("/")[-1].replace("-", " ").title()
        # Clean encoding artifacts
        name = re.sub(r"[^\x00-\x7F]+", "", name).strip(" -–")
        if not name:
            name = url.split("/")[-1].replace("-", " ").title()

        # Category from breadcrumb or nav
        category_slug = "tien-ich"
        breadcrumb = soup.find("nav", {"aria-label": re.compile("breadcrumb", re.I)})
        if not breadcrumb:
            breadcrumb = soup.find(class_=re.compile("breadcrumb", re.I))
        if breadcrumb:
            links = breadcrumb.find_all("a")
            for link in links:
                cat_text = link.get_text(strip=True)
                if cat_text.lower() not in ("home", "freeai", "freeai.run", ""):
                    category_slug = map_category(cat_text)
                    break

        # If no breadcrumb, try category tags/badges on the page
        if category_slug == "tien-ich":
            page_text = soup.get_text()
            for keyword, slug in CATEGORY_MAP.items():
                if keyword in page_text.lower()[:500]:
                    category_slug = slug
                    break

        # Description - prefer first substantial paragraph on page, fallback to meta
        description = ""
        if h1:
            for sib in h1.find_all_next("p"):
                txt = sib.get_text(strip=True)
                if len(txt) > 80:
                    description = txt[:1000]
                    break
        if not description:
            meta_desc = soup.find("meta", {"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()

        # Pricing - look for pricing badges/text
        pricing = "free"
        page_text_lower = soup.get_text().lower()
        if "freemium" in page_text_lower:
            pricing = "freemium"
        elif any(w in page_text_lower for w in ["paid", "premium plan", "pro plan", "subscription"]):
            pricing = "paid"

        # Website URL - look for "Visit Website" link
        visit_link = soup.find("a", string=re.compile("visit website", re.I))
        if not visit_link:
            visit_link = soup.find("a", href=re.compile(r"^https?://(?!www\.freeai\.run)"))
        website_url = visit_link["href"] if visit_link and visit_link.get("href") else ""

        # Thumbnail - og:image
        og_image = soup.find("meta", property="og:image")
        thumbnail_url = og_image["content"] if og_image and og_image.get("content") else ""

        # Slug from URL
        slug = url.split("/product/")[-1].strip("/")

        return {
            "id": str(uuid.uuid4()),
            "slug": slug,
            "name": name[:200],
            "description_en": description[:1000],
            "description_vi": "",
            "website_url": website_url[:500],
            "affiliate_url": website_url[:500],
            "thumbnail_url": thumbnail_url[:500],
            "pricing": pricing,
            "tags": [],
            "category_slug": category_slug,
            "featured": False,
            "status": "published",
            "source": "freeai.run",
            "click_count": 0,
        }

    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return None


def escape_sql(s: str) -> str:
    return s.replace("'", "''")


def generate_sql(tools: list[dict]) -> str:
    lines = [
        "-- Generated from freeai.run scraper",
        "-- Run AFTER 001_initial_schema.sql",
        "",
        "-- Map category slugs to IDs (adjust if your UUIDs differ)",
        "DO $$",
        "DECLARE",
        "  cat_id UUID;",
        "BEGIN",
        "",
    ]

    for tool in tools:
        cat_slug = tool.pop("category_slug", "tien-ich")
        tags_json = json.dumps(tool["tags"]).replace("'", "''")
        desc_en = escape_sql(tool["description_en"])
        desc_vi = escape_sql(tool["description_vi"])
        name = escape_sql(tool["name"])
        slug = escape_sql(tool["slug"])
        website_url = escape_sql(tool["website_url"])
        affiliate_url = escape_sql(tool["affiliate_url"])
        thumbnail_url = escape_sql(tool["thumbnail_url"])

        lines.append(f"  SELECT id INTO cat_id FROM categories WHERE slug = '{cat_slug}';")
        lines.append(f"  INSERT INTO tools (id, slug, name, description_en, description_vi, website_url, affiliate_url, thumbnail_url, pricing, tags, category_id, featured, status, source, click_count)")
        lines.append(f"  VALUES ('{tool['id']}', '{slug}', '{name}', '{desc_en}', '{desc_vi}', '{website_url}', '{affiliate_url}', '{thumbnail_url}', '{tool['pricing']}', '{tags_json}'::jsonb, cat_id, {str(tool['featured']).lower()}, '{tool['status']}', '{tool['source']}', {tool['click_count']})")
        lines.append(f"  ON CONFLICT (slug) DO NOTHING;")
        lines.append("")

    lines.append("END $$;")
    return "\n".join(lines)


def main():
    with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        product_urls = get_all_product_urls(client)

        tools = []
        for i, url in enumerate(product_urls):
            logger.info(f"[{i+1}/{len(product_urls)}] Scraping {url}")
            tool = scrape_product_page(client, url)
            if tool and tool["name"]:
                tools.append(tool)
            time.sleep(1.5 + random.uniform(0, 0.5))

        logger.info(f"Scraped {len(tools)} tools")

        sql = generate_sql(tools)
        output_path = "migrations/002_freeai_tools.sql"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sql)

        logger.info(f"SQL written to {output_path}")
        print(f"\nDone! {len(tools)} tools -> {output_path}")


if __name__ == "__main__":
    main()
