"""Copy a stopped Pulse data directory into a new release, preserving the source."""

import argparse
import os
import shutil
import socket
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def import_data(source, target, require_stopped=True):
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("Source and destination must be separate data directories.")
    if not (source / "cirrus.sqlite3").is_file() or not (source / "session.key").is_file():
        raise ValueError(
            "Select the old Pulse data folder containing cirrus.sqlite3 and session.key. Never select Workplace data."
        )
    if target.exists() and any(target.iterdir()):
        raise ValueError(
            "The new data directory is not empty. Import into a fresh release folder before setup; no files were replaced."
        )
    if require_stopped:
        with socket.socket() as check:
            if check.connect_ex(("127.0.0.1", 8000)) == 0:
                raise ValueError(
                    "Port 8000 is still listening. Stop the old application before importing data."
                )
    with sqlite3.connect((source / "cirrus.sqlite3").as_uri() + "?mode=ro", uri=True) as original:
        expected = {"users", "notices", "assets", "assignments", "schema_versions"}
        tables = {
            row[0] for row in original.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not expected <= tables:
            raise ValueError(
                "This does not look like a Cirrus Pulse + AssetPass database. Source was not changed."
            )
        if original.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError(
                "Source database integrity check failed. Restore a valid backup before upgrading."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        staged = Path(tempfile.mkdtemp(prefix=".cirrus-import-", dir=target.parent))
        try:
            with sqlite3.connect(staged / "cirrus.sqlite3") as copied:
                original.backup(copied)
                if copied.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Copied database integrity check failed.")
            shutil.copy2(source / "session.key", staged / "session.key")
            if (source / "uploads").is_dir():
                shutil.copytree(source / "uploads", staged / "uploads")
            else:
                (staged / "uploads").mkdir()
            (staged / "logs").mkdir()
            (staged / "backups").mkdir()
            if target.exists():
                target.rmdir()  # Only the verified empty destination, never source data.
            staged.rename(target)
        except BaseException:
            shutil.rmtree(staged, ignore_errors=True)
            raise
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-data")
    parser.add_argument(
        "--target-data", default=os.environ.get("CIRRUS_DATA_DIR", str(ROOT / "data"))
    )
    args = parser.parse_args()
    value = args.source_data or input(
        "Old Pulse DATA folder (or old application folder): "
    ).strip().strip('"')
    source = Path(value)
    if not (source / "cirrus.sqlite3").is_file() and (source / "data" / "cirrus.sqlite3").is_file():
        source = source / "data"
    try:
        target = import_data(source, args.target_data)
    except (ValueError, OSError, sqlite3.Error) as error:
        print(f"Import refused: {error}")
        return 1
    print(f"Data copied and verified: {target}")
    print("Original data remains untouched. Now run Setup-Cirrus.cmd; use your existing account.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
