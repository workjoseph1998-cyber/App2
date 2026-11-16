import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

ROLES = (
    "admin",
    "publisher",
    "department_publisher",
    "viewer",
    "asset_manager",
    "department_manager",
    "employee",
)
SEVERITIES = ("Info", "Notice", "Important", "Warning", "Critical")
ASSET_CATEGORIES = (
    "Laptop",
    "Desktop computer",
    "Monitor",
    "Phone",
    "Tablet",
    "Docking station",
    "Headset",
    "Keyboard / mouse",
    "Network equipment",
    "Other accessory",
)
ASSET_STATUSES = ("Available", "Assigned", "Under Repair", "Missing", "Retired")


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def rows(sql, args=()):
    return db().execute(sql, args).fetchall()


def one(sql, args=()):
    return db().execute(sql, args).fetchone()


def notify(uid, message, url):
    if request.script_root and url.startswith(request.script_root + "/"):
        url = url[len(request.script_root) :]
    db().execute(
        "INSERT INTO notifications(user_id,message,url,created_at) VALUES(?,?,?,?)",
        (uid, message, url, now()),
    )


def audit(aid, action, detail=""):
    db().execute(
        "INSERT INTO audit(actor_id,asset_id,action,detail,created_at) VALUES(?,?,?,?,?)",
        (g.user["id"], aid, action, detail, now()),
    )


def manager():
    return g.user["role"] in ("admin", "asset_manager")


def publisher():
    return g.user["role"] in ("admin", "publisher", "department_publisher")


def protected(*roles):
    def decorate(fn):
        @wraps(fn)
        def wrapped(*a, **kw):
            if not g.user:
                return redirect(url_for("login", next=request.path))
            if roles and g.user["role"] not in roles:
                abort(403)
            return fn(*a, **kw)

        return wrapped

    return decorate


def visible_notice(n):
    if (
        n["severity"] == "Critical"
        and not rows("SELECT 1 FROM notice_departments WHERE notice_id=?", (n["id"],))
        and not rows("SELECT 1 FROM notice_roles WHERE notice_id=?", (n["id"],))
    ):
        return True
    ds = [
        r[0]
        for r in rows("SELECT department_id FROM notice_departments WHERE notice_id=?", (n["id"],))
    ]
    rs = [r[0] for r in rows("SELECT role FROM notice_roles WHERE notice_id=?", (n["id"],))]
    return (not ds or g.user["department_id"] in ds) and (not rs or g.user["role"] in rs)


def notice_status(n):
    if n["status"] == "active" and n["expires_at"] and n["expires_at"] <= now():
        return "expired"
    return n["status"]


def can_asset(a):
    if manager():
        return True
    if one(
        "SELECT 1 FROM assignments WHERE asset_id=? AND user_id=? AND returned_at IS NULL",
        (a["id"], g.user["id"]),
    ):
        return True
    if g.user["role"] == "department_manager" and g.user["department_id"]:
        return (
            one(
                "SELECT 1 FROM assignments x JOIN users u ON u.id=x.user_id WHERE x.asset_id=? AND x.returned_at IS NULL AND u.department_id=?",
                (a["id"], g.user["department_id"]),
            )
            is not None
        )
    return False


def asset_or_404(aid):
    a = one("SELECT * FROM assets WHERE id=?", (aid,))
    if not a:
        abort(404)
    if not can_asset(a):
        abort(403)
    return a


def required(name):
    value = request.form.get(name, "").strip()
    if not value:
        raise ValueError(f"{name.replace('_', ' ').title()} is required.")
    if len(value) > 10000:
        raise ValueError("Input is too long.")
    return value


def choice(name, allowed):
    value = required(name)
    if value not in allowed:
        raise ValueError(f"Invalid {name}.")
    return value


def date_value(name, time=False):
    v = request.form.get(name, "").strip()
    if not v:
        return None
    d = datetime.fromisoformat(v)
    return d.replace(tzinfo=timezone.utc).isoformat() if time else d.date().isoformat()


