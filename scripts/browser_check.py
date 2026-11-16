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
out = root / "docs" / "screenshots" / "v2"
out.mkdir(parents=True, exist_ok=True)
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
        page.on(
            "console",
            lambda message: errors.append(message.text) if message.type == "error" else None,
        )

        def capture(name):
            page.evaluate("document.fonts.ready")
            if "/login" not in page.url:
                page.wait_for_selector(".toolbar")
            page.wait_for_timeout(850)
            page.screenshot(path=str(out / name), full_page=True)

        def login(name):
            page.goto("http://127.0.0.1:8000/login")
            page.get_by_label("Username", exact=True).fill(name)
            page.get_by_label("Password", exact=True).fill(password)
            page.get_by_role("button", name="Sign in").click()
            page.wait_for_url("http://127.0.0.1:8000/")

        page.goto("http://127.0.0.1:8000/login")
        capture("login.png")
        login("demo.admin")
        assert page.get_by_role("heading", name="Live Board").is_visible()
        capture("pulse-board.png")
        # Rich workspace controls, keyboard navigation and real notification actions.
        assert page.locator('[data-count="6"]').inner_text() == "6"
        page.get_by_role("tab", name="Critical", exact=False).click()
        assert page.locator("#notice-feed article:visible").count() == 1
        page.get_by_role("tab", name="Pinned", exact=False).click()
        assert page.locator("#notice-feed article:visible").count() == 2
        page.get_by_role("tab", name="All updates", exact=False).click()
        page.get_by_role("button", name="list board view", exact=True).click()
        assert page.locator("#notice-feed").get_attribute("data-view") == "list"
        page.get_by_role("button", name="grid board view", exact=True).click()
        page.get_by_role("button", name="Switch to dark theme").click()
        capture("pulse-dark.png")
        assert page.locator("html").get_attribute("data-theme") == "dark"
        page.get_by_role("button", name="Switch to light theme").click()
        page.keyboard.press("Control+k")
        page.get_by_role("textbox", name="Search pages and records").fill("CIR-0003")
        page.locator(".command-result").filter(has_text="CIR-0003").wait_for()
        capture("command-palette.png")
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        page.wait_for_url("**/assetpass/assets/3")
        page.goto("http://127.0.0.1:8000/")
        page.locator(".toolbar button").filter(has=page.locator("svg.lucide-bell")).click()
        page.get_by_role("dialog", name="Your notifications").wait_for()
        page.locator(".drawer-item").first.wait_for()
        capture("notification-drawer.png")
        page.get_by_role("button", name="Mark all as read").click()
        page.get_by_text("0 unread updates", exact=True).wait_for()
        page.get_by_role("button", name="Close notifications").click()
        page.get_by_role("link", name="+ Publish update").click()
        page.get_by_label("Title", exact=True).fill("Browser acceptance update")
        page.get_by_label("Message", exact=True).fill("Synthetic browser validation.")
        page.get_by_label("Require acknowledgement").check()
        page.get_by_role("button", name="Save update").click()
        assert page.get_by_role("heading", name="Browser acceptance update").is_visible()
        page.goto("http://127.0.0.1:8000/assetpass")
        capture("assetpass-overview.png")
        page.goto("http://127.0.0.1:8000/assetpass/inventory")
        capture("assetpass-inventory.png")
        page.get_by_role("button", name="Cards equipment view").click()
        capture("equipment-cards.png")
        page.get_by_role("textbox", name="Find in inventory results").fill("Latitude")
        assert page.locator(".equipment-card").count() == 1
        page.get_by_role("textbox", name="Find in inventory results").fill("")
        page.get_by_role("button", name="Quick view CIR-0003", exact=True).click()
        page.get_by_role("dialog", name="Equipment quick view: CIR-0003").wait_for()
        capture("equipment-quick-view.png")
        page.get_by_role("button", name="Close equipment quick view").click()
        page.get_by_role("checkbox", name="Select CIR-0003", exact=True).check()
        page.get_by_role("link", name="Print labels", exact=False).click()
        assert page.get_by_role("heading", name="Equipment labels").is_visible()
        capture("print-studio.png")
        page.goto("http://127.0.0.1:8000/assetpass/inventory")
        page.get_by_role("link", name="+ Register equipment").click()
        page.get_by_label("Unique asset ID").fill("CIR-BROWSER")
        page.get_by_label("Condition", exact=True).fill("New")
        page.get_by_label("Model", exact=True).fill("Browser Test Laptop")
        page.get_by_role("button", name="Register asset").click()
        page.locator("select[name=user_id]").select_option("2")
        page.get_by_label("Condition at handover").fill("New")
        page.get_by_role("button", name="Submit handover").click()
        assert page.get_by_text("Awaiting employee confirmation", exact=True).is_visible()
        capture("assetpass-handover.png")
        page.get_by_role("button", name="Sign out").click()
        login("demo.employee")
        page.get_by_role("link", name="My Equipment", exact=True).click()
        capture("my-equipment.png")
        page.get_by_role("link", name="CIR-BROWSER", exact=True).click()
        page.get_by_role("button", name="I confirm receipt").click()
        page.get_by_role("link", name="My Equipment", exact=True).click()
        page.get_by_role("link", name="CIR-BROWSER", exact=True).click()
        assert page.locator(".badge").filter(has_text="Receipt confirmed").is_visible()
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
        capture("assetpass-reports.png")
        with page.expect_download() as dl:
            page.get_by_role("link", name="Full equipment inventory", exact=False).click()
        assert dl.value.suggested_filename.endswith(".xlsx")
        page.goto("http://127.0.0.1:8000/")
        page.set_viewport_size({"width": 390, "height": 844})
        capture("mobile-board.png")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert page.locator(".sidebar").evaluate("(el) => el.inert")
        page.get_by_role("button", name="Open navigation").click()
        assert page.locator("body").evaluate('(el) => el.classList.contains("nav-open")')
        assert not page.locator(".sidebar").evaluate("(el) => el.inert")
        page.keyboard.press("Escape")
        assert page.locator(".sidebar").evaluate("(el) => el.inert")
        # Reduced-motion mode must eliminate the continuous decorative animations.
        reduced = browser.new_page(
            reduced_motion="reduce", viewport={"width": 1440, "height": 1000}
        )
        reduced.goto("http://127.0.0.1:8000/login")
        assert (
            reduced.locator(".orbit-ring").first.evaluate(
                "(el) => getComputedStyle(el).animationName"
            )
            == "none"
        )
        reduced.close()
        browser.close()
    assert not errors, errors
    print(
        "Browser acceptance PASSED: login, publish, register, assign, employee confirmation, return verification, Excel download, mobile layout. Fourteen screenshots captured, including dark theme, search, notifications, cards, quick view and print studio. Keyboard, reduced-motion and responsive checks passed."
    )
finally:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
