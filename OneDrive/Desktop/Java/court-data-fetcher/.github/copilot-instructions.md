## Court Data Fetcher — Copilot instructions (concise)

These notes help an AI agent be productive in this repository immediately. Focus on the concrete, discoverable patterns in the codebase.

- Entry point: `app.py` (FastAPI). Key endpoints:
  - `POST /start-search` — accepts search payload and returns `{sessionId, captchaImageBase64}`. It creates a Playwright scraper instance and stores it in the in-memory `SEARCH_SESSIONS` map.
  - `POST /solve-captcha` — form fields `sessionId` + `captchaText`. Uses the saved scraper to submit captcha, parse results, persist rows to SQLite, and return parsed JSON + orders list.
  - `GET /download/{doc_id}` — serves saved PDF files referenced in `db.models.OrderDocument.file_path`.
  - `GET /cause-list` — uses scraper.fetch_cause_list to collect cause-list PDFs/links.

- High-level architecture:
  - UI/API layer: `app.py` (FastAPI + Jinja templates in `templates/`). Static files in `static/`.
  - Scrapers: `scrapers/` folder with `BaseScraper`, `HCServicesScraper`, `DistrictServicesScraper` (Playwright async flows + BeautifulSoup parsing). Scrapers return a structured dict: {"portal","court","input","parsed","orders","raw_html"}.
  - Persistence: `db/` contains `database.py` (SQLAlchemy engine/session) and `models.py` (tables: QueryLog, RawResponse, CaseDetail, OrderDocument). Default DB: `sqlite:///./data/app.db`.
  - Downloads: PDFs saved to `data/downloads` (env var `DOWNLOAD_DIR` supported).

- Important data shapes and conventions (examples):
  - Scraper result (returned to `app.py`):
    {"portal": "HIGH_COURT"|"DISTRICT_COURT", "court": <str|dict>, "input": <original payload dict>, "parsed": {"parties":..., "filing_date":..., "next_hearing_date":..., "case_status":...}, "orders": [{"id": "<uuid>", "title":..., "file_path": "data/downloads/<uuid>.pdf"|null, "source_url":...}], "raw_html": "<full page HTML>"}
  - DB ids are UUID strings; downloads are saved as `<uuid>.pdf` and OrderDocument.id = filename-without-ext.

- Playwright & session lifecycle patterns:
  - Each scraper creates its own Playwright browser/context/page in `prepare_search()` and stores state on the scraper instance. The instance is kept in `SEARCH_SESSIONS` until `solve-captcha` completes.
  - CAPTCHA flow: `prepare_search()` returns a base64 PNG of the captcha via `_screenshot_element_b64()`; the frontend sends back the typed captcha to `solve-captcha` which calls `submit_and_fetch()`.
  - Scrapers raise an `InvalidCaptcha` exception with `new_captcha_b64` when portal reports an invalid captcha — `app.py` handles that by returning a `captchaError` and a fresh image.

- How to run / dev workflow (from README; repeat here as runnable steps):
  1. Create venv and install deps: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
  2. Install Playwright browsers: `playwright install chromium`
  3. Initialize DB: `python init_db.py` (or run once on startup, FastAPI calls `init_db()`)
  4. Start server: `uvicorn app:app --reload`
  5. For debugging browser interactions set `PLAYWRIGHT_HEADLESS=false` in the environment.

- Project-specific conventions and editing notes for agents:
  - Selector fragility: portal HTML/ids change frequently. When adjusting selectors, update the two scrapers in `scrapers/hc_services.py` and `scrapers/district_services.py` (look for comments like "names can vary; adjust if needed" and locators such as `img#captcha_image` or `select[name='case_type']`).
  - Persist raw HTML: the app stores full HTML into `RawResponse.html` — use this for offline parsing tests.
  - DB pattern: `db.database.get_session()` is a generator used with FastAPI `Depends(get_session)`; code expects a synchronous SQLAlchemy session object in request handlers.
  - Downloads and file existence: `OrderDocument.file_path` may be null when a download failed — code must check file exists before serving.

- Debugging and testing tips (concrete):
  - To reproduce parser issues without Playwright: save a sample result page (`right-click -> View page source`) to disk and write a small test that calls the scraper's `_parse_case_details(html)` with that string (the parsers use BeautifulSoup + regex heuristics).
  - To iterate on selectors quickly: run `playwright codegen https://hcservices.ecourts.gov.in/hcservices/` and copy the relevant selectors into the scraper.
  - To see browser UI while debugging: set `PLAYWRIGHT_HEADLESS=false` and `DOWNLOAD_DIR` to a writable path.

- Files to inspect for changes or extension points:
  - `app.py` — request flow, session management, DB persistence examples
  - `scrapers/base.py` — scraper interface/teardown helpers
  - `scrapers/hc_services.py` and `scrapers/district_services.py` — primary scraping logic, downloads, parsing heuristics
  - `db/models.py` — DB schema and relationships
  - `db/database.py` — engine/session creation, `DATABASE_URL` env support

### Example API payloads & responses

Copyable examples to use in tests or when crafting requests. Field names match `StartSearchPayload` in `app.py`.

- Example `/start-search` request (High Court):

```json
{
  "portal": "HIGH_COURT",
  "high_court": "KARNATAKA_HIGH_COURT",
  "case_type": "CIVIL",
  "case_number": "1234",
  "case_year": "2021"
}
```

- Example `/start-search` request (District Court):

```json
{
  "portal": "DISTRICT_COURT",
  "state": "KAR",
  "district": "BENGALURU",
  "establishment": "MUN_01",
  "case_type": "CR",
  "case_number": "987",
  "case_year": "2020"
}
```

- Example `/start-search` response (successful):

```json
{
  "sessionId": "a1b2c3d4-...",
  "captchaImageBase64": "iVBORw0KGgoAAAANS..."
}
```

- Example `/solve-captcha` form fields (POST form):
  - `sessionId` (string)
  - `captchaText` (string)

- Example `/solve-captcha` response (successful):

```json
{
  "queryId": "uuid-query-id",
  "parsed": {
    "parties": "A v. B",
    "filing_date": "01-01-2020",
    "next_hearing_date": "15-08-2025",
    "case_status": "Pending"
  },
  "orders": [
    {"id": "order-uuid-1", "title": "Order on 01-01-2021", "date": "2021-01-01", "downloadUrl": "/download/order-uuid-1"},
    {"id": "order-uuid-2", "title": "Judgment PDF", "date": null, "downloadUrl": "/download/order-uuid-2"}
  ]
}
```

- Example scraper result shape (internal):

```json
{
  "portal": "HIGH_COURT",
  "court": "KARNATAKA_HIGH_COURT",
  "input": { /* original payload */ },
  "parsed": {"parties": "..", "filing_date": "..", "next_hearing_date": "..", "case_status": ".."},
  "orders": [{"id":"uuid","title":"...","file_path":"data/downloads/<uuid>.pdf"|null,"source_url":"https://..."}],
  "raw_html": "<full page HTML>"
}
```

- Example download usage:

Request: `GET /download/{doc_id}` — returns the PDF saved at `OrderDocument.file_path` if present; otherwise 404.

If any of these sections need more detail (example payloads, failing endpoints, or test harnesses), tell me which part you want expanded and I will iterate.
