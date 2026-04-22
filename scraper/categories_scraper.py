"""
Scrapes all 149 AI tools from freeai.run/categories pages.
Parses embedded __next_f JSON data directly from page HTML — no extra API calls needed.

Usage:  python -m scraper.categories_scraper
Output: scraper/freeai_categories_tools.json
"""
import httpx
import re
import time
import random
import json
import uuid
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.freeai.run"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CATEGORIES = [
    "artificial-intelligence",
    "directory",
    "image-generation-editing",
    "video",
    "chatbots",
    "writing",
    "audio",
    "boilerplates",
    "design",
    "content-creators",
    "building-products",
    "social-media",
    "education",
    "automation",
    "health",
    "productivity",
    "translation",
    "games",
    "browser-extensions",
    "seo",
    "daily-life",
    "advertising",
    "developer-tools",
    "marketing",
    "no-code",
    "analytics",
]


def decode_next_f_chunks(html: str) -> str:
    """Decode all self.__next_f.push([1, "..."]) script blocks and join into one string."""
    marker = 'self.__next_f.push([1,"'
    chunks = []
    pos = 0
    while True:
        start = html.find(marker, pos)
        if start < 0:
            break
        content_start = start + len(marker) - 1  # include opening quote
        i = content_start + 1
        while i < len(html):
            if html[i] == '"' and html[i - 1] != chr(92):  # not escaped
                if html[i + 1:i + 3] == '])':
                    break
            i += 1
        raw_str = html[content_start:i + 1]
        try:
            decoded = json.loads(raw_str)
            chunks.append(decoded)
        except Exception:
            pass
        pos = i + 1
    return ''.join(chunks)


def extract_array_from_key(combined: str, key: str) -> list[dict]:
    """Find all JSON arrays following the given key and return merged list of dicts."""
    results = {}
    for match in re.finditer(re.escape(key), combined):
        start = match.end()
        if start >= len(combined) or combined[start] != '[':
            continue
        depth = 0
        end = start
        for i in range(start, len(combined)):
            if combined[i] == '[':
                depth += 1
            elif combined[i] == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        arr_str = combined[start:end]
        try:
            items = json.loads(arr_str)
            for item in items:
                if isinstance(item, dict):
                    slug = item.get('slug', '')
                    if slug and slug not in results:
                        results[slug] = item
        except Exception:
            pass
    return list(results.values())


def extract_tools_from_html(html: str) -> list[dict]:
    """Extract all product objects embedded in page HTML."""
    combined = decode_next_f_chunks(html)
    seen = {}
    for key in ['"products":', '"initialProducts":', '"items":']:
        for item in extract_array_from_key(combined, key):
            slug = item.get('slug', '')
            if slug and slug not in seen:
                seen[slug] = item
    return list(seen.values())


def clean_name(raw: str, slug: str) -> str:
    """Return ASCII-safe tool name, falling back to slug if garbled."""
    clean = re.sub(r'[^\x20-\x7E]', '', raw).strip()
    return clean if clean else slug.replace('-', ' ').title()


def normalize_tool(raw: dict) -> dict:
    """Convert raw product dict from page JSON to our normalized schema."""
    slug = raw.get('slug', '')
    name = clean_name(raw.get('nameLocalized') or raw.get('name', ''), slug)
    tagline = (raw.get('taglineLocalized') or raw.get('tagline', '')).strip()

    # Categories
    categories = []
    for pc in raw.get('productCategories', []):
        cat = pc.get('category', {})
        cat_slug = cat.get('slug', '')
        cat_name = (cat.get('nameI18n') or {}).get('en') or cat.get('name', '')
        cat_name = re.sub(r'[^\x20-\x7E]', '', cat_name).strip()
        if cat_slug:
            categories.append({'slug': cat_slug, 'name': cat_name})

    # Also check top-level categories field
    for cat in raw.get('categories', []):
        if isinstance(cat, dict):
            cat_slug = cat.get('slug', '')
            if cat_slug and not any(c['slug'] == cat_slug for c in categories):
                cat_name = (cat.get('nameI18n') or {}).get('en') or cat.get('name', '')
                cat_name = re.sub(r'[^\x20-\x7E]', '', cat_name).strip()
                categories.append({'slug': cat_slug, 'name': cat_name})

    # Website URL — strip utm params for cleanliness but keep full href
    website_url = (raw.get('url') or '').strip()

    return {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, f"{BASE_URL}/product/{slug}")),
        'slug': slug,
        'name': name,
        'tagline': tagline,
        'logo_url': raw.get('logoUrl', ''),
        'cover_url': raw.get('coverImage', ''),
        'website_url': website_url,
        'pricing': raw.get('pricingModel', 'Free'),
        'categories': categories,
        'tags': [c['slug'] for c in categories],
        'rating': raw.get('rating'),
        'is_featured': raw.get('isFeatured', False),
        'is_new': False,
        'source_url': f"{BASE_URL}/product/{slug}",
    }


