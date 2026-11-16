"""Create synthetic demo data in an explicitly separate, empty database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta, timezone

from flask import g
from werkzeug.security import generate_password_hash

from cirrus import create_app, db, now


def seed_demo(directory, password):
    target = Path(directory).resolve()
    if target == Path(__file__).resolve().parents[1] / "data":
        raise ValueError(
            "Choose a separate demo subdirectory, never the production data directory."
        )
    app = create_app({"DATA_DIR": str(target)})
    with app.app_context():
        g.app_db = app.config["DATABASE"]
        if db().execute("SELECT 1 FROM users").fetchone():
            raise ValueError("Refusing to seed a nonempty database.")
        with db():
            for uid, username, name, role, dept in [
                (1, "demo.admin", "Morgan Ellis", "admin", 1),
                (2, "demo.employee", "Alex Rivera", "employee", 1),
                (3, "demo.operations", "Sam Parker", "department_manager", 2),
            ]:
                db().execute(
                    "INSERT INTO users(id,username,name,password,role,department_id) VALUES(?,?,?,?,?,?)",
                    (uid, username, name, generate_password_hash(password), role, dept),
                )
            today = datetime.now(timezone.utc).date()
            for title, body, category, severity, pinned, ack in [
                (
                    "Network maintenance · tonight at 22:00",
                    "IT will perform scheduled core network maintenance. Save your work before 22:00 UTC. Expect brief interruptions until 23:00.",
                    "Maintenance",
                    "Critical",
                    1,
                    1,
                ),
                (
                    "Visitor access process updated",
                    "All visitors must check in at reception and wear a visitor badge. Hosts should register their guests one day in advance.",
                    "Security",
                    "Important",
                    1,
                    1,
                ),
                (
                    "Month-end expense deadline",
                    "Submit your expense reports and supporting documents by Friday. Finance is available for questions.",
                    "Deadlines",
                    "Warning",
                    0,
                    0,
                ),
                (
                    "New equipment handovers are ready",
                    "The IT team has prepared the next round of laptop handovers. Check My Equipment to review and confirm receipt.",
                    "IT / Infrastructure",
                    "Notice",
                    0,
                    0,
                ),
                (
                    "Delivery window · loading bay B",
                    "A facilities delivery is expected tomorrow morning. Please keep the loading bay clear between 08:00 and 10:00.",
                    "Operations",
                    "Info",
                    0,
                    0,
                ),
                (
                    "Welcome to Cirrus Pulse",
                    "Your company operations board is live. Use this space for practical updates that help everyone stay informed.",
                    "General",
                    "Info",
                    0,
                    0,
                ),
            ]:
                db().execute(
                    "INSERT INTO notices(title,body,category,severity,author_id,published_at,expires_at,pinned,requires_ack,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        title,
                        body,
                        category,
                        severity,
                        1,
                        now(),
                        (today + timedelta(days=7)).isoformat() + "T23:59:00+00:00",
                        pinned,
                        ack,
                        "active",
                    ),
                )
            for i, (category, model, status, location) in enumerate(
                [
                    ("Laptop", "Latitude 7450", "Assigned", "Head office"),
                    ("Monitor", "UltraSharp 27", "Assigned", "Head office"),
                    ("Laptop", "ThinkPad T14", "Available", "IT store"),
                    ("Phone", "iPhone 15", "Available", "IT store"),
                    ("Docking station", "USB-C Dock", "Under Repair", "IT workshop"),
                    ("Laptop", "EliteBook 840", "Missing", "Head office"),
                    ("Headset", "Evolve2 65", "Available", "IT store"),
                    ("Tablet", "iPad Air", "Available", "Operations"),
                ],
                1,
            ):
                db().execute(
                    "INSERT INTO assets(id,asset_tag,category,manufacturer,model,serial,purchase_date,purchase_cost,warranty_expiration,condition,status,location) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        i,
                        f"CIR-{i:04}",
                        category,
                        "Demo supplier",
                        model,
                        f"DEMO-SN-{i:04}",
                        (today - timedelta(days=180)).isoformat(),
                        "1250.00",
                        (today + timedelta(days=15 if i % 3 == 0 else 240)).isoformat(),
                        "Good" if status != "Under Repair" else "Needs inspection",
                        status,
                        location,
                    ),
                )
                db().execute(
                    "INSERT INTO audit(actor_id,asset_id,action,detail,created_at) VALUES(1,?,?,?,?)",
                    (i, "Registered", "Synthetic demo equipment", now()),
                )
                if status in ("Assigned", "Missing"):
                    db().execute(
                        "INSERT INTO assignments(asset_id,user_id,assigned_at,condition_out,notes,created_by) VALUES(?,2,?,?,?,1)",
                        (i, now(), "Good", "Synthetic handover for demonstration"),
                    )
    return app


if __name__ == "__main__":
    import argparse
    import getpass

    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Demo password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters.")
    seed_demo(args.data_dir, password)
    print(
        "Synthetic demo created. Accounts: demo.admin, demo.employee, demo.operations. Use the password you supplied. Set CIRRUS_DATA_DIR to this demo directory to run it."
    )
