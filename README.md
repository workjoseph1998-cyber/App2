# Cirrus Experience 2.0

**A new interface for Cirrus Pulse + Cirrus AssetPass.** One internal workspace, one Python application, the same `127.0.0.1:8000` endpoint.

This release replaces the v1 interface with an animated, responsive workspace: orbital and equipment visuals, a floating navigation shell, light/dark themes, keyboard command search, a notification drawer, priority views, interactive equipment charts, sortable inventory tables, equipment cards, quick-view dialogs, selection and batch label printing. All counts and search results come from permitted records. There are no fabricated uptime percentages, activity trends or equipment metrics.

## Install on your Windows server

Download **`dist/Cirrus-Experience-Version-2.0.0.zip`** and extract it into a **new folder**. Do not overwrite your current installation.

1. **Stop the old app** (Ctrl+C in its server window).
2. If retaining your existing accounts/equipment/notices, double-click **`Import-Existing-Data.cmd`** in the new folder. Paste your old application folder or its `data` folder. The original data remains untouched. Run this before setup.
3. Double-click **`Setup-Cirrus.cmd`**. It creates a separate Python 3.12 virtual environment, installs the pinned dependencies and initializes the app. It asks for an administrator only when one does not already exist.
4. Double-click **`Start-Cirrus.cmd`**. It opens the browser after the server responds. Keep the window open; press Ctrl+C to stop. **`Stop-Cirrus.cmd`** is also provided and checks process identity before stopping anything.

These `.cmd` launchers do not invoke unsigned `.ps1` scripts. **Node.js is not needed on Windows:** the compiled React interface, icons and fonts are included, served locally by Flask/Waitress. Python 3.12 x64 is required; there is no default production password.

Open the server's `http://127.0.0.1:8000` or your existing IIS HTTPS address. Only one application may use port 8000. Startup refuses an occupied port; it never terminates its owner.

See [the v2 upgrade guide](docs/UPGRADE_2.0.md) for your existing installation path, data retention, configuration and rollback. [Full installation/IIS instructions](docs/INSTALLATION.md) also cover the existing PowerShell alternatives.

## Explore the interface

- **Pulse:** animated operations hero, priority summaries, critical/pinned/action-needed views, grid/list layouts, searchable/filterable updates, acknowledgements, scheduled publication and archive.
- **AssetPass:** animated equipment scene, a real equipment-distribution chart, sortable/searchable inventory, equipment cards, quick views, warranties, selection and printable QR labels.
- **Your equipment:** personal equipment workspace with receipt confirmation, return requests, issue reporting and your handover history.
- **Workspace:** Ctrl+K / Command+K search across permitted pages and records; keyboard navigation, native modal focus handling, escape-to-close, mobile navigation and reduced-motion support.
- **Notifications:** drawer with unread count, permission-scoped items, mark-all-read action and a sixty-second refresh while signed in. The board itself refreshes on navigation or its explicit Refresh button.
- **Details:** lifecycle progress steps derived from actual timestamps, clean specification panels, readable notices and consistent forms across both modules.

[View the new screenshots](docs/SCREENSHOTS_V2.md).

## Roles and data protection

| Role | Pulse | AssetPass |
|---|---|---|
| Admin | Manage accounts, departments/categories and notices | Full management, costs, reports and clearance |
| Publisher | Publish/target/manage own notices | Own equipment workflows |
| Department publisher | Publish/manage own notices; own department always enforced | Own equipment workflows |
| Asset manager | Read targeted notices, acknowledge | Full asset management, costs, exports and clearance |
| Department manager | Read targeted notices, acknowledge | Department-scoped assets, history and exports; no costs or inventory changes |
| Employee / Viewer | Read targeted notices, acknowledge | Own equipment/history, confirmation, returns and issue reports |

Authorization is enforced by Flask, including new search, notification and batch-label endpoints. The interface is not an authorization boundary. Search and quick views do not include purchase prices. Employees cannot confirm for someone else or assign equipment to themselves. Accounts have one role. Authors and admins can review managed notices. Critical global notices reach all users; explicitly targeted notices retain their audience.

The transactional SQLite workflows from v1 remain: unique asset IDs and serials, one open assignment per asset, actual employee confirmation, staff-verified returns, lifecycle audits, protected attachments, formula-safe Excel exports and equipment clearance without disabling accounts. CSRF protection, scrypt hashing, login throttling, session revocation and response security headers remain enabled.

## Storage and deployment

Independent data defaults to the ignored `data/` folder: `cirrus.sqlite3`, `uploads/`, `session.key`, `logs/` and `backups/`. Never use Workplace data. Production uses Waitress on loopback only; IIS can continue proxying to it. No external font/CDN connections or Node server are required.

Optional environment variables:

- `CIRRUS_DATA_DIR`: private data directory; preserve existing custom values.
- `CIRRUS_COOKIE_SECURE=1`: when users access IIS over HTTPS.
- `CIRRUS_PUBLIC_BASE_URL`: external origin for QR labels and automatic browser opening, e.g. `https://operations.example.internal`.
- `CIRRUS_URL_PREFIX`: optional preserved IIS path, e.g. `/pulse`.

If reusing a custom `CIRRUS_DATA_DIR`, take a backup and use the same value; do not import it into itself. The copy-based upgrade guide is the safer default for the ordinary local `data` deployment.

## Develop

Use the existing checkout. Cloud tasks are already isolated; do not create another worktree unless explicitly requested.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock -r requirements-dev.txt
.venv/bin/python -m flask --app cirrus:create_app init-admin
.venv/bin/python run.py
```

Only frontend development requires Node.js (22.12+; this release was built on Node 24):

```sh
npm ci --prefix frontend
npm run build --prefix frontend
```

The build writes the production files to `cirrus/static/experience/`. Commit them with frontend changes so Windows installations can run without a JavaScript build. Sources and dependency lockfiles are included in the release. Bundled third-party licenses are in `frontend/licenses/`; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Validation, while port 8000 is free:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/browser_check.py
```

The browser check requires Playwright and Chromium and uses a separate synthetic database. It writes the v2 screenshot gallery, exercises the real Waitress server, then stops only the process it started. Runtime processes must be restarted in a restored cloud task. No production Windows deployment is performed automatically.

## Documentation

- [Upgrade and rollback](docs/UPGRADE_2.0.md)
- [Windows/IIS installation](docs/INSTALLATION.md)
- [Database migration and backup](docs/MIGRATIONS.md)
- [V2 test results and limitations](docs/TEST_RESULTS_V2.md)
- [Screenshots](docs/SCREENSHOTS_V2.md)
- [Changelog](CHANGELOG.md)

Windows Server 2022, native `.cmd` execution, NTFS ACLs and real IIS acceptance must still be verified on your server. Tests here run on Linux. There is no SSO, email reminder worker, built-in malware scanner, shared checkout or automatic employee account revocation. Equipment categories remain fixed in v2. All recorded times are UTC; the toolbar clock follows the browser's local time. Continuous animations stop when the operating system requests reduced motion.
