import asyncio
from fastapi.testclient import TestClient
import uuid

import app
from scrapers.district_services import DistrictServicesScraper


class DummyDB:
    def add(self, obj):
        pass

    def flush(self):
        pass

    def commit(self):
        pass

    def close(self):
        pass


def fake_get_session():
    db = DummyDB()
    try:
        yield db
    finally:
        db.close()


def make_async_callable(fn):
    async def _c(*a, **k):
        return fn(*a, **k)

    return _c


def test_solve_captcha_invalid(monkeypatch):
    client = TestClient(app.app)

    # fake scraper that raises InvalidCaptcha
    class FakeScraper:
        async def submit_and_fetch(self, captcha_text):
            raise DistrictServicesScraper.InvalidCaptcha("new-image-base64")

        async def teardown(self):
            return None

    session_id = str(uuid.uuid4())
    app.SEARCH_SESSIONS[session_id] = FakeScraper()

    # patch dependency
    monkeypatch.setattr(app, 'get_session', fake_get_session)

    resp = client.post('/solve-captcha', data={'sessionId': session_id, 'captchaText': 'wrong'})
    assert resp.status_code == 400
    j = resp.json()
    assert j.get('captchaError') is True
    assert j.get('captchaImageBase64') == 'new-image-base64'


def test_solve_captcha_success(monkeypatch):
    client = TestClient(app.app)

    # fake scraper that returns a successful result
    import uuid as _uuid

    class FakeScraper2:
        async def submit_and_fetch(self, captcha_text):
            return {
                'portal': 'DISTRICT_COURT',
                'court': {'state': 'KAR', 'district': 'BENGALURU'},
                'input': {'case_type': 'CR', 'case_number': '987', 'case_year': '2020'},
                'parsed': {'parties': 'A v B', 'filing_date': '05-05-2019', 'next_hearing_date': '20-10-2025', 'case_status': 'Disposed'},
                'orders': [{'id': _uuid.uuid4().hex, 'title': 'Order 1', 'date': None, 'file_path': None, 'source_url': 'http://example.com/doc.pdf'}],
                'raw_html': '<html></html>'
            }

        async def teardown(self):
            return None

    session_id = str(uuid.uuid4())
    app.SEARCH_SESSIONS[session_id] = FakeScraper2()
    monkeypatch.setattr(app, 'get_session', fake_get_session)

    resp = client.post('/solve-captcha', data={'sessionId': session_id, 'captchaText': 'right'})
    assert resp.status_code == 200
    j = resp.json()
    assert 'queryId' in j
    assert j['parsed']['parties'] == 'A v B'
    assert len(j['orders']) == 1
