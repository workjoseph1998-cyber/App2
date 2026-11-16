"""Stop only the verified runner belonging to this installation."""

import os
import sys
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]


def matches_runner(process, root, executable):
    try:
        args = process.cmdline()
        allowed = {
            Path(executable).resolve(),
            Path(getattr(sys, "_base_executable", executable)).resolve(),
        }
        return (
            len(args) >= 2
            and Path(process.exe()).resolve() in allowed
            and Path(args[1]).resolve() == Path(root).resolve() / "run.py"
            and Path(process.cwd()).resolve() == Path(root).resolve()
        )
    except (psutil.Error, OSError, ValueError):
        return False


def main():
    data = Path(os.environ.get("CIRRUS_DATA_DIR", ROOT / "data"))
    pidfile = data / "cirrus.pid"
    if not pidfile.exists():
        print("No Cirrus PID file. Nothing was stopped.")
        return 0
    try:
        process = psutil.Process(int(pidfile.read_text().strip()))
    except psutil.NoSuchProcess:
        pidfile.unlink(missing_ok=True)
        print("Stale PID file removed. No process was stopped.")
        return 0
    except (ValueError, OSError) as error:
        print(f"Cannot verify the PID file: {error}. Nothing was stopped.")
        return 1
    if not matches_runner(process, ROOT, sys.executable):
        print("Process identity mismatch. Refusing to stop an unrelated application.")
        return 1
    process.terminate()
    try:
        process.wait(timeout=15)
    except psutil.TimeoutExpired:
        print(
            "The verified Cirrus process is still stopping. No additional process was terminated."
        )
        return 1
    pidfile.unlink(missing_ok=True)
    print("This Cirrus installation was stopped. Your other applications were not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
