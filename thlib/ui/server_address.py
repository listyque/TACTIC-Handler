"""Canonical TACTIC server-address handling for configuration entry points."""

from __future__ import annotations

from urllib.parse import urlparse


def normalize_tactic_server_url(value: object) -> str:
    """Return the root server URL accepted by the TACTIC client stub."""
    server_url = str(value or "").strip()
    if not server_url:
        return ""
    while server_url.endswith("/") and not server_url.endswith("://"):
        server_url = server_url[:-1]
    if "://" not in server_url:
        server_url = f"http://{server_url}"
    else:
        scheme, separator, remainder = server_url.partition("://")
        server_url = f"{scheme.lower()}{separator}{remainder}"
    if server_url.lower().endswith("/tactic"):
        server_url = server_url[:-7].rstrip("/")
    return server_url


def is_valid_tactic_server_url(value: object) -> bool:
    """Validate a normalized root URL without contacting the server."""
    parsed = urlparse(normalize_tactic_server_url(value))
    hostname = str(parsed.hostname or "")
    try:
        parsed.port
    except ValueError:
        return False
    return bool(
        parsed.scheme in {"http", "https"}
        and hostname
        and not any(
            character.isspace() or character in {",", "/"}
            for character in hostname
        )
        and parsed.path in {"", "/"}
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    )