def scrape_category_all_pages(client: httpx.Client, cat_slug: str) -> dict[str, dict]:
    """Scrape all pages of a category, return dict keyed by tool slug."""
    tools: dict[str, dict] = {}
    page = 1
    while True:
        url = f"{BASE_URL}/categories/{cat_slug}" + (f"?page={page}" if page > 1 else "")
        logger.info(f"  {url}")
        try:
            r = client.get(url, timeout=20)
            r.raise_for_status()
            page_tools = extract_tools_from_html(r.text)
            if not page_tools:
                break
            new_count = 0
            for raw in page_tools:
                slug = raw.get('slug', '')
                if slug and slug not in tools:
                    tools[slug] = normalize_tool(raw)
                    new_count += 1
            logger.info(f"    page {page}: {len(page_tools)} tools ({new_count} new)")
            # If we got fewer tools than expected or no new ones, stop paginating
            if new_count == 0 or len(page_tools) < 12:
                break
            page += 1
            time.sleep(0.8 + random.uniform(0, 0.3))
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            break
    return tools


def scrape_product_page_fallback(client: httpx.Client, slug: str) -> dict | None:
    """Fallback: scrape a single product detail page for tools not found in category pages."""
    url = f"{BASE_URL}/product/{slug}"
    try:
        r = client.get(url, timeout=20)
        r.raise_for_status()
        # Try to extract embedded JSON first
        tools = extract_tools_from_html(r.text)
        for raw in tools:
            if raw.get('slug') == slug:
                return normalize_tool(raw)
        # If not found in embedded data, build minimal record from HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        h1 = soup.find('h1')
        name = h1.get_text(strip=True) if h1 else slug.replace('-', ' ').title()
        name = re.sub(r'[^\x20-\x7E]', '', name).strip() or slug.replace('-', ' ').title()
        tagline = ''
        if h1:
            p = h1.find_next('p')
            if p:
                tagline = p.get_text(strip=True)[:300]
        og = soup.find('meta', property='og:image')
        cover = og['content'] if og and og.get('content') else ''
        logo = ''
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'product-logos' in src or 'logos' in src:
                from urllib.parse import unquote
                if '/_next/image?url=' in src:
                    m = re.search(r'url=([^&]+)', src)
                    logo = unquote(m.group(1)) if m else src
                else:
                    logo = src
                break
        visit = soup.find('a', string=re.compile(r'visit\s+website', re.I))
        if not visit:
            visit = soup.find('a', href=re.compile(r'^https?://(?!www\.freeai\.run)'))
        website_url = visit.get('href', '') if visit else ''
        cats = []
        for cl in soup.find_all('a', href=re.compile(r'/categories/')):
            cs = cl['href'].replace('/categories/', '').strip('/')
            cn = cl.get_text(strip=True).lstrip('#').strip()
            if cs and not any(c['slug'] == cs for c in cats):
                cats.append({'slug': cs, 'name': cn})
        return {
            'id': str(uuid.uuid5(uuid.NAMESPACE_URL, url)),
            'slug': slug,
            'name': name,
            'tagline': tagline,
            'logo_url': logo,
            'cover_url': cover,
            'website_url': website_url,
            'pricing': 'Free',
            'categories': cats,
            'tags': [c['slug'] for c in cats],
            'rating': None,
            'is_featured': False,
            'is_new': False,
            'source_url': url,
        }
    except Exception as e:
        logger.warning(f"Fallback failed for {slug}: {e}")
        return None


def get_all_sitemap_slugs(client: httpx.Client) -> list[str]:
    r = client.get(f"{BASE_URL}/sitemap.xml", timeout=20)
    r.raise_for_status()
    return re.findall(r'<loc>https://www\.freeai\.run/product/([^<]+)</loc>', r.text)


def main():
    output_json = "scraper/freeai_categories_tools.json"
    all_tools: dict[str, dict] = {}

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        # Phase 1: scrape all category pages
        logger.info("=== Phase 1: Category pages ===")
        for cat in CATEGORIES:
            logger.info(f"Category: {cat}")
            tools = scrape_category_all_pages(client, cat)
            for slug, tool in tools.items():
                if slug not in all_tools:
                    all_tools[slug] = tool
                else:
                    existing_cats = {c['slug'] for c in all_tools[slug]['categories']}
                    for c in tool['categories']:
                        if c['slug'] not in existing_cats:
                            all_tools[slug]['categories'].append(c)
                            all_tools[slug]['tags'].append(c['slug'])
            logger.info(f"  -> total so far: {len(all_tools)}")
            time.sleep(1.0 + random.uniform(0, 0.4))

        # Phase 2: fill gaps from sitemap
        logger.info("\n=== Phase 2: Sitemap gap fill ===")
        sitemap_slugs = get_all_sitemap_slugs(client)
        logger.info(f"Sitemap has {len(sitemap_slugs)} products")
        missing = [s for s in sitemap_slugs if s not in all_tools]
        logger.info(f"Missing {len(missing)} tools — fetching individually...")
        for i, slug in enumerate(missing):
            logger.info(f"  [{i+1}/{len(missing)}] {slug}")
            tool = scrape_product_page_fallback(client, slug)
            if tool:
                all_tools[slug] = tool
            time.sleep(1.2 + random.uniform(0, 0.4))

    tools_list = list(all_tools.values())
    logger.info(f"\nTotal unique tools: {len(tools_list)}")

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(tools_list, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved to {output_json}")
    print(f"\nDone! {len(tools_list)} tools -> {output_json}")


if __name__ == '__main__':
    main()
