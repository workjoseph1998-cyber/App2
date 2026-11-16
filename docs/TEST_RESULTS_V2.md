# Cirrus Experience 2.0 — validation

Executed on 2026-11-16 in the isolated App2 cloud checkout, with synthetic data only. Python 3.12.14; Linux; Chromium 156; React 19.2; production Vite 7.3.8 build. No production Windows server, IIS site, Workplace application or company database was accessed.

## Automated regression: 37 passed

`python -m pytest -q`: **37 passed**, 0 failed, 0 skipped. Recorded source-tree run: 28.85 seconds.

The original 27 regression/permission tests still pass, including administrator creation outside a request, login, session revocation, CSRF, targeted visibility, acknowledgements, expiry/archive/filtering, concurrent assignment prevention, restricted costs/exports, protected uploads, actual receipt confirmation and staff-verified returns.

New coverage verifies:

- Search results respect department/role audiences, future publication restrictions and current equipment ownership. Cost/password fields are excluded.
- Notification drawer items/read counts are user-scoped. Mark-read requires a valid CSRF token.
- Batch QR label printing is restricted to asset staff, rejects invalid selections and limits requests to 50 assets.
- Compiled React/CSS files are served from the app; a Node runtime is not required for these requests.
- The copy-based upgrade preserves original SQLite bytes, users, equipment, uploads and session key, verifies the copy and remains readable after normal initialization.
- Upgrade refuses a nonempty destination, overlapping source/destination, an unrelated database and a still-running port 8000 listener.
- Process-stop identity checks reject the current unrelated test process. A real Waitress runner is started and stopped using the verified PID helper, without terminating the test process.
- The Windows setup's **Python helper** creates the first administrator through the real Flask CLI, then detects and preserves that account on a second run. This specifically guards the earlier bootstrap bug.

## Real browser acceptance: passed

`python scripts/browser_check.py` exercises the actual Waitress server on port 8000 using a separate synthetic database. It checks:

- Login, publishing an update and registration/assignment of an asset.
- Employee receipt confirmation and a return request, followed by staff physical verification.
- Download of a real Excel workbook.
- Accurate count rendering, critical/pinned feed filters and list/grid switching.
- Light/dark appearance switching and the new dark screen.
- Ctrl+K command search, keyboard focus movement and Enter navigation to a permitted asset.
- Notification drawer contents and the real mark-all-read action.
- Equipment card/table switching, local search, quick-view dialog, selection and authenticated batch-label page.
- Mobile page width, opening/closing navigation, inert hidden navigation and Escape handling.
- Reduced-motion preference disables continuous orbital animations.

No JavaScript page errors or console errors were observed in the passing run. Fourteen screenshots were captured from the actual application. The script stops only the server process it started. See [SCREENSHOTS_V2.md](SCREENSHOTS_V2.md).

## Build, dependency and package checks

- Production frontend build passed; React, Motion, icons and fonts are included locally. Approximate JS size: 356 kB (114 kB gzip); the two font files total approximately 40 kB. There are no runtime CDN or font-service dependencies.
- `npm audit` for the full locked frontend dependency set reported **0 known vulnerabilities** after updating Vite to 7.3.8. This is an advisory-database result, not a penetration test.
- Python dependency checks, Ruff and compilation passed. The added psutil 7.2.2 Windows x64/Python 3.12-compatible wheel was downloaded successfully through normal verified pip access; it was not executed on Windows.
- The release ZIP is checked for CRC integrity, expected scripts, compiled assets, source/lockfiles, license notices and documentation. Private data, session keys, virtualenvs, node_modules and caches are excluded.
- The regression suite and real browser acceptance are also run from an extracted release copy to verify that the prebuilt application functions without a JavaScript build.

## Target-platform acceptance remains

Native `.cmd`/PowerShell execution, Windows Server 2022 process semantics, NTFS ACLs, actual IIS HTTPS/path forwarding and physical QR scanning require checks on the user's server. The Python setup/import/stop helpers and Waitress runtime have been exercised on Linux; this is not a claim of Windows deployment testing. No Windows or IIS deployment was performed.

This release preserves the original product boundaries: in-app notifications only, no SSO/email worker, no shared equipment checkout, no built-in antivirus, and equipment clearance without automatic account revocation. Keyboard/modal/reduced-motion behaviors were checked; a full external accessibility or security audit was not performed.
