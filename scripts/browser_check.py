"""Local browser acceptance test and synthetic screenshots. Requires Playwright + Chromium."""

import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

from scripts.demo import seed_demo

root = Path(__file__).resolve().parents[1]
(root / "data").mkdir(exist_ok=True)
data = Path(tempfile.mkdtemp(prefix="browser-", dir=root / "data"))
password = secrets.token_urlsafe(24)
seed_demo(data, password)
out = root / "docs" / "screenshots"
out.mkdir(exist_ok=True)
errors = []
proc = subprocess.Popen(
    [sys.executable, str(root / "run.py")],
    cwd=root,
    env={**os.environ, "CIRRUS_DATA_DIR": str(data)},
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
try:
    for _ in range(40):
        if proc.poll() is not None:
            raise RuntimeError(proc.communicate()[1].decode())
        try:
            if urlopen("http://127.0.0.1:8000/login", timeout=2).status == 200:
                break
        except OSError:
            time.sleep(0.25)
    else:
        raise RuntimeError("Server did not become ready")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=shutil.which("chromium"), headless=True, args=["--no-sandbox"]
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
        page.on("pageerror", lambda e: errors.append(str(e)))

        def login(name):
            page.goto("http://127.0.0.1:8000/login")
            page.get_by_label("Username", exact=True).fill(name)
            page.get_by_label("Password", exact=True).fill(password)
            page.get_by_role("button", name="Sign in").click()
            page.wait_for_url("http://127.0.0.1:8000/")

        page.goto("http://127.0.0.1:8000/login")
        page.screenshot(path=str(out / "login.png"), full_page=True)
        login("demo.admin")
        assert page.get_by_role("heading", name="Live Board").is_visible()
        page.screenshot(path=str(out / "pulse-board.png"), full_page=True)
        page.get_by_role("link", name="+ Publish update").click()
        page.get_by_label("Title", exact=True).fill("Browser acceptance update")
        page.get_by_label("Message", exact=True).fill("Synthetic browser validation.")
        page.get_by_label("Require acknowledgement").check()
        page.get_by_role("button", name="Save update").click()
        assert page.get_by_role("heading", name="Browser acceptance update").is_visible()
        page.goto("http://127.0.0.1:8000/assetpass")
        page.screenshot(path=str(out / "assetpass-overview.png"), full_page=True)
        page.goto("http://127.0.0.1:8000/assetpass/inventory")
        page.screenshot(path=str(out / "assetpass-inventory.png"), full_page=True)
        page.get_by_role("link", name="+ Register equipment").click()
        page.get_by_label("Unique asset ID").fill("CIR-BROWSER")
        page.get_by_label("Condition", exact=True).fill("New")
        page.get_by_label("Model", exact=True).fill("Browser Test Laptop")
        page.get_by_role("button", name="Register asset").click()
        page.locator("select[name=user_id]").select_option("2")
        page.get_by_label("Condition at handover").fill("New")
        page.get_by_role("button", name="Submit handover").click()
        assert page.get_by_text("Awaiting employee confirmation", exact=True).is_visible()
        page.screenshot(path=str(out / "assetpass-handover.png"), full_page=True)
        page.get_by_role("button", name="Sign out").click()
        login("demo.employee")
        page.get_by_role("link", name="My Equipment", exact=True).click()
        page.screenshot(path=str(out / "my-equipment.png"), full_page=True)
        page.get_by_role("link", name="CIR-BROWSER", exact=True).click()
        page.get_by_role("button", name="I confirm receipt").click()
        page.get_by_role("link", name="My Equipment", exact=True).click()
        page.get_by_role("link", name="CIR-BROWSER", exact=True).click()
        assert page.get_by_text("Receipt confirmed", exact=False).is_visible()
        page.get_by_role("button", name="Request return", exact=True).click()
        page.get_by_role("button", name="Sign out").click()
        login("demo.admin")
        page.goto("http://127.0.0.1:8000/assetpass/assets/9")
        page.get_by_text("Verify physical return", exact=True).click()
        page.get_by_label("Return condition", exact=True).fill("Good")
        page.get_by_label("I physically verified the equipment").check()
        page.get_by_role("button", name="Close assignment & record return").click()
        assert page.get_by_role("heading", name="Assign & hand over", exact=True).is_visible()
        page.goto("http://127.0.0.1:8000/assetpass/reports")
        page.screenshot(path=str(out / "assetpass-reports.png"), full_page=True)
        with page.expect_download() as dl:
            page.get_by_role("link", name="Full equipment inventory", exact=False).click()
        assert dl.value.suggested_filename.endswith(".xlsx")
        page.goto("http://127.0.0.1:8000/")
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=str(out / "mobile-board.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser.close()
    assert not errors, errors
    print(
        "Browser acceptance PASSED: login, publish, register, assign, employee confirmation, return verification, Excel download, mobile layout. Eight screenshots captured."
    )
finally:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
