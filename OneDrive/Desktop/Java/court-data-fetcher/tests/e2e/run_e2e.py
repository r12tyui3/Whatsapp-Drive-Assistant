#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        resp = page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        status = resp.status if resp else None
        print('GET / status=', status)
        success = (status == 200)
        if not success:
            print(f'Unexpected status {status}')
        else:
            print('E2E smoke check passed')
        # write a simple report for CI artifact upload
        import json, pathlib
        out = {"status": status, "success": success}
        p = pathlib.Path('tests/e2e/report.json')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out))
        browser.close()

if __name__ == '__main__':
    main()
