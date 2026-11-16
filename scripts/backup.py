"""Consistent SQLite backup; stop the app first to capture matching uploads."""

import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cirrus import create_app

app = create_app()
root = Path(app.config["DATA_DIR"])
target = root / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
target.mkdir(parents=True)
with (
    sqlite3.connect(app.config["DATABASE"]) as src,
    sqlite3.connect(target / "cirrus.sqlite3") as dst,
):
    src.backup(dst)
shutil.copytree(root / "uploads", target / "uploads")
shutil.copy2(root / "session.key", target / "session.key")
print(f"Backup created: {target}")
