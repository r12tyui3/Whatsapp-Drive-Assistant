import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scrapers.hc_services import HCServicesScraper
from scrapers.district_services import DistrictServicesScraper


def load_fixture(name: str) -> str:
    p = ROOT / 'tests' / 'fixtures' / name
    return p.read_text(encoding='utf-8')


def test_hc_parse():
    html = load_fixture('hc_sample.html')
    s = HCServicesScraper()
    parsed = s._parse_case_details(html)
    assert parsed['parties'] == 'John v. Doe'
    assert parsed['filing_date'] == '01-01-2020'
    assert parsed['next_hearing_date'] == '15-08-2025'
    assert parsed['case_status'] == 'Pending'


def test_district_parse():
    html = load_fixture('district_sample.html')
    s = DistrictServicesScraper()
    parsed = s._parse_case_details(html)
    assert parsed['parties'] == 'A v B'
    assert parsed['filing_date'] == '05-05-2019'
    assert parsed['next_hearing_date'] == '20-10-2025'
    assert parsed['case_status'] == 'Disposed'
