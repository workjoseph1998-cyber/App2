import socket
import subprocess
import sys

from cirrus import create_app
from run import check_port


def test_port_in_use_protection():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        try:
            check_port(port=port)
        except RuntimeError as e:
            assert "in use" in str(e)
        else:
            raise AssertionError("Occupied port accepted")
    check_port(port=port)


def test_additive_schema_repeatable(app):
    import sqlite3

    create_app({"TESTING": True, "DATA_DIR": app.config["DATA_DIR"]})
    with sqlite3.connect(app.config["DATABASE"]) as c:
        assert c.execute("SELECT count(*) FROM users").fetchone()[0] == 8
        assert c.execute("SELECT version FROM schema_versions").fetchone()[0] == 1
        assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_actual_runner_refuses_occupied_8000():
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 8000))
        listener.listen()
        result = subprocess.run(
            [sys.executable, "run.py"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 1
        assert "Port 8000 is in use" in result.stderr


def test_iis_subpath_links_and_login(monkeypatch, tmp_path):
    from werkzeug.test import Client
    from werkzeug.wrappers import Response

    from wsgi import build_wsgi

    monkeypatch.setenv("CIRRUS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CIRRUS_URL_PREFIX", "/pulse")
    app, wsgi = build_wsgi()
    client = Client(wsgi, Response)
    assert client.get("/login").status_code == 404
    r = client.get("/pulse/login")
    assert r.status_code == 200
    assert b"/pulse/static/app.css" in r.data
    assert client.get("/pulse/").headers["Location"] == "/pulse/login?next=/".replace(
        "?next=/", "?next=/"
    )


def test_retained_listener_prevents_competing_start():
    from run import reserve_port

    with reserve_port(port=0) as listener:
        port = listener.getsockname()[1]
        try:
            check_port(port=port)
        except RuntimeError:
            pass
        else:
            raise AssertionError("A second startup acquired the retained listener")


def test_existing_v1_records_survive_additive_migration(tmp_path):
    import sqlite3
    from pathlib import Path

    database = tmp_path / "cirrus.sqlite3"
    with sqlite3.connect(database) as c:
        c.executescript(Path("cirrus/schema.sql").read_text())
        c.execute(
            "INSERT INTO users(id,username,name,password,role) VALUES(1,'legacy','Legacy','not-a-real-password','viewer')"
        )
        c.execute(
            "INSERT INTO notices(id,title,body,category,severity,author_id,published_at,status) VALUES(1,'Retained notice','Keep this record','General','Info',1,'2020-01-01','active')"
        )
    create_app({"TESTING": True, "DATA_DIR": str(tmp_path)})
    with sqlite3.connect(database) as c:
        assert c.execute("SELECT auth_version FROM users WHERE id=1").fetchone()[0] == 1
        assert c.execute("SELECT title FROM notices WHERE id=1").fetchone()[0] == "Retained notice"
        assert [
            r[0] for r in c.execute("SELECT version FROM schema_versions ORDER BY version")
        ] == [1, 2]