def create_app(config=None):
    app = Flask(__name__)
    root = Path(os.environ.get("CIRRUS_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
    app.config.update(
        PUBLIC_BASE_URL=os.environ.get("CIRRUS_PUBLIC_BASE_URL"),
        DATA_DIR=str(root),
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("CIRRUS_COOKIE_SECURE") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    if config:
        app.config.update(config)
    root = Path(app.config["DATA_DIR"])
    root.mkdir(parents=True, exist_ok=True)
    for folder in ("uploads", "logs", "backups"):
        (root / folder).mkdir(exist_ok=True)
    key = root / "session.key"
    if not key.exists():
        try:
            with key.open("x") as f:
                f.write(secrets.token_hex(32))
            key.chmod(0o600)
        except FileExistsError:
            pass
    app.secret_key = key.read_text().strip()
    import logging
    from logging.handlers import RotatingFileHandler

    logfile = str(root / "logs" / "cirrus.log")
    if not app.testing and not any(
        getattr(h, "baseFilename", None) == logfile for h in app.logger.handlers
    ):
        handler = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)
    app.config.setdefault("DATABASE", str(root / "cirrus.sqlite3"))
    with sqlite3.connect(app.config["DATABASE"]) as c:
        c.executescript(Path(__file__).with_name("schema.sql").read_text())
        c.execute("PRAGMA journal_mode=WAL")
        if "auth_version" not in [r[1] for r in c.execute("PRAGMA table_info(users)")]:
            c.execute("ALTER TABLE users ADD COLUMN auth_version INTEGER NOT NULL DEFAULT 1")
        c.execute("INSERT OR IGNORE INTO schema_versions VALUES(2,?)", (now(),))
        c.execute("INSERT OR IGNORE INTO schema_versions VALUES(1,?)", (now(),))
        for d in ("IT", "Operations", "Security", "Sales", "Finance", "HR", "Management"):
            c.execute("INSERT OR IGNORE INTO departments(name) VALUES(?)", (d,))
        for d in (
            "General",
            "IT / Infrastructure",
            "Operations",
            "Security",
            "Sales",
            "Finance",
            "HR / Administration",
            "Management",
            "Maintenance",
            "Deadlines",
        ):
            c.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (d,))

    @app.before_request
    def before():
        g.app_db = app.config["DATABASE"]
        g.user = one("SELECT * FROM users WHERE id=? AND enabled=1", (session.get("uid"),))
        if g.user and session.get("auth_version") != g.user["auth_version"]:
            session.clear()
            g.user = None
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        if g.user and request.method == "GET":
            with db():
                for n in rows(
                    "SELECT * FROM notices WHERE status='active' AND (starts_at IS NULL OR starts_at<=?) AND (expires_at IS NULL OR expires_at>?)",
                    (now(), now()),
                ):
                    if visible_notice(n):
                        url = f"/updates/{n['id']}"
                        if not one(
                            "SELECT 1 FROM notifications WHERE user_id=? AND url=?",
                            (g.user["id"], url),
                        ):
                            notify(g.user["id"], n["title"], url)
        if request.method == "POST" and not secrets.compare_digest(
            request.form.get("csrf", ""), session["csrf"]
        ):
            abort(400, "Invalid CSRF token")

    @app.teardown_appcontext
    def teardown(exc):
        if "db" in g:
            g.db.close()

    @app.after_request
    def headers(r):
        r.headers["X-Content-Type-Options"] = "nosniff"
        r.headers["X-Frame-Options"] = "DENY"
        r.headers["Referrer-Policy"] = "same-origin"
        r.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        if request.endpoint != "static":
            r.headers["Cache-Control"] = "no-store"
        return r

    @app.errorhandler(ValueError)
    @app.errorhandler(sqlite3.IntegrityError)
    def validation(e):
        db().rollback()
        message = (
            str(e)
            if isinstance(e, ValueError)
            else "This conflicts with an existing record or active assignment."
        )
        return render_template("error.html", message=message), 400

    @app.errorhandler(HTTPException)
    def http_error(e):
        return render_template("error.html", message=e.description), e.code

    @app.context_processor
    def context():
        return dict(
            user=g.get("user"),
            csrf=session.get("csrf"),
            roles=ROLES,
            severities=SEVERITIES,
            asset_categories=ASSET_CATEGORIES,
            asset_statuses=ASSET_STATUSES,
            manager=manager() if g.user else False,
            publisher=publisher() if g.user else False,
            departments=rows("SELECT * FROM departments ORDER BY name"),
            categories=rows("SELECT * FROM categories ORDER BY name"),
            notice_status=notice_status,
            warranty_soon=(datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat(),
            utc_today=datetime.now(timezone.utc).date().isoformat(),
        )

    @app.cli.command("init-admin")
    def init_admin():
        import click

        username = click.prompt("Admin username").strip()
        if not username:
            raise click.ClickException("Username cannot be empty.")
        password = click.prompt(
            "Password (12+ characters)", hide_input=True, confirmation_prompt=True
        )
        if len(password) < 12:
            raise click.ClickException("Use at least 12 characters.")
        try:
            with db():
                db().execute(
                    "INSERT INTO users(username,name,password,role) VALUES(?,?,?,?)",
                    (username, username, generate_password_hash(password), "admin"),
                )
        except sqlite3.IntegrityError as exc:
            raise click.ClickException(
                "That username already exists. Choose another username."
            ) from exc
        click.echo("Administrator created.")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            import hashlib
            import time

            identity = hashlib.sha256(
                (request.remote_addr + "|" + request.form.get("username", "").lower()).encode()
            ).hexdigest()
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
            attempts = one(
                "SELECT count(*) FROM login_attempts WHERE identity=? AND attempted_at>?",
                (identity, cutoff),
            )[0]
            if attempts >= 10:
                abort(429, "Too many failed login attempts. Try again after 15 minutes.")
            u = one(
                "SELECT * FROM users WHERE username=? AND enabled=1",
                (request.form.get("username"),),
            )
            if u and check_password_hash(u["password"], request.form.get("password", "")):
                with db():
                    db().execute("DELETE FROM login_attempts WHERE identity=?", (identity,))
                session.clear()
                session["uid"] = u["id"]
                session["auth_version"] = u["auth_version"]
                session.permanent = True
                from urllib.parse import urlsplit

                target = request.args.get("next", "")
                parsed = urlsplit(target)
                if (
                    target.startswith("/")
                    and not target.startswith("//")
                    and not parsed.scheme
                    and not parsed.netloc
                    and "\\" not in target
                ):
                    return redirect(request.script_root + target)
                return redirect(url_for("dashboard"))
            with db():
                db().execute("INSERT INTO login_attempts VALUES(?,?)", (identity, now()))
                db().execute("DELETE FROM login_attempts WHERE attempted_at<?", (cutoff,))
            time.sleep(0.4)
            flash("Invalid username or password.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @protected()
    def logout():
        session.clear()
        return redirect(url_for("login"))

    def get_notices(archive=False):
        result = []
        for n in rows(
            "SELECT n.*,u.name author FROM notices n JOIN users u ON u.id=n.author_id ORDER BY CASE severity WHEN 'Critical' THEN 0 WHEN 'Warning' THEN 1 ELSE 2 END,pinned DESC,published_at DESC"
        ):
            if not visible_notice(n) and not (
                g.user["role"] == "admin" or n["author_id"] == g.user["id"]
            ):
                continue
            status = notice_status(n)
            if n["status"] == "draft" and not (
                g.user["role"] == "admin" or n["author_id"] == g.user["id"]
            ):
                continue
            if not archive and (status != "active" or (n["starts_at"] and n["starts_at"] > now())):
                continue
            q = request.args.get("q", "").lower()
            if q and q not in (n["title"] + " " + n["body"]).lower():
                continue
            if any(
                request.args.get(k) and request.args[k] != (status if k == "status" else n[k])
                for k in ("severity", "category", "status")
            ):
                continue
            if request.args.get("pinned") and not n["pinned"]:
                continue
            if request.args.get("from") and n["published_at"][:10] < request.args["from"]:
                continue
            if request.args.get("to") and n["published_at"][:10] > request.args["to"]:
                continue
            if request.args.get("department") and not one(
                "SELECT 1 FROM notice_departments WHERE notice_id=? AND department_id=?",
                (n["id"], request.args["department"]),
            ):
                continue
            result.append(n)
        return result

    @app.get("/")
    @protected()
    def dashboard():
        ns = get_notices()
        acked = {
            r[0]
            for r in rows("SELECT notice_id FROM acknowledgements WHERE user_id=?", (g.user["id"],))
        }
        return render_template("pulse.html", notices=ns, acked=acked, dashboard=True, archive=False)

    @app.get("/updates")
    @app.get("/archive")
    @protected()
    def updates():
        return render_template(
            "pulse.html",
            notices=get_notices(request.path == "/archive"),
            acked={
                r[0]
                for r in rows(
                    "SELECT notice_id FROM acknowledgements WHERE user_id=?", (g.user["id"],)
                )
            },
            dashboard=False,
            archive=request.path == "/archive",
        )

    @app.route("/updates/new", methods=["GET", "POST"])
    @protected("admin", "publisher", "department_publisher")
    def new_notice():
        if request.method == "POST":
            ds = request.form.getlist("departments")
            rs = request.form.getlist("roles")
            if any(r not in ROLES for r in rs):
                raise ValueError("Invalid role")
            if g.user["role"] == "department_publisher":
                if not g.user["department_id"]:
                    raise ValueError("A department is required for this account.")
                ds = [g.user["department_id"]]
            start = date_value("starts_at", True)
            end = date_value("expires_at", True)
            if start and end and start >= end:
                raise ValueError("Expiry must follow the start date.")
            with db():
                nid = (
                    db()
                    .execute(
                        "INSERT INTO notices(title,body,category,severity,author_id,published_at,starts_at,expires_at,pinned,requires_ack,status) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            required("title"),
                            required("body"),
                            choice(
                                "category", [r["name"] for r in rows("SELECT name FROM categories")]
                            ),
                            choice("severity", SEVERITIES),
                            g.user["id"],
                            now(),
                            start,
                            end,
                            int("pinned" in request.form),
                            int("requires_ack" in request.form),
                            choice("status", ("draft", "active")),
                        ),
                    )
                    .lastrowid
                )
                for d in ds:
                    db().execute("INSERT INTO notice_departments VALUES(?,?)", (nid, int(d)))
                for r in rs:
                    db().execute("INSERT INTO notice_roles VALUES(?,?)", (nid, r))
                n = one("SELECT * FROM notices WHERE id=?", (nid,))
                original = g.user
                for u in rows("SELECT * FROM users WHERE enabled=1"):
                    g.user = u
                    if (
                        visible_notice(n)
                        and n["status"] == "active"
                        and (not n["starts_at"] or n["starts_at"] <= now())
                    ):
                        notify(u["id"], n["title"], f"/updates/{nid}")
                g.user = original
                if n["status"] == "draft":
                    notify(original["id"], "Draft saved: " + n["title"], f"/updates/{nid}")
            return redirect(url_for("updates"))
        return render_template("notice_form.html")

    @app.route("/updates/<int:nid>", methods=["GET", "POST"])
    @protected()
    def notice_detail(nid):
        n = one(
            "SELECT n.*,u.name author FROM notices n JOIN users u ON u.id=n.author_id WHERE n.id=?",
            (nid,),
        )
        if not n:
            abort(404)
        owner = g.user["role"] == "admin" or (publisher() and n["author_id"] == g.user["id"])
        if (not visible_notice(n) and not owner) or (
            (n["status"] == "draft" or (n["starts_at"] and n["starts_at"] > now())) and not owner
        ):
            abort(403)
        if request.method == "POST":
            action = required("action")
            with db():
                if action == "ack":
                    if (
                        notice_status(n) != "active"
                        or (n["starts_at"] and n["starts_at"] > now())
                        or not n["requires_ack"]
                    ):
                        abort(400)
                    db().execute(
                        "INSERT OR IGNORE INTO acknowledgements VALUES(?,?,?)",
                        (nid, g.user["id"], now()),
                    )
                elif owner and action in ("archive", "publish"):
                    db().execute(
                        "UPDATE notices SET status=? WHERE id=?",
                        ("archived" if action == "archive" else "active", nid),
                    )
                    if action == "publish":
                        original = g.user
                        for u in rows("SELECT * FROM users WHERE enabled=1"):
                            g.user = u
                            if visible_notice(n) and (
                                not n["starts_at"] or n["starts_at"] <= now()
                            ):
                                notify(u["id"], n["title"], f"/updates/{nid}")
                        g.user = original
                else:
                    abort(403)
            return redirect(url_for("notice_detail", nid=nid))
        acks = (
            rows(
                "SELECT u.name,a.acknowledged_at FROM acknowledgements a JOIN users u ON u.id=a.user_id WHERE notice_id=?",
                (nid,),
            )
            if owner
            else []
        )
        pending = []
        if owner:
            original = g.user
            for u in rows("SELECT * FROM users WHERE enabled=1"):
                g.user = u
                if visible_notice(n) and not one(
                    "SELECT 1 FROM acknowledgements WHERE notice_id=? AND user_id=?", (nid, u["id"])
                ):
                    pending.append(u["name"])
            g.user = original
        return render_template(
            "notice_detail.html",
            n=n,
            owner=owner,
            acks=acks,
            pending=pending,
            ack=one(
                "SELECT * FROM acknowledgements WHERE notice_id=? AND user_id=?",
                (nid, g.user["id"]),
            ),
        )

    @app.route("/notifications", methods=["GET", "POST"])
    @protected()
    def notifications():
        if request.method == "POST":
            with db():
                db().execute("UPDATE notifications SET seen=1 WHERE user_id=?", (g.user["id"],))
        return render_template(
            "notifications.html",
            items=rows(
                "SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC", (g.user["id"],)
            ),
        )

    @app.route("/admin/users", methods=["GET", "POST"])
    @protected("admin")
    def users():
        if request.method == "POST":
            role = choice("role", ROLES)
            dept = request.form.get("department_id") or None
            password = request.form.get("password", "")
            uid = request.form.get("id")
            if password and len(password) < 12:
                raise ValueError("Passwords need at least 12 characters.")
            if (
                uid
                and int(uid) == g.user["id"]
                and (role != "admin" or "enabled" not in request.form)
            ):
                raise ValueError("You cannot disable or demote your own administrator account.")
            with db():
                if uid:
                    db().execute(
                        "UPDATE users SET name=?,role=?,department_id=?,enabled=?,auth_version=auth_version+1 WHERE id=?",
                        (required("name"), role, dept, int("enabled" in request.form), uid),
                    )
                    if password:
                        db().execute(
                            "UPDATE users SET password=? WHERE id=?",
                            (generate_password_hash(password), uid),
                        )
                else:
                    if not password:
                        raise ValueError("Password is required.")
                    db().execute(
                        "INSERT INTO users(username,name,password,role,department_id) VALUES(?,?,?,?,?)",
                        (
                            required("username"),
                            required("name"),
                            generate_password_hash(password),
                            role,
                            dept,
                        ),
                    )
            flash("Account saved.")
            return redirect(url_for("users"))
        return render_template("users.html", items=rows("SELECT * FROM users ORDER BY name"))

    @app.route("/settings", methods=["GET", "POST"])
    @app.route("/departments", methods=["GET", "POST"])
    @protected("admin")
    def settings():
        if request.method == "POST":
            table = "categories" if request.form.get("kind") == "category" else "departments"
            with db():
                db().execute(f"INSERT INTO {table}(name) VALUES(?)", (required("name"),))
            return redirect(request.path)
        return render_template("settings.html")

    @app.get("/api/experience/search")
    @protected()
    def experience_search():
        query = request.args.get("q", "").strip()[:200]
        if len(query) < 2:
            return jsonify(results=[])
        results = []
        for n in get_notices(archive=True):
            owner = g.user["role"] == "admin" or n["author_id"] == g.user["id"]
            if n["starts_at"] and n["starts_at"] > now() and not owner:
                continue
            results.append(
                {
                    "type": "notice",
                    "title": n["title"],
                    "subtitle": n["category"] + " · " + n["severity"],
                    "url": f"/updates/{n['id']}",
                }
            )
            if len(results) >= 10:
                break
        for asset in rows(
            "SELECT id,asset_tag,category,model,manufacturer FROM assets ORDER BY asset_tag"
        ):
            if not can_asset(asset):
                continue
            searchable = " ".join(
                str(asset[k] or "") for k in ("asset_tag", "category", "model", "manufacturer")
            )
            if query.lower() not in searchable.lower():
                continue
            results.append(
                {
                    "type": "asset",
                    "title": asset["asset_tag"],
                    "subtitle": " ".join(
                        str(asset[k] or "") for k in ("manufacturer", "model", "category")
                    ),
                    "url": f"/assetpass/assets/{asset['id']}",
                }
            )
            if len(results) >= 20:
                break
        return jsonify(results=results)

    def permitted_notifications():
        items = []
        for item in rows(
            "SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC", (g.user["id"],)
        ):
            if item["url"].startswith("/updates/"):
                try:
                    nid = int(item["url"].split("/")[2])
                except (ValueError, IndexError):
                    continue
                n = one("SELECT * FROM notices WHERE id=?", (nid,))
                if not n:
                    continue
                owner = g.user["role"] == "admin" or n["author_id"] == g.user["id"]
                if not owner and (
                    not visible_notice(n)
                    or n["status"] == "draft"
                    or (n["starts_at"] and n["starts_at"] > now())
                ):
                    continue
            items.append(dict(item))
        return items

    @app.get("/api/experience/notifications")
    @protected()
    def experience_notifications():
        items = permitted_notifications()
        return jsonify(items=items[:50], unread=sum(not item["seen"] for item in items))

    @app.post("/api/experience/notifications/read")
    @protected()
    def experience_notifications_read():
        with db():
            db().execute("UPDATE notifications SET seen=1 WHERE user_id=?", (g.user["id"],))
        return jsonify(ok=True)

    from .assets import register_assets

    register_assets(app)
    return app
