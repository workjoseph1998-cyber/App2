# Fix administrator creation: 1.0.0 → 1.0.1

Python and package installation succeeded. The `AttributeError: app_db` traceback is an application defect: the administrator CLI used a database-path variable initialized only by web requests. Version 1.0.1 reads the configured database path directly from Flask's application context.

If upgrading an existing v1.0.0 installation:

1. Stop only this app if it is running (Ctrl+C for a foreground `run.py`).
2. Download `Cirrus-Pulse-Admin-Fix-1.0.1.zip` and extract its `cirrus` folder into your existing application folder. Replace only `cirrus\__init__.py`. Keep `.venv` and `data` unchanged. The patch contains no database, configuration, passwords or dependencies.
3. From the same application folder, rerun:

```powershell
.\.venv\Scripts\python.exe -m flask --app cirrus:create_app init-admin
```

Enter your chosen administrator username/password. The earlier `app_db` failure occurred before insertion; it did not create the administrator. If an account already exists, this release reports it without replacing its password.

4. Stop Workplace using its own procedure before starting Pulse:

```powershell
.\.venv\Scripts\python.exe run.py
```

Open the server's `http://127.0.0.1:8000` or existing IIS address. Keep the PowerShell window open for the foreground server. Use Ctrl+C to stop it.

No database migration or package reinstall is needed for this fix. A full updated application ZIP is also available as `Cirrus-Pulse-Version-1.0.1.zip`. The original v1.0.0 tag and archive are retained.
