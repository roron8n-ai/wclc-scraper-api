import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup


def _clean_int(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else None


def _clean_money(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    x = re.sub(r"[^0-9.]", "", s)
    return float(x) if x else None


def _table_header_text(table) -> str:
    ths = table.find_all("th")
    return " ".join(th.get_text(" ", strip=True) for th in ths)


def _find_game_title_near(table) -> str:
    """
    Attempts to find a nearby title (usually above the table) containing a 5-digit game number.
    Returns a short snippet.
    """
    for cand in table.find_all_previous(
        ["h1", "h2", "h3", "h4", "strong", "b", "p", "div", "span"],
        limit=18,
    ):
        txt = cand.get_text(" ", strip=True)
        if re.search(r"\b\d{5}\b", txt):
            return txt[:200]
    return ""


def scrape_wclc(url: str) -> Dict[str, Any]:
    """
    Scrape a WCLC page for scratch ticket prize tables.
    Returns dict with keys: source_url, scrape_ts_utc, row_count, rows.
    Each row includes: game, release_date, prize, prize_amount, prizes_remaining, scrape_ts_utc, source_url.
    """
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()

    # Some WCLC pages are XHTML-ish, but lxml parser is more robust than "xml".
    soup = BeautifulSoup(r.text, "lxml")
    scrape_ts = datetime.now(timezone.utc).isoformat()

    tables = soup.find_all("table")
    print(f"[scraper] Found {len(tables)} tables total")

    if tables:
        h0 = [th.get_text(" ", strip=True) for th in tables[0].find_all("th")]
        print("[scraper] First table headers:", h0)

    out_rows: List[Dict[str, Any]] = []

    # We look for tables that smell like the ones in your screenshot:
    # headers contain "Prizes" and "Prizes Remaining" and often "Release Date"
    matched_tables = 0

    for t in tables:
        header_text = _table_header_text(t)

        if ("Prizes" not in header_text) or ("Remaining" not in header_text):
            continue

        matched_tables += 1
        game_title = _find_game_title_near(t)

        # Find release date in row cells if present
        # We will parse each table row, expecting columns: Release Date | Prizes | Prizes Remaining
        rows = t.find_all("tr")
        if not rows:
            continue

        # Determine header mapping (best-effort)
        header_cells = [th.get_text(" ", strip=True) for th in rows[0].find_all(["th", "td"])]
        # Normalize
        norm = [c.lower() for c in header_cells]

        # Try to locate columns
        def col_index(keywords: List[str]) -> Optional[int]:
            for i, c in enumerate(norm):
                if any(k in c for k in keywords):
                    return i
            return None

        idx_release = col_index(["release"])
        idx_prize = col_index(["prize"])
        idx_remaining = col_index(["remaining"])

        print(
            f"[scraper] Matched table headers='{header_text[:120]}...' "
            f"idx_release={idx_release} idx_prize={idx_prize} idx_remaining={idx_remaining} "
            f"title='{game_title}'"
        )

        # Iterate data rows (skip header row if it looks like a header)
        for tr in rows[1:] if header_cells else rows:
            tds = tr.find_all(["td", "th"])
            if not tds:
                continue

            cells = [c.get_text(" ", strip=True) for c in tds]

            # Sometimes there are spacer rows etc.
            if all(not c for c in cells):
                continue

            # If indexes not found, attempt fallback:
            # If table seems to have 3 columns, map 0/1/2.
            rel = None
            prize_text = None
            remaining_text = None

            if idx_release is not None and idx_release < len(cells):
                rel = cells[idx_release]
            if idx_prize is not None and idx_prize < len(cells):
                prize_text = cells[idx_prize]
            if idx_remaining is not None and idx_remaining < len(cells):
                remaining_text = cells[idx_remaining]

            if (rel is None and prize_text is None and remaining_text is None) and len(cells) >= 3:
                rel, prize_text, remaining_text = cells[0], cells[1], cells[2]

            # Some tables repeat release date only on first row; subsequent rows have blank release.
            # We'll keep release as-is; n8n/sheets can fill forward later if needed.
            prize_amount = _clean_money(prize_text)
            prizes_remaining = _clean_int(remaining_text)

            # If we can't interpret prize or remaining, skip
            if prize_text is None or prizes_remaining is None:
                continue

            out_rows.append(
                {
                    "scrape_ts_utc": scrape_ts,
                    "source_url": url,
                    "game": game_title,
                    "release_date": rel,
                    "prize": prize_text,
                    "prize_amount": prize_amount,
                    "prizes_remaining": prizes_remaining,
                }
            )

    print(f"[scraper] Matched {matched_tables} candidate tables; extracted {len(out_rows)} rows")

    return {
        "source_url": url,
        "scrape_ts_utc": scrape_ts,
        "row_count": len(out_rows),
        "rows": out_rows,
    }
