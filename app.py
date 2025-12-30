import os
from flask import Flask, jsonify, request
from scraper import scrape_wclc

app = Flask(__name__)

# Env vars (set these in Railway)
WCLC_URL = os.environ.get("WCLC_URL", "").strip()
API_KEY = os.environ.get("API_KEY", "").strip()  # optional

def require_key():
    """Return (ok, response)"""
    if not API_KEY:
        return True, None  # no auth required
    incoming = request.headers.get("x-api-key", "").strip()
    if incoming != API_KEY:
        return False, (jsonify({"error": "Unauthorized"}), 401)
    return True, None

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.get("/scrape")
def scrape():
    ok, resp = require_key()
    if not ok:
        return resp

    if not WCLC_URL:
        return jsonify({"error": "Missing WCLC_URL env var"}), 500

    try:
        data = scrape_wclc(WCLC_URL)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Local dev
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "3000")), debug=True)
