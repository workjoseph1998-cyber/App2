import pytest
from werkzeug.security import generate_password_hash

from cirrus import create_app, db


@pytest.fixture()
def app(tmp_path):
    app = create_app({"TESTING": True, "DATA_DIR": str(tmp_path)})
    with app.app_context():
        from flask import g

        g.app_db = app.config["DATABASE"]
        with db():
            for uid, name, role, dept in [
                (1, "admin", "admin", 1),
                (2, "publisher", "publisher", 1),
                (3, "deptpub", "department_publisher", 1),
                (4, "alice", "employee", 1),
                (5, "bob", "employee", 2),
                (6, "assets", "asset_manager", 1),
                (7, "deptmgr", "department_manager", 1),
                (8, "viewer", "viewer", 2),
            ]:
                db().execute(
                    "INSERT INTO users(id,username,name,password,role,department_id) VALUES(?,?,?,?,?,?)",
                    (uid, name, name, generate_password_hash("TestingPassword123!"), role, dept),
                )
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, name="admin"):
    client.get("/login")
    response = post(client, "/login", username=name, password="TestingPassword123!")
    if response.status_code == 302:
        client.get("/")
    return response


def post(client, path, **data):
    with client.session_transaction() as s:
        token = s.get("csrf", "")
    return client.post(path, data={"csrf": token, **data})


def asset(client, tag="CIR-001", serial="serial-1"):
    return post(
        client,
        "/assetpass/new",
        asset_tag=tag,
        category="Laptop",
        manufacturer="Cirrus",
        model="Pro 14",
        serial=serial,
        condition="Good",
        purchase_cost="1234.56",
        warranty_expiration="2027-01-01",
    )


def notice(client, **kw):
    data = dict(
        title="Scheduled maintenance",
        body="Synthetic maintenance update",
        category="IT / Infrastructure",
        severity="Warning",
        status="active",
        requires_ack="on",
    )
    data.update(kw)
    return post(client, "/updates/new", **data)
