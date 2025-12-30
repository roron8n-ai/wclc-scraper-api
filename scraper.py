import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

def _clean_int(s: str):
    digits = re.sub(r"[^\d]", "", s or "")
    return int(digits) if digits else None

def _clean_money(s: str):
    # returns float if it looks like money, else None
    if s is None:
        return None
    x = re.sub(r"[^0-9.]", "", s)
    return float(x) if x else None

def scrape_wclc(url: str):
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    now = datetime.now(timezone.utc).isoformat()

    out_rows = []
    tables = soup.find_all("table")

    def table_header_text(table):
        ths = table.find_all("th")
        return " ".join(th.get_text(" ", strip=True) for th in ths)

    def find_game_title_near(table):
        # Try to find a nearby heading/title text that includes a 5-digit game number
        for cand in table.find_all_previous(["h1","h2","h3","h4","strong","b","p","div","span"], limit=12):
            txt = cand.get_text(" ", strip=True)
            if re.search(r"\b\d{5}\b", txt):
                # keep it short-ish
                return txt[:180]
        return ""

    for t in tables:
        header = table_header_text(t)
        # The exact labels vary, but these are common on scratch prize tables
        if ("Prizes Remaining" not in header) or ("Prizes" not in header):
            continue

        game_title = find_game_title_near(t)

        # Try to map columns by reading the first header row
        ths = [th.get_text(" ", strip=True) for th in t.find_all("th")]
        # Common columns: Release Date | Prize | Prizes Remaining  (or similar)
        # We'll just read each row's td cells and keep those we can interpret.
        for tr in t.find_all("tr"):
            tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(tds) < 2:
                continue

            # Heuristic: last cell often "remaining"
            remaining = tds[-1]
            remaining_n = _clean_int(remaining)

            # prize is often middle/2nd column
            prize_text = tds[1] if len(tds) >= 3 else tds[0]
            prize_amt = _clean_money(prize_text)

            release_date = tds[0] if len(tds) >= 3 else None

            if remaining_n is None:
                continue

            out_rows.append({
                "scrape_ts_utc": now,
                "game": game_title,
                "release_date": release_date,
                "prize": prize_text,
                "prize_amount": prize_amt,
                "prizes_remaining": remaining_n,
                "source_url": url,
            })

    return {
        "source_url": url,
        "scrape_ts_utc": now,
        "rows": out_rows,
        "row_count": len(out_rows),
    }
