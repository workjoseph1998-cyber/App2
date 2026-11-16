from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from conftest import asset, login, post
from openpyxl import load_workbook


def assign(client, uid="4"):
    return post(
        client,
        "/assetpass/assets/1/assign",
        user_id=uid,
        condition="Good",
        notes="Synthetic handover",
    )


def test_full_handover_return_issue_clearance(client, app):
    login(client)
    assert asset(client).status_code == 302
    assert assign(client).status_code == 302
    assert post(client, "/assetpass/assignments/1/confirm").status_code == 403
    assert b"Awaiting employee confirmation" in client.get("/assetpass/assets/1").data
    login(client, "alice")
    assert b"CIR-001" in client.get("/assetpass/mine").data
    assert b"1234.56" not in client.get("/assetpass/assets/1").data
    assert post(client, "/assetpass/assignments/1/confirm").status_code == 302
    assert post(client, "/assetpass/assignments/1/confirm").status_code == 400
    assert (
        post(
            client,
            "/assetpass/issues",
            asset_id="1",
            kind="Damage",
            description="Synthetic scratch",
        ).status_code
        == 302
    )
    assert post(client, "/assetpass/issues/1/close", resolution="No").status_code == 403
    assert post(client, "/assetpass/assignments/1/request-return").status_code == 302
    assert (
        post(
            client,
            "/assetpass/assignments/1/return",
            verified="on",
            status="Available",
            condition="Good",
        ).status_code
        == 403
    )
    login(client, "assets")
    assert post(client, "/assetpass/clearance", user_id="4").status_code == 400
    assert (
        post(
            client, "/assetpass/assignments/1/return", status="Available", condition="Good"
        ).status_code
        == 400
    )
    assert (
        post(
            client,
            "/assetpass/assignments/1/return",
            verified="on",
            status="Under Repair",
            condition="Scratched",
            notes="Repair needed",
        ).status_code
        == 302
    )
    assert assign(client).status_code == 400
    assert post(client, "/assetpass/issues/1/close", resolution="Repaired").status_code == 302
    assert (
        post(
            client, "/assetpass/assets/1", status="Available", condition="Good", notes="Repaired"
        ).status_code
        == 302
    )
    assert post(client, "/assetpass/clearance", user_id="4").status_code == 200
    assert assign(client, uid="5").status_code == 302
    login(client, "alice")
    assert b"CIR-001" in client.get("/assetpass/history").data
    assert client.get("/assetpass/assets/1").status_code == 403
    assert post(client, "/assetpass/assignments/2/confirm").status_code == 403
    login(client, "bob")
    assert post(client, "/assetpass/assignments/2/confirm").status_code == 302


def test_duplicates_atomicity_and_status_transitions(client):
    login(client)
    assert asset(client).status_code == 302
    assert asset(client, tag="CIR-002").status_code == 400
    assert asset(client, tag="CIR-001", serial="other").status_code == 400
    assert (
        post(client, "/assetpass/assets/1", status="Assigned", condition="Good").status_code == 400
    )
    assert assign(client).status_code == 302
    assert assign(client, "5").status_code == 400
    assert (
        post(client, "/assetpass/assets/1", status="Available", condition="Good").status_code == 400
    )
    assert (
        post(client, "/assetpass/assets/1", status="Retired", condition="Good").status_code == 400
    )
    assert (
        post(
            client,
            "/assetpass/assignments/1/return",
            verified="on",
            status="Retired",
            condition="Old",
        ).status_code
        == 302
    )
    assert (
        post(client, "/assetpass/assets/1", status="Available", condition="Good").status_code == 400
    )


def test_concurrent_assignment(app, client):
    login(client)
    asset(client)

    def attempt(uid):
        c = app.test_client()
        login(c, "assets")
        return assign(c, uid).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, ["4", "5"]))
    assert sorted(outcomes) == [302, 400]


def test_permissions_exports_and_department_scope(client):
    login(client)
    asset(client)
    assign(client)
    assert b"1234.56" in client.get("/assetpass/assets/1").data
    login(client, "bob")
    for path in [
        "/assetpass/assets/1",
        "/assetpass/assets/1/qr",
        "/assetpass/assets/1/label",
        "/assetpass/reports",
        "/assetpass/export/inventory",
    ]:
        assert client.get(path).status_code == 403, path
    assert (
        post(client, "/assetpass/assets/1/assign", user_id="5", condition="Good").status_code == 403
    )
    login(client, "deptmgr")
    assert client.get("/assetpass/assets/1").status_code == 200
    assert b"1234.56" not in client.get("/assetpass/assets/1").data
    workbook = load_workbook(BytesIO(client.get("/assetpass/export/inventory").data))
    values = list(workbook.active.values)
    assert "purchase_cost" not in values[0]
    assert "CIR-001" in values[1]
    assert (
        len(
            list(
                load_workbook(
                    BytesIO(client.get("/assetpass/export/inventory?department=2").data)
                ).active.values
            )
        )
        == 1
    )
    login(client, "assets")
    for kind in [
        "inventory",
        "category",
        "department",
        "assignments",
        "pending",
        "warranty",
        "returns",
        "issues",
    ]:
        r = client.get("/assetpass/export/" + kind)
        assert r.status_code == 200
        assert len(list(load_workbook(BytesIO(r.data)).active.values)) >= 1
    wb = load_workbook(BytesIO(client.get("/assetpass/export/inventory").data))
    assert "purchase_cost" in list(wb.active.values)[0]


