import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


def _clean_int(s):
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", str(s))
    return int(digits) if digits else None


def scrape_wclc(url: str):
    """
    Scrape WCLC scratch-win prizes remaining tables from HTML.

    Returns a dict with:
      - source_url
      - row_count
      - rows (list of dicts)
    """
    resp = requests.get(
        url,
        timeout=45,
        headers={"User-Agent": "Mozilla/5.0"},
        allow_redirects=True,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    print(f"[scraper] Final URL: {resp.url}")
    print(f"[scraper] Status: {resp.status_code}")
    print(f"[scraper] Content-Type: {resp.headers.get('content-type')}")
    print(f"[scraper] First 300 chars:\n{resp.text[:300]}")
    print(f"[scraper] Contains 'dataTable'? {'dataTable' in resp.text}")
    print(f"[scraper] Contains '<table'? {'<table' in resp.text.lower()}")

    scrape_ts = datetime.now(timezone.utc).isoformat()

    # WCLC uses <table class="dataTable" summary="Game Name - 21401">
    tables = soup.find_all("table", class_="dataTable")
    print(f"[scraper] Found {len(tables)} dataTable tables")

    rows = []

    for table in tables:
        summary = (table.get("summary") or "").strip()

        # Expect: "$1 Cash Match - 21401"
        m = re.search(r"(.+?)\s*-\s*(\d{5})\b", summary)
        if not m:
            # If a dataTable isn't a game table, skip it
            continue

        game_name = m.group(1).strip()
        game_number = m.group(2)

        tbody = table.find("tbody")
        if not tbody:
            continue

        last_release = None

        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) != 3:
                continue

            release_date = tds[0].get_text(" ", strip=True)
            prize = tds[1].get_text(" ", strip=True)
            remaining = tds[2].get_text(" ", strip=True)

            # Release date can be blank for subsequent prize rows
            if release_date:
                last_release = release_date
            else:
                release_date = last_release

            prizes_remaining = _clean_int(remaining)

            # Skip malformed rows
            if not prize or prizes_remaining is None:
                continue

            rows.append(
                {
                    "scrape_ts_utc": scrape_ts,
                    "source_url": resp.url,
                    "game_name": game_name,
                    "game_number": game_number,
                    "release_date": release_date,
                    "prize": prize,
                    "prizes_remaining": prizes_remaining,
                }
            )

    print(f"[scraper] Extracted {len(rows)} rows")

    return {
        "source_url": resp.url,
        "scrape_ts_utc": scrape_ts,
        "row_count": len(rows),
        "rows": rows,
    }
