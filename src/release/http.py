from __future__ import annotations

import ssl
from typing import Any
from urllib.request import urlopen

import certifi


def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def open_url(request: Any, timeout: float = 20) -> Any:
    return urlopen(request, timeout=timeout, context=ssl_context())
