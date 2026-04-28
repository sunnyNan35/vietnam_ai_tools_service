import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from urllib.error import URLError, HTTPError

IMAGES_DIR = Path(__file__).parent / "images"


def safe_filename(url: str) -> str:
    return url.split("/")[-1].split("?")[0]


def download(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except (HTTPError, URLError) as e:
        print(f"  FAIL {url}: {e}", file=sys.stderr)
        return False


def main():
    json_path = Path(__file__).parent / "freeai_categories_tools.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    ok = fail = skip = 0

    for item in data:
        slug = item.get("slug", "").strip()
        if not slug:
            continue

        folder = IMAGES_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)

        for field in ("logo_url", "cover_url"):
            url = item.get(field, "")
            if not url:
                continue
            filename = safe_filename(url)
            dest = folder / filename
            if dest.exists():
                skip += 1
                continue
            print(f"[{field}] {slug} -> {filename}")
            if download(url, dest):
                ok += 1
            else:
                fail += 1

    print(f"\nDone: {ok} downloaded, {skip} skipped, {fail} failed.")


if __name__ == "__main__":
    main()
