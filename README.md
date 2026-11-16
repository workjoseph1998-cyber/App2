# Cirrus Pulse + Cirrus AssetPass · 1.0.0

One independent internal Flask application containing two integrated modules:

- **Pulse:** live operations board, priorities, department/role targeting, schedules and expiry, pinned announcements, acknowledgement tracking, drafts/archive, search and filters.
- **AssetPass:** inventory, employee equipment, pending handovers and receipt confirmation, verified returns, damage/loss reports with protected attachments, lifecycle audit history, warranty tracking, QR labels, Excel exports and equipment clearance.

Both modules share internal accounts, departments, server-side permissions, notifications and one SQLite database. This application never reads Cirrus Workplace code or data.

## Run on Windows Server 2022

See [installation, IIS, startup, shutdown and rollback](docs/INSTALLATION.md). The only production listener is **127.0.0.1:8000**. An occupied port refuses startup without stopping its owner. No deployment is performed by this repository.

```powershell
cd C:\Apps\CirrusPulse
powershell -File scripts\setup.ps1
.venv\Scripts\python.exe -m flask --app cirrus:create_app init-admin
powershell -File scripts\start.ps1
# Later:
powershell -File scripts\stop.ps1
```

Use Python 3.12 (64-bit). Create your administrator interactively; there is no default production password and no public registration.

## Develop locally

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m flask --app cirrus:create_app init-admin
.venv/bin/python run.py
.venv/bin/python -m pytest -q
```

Use the existing checkout. Each cloud task is isolated; do not create another worktree unless explicitly requested. Data defaults to the ignored `data/` directory. Live processes need restarting in a new environment. The production runner uses Waitress, never Flask debug mode.

## Roles

| Role | Pulse | AssetPass |
|---|---|---|
| Admin | Manage accounts/departments/categories; publish and manage all notices | Full inventory, cost, assignment, return, report/export and clearance access |
| Publisher | Publish, target and manage own notices; review own acknowledgements | Own equipment only |
| Department publisher | Publish and manage own notices; targeting always limited to own department | Own equipment only |
| Asset manager | Read targeted notices and acknowledge | Full asset management, costs, reports, exports and clearance |
| Department manager | Read targeted notices and acknowledge | View assets currently assigned to own department; department-scoped history and exports; no costs or inventory mutations |
| Employee / Viewer | Read targeted notices and acknowledge | Own current equipment and own handover/return history; confirm own receipt, request own return, report own issues |

Accounts have one role. Department managers with no department have no departmental access. Authenticated users can always use their own equipment workflows regardless of role. Authors and administrators may review authored/managed notices even when not in the notice audience. Critical **global** notices are visible to all enabled accounts; deliberately targeted critical notices retain their audience restrictions.

## Data integrity and security

- SQLite foreign keys, WAL mode, explicit write transactions, unique asset IDs/serial numbers and one open assignment per asset. Shared checkout is intentionally unsupported in v1.
- A handover is pending until the actual recipient confirms; staff cannot confirm for them. Returns require staff physical verification and recorded condition. Clearance does not disable accounts.
- Server-side audience/ownership checks, CSRF tokens on all POSTs, scrypt password hashing, 8-hour sessions, login throttling, account-change session invalidation, response security headers, safe spreadsheet cells, and protected PNG/JPEG/PDF downloads.
- Optional attachment files have opaque storage names outside static files. Downloads are forced as attachments. No executable/HTML uploads. Report photos remain accessible only to the reporter and asset staff. Use your existing endpoint antivirus scanning policy; there is no built-in malware scanner.
- Scheduled notices and their notifications become available on authenticated visits after their start time. Expiry is evaluated on reads; original publication status is retained for history.
- Prices, supplier information and internal inventory notes are rendered only for admin/asset manager. Employees see handover notes relevant to them.
- All dates/times are UTC. Database and backups contain private company information; restrict Windows ACLs and backup access.

## Documentation and release files

- [Installation and rollback](docs/INSTALLATION.md)
- [Schema migration and backup](docs/MIGRATIONS.md)
- [Test results and limitations](docs/TEST_RESULTS.md)
- [Changelog](CHANGELOG.md)
- [Sample screenshots](docs/SCREENSHOTS.md) — synthetic records only
- ZIP: `dist/Cirrus-Pulse-Version-1.0.zip` (generated with `python scripts/package.py`; excludes databases, secrets, virtualenvs and caches)

## Optional synthetic demo

```powershell
.venv\Scripts\python.exe scripts\demo.py --data-dir data\demo
$env:CIRRUS_DATA_DIR = (Join-Path $PWD 'data\demo')
# Start only while port 8000 is free.
powershell -File scripts\start.ps1
```

The demo script prompts for a password and refuses a nonempty database. Accounts are `demo.admin`, `demo.employee`, `demo.operations`. Never point a production deployment at the demo directory. Remove the environment override before using real data.

## Known boundaries

Windows Server/IIS/PowerShell must be verified on the target VM; Linux browser and Python tests are not a production deployment test. There is no SSO, email delivery, background reminder service, built-in antivirus, multi-currency accounting, shared equipment checkout, or account revocation on clearance. Asset categories are fixed in v1; Pulse categories and departments can be added in the admin UI. The image mentioned in the specification was not supplied, so the UI follows its written palette. No Workplace changes or automatic deployment are included.
