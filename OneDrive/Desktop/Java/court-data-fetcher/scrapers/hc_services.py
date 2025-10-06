import os, uuid, re, asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from bs4 import BeautifulSoup
from .base import BaseScraper

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "data/downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class HCServicesScraper(BaseScraper):
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
        await self.page.goto("https://hcservices.ecourts.gov.in/hcservices/", wait_until="domcontentloaded", timeout=45000)
        # Navigate to Case Status (this may vary slightly; adjust if needed)
        await self.page.click("text=Case Status")
        # Select High Court
        if payload.get("high_court"):
            await self.page.select_option("select[name='hc']" , payload["high_court"])
        # Choose 'By Case Number'
        await self.page.click("text=Case Number")
        # Fill case fields (names can vary; inspect once and adjust)
        await self.page.select_option("select[name='case_type']", payload["case_type"])
        await self.page.fill("input[name='case_no']", payload["case_number"])
        await self.page.fill("input[name='rgyear']", payload["case_year"])
        # Locate captcha image
        captcha_img = self.page.locator("img#captcha_image, img[alt*='captcha']")
        captcha_b64 = await self._screenshot_element_b64(captcha_img)
        return captcha_b64

    async def submit_and_fetch(self, captcha_text: str) -> dict:
        # Fill captcha and submit
        await self.page.fill("input[name='captcha']", captcha_text)
        await self.page.click("button:has-text('Submit'), input[type='submit']")
        # Check for invalid captcha feedback
        try:
            await self.page.wait_for_selector("text=Invalid CAPTCHA, try again", timeout=4000)
            # Refresh captcha image
            captcha_img = self.page.locator("img#captcha_image, img[alt*='captcha']")
            captcha_b64 = await self._screenshot_element_b64(captcha_img)
            raise HCServicesScraper.InvalidCaptcha(captcha_b64)
        except PWTimeoutError:
            pass
        # Wait for result block/table
        await self.page.wait_for_selector("table, #results, .result", timeout=30000)
        html = await self.page.content()
        parsed = self._parse_case_details(html)
        orders = await self._collect_orders()
        return {
            "portal": "HIGH_COURT",
            "court": self.input_payload.get("high_court"),
            "input": self.input_payload,
            "parsed": parsed,
            "orders": orders,
            "raw_html": html
        }

    def _parse_case_details(self, html: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        # Heuristics: look for labels commonly used by HC services
        def text_of(label):
            el = soup.find(string=re.compile(label, re.I))
            if not el: return None
            # next td or sibling
            td = el.find_parent("td")
            if td and td.find_next("td"):
                return td.find_next("td").get_text(strip=True)
            # fallback
            return el.parent.get_text(strip=True) if el and el.parent else None

        parties = text_of(r"Party|Petitioner|Respondent")
        filing_date = text_of(r"Filing Date|Filed on|Registration Date")
        next_date = text_of(r"Next Hearing|Next date|Listing Date")
        status = text_of(r"Status|Case Status|Stage")
        return {"parties": parties, "filing_date": filing_date, "next_hearing_date": next_date, "case_status": status}

    async def _collect_orders(self):
        orders = []
        # Try to switch to Orders/Judgments tab if present
        try:
            if await self.page.is_visible("text=Orders") or await self.page.is_visible("text=Judgements") or await self.page.is_visible("text=Judgments"):
                await self.page.click("text=Orders, text=Judgements, text=Judgments")
                await self.page.wait_for_timeout(500)
        except:
            pass
        # Collect links that look like PDFs or order download endpoints
        links = await self.page.locator("a").all()
        for l in links:
            href = await l.get_attribute("href")
            text = (await l.inner_text()).strip() if await l.is_visible() else ""
            if not href: continue
            if "order" in href.lower() or "judg" in href.lower() or href.lower().endswith(".pdf"):
                # Download via same session
                try:
                    with self.page.expect_download(timeout=15000) as dl_info:
                        await l.click(force=True)
                    download = await dl_info.value
                    save_as = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.pdf")
                    await download.save_as(save_as)
                    orders.append({"id": os.path.splitext(os.path.basename(save_as))[0], "title": text or "Order/Judgment", "date": None, "file_path": save_as, "source_url": href})
                except:
                    # If not a real download, just record the link
                    orders.append({"id": str(uuid.uuid4()), "title": text or "Order/Judgment (link)", "source_url": href, "file_path": None})
        return orders
