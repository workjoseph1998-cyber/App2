"""Exercise the documented first-install command without a web request."""

from conftest import login
from werkzeug.security import check_password_hash

from cirrus import create_app, db


def test_first_admin_created_and_can_sign_in(tmp_path):
    app = create_app({"TESTING": True, "DATA_DIR": str(tmp_path)})
    result = app.test_cli_runner().invoke(
        args=["init-admin"], input="first-admin\nTestingPassword123!\nTestingPassword123!\n"
    )
    assert result.exit_code == 0, result.output
    assert "Administrator created." in result.output
    with app.app_context():
        user = db().execute("SELECT * FROM users WHERE username=?", ("first-admin",)).fetchone()
        assert user["role"] == "admin" and user["enabled"] == 1
        assert check_password_hash(user["password"], "TestingPassword123!")
    client = app.test_client()
    assert login(client, "first-admin").status_code == 302
    assert client.get("/admin/users").status_code == 200


def test_short_password_creates_no_account(tmp_path):
    app = create_app({"TESTING": True, "DATA_DIR": str(tmp_path)})
    result = app.test_cli_runner().invoke(args=["init-admin"], input="first-admin\nshort\nshort\n")
    assert result.exit_code != 0
    assert "Use at least 12 characters." in result.output
    with app.app_context():
        assert db().execute("SELECT count(*) FROM users").fetchone()[0] == 0


def test_duplicate_admin_is_reported_without_changing_existing_account(tmp_path):
    app = create_app({"TESTING": True, "DATA_DIR": str(tmp_path)})
    runner = app.test_cli_runner()
    assert (
        runner.invoke(
            args=["init-admin"], input="first-admin\nTestingPassword123!\nTestingPassword123!\n"
        ).exit_code
        == 0
    )
    result = runner.invoke(
        args=["init-admin"], input="first-admin\nDifferentPassword123!\nDifferentPassword123!\n"
    )
    assert result.exit_code != 0
    assert "That username already exists." in result.output
    with app.app_context():
        user = db().execute("SELECT * FROM users").fetchone()
        assert check_password_hash(user["password"], "TestingPassword123!")
        assert db().execute("SELECT count(*) FROM users").fetchone()[0] == 1
