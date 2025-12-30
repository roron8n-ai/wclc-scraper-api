\# WCLC Scraper API (Railway + n8n)



\## Deploy to Railway

1\. Create a GitHub repo and push these files.

2\. Go to Railway -> New Project -> Deploy from GitHub repo.

3\. Set Environment Variables in Railway:

&nbsp;  - WCLC\_URL = https://... (the lottery page you want to scrape)

&nbsp;  - API\_KEY  = some-random-secret (optional)

4\. Railway will build and give you a public URL.



\## Endpoints

\- GET /health

\- GET /scrape  (requires header x-api-key if API\_KEY is set)



\## n8n Setup

1\. Cron node (daily/weekly)

2\. HTTP Request node:

&nbsp;  - Method: GET

&nbsp;  - URL: https://YOUR-RAILWAY-APP/scrape

&nbsp;  - Headers:

&nbsp;      x-api-key: YOUR\_API\_KEY (if enabled)

3\. Use a "Item Lists" or "Function" node to turn rows into items:

&nbsp;  - items = $json.rows

4\. Google Sheets node -> Append rows



