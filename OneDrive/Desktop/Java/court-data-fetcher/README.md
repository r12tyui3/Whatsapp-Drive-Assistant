Court-Data Fetcher & Judgment Downloader (India)
- Enter Case Type, Case Number, Year; choose portal (High vs District).
- Manual CAPTCHA entry; parses parties, filing date, next hearing date, status.
- Downloads judgments/orders PDFs when available.
- Saves raw HTML and metadata in SQLite.

Run
- python -m venv .venv && source .venv/bin/activate
- pip install -r requirements.txt
- playwright install chromium
- uvicorn app:app --reload
- Open http://127.0.0.1:8000

CI

- GitHub Actions CI is included and runs parser unit tests on push/PR to `main`.
- Badge (replace `OWNER/REPO` and branch if you move repository):


Development & testing (PowerShell)

Use these commands from the project root on Windows PowerShell (keeps steps explicit):

```powershell
& .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
# Run unit tests (parser tests do not need Playwright)
pytest -q
# To run the server for manual testing (Playwright flows require installed browsers):
playwright install chromium
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Notes
- Unit tests we added exercise only the BeautifulSoup parsing helpers; they do not require Playwright or browser downloads. Keep Playwright browser installs out of CI unless you add browser-dependent E2E tests.
- If you prefer a single requirements file for dev, we added `requirements-dev.txt` for test/dev-only packages (pytest).

Config
- Set PLAYWRIGHT_HEADLESS=false for debugging.
- Switch DB by setting DATABASE_URL.

Notes on selectors and robustness
- The portals occasionally change element names. If you see failures:
  - Run: playwright codegen https://hcservices.ecourts.gov.in/hcservices/ and record the selectors for: Case Status -> Case Number -> fields -> captcha.
  - Update the selectors in scrapers/hc_services.py and scrapers/district_services.py where noted.
- If CAPTCHA is rejected, the API returns captchaError with a fresh image.

Cause list
- The cause list retrieval is generic and looks for "Cause/Causelist" and PDF links on portal menus. For specific High Courts, you can extend HCServicesScraper.fetch_cause_list to navigate to that HC's dedicated cause list page and apply date filters.

Error handling
- Common errors: invalid case inputs, wrong captcha, no records. We return clear messages and store raw HTML for debugging.

Security/legal
- Do not store or share scraped PII without consent. Respect robots.txt and portal terms. This app does not bypass CAPTCHAs.

Testing
- Save sample HTML of result pages (right-click -> Save page source). Add unit tests to parse with BeautifulSoup without hitting the network.

Next improvements (quick wins)
- Auto-suggest lists for High Courts, States, Districts (static JSON).
- Better parsers per court layout (strategy pattern).
- Retry with backoff; circuit breaker for portal downtime.
- Auth and audit log for who accessed what.
- Dockerfile/docker-compose for deployment.
- Postgres migration, S3 storage for PDFs, and role-based access.