def test_attachments_and_qr(client):
    from PIL import Image

    login(client)
    asset(client)
    assign(client)
    assert client.get("/assetpass/assets/1/label").status_code == 200
    qr = client.get("/assetpass/assets/1/qr")
    assert qr.status_code == 200 and qr.data.startswith(b"\x89PNG")
    login(client, "alice")
    assert (
        post(
            client,
            "/assetpass/issues",
            asset_id="1",
            kind="Malfunction",
            description="Photo evidence",
        ).status_code
        == 302
    )
    image = BytesIO()
    Image.new("RGB", (10, 10), "orange").save(image, format="PNG")
    image.seek(0)
    r = post(client, "/assetpass/assets/1/attachments", issue_id="1", file=(image, "../photo.png"))
    assert r.status_code == 302
    assert client.get("/assetpass/attachments/1").status_code == 200
    assert (
        post(
            client,
            "/assetpass/assets/1/attachments",
            issue_id="1",
            file=(BytesIO(b"<script>bad</script>"), "bad.html"),
        ).status_code
        == 400
    )
    login(client, "bob")
    assert client.get("/assetpass/attachments/1").status_code == 403
    assert (
        post(
            client,
            "/assetpass/assets/1/attachments",
            issue_id="1",
            file=(BytesIO(b"%PDF-1.4"), "x.pdf"),
        ).status_code
        == 403
    )


def test_spreadsheet_formula_escaping(client):
    login(client)
    asset(client, tag="=1+2")
    wb = load_workbook(BytesIO(client.get("/assetpass/export/inventory").data))
    assert wb.active["A2"].value == "'=1+2"


def test_specification_edit_and_case_insensitive_identifiers(client):
    login(client)
    asset(client)
    assert asset(client, tag="cir-001", serial="another-serial").status_code == 400
    assert client.get("/assetpass/assets/1/edit").status_code == 200
    assert (
        post(
            client,
            "/assetpass/assets/1/edit",
            asset_tag="CIR-EDITED",
            category="Monitor",
            model="Updated model",
            purchase_cost="500.00",
        ).status_code
        == 302
    )
    assert b"Updated model" in client.get("/assetpass/assets/1").data
    login(client, "alice")
    assert post(client, "/assetpass/assets/1/edit", asset_tag="Unauthorized").status_code == 403


def test_department_history_does_not_reveal_previous_employee(client):
    login(client)
    asset(client)
    assign(client, "5")
    assert (
        post(
            client,
            "/assetpass/assignments/1/return",
            verified="on",
            status="Available",
            condition="Good",
        ).status_code
        == 302
    )
    assert assign(client, "4").status_code == 302
    login(client, "deptmgr")
    page = client.get("/assetpass/assets/1")
    assert page.status_code == 200
    assert b"bob" not in page.data
    assert b"alice" in page.data


def test_prefixed_qr_and_notification_urls(app, client, monkeypatch):
    import qrcode
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.wrappers import Response

    app.wsgi_app = DispatcherMiddleware(Response("Not found", status=404), {"/pulse": app.wsgi_app})
    client.get("/pulse/login")
    assert (
        post(client, "/pulse/login", username="admin", password="TestingPassword123!").status_code
        == 302
    )
    client.get("/pulse/")
    assert (
        post(
            client,
            "/pulse/assetpass/new",
            asset_tag="PREFIX-1",
            category="Laptop",
            condition="Good",
        ).status_code
        == 302
    )
    captured = []
    make = qrcode.make

    def record(payload):
        captured.append(payload)
        return make(payload)

    monkeypatch.setattr(qrcode, "make", record)
    assert client.get("/pulse/assetpass/assets/1/qr").status_code == 200
    assert captured == ["http://localhost/pulse/assetpass/assets/1"]
    assert (
        post(
            client,
            "/pulse/assetpass/issues",
            asset_id="1",
            kind="Damage",
            description="Prefix test",
        ).status_code
        == 302
    )
    notifications = client.get("/pulse/notifications").data
    assert b'href="/pulse/assetpass/issues"' in notifications
    assert b"/pulse/pulse/" not in notifications
