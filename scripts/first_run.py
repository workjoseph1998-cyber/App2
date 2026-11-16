"""Initialize independent data and create an admin only when none exists."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cirrus import create_app, db


def main():
    app = create_app()
    with app.app_context():
        existing = (
            db()
            .execute("SELECT count(*) FROM users WHERE role='admin' AND enabled=1")
            .fetchone()[0]
        )
    print("Cirrus database initialized. Existing records are preserved.")
    if existing:
        print("An enabled administrator already exists. Sign in with your existing account.")
        return 0
    print("Create your first administrator. Password entry is hidden.")
    return subprocess.call(
        [sys.executable, "-m", "flask", "--app", "cirrus:create_app", "init-admin"],
        cwd=Path(__file__).resolve().parents[1],
    )


if __name__ == "__main__":
    raise SystemExit(main())
