"""Shared WSGI configuration, including optional IIS subpath mounting."""

import os

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

from cirrus import create_app


def build_wsgi():
    app = create_app()
    prefix = os.environ.get("CIRRUS_URL_PREFIX", "").rstrip("/")
    if prefix:
        if not prefix.startswith("/") or "//" in prefix or ".." in prefix:
            raise ValueError("CIRRUS_URL_PREFIX must be a path such as /pulse")
        return app, DispatcherMiddleware(Response("Not found", status=404), {prefix: app})
    return app, app
