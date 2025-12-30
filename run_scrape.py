import json
import os
import sys
import urllib.request

from scraper import scrape_wclc

def post_json(url: str, token: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "github-actions-scraper",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        # Read response for debugging if needed
        resp.read()

def main():
    wclc_url = os.environ.get("WCLC_URL", "").strip()
    n8n_webhook_url = os.environ.get("N8N_WEBHOOK_URL", "").strip()
    n8n_token = os.environ.get("N8N_TOKEN", "").strip()

    if not wclc_url:
        print("ERROR: Missing WCLC_URL env var", file=sys.stderr)
        sys.exit(1)
    if not n8n_webhook_url:
        print("ERROR: Missing N8N_WEBHOOK_URL env var", file=sys.stderr)
        sys.exit(1)
    if not n8n_token:
        print("ERROR: Missing N8N_TOKEN env var", file=sys.stderr)
        sys.exit(1)

    payload = scrape_wclc(wclc_url)

    # Optional: keep payload smaller if you want:
    # payload = {"source_url": payload["source_url"], "scrape_ts_utc": payload["scrape_ts_utc"], "rows": payload["rows"]}

    post_json(n8n_webhook_url, n8n_token, payload)
    print(f"Posted {payload.get('row_count')} rows to n8n")

if __name__ == "__main__":
    main()
