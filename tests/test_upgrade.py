import sqlite3

import pytest

from cirrus import create_app
from scripts.upgrade import import_data


def test_upgrade_copies_database_uploads_and_key_without_changing_source(tmp_path):
    source = tmp_path / "old-data"
    create_app({"TESTING": True, "DATA_DIR": str(source)})
    with sqlite3.connect(source / "cirrus.sqlite3") as c:
        c.execute(
            "INSERT INTO users(username,name,password,role) VALUES('existing','Existing','synthetic-hash','admin')"
        )
        c.execute(
            "INSERT INTO assets(asset_tag,category,condition,status) VALUES('KEEP-ME','Laptop','Good','Available')"
        )
    (source / "uploads" / "evidence.png").write_bytes(b"synthetic attachment")
    original = (source / "cirrus.sqlite3").read_bytes()
    target = tmp_path / "new-data"
    import_data(source, target, require_stopped=False)
    assert (source / "cirrus.sqlite3").read_bytes() == original
    assert (source / "session.key").read_bytes() == (target / "session.key").read_bytes()
    assert (target / "uploads" / "evidence.png").read_bytes() == b"synthetic attachment"
    with sqlite3.connect(target / "cirrus.sqlite3") as c:
        assert c.execute("SELECT username FROM users").fetchone()[0] == "existing"
        assert c.execute("SELECT asset_tag FROM assets").fetchone()[0] == "KEEP-ME"
        assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    create_app({"TESTING": True, "DATA_DIR": str(target)})
    with sqlite3.connect(target / "cirrus.sqlite3") as c:
        assert c.execute("SELECT count(*) FROM users").fetchone()[0] == 1


def test_upgrade_refuses_overwrite_and_wrong_database(tmp_path):
    source = tmp_path / "source"
    create_app({"TESTING": True, "DATA_DIR": str(source)})
    target = tmp_path / "target"
    target.mkdir()
    (target / "keep.txt").write_text("User data")
    with pytest.raises(ValueError, match="not empty"):
        import_data(source, target, require_stopped=False)
    assert (target / "keep.txt").read_text() == "User data"
    with pytest.raises(ValueError, match="separate"):
        import_data(source, source, require_stopped=False)
    wrong = tmp_path / "wrong"
    wrong.mkdir()
    (wrong / "session.key").write_text("synthetic")
    with sqlite3.connect(wrong / "cirrus.sqlite3") as c:
        c.execute("CREATE TABLE unrelated(id)")
    with pytest.raises(ValueError, match="does not look"):
        import_data(wrong, tmp_path / "destination", require_stopped=False)
