from fastapi.testclient import TestClient
import uuid
import app
from scrapers.hc_services import HCServicesScraper
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


def test_lifecycle_high_court(monkeypatch):
    client = TestClient(app.app)

    async def fake_prepare(self, payload):
        return 'fake-captcha-b64-hc'

    # Patch prepare_search so start-search doesn't try to control a browser
    monkeypatch.setattr(HCServicesScraper, 'prepare_search', fake_prepare)

    payload = {
        'portal': 'HIGH_COURT',
        'high_court': 'KARNATAKA_HIGH_COURT',
        'case_type': 'CIVIL',
        'case_number': '1234',
        'case_year': '2021'
    }

    resp = client.post('/start-search', json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 'sessionId' in data and data['captchaImageBase64'] == 'fake-captcha-b64-hc'

    # Replace stored scraper with a fake that returns a successful result
    class FakeScraper:
        async def submit_and_fetch(self, captcha_text):
            return {
                'portal': 'HIGH_COURT',
                'court': 'KARNATAKA_HIGH_COURT',
                'input': payload,
                'parsed': {'parties': 'P v R', 'filing_date': '01-01-2020', 'next_hearing_date': '01-02-2021', 'case_status': 'Pending'},
                'orders': [{'id': __import__('uuid').uuid4().hex, 'title': 'Order 1', 'date': None, 'file_path': None, 'source_url': 'http://example.com/o1.pdf'}],
                'raw_html': '<html></html>'
            }

        async def teardown(self):
            return None

    session_id = data['sessionId']
    app.SEARCH_SESSIONS[session_id] = FakeScraper()
    monkeypatch.setattr(app, 'get_session', fake_get_session)

    resp2 = client.post('/solve-captcha', data={'sessionId': session_id, 'captchaText': 'any'})
    assert resp2.status_code == 200
    j = resp2.json()
    assert 'queryId' in j
    assert j['parsed']['parties'] == 'P v R'


def test_lifecycle_district_court(monkeypatch):
    client = TestClient(app.app)

    async def fake_prepare(self, payload):
        return 'fake-captcha-b64-dc'

    monkeypatch.setattr(DistrictServicesScraper, 'prepare_search', fake_prepare)

    payload = {
        'portal': 'DISTRICT_COURT',
        'state': 'KAR',
        'district': 'BENGALURU',
        'establishment': 'MUN_01',
        'case_type': 'CR',
        'case_number': '987',
        'case_year': '2020'
    }

    resp = client.post('/start-search', json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 'sessionId' in data and data['captchaImageBase64'] == 'fake-captcha-b64-dc'

    class FakeScraper2:
        async def submit_and_fetch(self, captcha_text):
            return {
                'portal': 'DISTRICT_COURT',
                'court': {'state': 'KAR', 'district': 'BENGALURU'},
                'input': payload,
                'parsed': {'parties': 'A v B', 'filing_date': '05-05-2019', 'next_hearing_date': '20-10-2025', 'case_status': 'Disposed'},
                'orders': [{'id': __import__('uuid').uuid4().hex, 'title': 'Order 1', 'date': None, 'file_path': None, 'source_url': 'http://example.com/doc.pdf'}],
                'raw_html': '<html></html>'
            }

        async def teardown(self):
            return None

    session_id = data['sessionId']
    app.SEARCH_SESSIONS[session_id] = FakeScraper2()
    monkeypatch.setattr(app, 'get_session', fake_get_session)

    resp2 = client.post('/solve-captcha', data={'sessionId': session_id, 'captchaText': 'right'})
    assert resp2.status_code == 200
    j = resp2.json()
    assert 'queryId' in j
    assert j['parsed']['parties'] == 'A v B'
