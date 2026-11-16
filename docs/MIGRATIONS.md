# Schema, migration and recovery

This first combined release starts an independent `cirrus.sqlite3`. There is no previous Pulse database in the selected repository and no migration/import from Cirrus Workplace.

`create_app()` initializes the schema with `CREATE TABLE/INDEX IF NOT EXISTS`, inserts schema version records, and applies the additive v2 `users.auth_version` column only when absent. Version 1 contains the shared operations and equipment tables; version 2 introduces session invalidation and login-attempt tracking. Existing notice/user/asset records are preserved. No destructive downgrade, table drop or automatic account removal is performed.

Before upgrades:

1. Stop only this app, preserving its configured `CIRRUS_DATA_DIR`.
2. Run `python scripts/backup.py` from its dedicated virtualenv. It uses the SQLite backup API and copies uploads and session key into a timestamped private backup.
3. Keep an off-machine copy, prior application code and runtime environment settings together.
4. Install the release into a separate folder/virtualenv and use the same Pulse data directory. Run setup once to apply additive initialization; never point it at Workplace.
5. Run an integrity check and validate login, a Pulse notice and a sample assignment before opening general access.

SQLite integrity check:

```powershell
.venv\Scripts\python.exe -c "from cirrus import create_app; import sqlite3; a=create_app(); c=sqlite3.connect(a.config['DATABASE']); print(c.execute('PRAGMA integrity_check').fetchone()[0]); c.close()"
```

Expected output: `ok`. Migration repeatability and preservation of user records are covered by the tests. Future migrations must increment the version and make explicit, additive changes. Do not remove uniqueness constraints to bypass duplicate data; inspect and resolve the conflicting records before migration.

For recovery, stop the app and restore the backup's `cirrus.sqlite3`, `uploads/` and `session.key` into the dedicated data directory. Move aside the failed database and any `-wal`/`-shm` files together before restoring; never mix old/new SQLite sidecars. Retain failed files until recovery has been verified. Restore the matching application release as described in INSTALLATION.md.
