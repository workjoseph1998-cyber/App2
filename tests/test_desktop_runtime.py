import os
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

import psutil
import pytest

from cirrus import create_app
from scripts.stop import matches_runner
from scripts.upgrade import import_data


def test_import_refuses_running_old_application(tmp_path):
    source = tmp_path / "source"
    create_app({"TESTING": True, "DATA_DIR": str(source)})
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 8000))
        listener.listen()
        with pytest.raises(ValueError, match="still listening"):
            import_data(source, tmp_path / "destination")
    assert not (tmp_path / "destination").exists()


def test_stop_refuses_unrelated_process():
    assert not matches_runner(psutil.Process(os.getpid()), Path.cwd(), sys.executable)


def test_real_runner_stops_only_its_verified_pid(tmp_path):
    root = Path.cwd()
    env = {**os.environ, "CIRRUS_DATA_DIR": str(tmp_path)}
    process = subprocess.Popen(
        [sys.executable, str(root / "run.py")],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        for _ in range(40):
            assert process.poll() is None, "Runner exited before readiness"
            try:
                if urlopen("http://127.0.0.1:8000/login", timeout=1).status == 200:
                    break
            except OSError:
                time.sleep(0.15)
        else:
            raise AssertionError("Runner never became ready")
        assert (tmp_path / "cirrus.pid").read_text() == str(process.pid)
        # Reap our child as it exits, as the Windows command launcher does.
        with ThreadPoolExecutor(max_workers=1) as executor:
            exited = executor.submit(process.wait, timeout=20)
            stopped = subprocess.run(
                [sys.executable, str(root / "scripts/stop.py")],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                timeout=20,
            )
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr
            exited.result()
        assert not (tmp_path / "cirrus.pid").exists()
        assert psutil.pid_exists(os.getpid())
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


def test_windows_setup_helper_creates_admin_once_and_preserves_it(tmp_path):
    import sqlite3

    from werkzeug.security import check_password_hash

    root = Path.cwd()
    env = {**os.environ, "CIRRUS_DATA_DIR": str(tmp_path)}
    first = subprocess.run(
        [sys.executable, str(root / "scripts/first_run.py")],
        cwd=root,
        env=env,
        input="first-run-admin\nSyntheticTestPassword123!\nSyntheticTestPassword123!\n",
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    assert "Administrator created." in first.stdout
    second = subprocess.run(
        [sys.executable, str(root / "scripts/first_run.py")],
        cwd=root,
        env=env,
        input="",
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert second.returncode == 0
    assert "already exists" in second.stdout
    with sqlite3.connect(tmp_path / "cirrus.sqlite3") as connection:
        users = connection.execute("SELECT username,password,role FROM users").fetchall()
    assert len(users) == 1 and users[0][0] == "first-run-admin" and users[0][2] == "admin"
    assert check_password_hash(users[0][1], "SyntheticTestPassword123!")
