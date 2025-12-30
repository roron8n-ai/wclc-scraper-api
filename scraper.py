import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import re


def clean_int(s: str):
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else None


def scrape_wclc(url: str):
    r = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    now = datetime.now(timezone.utc).isoformat()

    out_rows = []

    tables = soup.find_all("table", class_="dataTable")
    print(f"[scraper] Found {len(tables)} tables total")

    for table in tables:
        summary = table.get("summary", "").strip()

        # Expect something like "$1 Cash Match - 21401"
        m = re.search(r"(.*)\s+-\s+(\d{5})$", summary)
        if not m:
            continue

        game_name = m.group(1).strip()
        game_number = m.group(2)

        tbody = table.find("tbody")
        if not tbody:
            continue

        for tr in tbody.find_all("tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(tds) != 3:
                continue

            release_date, prize, remaining = tds

            out_rows.append(
                {
                    "scraped_at": now,
                    "game_number": game_number,
                    "game_name": game_name,
                    "release_date": release_date,
                    "prize": prize,
                    "prizes_remaining": clean_int(remaining),
                }
            )

    print(
        f"[scraper] Matched {len(tables)} tables; extracted {len(out_rows)} rows"
    )

    return {
        "source_url": url,
        "row_count": len(out_rows),
        "rows": out
