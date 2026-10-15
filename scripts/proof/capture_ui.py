"""Browser screenshots used as grading evidence (run in CI or locally).

python capture_ui.py app        OUT_DIR BASE_URL PREFIX   # StockPilot UI
python capture_ui.py prometheus OUT_DIR BASE_URL          # Prometheus targets + graph
python capture_ui.py grafana    OUT_DIR BASE_URL USER PASS
"""
import os
import sys
import time
import urllib.parse

from playwright.sync_api import sync_playwright


def launch(p):
    exe = os.environ.get("CHROMIUM_PATH")
    return p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()


def app(out, base, prefix):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(base)
        pg.wait_for_selector("tbody tr", timeout=60000)
        pg.wait_for_timeout(800)
        pg.screenshot(path=f"{out}/{prefix}-app.png")
        # create a product through the UI to prove the write path end-to-end
        sku = f"DEMO-{int(time.time()) % 100000}"
        pg.click("text=＋ Add product")
        pg.fill("input[name=sku]", sku)
        pg.fill("input[name=name]", "Thermal Label Printer")
        pg.fill("input[name=category]", "Electronics")
        pg.fill("input[name=supplier]", "ScanCo")
        pg.fill("input[name=quantity]", "12")
        pg.fill("input[name=unit_price]", "8999")
        pg.click("text=Create product")
        pg.wait_for_selector(f"text={sku}", timeout=30000)
        pg.wait_for_timeout(500)
        pg.screenshot(path=f"{out}/{prefix}-app-after-create.png")
        b.close()


def prometheus(out, base):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(f"{base}/targets?search=stockpilot")
        pg.wait_for_timeout(4000)
        # expand any collapsed pools so the UP state is visible
        for btn in pg.locator("button:has-text('show more'), button:has-text('Show more')").all():
            try:
                btn.click()
            except Exception:
                pass
        pg.screenshot(path=f"{out}/prometheus-targets.png", full_page=True)
        q = urllib.parse.quote('sum by (handler) (rate(http_requests_total{job=~".*stockpilot.*"}[1m]))')
        pg.goto(f"{base}/query?g0.expr={q}&g0.tab=graph&g0.range_input=15m")
        pg.wait_for_timeout(5000)
        pg.screenshot(path=f"{out}/prometheus-query.png", full_page=True)
        b.close()


def grafana(out, base, user, password):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1600, "height": 1000})
        pg.goto(f"{base}/login")
        pg.fill("input[name=user]", user)
        pg.fill("input[name=password]", password)
        pg.click("button[type=submit]")
        pg.wait_for_url(lambda url: "/login" not in url, timeout=30000)
        pg.goto(f"{base}/d/stockpilot-api/stockpilot-api?orgId=1&from=now-20m&to=now&refresh=10s")
        pg.wait_for_timeout(12000)
        pg.screenshot(path=f"{out}/grafana-dashboard.png", full_page=True)
        b.close()


if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    {"app": app, "prometheus": prometheus, "grafana": grafana}[mode](out, *sys.argv[3:])
