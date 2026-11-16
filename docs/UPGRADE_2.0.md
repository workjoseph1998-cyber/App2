# Upgrade your existing installation to Cirrus Experience 2.0

This release changes the interface and adds independent `.cmd` launchers. It retains the Flask/SQLite account, notice, equipment, attachment and audit structures. No destructive database migration is required. The original v1.0.0 and v1.0.1 Git tags and ZIPs are preserved.

## Recommended upgrade: new folder, copied data

1. Download `Cirrus-Experience-Version-2.0.0.zip` and extract it into a new location, for example `C:\Apps\Cirrus-Experience-2.0.0`. Open the extracted folder that directly contains `Start-Cirrus.cmd` and `run.py`. Do not extract over your old app and do not copy its `.venv`.
2. Stop the old Pulse server with **Ctrl+C** in its running window. If Workplace is running instead, use its own stop procedure. Confirm port 8000 has no listener before switching.
3. In the **new** folder, double-click **`Import-Existing-Data.cmd`**. This runs before setup and uses the Python 3.12 installation you already installed. At the prompt, paste your old application folder:

```text
C:\Users\Administrator\Desktop\App2\App2-feature-cirrus-pulse-assetpass\App2-feature-cirrus-pulse-assetpass
```

The importer finds its `data` directory automatically. You may instead paste the full old data-directory path. It checks the database identity and integrity, copies it through SQLite's backup API, copies uploads and the session key, and verifies the copy. It refuses a nonempty destination or an active listener on port 8000. The old database, uploads, logs and backups remain in the original installation. The new release starts with fresh logs and a new backup directory.

4. Double-click **`Setup-Cirrus.cmd`**. It creates a new Python 3.12 virtualenv, installs `requirements.lock` and initializes the additive schema. Existing users and passwords are preserved. If an enabled administrator exists, setup does not ask you to create another one. If no administrator exists, it prompts securely to create one.
5. Double-click **`Start-Cirrus.cmd`**. Wait for the browser to open, then use your existing login. The app listens only at **127.0.0.1:8000**. Keep its console window open; Ctrl+C stops it. `Stop-Cirrus.cmd` is also available; it reads this installation's PID and verifies the interpreter, runner path and working directory before terminating it.
6. Verify an existing notice, the equipment inventory and an attachment before entering new data. Check the command palette (Ctrl+K), theme toggle and equipment card switch. Test one real IIS login and scan a QR label if IIS is in use.

No Node.js installation, npm build, second port or second IIS site is required. The release includes the compiled UI and locally served fonts. The new `.cmd` files do not call unsigned PowerShell scripts; they use the installed Python directly.

## First installation with no previous data

Skip import. Double-click `Setup-Cirrus.cmd`, create your administrator at the prompt, and then `Start-Cirrus.cmd`. No demo data or default account is installed automatically.

## Custom data paths and IIS settings

If you previously configured `CIRRUS_DATA_DIR`, first identify that exact directory and take a stopped-app backup. Do not import a directory into itself. You can either set `CIRRUS_DATA_DIR` to a distinct new data location for the copy, or deliberately reuse the backed-up original directory without running import. Reusing the original means new writes also affect the old installation's data, so copying to a separate destination is preferable for rollback isolation.

Keep your existing `CIRRUS_COOKIE_SECURE`, `CIRRUS_PUBLIC_BASE_URL` and `CIRRUS_URL_PREFIX` settings. Values set only inside an old PowerShell window are not automatically inherited by a double-click from Explorer; persist them in your approved Windows service/task environment, or launch the new command file from the configured terminal. The same IIS proxy to port 8000 remains usable. The public base value is the origin only; the optional prefix is configured separately.

## Roll back

1. Stop **only the new Cirrus app**, with Ctrl+C or its own `Stop-Cirrus.cmd`.
2. Verify port 8000 is free.
3. Return to the **old application folder** and start its original `run.py` with its original `.venv` and original data configuration.
4. Verify your existing IIS address or the server's local browser.

Because the recommended upgrade copies data and leaves the old installation intact, the old release remains available. New records entered into v2 after the copy will not appear in the untouched old data. Preserve the new folder and take a backup before choosing whether/how to reconcile later records; never overwrite either database blindly.

## Troubleshooting

- **Import says destination is not empty:** do not delete existing data. Use a fresh extracted release folder and import before setup. Existing destination files are intentionally protected.
- **Port occupied:** stop the selected app using its own procedure. The launcher does not terminate the listener.
- **No Python 3.12:** run `py -0p`; install Python 3.12 x64 alongside other versions if missing. Do not replace Python used by another app.
- **Python environment belongs to another installation:** do not copy `.venv`. Setup creates a dedicated environment in the new folder.
- **Login credentials rejected:** use the original account, including username casing. Confirm you imported the correct Pulse data directory. Do not create replacement production users blindly.
- **Browser opens but secure-cookie login does not stick:** use the configured IIS HTTPS URL when `CIRRUS_COOKIE_SECURE=1`.
- **Missing animations:** the interface intentionally reduces animation when the operating system/browser requests reduced motion.
- **Old-looking page after upgrade:** confirm the process was started from the new folder, then refresh the browser. The new sidebar shows `2.0`, and the sign-in screen has the new split-screen artwork.

Native Windows and IIS execution must be accepted on the target server. The recorded tests validate the Python importer, real runner/stop identity logic, React build and browser workflows on Linux.
