import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def run_scraper_job():
    """Runs daily at 02:00 UTC. Fetches tools and upserts into Supabase."""
    from database import get_supabase
    from scraper import theresanaiforthat, toolify

    sb = get_supabase()

    existing = sb.table("tools").select("website_url").execute()
    existing_urls = {row["website_url"] for row in (existing.data or [])}

    cats = sb.table("categories").select("id, slug").execute()
    cat_map = {row["slug"]: row["id"] for row in (cats.data or [])}

    all_tools = []
    try:
        all_tools += theresanaiforthat.scrape(max_pages=5)
    except Exception as e:
        logger.error(f"theresanaiforthat scrape failed: {e}")
    try:
        all_tools += toolify.scrape(max_pages=5)
    except Exception as e:
        logger.error(f"toolify scrape failed: {e}")

    new_count = 0
    for tool in all_tools:
        if tool["website_url"] in existing_urls:
            continue
        category_slug = tool.pop("category_slug", "tien-ich")
        tool["category_id"] = cat_map.get(category_slug)
        try:
            sb.table("tools").insert(tool).execute()
            existing_urls.add(tool["website_url"])
            new_count += 1
        except Exception as e:
            logger.warning(f"Insert failed for {tool.get('name')}: {e}")

    logger.info(f"Scraper job complete: {new_count} new tools inserted")


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scraper_job,
        trigger=CronTrigger(hour=2, minute=0, timezone="UTC"),
        id="daily_scraper",
        replace_existing=True,
    )
    return scheduler
