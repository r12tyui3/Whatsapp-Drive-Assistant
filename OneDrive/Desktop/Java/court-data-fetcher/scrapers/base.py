import base64, os
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    @abstractmethod
    async def prepare_search(self, payload: dict) -> str:
        """Navigate to portal, fill form (except captcha), return captcha PNG as base64."""
        ...

    @abstractmethod
    async def submit_and_fetch(self, captcha_text: str) -> dict:
        """Submit captcha, parse results, download PDFs. Return structured result."""
        ...

    async def _screenshot_element_b64(self, locator):
        buf = await locator.screenshot()
        return base64.b64encode(buf).decode("ascii")

    async def teardown(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except:
            pass
