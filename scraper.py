# scraper.py
# Replace your entire scraper.py with this file.

import re
from datetime import datetime, timezone

import cloudscraper
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
      - scrape_ts_utc
      - row_count
      - rows (list of dicts)
    """
    # --- FETCH (cloudscraper instead of requests) ---
    cs = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )

    resp = cs.get(
        url,
        timeout=45,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://www.wclc.com/",
        },
    )
    resp.raise_for_status()

    # --- DIAGNOSTICS (keep for now; remove later if you want) ---
    print(f"[scraper] Final URL: {resp.url}")
    print(f"[scraper] Status: {resp.status_code}")
    print(f"[scraper] Content-Type: {resp.headers.get('content-type')}")
    print(f"[scraper] First 300 chars:\n{resp.text[:300]}")
    print(f"[scraper] Contains 'dataTable'? {'dataTable' in resp.text}")
    print(f"[scraper] Contains '<table'? {'<table' in resp.text.lower()}")

    # --- PARSE ---
    soup = BeautifulSoup(resp.text, "lxml")
    scrape_ts = datetime.now(timezone.utc).isoformat()

    tables = soup.find_all("table", class_="dataTable")
    print(f"[scraper] Found {len(tables)} dataTable tables")

    rows = []

    for table in tables:
        summary = (table.get("summary") or "").strip()

        # Expect: "$1 Cash Match - 21401"
        m = re.search(r"(.+?)\s*-\s*(\d{5})\b", summary)
        if not m:
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

            # Release date may be blank for subsequent prize rows
            if release_date:
                last_release = release_date
            else:
                release_date = last_release

            prizes_remaining = _clean_int(remaining)

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

    # --- RETURN ---
    return {
        "source_url": resp.url,
        "scrape_ts_utc": scrape_ts,
        "row_count": len(rows),
        "rows": rows,
    }
