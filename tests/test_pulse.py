from conftest import login, notice, post
from flask import g

from cirrus import db


def test_auth_csrf_and_disabled(client, app):
    assert client.get("/").status_code == 302
    assert client.post("/login", data={"username": "admin"}).status_code == 400
    assert login(client).status_code == 302
    assert client.get("/").status_code == 200
    with app.app_context():
        g.app_db = app.config["DATABASE"]
        with db():
            db().execute("UPDATE users SET enabled=0 WHERE id=1")
    assert client.get("/").status_code == 302


def test_targeted_visibility_roles_ack_and_archive(client):
    login(client)
    assert notice(client, departments="1", roles="employee").status_code == 302
    assert notice(client, title="Global critical", severity="Critical").status_code == 302
    login(client, "bob")
    assert b"Global critical" in client.get("/").data
    assert b"Scheduled maintenance" not in client.get("/").data
    assert client.get("/updates/1").status_code == 403
    assert post(client, "/updates/1", action="ack").status_code == 403
    assert post(client, "/updates/2", action="archive").status_code == 403
    login(client, "alice")
    assert b"Scheduled maintenance" in client.get("/").data
    assert post(client, "/updates/1", action="ack").status_code == 302
    assert b"Acknowledged" in client.get("/updates/1").data
    assert post(client, "/updates/1", action="ack").status_code == 302
    login(client)
    assert post(client, "/updates/2", action="archive").status_code == 302
    assert b"Global critical" not in client.get("/").data
    assert (
        b"Global critical" in client.get("/archive?q=Global&severity=Critical&status=archived").data
    )
    assert b"Global critical" not in client.get("/archive?q=absent").data


def test_department_publisher_drafts_dates_and_notifications(client):
    login(client, "deptpub")
    assert notice(client, departments="2", title="Only IT").status_code == 302
    assert notice(client, title="Draft notice", status="draft").status_code == 302
    assert notice(client, title="Future secret", starts_at="2099-01-01T10:00").status_code == 302
    assert (
        notice(client, starts_at="2026-01-02T10:00", expires_at="2026-01-01T10:00").status_code
        == 400
    )
    login(client, "bob")
    assert b"Only IT" not in client.get("/").data
    assert client.get("/updates/2").status_code == 403
    login(client, "alice")
    assert b"Only IT" in client.get("/notifications").data
    assert b"Future secret" not in client.get("/notifications").data
    assert client.get("/updates/3").status_code == 403
    assert post(client, "/updates/new", title="Unauthorized").status_code == 403
    assert client.get("/admin/users").status_code == 403
    assert post(client, "/notifications").status_code == 200


def test_admin_users_categories_departments_and_self_protection(client):
    login(client)
    assert (
        post(
            client,
            "/admin/users",
            username="new",
            name="New User",
            password="long-password-123",
            role="viewer",
            department_id="1",
        ).status_code
        == 302
    )
    assert post(client, "/admin/users", id="1", name="Admin", role="viewer").status_code == 400
    assert post(client, "/settings", kind="category", name="Facilities").status_code == 302
    assert post(client, "/departments", kind="department", name="Legal").status_code == 302
    assert b"Facilities" in client.get("/updates/new").data


def test_all_main_pages_render(client):
    login(client)
    for path in [
        "/",
        "/updates",
        "/archive",
        "/updates/new",
        "/notifications",
        "/settings",
        "/departments",
        "/admin/users",
        "/assetpass",
        "/assetpass/inventory",
        "/assetpass/mine",
        "/assetpass/assignments",
        "/assetpass/returns",
        "/assetpass/issues",
        "/assetpass/history",
        "/assetpass/reports",
        "/assetpass/clearance",
        "/assetpass/new",
    ]:
        assert client.get(path).status_code == 200, path


def test_account_change_revokes_existing_sessions(app, client):
    other = app.test_client()
    login(other, "alice")
    login(client)
    assert (
        post(
            client,
            "/admin/users",
            id="4",
            name="Alice",
            role="employee",
            department_id="1",
            enabled="on",
            password="replacement-password-123",
        ).status_code
        == 302
    )
    assert other.get("/").status_code == 302


def test_login_throttle(client):
    client.get("/login")
    for _ in range(10):
        assert post(client, "/login", username="unknown-account", password="bad").status_code == 200
    assert post(client, "/login", username="unknown-account", password="bad").status_code == 429


def test_login_returns_to_authorized_qr_record_without_open_redirect(client):
    client.get("/login")
    assert (
        post(
            client,
            "/login?next=/assetpass/assets/42",
            username="alice",
            password="TestingPassword123!",
        ).headers["Location"]
        == "/assetpass/assets/42"
    )
    post(client, "/logout")
    client.get("/login")
    assert (
        post(
            client,
            "/login?next=//outside.example",
            username="alice",
            password="TestingPassword123!",
        ).headers["Location"]
        == "/"
    )


def test_severities_expiry_and_filters(client):
    login(client)
    for severity in ("Info", "Notice", "Important", "Warning", "Critical"):
        assert notice(client, title=f"{severity} test", severity=severity).status_code == 302
    assert notice(client, title="Expired test", expires_at="2000-01-01T00:00").status_code == 302
    assert b"Expired test" not in client.get("/").data
    assert b"Expired test" in client.get("/archive?status=expired").data
    for severity in ("Info", "Notice", "Important", "Warning", "Critical"):
        page = client.get("/updates?severity=" + severity)
        assert f"badge {severity.lower()}".encode() in page.data
        assert f"{severity} test".encode() in page.data
    assert b"Critical test" not in client.get("/updates?from=2099-01-01").data
    assert b"Critical test" not in client.get("/updates?to=2000-01-01").data
    assert (
        b"Critical test" in client.get("/updates?category=IT+%2F+Infrastructure&q=synthetic").data
    )
