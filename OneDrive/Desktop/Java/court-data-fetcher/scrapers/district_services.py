import os, uuid, re
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from bs4 import BeautifulSoup
from .base import BaseScraper

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "data/downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class DistrictServicesScraper(BaseScraper):
    class InvalidCaptcha(Exception):
        def __init__(self, new_captcha_b64):
            self.new_captcha_b64 = new_captcha_b64

    def __init__(self):
        super().__init__()
        self.input_payload = None

    async def prepare_search(self, payload: dict) -> str:
        self.input_payload = payload
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=True)
        self.context = await self.browser.new_context(accept_downloads=True)
        self.page = await self.context.new_page()
        await self.page.goto("https://services.ecourts.gov.in/ecourtindia_v6/", wait_until="domcontentloaded", timeout=45000)
        # Navigate to Case Status by Case Number
        await self.page.click("text=Case Status")
        await self.page.click("text=By Case Number")
        # State/District/Establishment are often required; fill if provided
        if payload.get("state"):
            await self.page.select_option("select[name='state_code']", payload["state"])
        if payload.get("district"):
            await self.page.select_option("select[name='dist_code']", payload["district"])
        if payload.get("establishment"):
            await self.page.select_option("select[name='est_code']", payload["establishment"])
        # Fill case details
        await self.page.select_option("select[name='case_type']", payload["case_type"])
        await self.page.fill("input[name='case_no']", payload["case_number"])
        await self.page.fill("input[name='case_year']", payload["case_year"])
        # Captcha
        captcha_img = self.page.locator("img#captcha_image, img[alt*='captcha']")
        captcha_b64 = await self._screenshot_element_b64(captcha_img)
        return captcha_b64

    async def submit_and_fetch(self, captcha_text: str) -> dict:
        await self.page.fill("input[name='captcha']", captcha_text)
        await self.page.click("button:has-text('Submit'), input[type='submit']")
        try:
            await self.page.wait_for_selector("text=Invalid Captcha", timeout=4000)
            captcha_b64 = await self._screenshot_element_b64(self.page.locator("img#captcha_image, img[alt*='captcha']"))
            raise DistrictServicesScraper.InvalidCaptcha(captcha_b64)
        except PWTimeoutError:
            pass
        await self.page.wait_for_selector("table, #results, .caseDetails", timeout=30000)
        html = await self.page.content()
        parsed = self._parse_case_details(html)
        orders = await self._collect_orders()
        return {"portal": "DISTRICT_COURT", "court": {"state": self.input_payload.get("state"), "district": self.input_payload.get("district")}, "input": self.input_payload, "parsed": parsed, "orders": orders, "raw_html": html}

    def _parse_case_details(self, html: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        def get_val(label_regex):
            lab = soup.find(string=re.compile(label_regex, re.I))
            if not lab: return None
            td = lab.find_parent("td")
            if td and td.find_next("td"):
                return td.find_next("td").get_text(strip=True)
            return None
        parties = get_val(r"Petitioner|Plaintiff|Respondent|Defendant|Parties")
        filing_date = get_val(r"Filing Date|Registration Date")
        next_date = get_val(r"Next Hearing|Next Date|Listing Date")
        status = get_val(r"Case Status|Stage")
        return {"parties": parties, "filing_date": filing_date, "next_hearing_date": next_date, "case_status": status}

    async def _collect_orders(self):
        orders = []
        # Often there's a 'Orders/Judgments' list with links
        links = await self.page.locator("a").all()
        for l in links:
            href = await l.get_attribute("href")
            text = (await l.inner_text()).strip() if await l.is_visible() else ""
            if not href: continue
            if "order" in href.lower() or "judg" in href.lower() or href.lower().endswith(".pdf"):
                try:
                    with self.page.expect_download(timeout=15000) as dl_info:
                        await l.click(force=True)
                    download = await dl_info.value
                    save_as = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.pdf")
                    await download.save_as(save_as)
                    orders.append({"id": os.path.splitext(os.path.basename(save_as))[0], "title": text or "Order/Judgment", "date": None, "file_path": save_as, "source_url": href})
                except:
                    orders.append({"id": str(uuid.uuid4()), "title": text or "Order/Judgment (link)", "source_url": href, "file_path": None})
        return orders

    async def fetch_cause_list(self, state: str | None, district: str | None, date: str | None):
        # Placeholder generic approach: many districts publish daily PDF cause lists; we try to locate a 'Cause List' menu and capture links
        await self.page.goto("https://services.ecourts.gov.in/ecourtindia_v6/", wait_until="domcontentloaded", timeout=45000)
        try:
            await self.page.click("text=Cause List")
        except:
            pass
        await self.page.wait_for_timeout(1000)
        anchors = await self.page.locator("a").all()
        items = []
        for a in anchors:
            href = await a.get_attribute("href")
            txt = (await a.inner_text()).strip() if await a.is_visible() else ""
            if not href: continue
            if "cause" in href.lower() or "causelist" in href.lower() or href.lower().endswith(".pdf"):
                items.append({"title": txt or "Cause List", "url": href})
        return items

    async def teardown(self):
        await super().teardown()
