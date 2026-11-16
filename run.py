"""Run only this application, with an exclusive loopback port check."""

import os
import socket
import sys
from pathlib import Path

from waitress import create_server

from wsgi import build_wsgi


def reserve_port(host="127.0.0.1", port=8000):
    """Bind and retain the listener, eliminating a check/start race."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(128)
        return sock
    except OSError as exc:
        sock.close()
        raise RuntimeError(
            f"Port {port} is in use. Stop the other application first; nothing was stopped."
        ) from exc


def check_port(host="127.0.0.1", port=8000):
    with reserve_port(host, port):
        pass


def main():
    listener = None
    try:
        listener = reserve_port()
        app, wsgi = build_wsgi()
        server = create_server(
            wsgi, sockets=[listener], threads=4, clear_untrusted_proxy_headers=True
        )
    except (RuntimeError, OSError, ValueError) as exc:
        if listener is not None:
            listener.close()
        print(str(exc), file=sys.stderr)
        return 1
    pid = Path(app.config["DATA_DIR"]) / "cirrus.pid"
    pid.write_text(str(os.getpid()))
    print("Cirrus Pulse + AssetPass listening on 127.0.0.1:8000", flush=True)
    try:
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        if pid.exists() and pid.read_text() == str(os.getpid()):
            pid.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
