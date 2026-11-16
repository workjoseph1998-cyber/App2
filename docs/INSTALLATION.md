# Windows Server 2022 installation and rollback

## Prepare a separate application

1. Keep Cirrus Workplace's existing installation, virtualenv, database and scripts intact. Do not extract this release over it.
2. Install 64-bit Python **3.12** from the official Python distribution, including the `py` launcher. Check `py -3.12 --version`.
3. Extract this release into a dedicated directory such as `C:\Apps\CirrusPulse`. Use a dedicated service/operator identity with write permission to its data directory. Restrict access to the code and data to approved administrators and the runtime identity. The data folder must not be served by IIS as static files.
4. In PowerShell under that identity:

```powershell
cd C:\Apps\CirrusPulse
powershell -File scripts\setup.ps1
.venv\Scripts\python.exe -m flask --app cirrus:create_app init-admin
```

The admin command prompts securely for a username and password (minimum 12 characters). Do not put production passwords in source files or command arguments. Keep PowerShell execution policy consistent with your organization's signed-script policy; do not disable it globally. If policy requires signing, have your administrator sign the supplied scripts.

Setup creates only this application's virtualenv, database, upload, log and backup directories. It is repeatable and does not replace application data. It uses a pinned dependency lock with normal TLS/package verification enabled. First installation requires access to `pypi.org` and `files.pythonhosted.org`, or your trusted internal Python package mirror.

## Runtime configuration

Set these in the operator/service environment **before** setup/start/stop/backup and use the same identity and values for every command:

| Variable | Default | Purpose |
|---|---|---|
| `CIRRUS_DATA_DIR` | `<application>\data` | Absolute path for this application's private SQLite, uploads, logs and backups |
| `CIRRUS_COOKIE_SECURE` | `0` | Set to `1` when employees access the application through HTTPS IIS |
| `CIRRUS_PUBLIC_BASE_URL` | incoming origin | Canonical externally reachable scheme and host, e.g. `https://operations.example.internal`; used for QR labels. Do not include the optional prefix here. |
| `CIRRUS_URL_PREFIX` | empty | Optional IIS path, e.g. `/pulse`; proxy this path intact to Waitress. All app links include it. |

Example (replace the example host with your actual IIS host):

```powershell
$env:CIRRUS_DATA_DIR = 'C:\Apps\CirrusPulseData'
$env:CIRRUS_COOKIE_SECURE = '1'
$env:CIRRUS_PUBLIC_BASE_URL = 'https://operations.example.internal'
```

Environment variables set in a PowerShell window last for that window and child processes. Persist them in your approved service/task configuration for unattended operation. No new app secret is required: `session.key` is generated locally. Protect this file using filesystem ACLs. Deleting/rotating it invalidates all sessions.

## Switch from Workplace to Pulse

1. Use **Workplace's own stop instructions** to stop Workplace manually. This application's scripts never stop another application.
2. Confirm the listener is free with `Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue`. If something still owns it, identify the owner and resolve it manually.
3. Start from the Cirrus Pulse folder:

```powershell
powershell -File scripts\start.ps1
```

The script checks port 8000, launches the dedicated virtualenv's Python/Waitress process, and requests the login page to verify startup. Python independently checks/binds port 8000 too, so a competing startup fails safely. Only `127.0.0.1:8000` is used. Logs: `<data>\logs\stdout.log`, `stderr.log`, and rotating `cirrus.log` for application errors. PID: `<data>\cirrus.pid`.

4. Reuse the existing IIS reverse proxy route to `http://127.0.0.1:8000`. No second VM, port or IIS site is needed while only one application runs. Keep the listener private; employees should use IIS HTTPS.
5. If the existing IIS route uses a subpath, set `CIRRUS_URL_PREFIX` and preserve that prefix in the rewrite target. If IIS strips it, adjust the rewrite to retain it. Do not trust arbitrary forwarded headers; the app doesn't depend on them. Set the canonical public origin for correct HTTPS QR labels.
6. Open the existing IIS URL, sign in, create departments/accounts and a synthetic test notice. Confirm role/department visibility and perform a test equipment handover/return before entering real records. Print one label and scan it from a device that can reach IIS. The QR includes only an authenticated record URL; it contains no name, asset metadata or price. Users without an active session sign in and then return to the selected record; its permissions are checked again.

If running unattended, use your approved Windows Scheduled Task/service wrapper under the dedicated identity, working directory set to this application, to invoke `.venv\Scripts\python.exe run.py`. Keep stop behavior scoped to that exact process. No service is installed automatically.

## Shutdown

```powershell
cd C:\Apps\CirrusPulse
powershell -File scripts\stop.ps1
```

Stop verifies PID, executable and exact application runner command before stopping anything. A stale/mismatched PID will not stop an unrelated application. Do not use broad `taskkill /IM python.exe` commands. Windows process stop is abrupt; SQLite transactions remain atomic, but stop during a maintenance window and allow requests to finish first. Recheck the listener before starting Workplace.

## Backups and additive migration

See [MIGRATIONS.md](MIGRATIONS.md). Stop this app before copying a complete database/upload snapshot:

```powershell
powershell -File scripts\stop.ps1
.venv\Scripts\python.exe scripts\backup.py
```

Copy the timestamped backup to protected storage outside the VM under your retention policy. The backup directory includes private records, uploads and a session key; do not distribute it as a release artifact.

## Roll back to Workplace

1. Stop only Cirrus Pulse with its stop script and verify port 8000 is free.
2. Leave Pulse's independent folder/data in place; take a backup if needed.
3. Use Workplace's original start script and original data/configuration.
4. Confirm Workplace through the existing IIS URL. Restore any IIS rewrite path adjustment you deliberately made for a Pulse subpath.

There is no database migration between these products and nothing to undo in Workplace.

## Roll back a future Pulse upgrade

Stop Pulse, retain the new folder for diagnosis, restore the **matched prior code + database + uploads + configuration** from backup into the dedicated Pulse paths, then start and validate. Do not run old code against an arbitrarily newer schema. Never restore over Workplace data. This is the first combined release; no earlier App2 release existed to tag or preserve.

## Troubleshooting

- **Port occupied:** startup deliberately refuses. Identify the process and stop the selected app with its own script. Never have both apps run on port 8000.
- **502 from IIS:** inspect loopback login response and this app's stderr; check working directory, Python executable, data ACLs and retained prefix. Avoid exposing a new public listener.
- **Login works over HTTP but not HTTPS / loops:** use the correct IIS HTTPS URL, set canonical origin, and check cookie path/secure setting. Secure cookies intentionally do not work over HTTP.
- **Login locked out:** failed attempts are limited per username and source address for 15 minutes. Wait for the window; verify username/account enabled state with an admin. Reset a password in Users / Roles; account changes invalidate its sessions.
- **Setup cannot download packages:** use normal verified HTTPS or a trusted organizational mirror. Do not disable TLS or signature/checksum checks.
- **SQLite locked:** only run one instance; keep the database on local disk, not an SMB share. Writes wait up to 15 seconds. Check that backup/antivirus tooling is not holding files open.
- **Uploads rejected:** PNG/JPEG/PDF only; request limit 8 MB including form overhead. IIS request limits must permit that size. Downloads require record access. Employees attach photos against their own issue ID.
- **Missing notices/assets:** check audience, scheduling, expiry, role, department and assignment. A recipient must confirm their own handover. A department manager sees assets currently assigned to that department, not the central store.
