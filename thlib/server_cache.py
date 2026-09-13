"""Persistent server-data cache built on the Handler configuration API.

The module owns storage mechanics only.  Search, Tasks, Notes, Messages and
other domain controllers remain responsible for deciding what a cache entry
means and when it must be refreshed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import threading
import time
from typing import Iterable
from urllib.parse import urlsplit


CACHE_DOMAINS = (
    "reference",
    "search",
    "snapshots",
    "relations",
    "tasks",
    "notes",
    "messages",
    "activity",
    "work_hours",
)

DEFAULT_CACHE_PREFERENCES = {
    domain: True for domain in CACHE_DOMAINS
}

DOMAIN_LIMITS = {
    "reference": 128,
    "search": 256,
    "snapshots": 1024,
    "relations": 512,
    "tasks": 256,
    "notes": 512,
    "messages": 64,
    "activity": 256,
    "work_hours": 256,
}

_CACHE_LOCK = threading.RLock()


@dataclass(frozen=True, slots=True)
class CacheToken:
    domain: str
    scope: str
    epoch: int
    domain_epoch: int
    revision: int


def _environment_api():
    from thlib.environment import env_read_config, env_write_config

    return env_read_config, env_write_config


def _identity(project_code: str = "") -> tuple[str, str, str]:
    from thlib.environment import env_server

    return (
        str(env_server.get_server() or "").strip().rstrip("/").casefold(),
        str(env_server.get_user() or "").strip().casefold(),
        str(project_code or "").strip(),
    )


def _scope(project_code: str = "") -> str:
    endpoint, login, project = _identity(project_code)
    parsed = urlsplit(endpoint if "://" in endpoint else "//" + endpoint)
    server = parsed.hostname or endpoint
    encoded = json.dumps(
        (endpoint, login, project), ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")

    def component(value: str, default: str) -> str:
        label = re.sub(r"[^\w.-]+", "_", str(value or "")).strip("_.-")
        return (label or default)[:28]

    return "{0}__{1}__{2}__{3}".format(
        component(project, "global"),
        component(login, "anonymous"),
        component(server, "server"),
        hashlib.sha256(encoded).hexdigest()[:8],
    )


def _entry_digest(key: str) -> str:
    return hashlib.sha256(str(key or "").encode("utf-8")).hexdigest()


def _preferences_payload() -> dict:
    env_read_config, _env_write_config = _environment_api()
    payload = env_read_config(
        filename="data_cache",
        unique_id="ui_conf",
        long_abs_path=True,
    )
    if not isinstance(payload, dict):
        return {}
    if set(payload) != {"enabled"} or not isinstance(
            payload.get("enabled"), dict):
        return {}
    return dict(payload)


def preferences() -> dict[str, bool]:
    payload = _preferences_payload()
    enabled = dict(payload.get("enabled") or {})
    return {
        domain: bool(enabled.get(domain, DEFAULT_CACHE_PREFERENCES[domain]))
        for domain in CACHE_DOMAINS
    }


def domain_enabled(domain: str) -> bool:
    domain = str(domain or "")
    return domain in CACHE_DOMAINS and preferences().get(domain, False)


def _default_control() -> dict:
    return {
        "epoch": 1,
        "domainEpochs": {domain: 1 for domain in CACHE_DOMAINS},
        "revisions": {},
        "cursors": {},
        "scopes": [],
    }


def _read_control() -> dict:
    env_read_config, _env_write_config = _environment_api()
    payload = env_read_config(
        filename="control",
        unique_id="cache/server_data",
        long_abs_path=True,
    )
    if (
        not isinstance(payload, dict)
        or set(payload) != {
            "epoch", "domainEpochs", "revisions", "cursors", "scopes",
        }
    ):
        return _default_control()
    control = _default_control()
    control.update(payload)
    control["domainEpochs"] = {
        domain: max(
            1, int(dict(payload.get("domainEpochs") or {}).get(domain) or 1)
        )
        for domain in CACHE_DOMAINS
    }
    control["revisions"] = dict(payload.get("revisions") or {})
    control["cursors"] = dict(payload.get("cursors") or {})
    control["scopes"] = list(dict.fromkeys(
        str(value or "") for value in payload.get("scopes") or [] if value
    ))
    return control


def _write_control(control: dict) -> None:
    _env_read_config, env_write_config = _environment_api()
    env_write_config(
        control,
        filename="control",
        unique_id="cache/server_data",
        long_abs_path=True,
    )


def _revision(control: dict, scope: str, domain: str) -> int:
    scoped = dict(dict(control.get("revisions") or {}).get(scope) or {})
    return max(0, int(scoped.get(domain) or 0))


def read_cursor(name: str, project_code: str = "") -> str:
    """Read an internal server cursor scoped by endpoint, login and project."""
    with _CACHE_LOCK:
        control = _read_control()
        scoped = dict(dict(control.get("cursors") or {}).get(
            _scope(project_code)
        ) or {})
        return str(scoped.get(str(name or "")) or "")


def write_cursor(name: str, value: str, project_code: str = "") -> None:
    with _CACHE_LOCK:
        control = _read_control()
        scope = _scope(project_code)
        cursors = dict(control.get("cursors") or {})
        scoped = dict(cursors.get(scope) or {})
        scoped[str(name or "")] = str(value or "")
        cursors[scope] = scoped
        control["cursors"] = cursors
        if scope not in control.get("scopes", []):
            control.setdefault("scopes", []).append(scope)
        _write_control(control)


def token(domain: str, project_code: str = "") -> CacheToken | None:
    domain = str(domain or "")
    if domain not in CACHE_DOMAINS or not domain_enabled(domain):
        return None
    with _CACHE_LOCK:
        control = _read_control()
        scope = _scope(project_code)
        return CacheToken(
            domain=domain,
            scope=scope,
            epoch=max(1, int(control.get("epoch") or 1)),
            domain_epoch=max(
                1, int(dict(control.get("domainEpochs") or {}).get(domain) or 1)
            ),
            revision=_revision(control, scope, domain),
        )


def _domain_path(scope: str, domain: str) -> tuple[str, str]:
    return "cache/server_data/{0}".format(scope), domain


def _domain_document_valid(
        document: object, cache_token: CacheToken) -> bool:
    return bool(
        isinstance(document, dict)
        and set(document) == {"domain", "scope", "entries"}
        and document.get("domain") == cache_token.domain
        and document.get("scope") == cache_token.scope
        and isinstance(document.get("entries"), dict)
    )


def _read_entry(
    domain: str,
    key: str,
    project_code: str = "",
    *,
    allow_stale_revision: bool = False,
) -> object | None:
    cache_token = token(domain, project_code)
    if cache_token is None:
        return None
    digest = _entry_digest(key)
    unique_id, filename = _domain_path(
        cache_token.scope, cache_token.domain
    )
    env_read_config, _env_write_config = _environment_api()
    with _CACHE_LOCK:
        document = env_read_config(
            filename=filename,
            unique_id=unique_id,
            long_abs_path=True,
        )
        if not _domain_document_valid(document, cache_token):
            return None
        entry = dict(dict(document.get("entries") or {}).get(digest) or {})
        if (
            set(entry) != {
                "key", "epoch", "domainEpoch", "revision", "updatedAt",
                "value",
            }
            or entry.get("key") != str(key or "")
            or int(entry.get("epoch") or 0) != cache_token.epoch
            or int(entry.get("domainEpoch") or 0) != cache_token.domain_epoch
            or (
                not allow_stale_revision
                and int(entry.get("revision", -1)) != cache_token.revision
            )
        ):
            return None
        return entry.get("value")


def read_entry(
    domain: str,
    key: str,
    project_code: str = "",
) -> object | None:
    return _read_entry(domain, key, project_code)


def read_stale_entry(
    domain: str,
    key: str,
    project_code: str = "",
) -> object | None:
    """Read an older revision without crossing a clear/preference boundary.

    Most consumers require current server data and must use ``read_entry``.
    Projections that remain useful as visibly stale lower bounds may opt into
    this method while they schedule their own authoritative refresh.
    """
    return _read_entry(
        domain, key, project_code, allow_stale_revision=True,
    )


def write_entry(
    domain: str,
    key: str,
    value: object,
    project_code: str = "",
    *,
    expected_token: CacheToken | None = None,
) -> bool:
    domain = str(domain or "")
    cache_token = expected_token or token(domain, project_code)
    if cache_token is None or cache_token.domain != domain:
        return False
    digest = _entry_digest(key)
    unique_id, filename = _domain_path(
        cache_token.scope, cache_token.domain
    )
    env_read_config, env_write_config = _environment_api()
    with _CACHE_LOCK:
        current = token(domain, project_code)
        if current != cache_token:
            return False
        document = env_read_config(
            filename=filename,
            unique_id=unique_id,
            long_abs_path=True,
        )
        entries = (
            dict(document.get("entries") or {})
            if _domain_document_valid(document, cache_token)
            else {}
        )
        entries[digest] = {
            "key": str(key or ""),
            "epoch": cache_token.epoch,
            "domainEpoch": cache_token.domain_epoch,
            "revision": cache_token.revision,
            "updatedAt": time.time(),
            "value": value,
        }
        maximum = max(1, DOMAIN_LIMITS[domain])
        if len(entries) > maximum:
            ordered = sorted(
                entries.items(),
                key=lambda item: float(dict(item[1]).get("updatedAt") or 0.0),
                reverse=True,
            )
            entries = dict(ordered[:maximum])
        env_write_config(
            {
                "domain": domain,
                "scope": cache_token.scope,
                "entries": entries,
            },
            filename=filename,
            unique_id=unique_id,
            long_abs_path=True,
        )
        control = _read_control()
        scopes = list(control.get("scopes") or [])
        if cache_token.scope not in scopes:
            scopes.append(cache_token.scope)
            control["scopes"] = scopes
            _write_control(control)
        return True


def invalidate_domains(
    domains: Iterable[str], project_code: str = ""
) -> list[str]:
    normalized = list(dict.fromkeys(
        str(domain or "") for domain in domains if domain in CACHE_DOMAINS
    ))
    if not normalized:
        return []
    with _CACHE_LOCK:
        control = _read_control()
        scope = _scope(project_code)
        revisions = dict(control.get("revisions") or {})
        scoped = dict(revisions.get(scope) or {})
        for domain in normalized:
            scoped[domain] = max(0, int(scoped.get(domain) or 0)) + 1
        revisions[scope] = scoped
        control["revisions"] = revisions
        if scope not in control.get("scopes", []):
            control.setdefault("scopes", []).append(scope)
        _write_control(control)
    return normalized


def _domains_for_search_type(search_type: str) -> set[str]:
    search_type = str(search_type or "").split("?", 1)[0]
    if search_type in {
        "sthpw/project", "sthpw/login", "sthpw/login_group",
        "sthpw/login_in_group", "sthpw/schema", "sthpw/pipeline",
        "sthpw/search_object", "config/process", "config/widget_config",
    }:
        return {"reference"}
    if search_type in {"sthpw/message", "sthpw/message_log", "sthpw/subscription"}:
        return {"messages"}
    if search_type in {"sthpw/task", "sthpw/status_log"}:
        return {"tasks", "search", "activity"}
    if search_type == "sthpw/note":
        return {"notes", "tasks", "search", "activity"}
    if search_type in {"sthpw/snapshot", "sthpw/file"}:
        # Relation pages may embed child snapshot metadata when expanded.
        return {"snapshots", "relations", "search", "activity"}
    if search_type == "sthpw/work_hour":
        return {"work_hours", "tasks", "activity"}
    if search_type == "sthpw/connection":
        return {"relations", "search", "notes", "messages", "activity"}
    if search_type:
        return {"search", "relations", "activity"}
    return set()


def apply_change_batch(
    changes: Iterable[dict], retired: Iterable[dict] = ()
) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = {}
    for record in list(changes or ()) + list(retired or ()):
        record = dict(record or {})
        project_code = str(record.get("projectCode") or "")
        domains = _domains_for_search_type(record.get("searchType"))
        if domains:
            grouped.setdefault(project_code, set()).update(domains)
    return {
        project_code: invalidate_domains(sorted(domains), project_code)
        for project_code, domains in grouped.items()
    }


def update_preferences(values: dict[str, object]) -> dict[str, bool]:
    normalized = {
        domain: bool(values.get(domain, DEFAULT_CACHE_PREFERENCES[domain]))
        for domain in CACHE_DOMAINS
    }
    with _CACHE_LOCK:
        previous = preferences()
        _env_read_config, env_write_config = _environment_api()
        env_write_config(
            {
                "enabled": normalized,
            },
            filename="data_cache",
            unique_id="ui_conf",
            long_abs_path=True,
        )
        changed = [
            domain for domain in CACHE_DOMAINS
            if previous.get(domain) != normalized.get(domain)
        ]
        if changed:
            control = _read_control()
            epochs = dict(control.get("domainEpochs") or {})
            for domain in changed:
                epochs[domain] = max(1, int(epochs.get(domain) or 1)) + 1
            control["domainEpochs"] = epochs
            _write_control(control)
    return normalized


def clear_all() -> int:
    """Invalidate first, then remove every owned cache document."""
    _env_read_config, env_write_config = _environment_api()
    with _CACHE_LOCK:
        control = _read_control()
        control["epoch"] = max(1, int(control.get("epoch") or 1)) + 1
        control["domainEpochs"] = {
            domain: max(
                1, int(dict(control.get("domainEpochs") or {}).get(domain) or 1)
            ) + 1
            for domain in CACHE_DOMAINS
        }
        control["revisions"] = {}
        control["cursors"] = {}
        env_write_config(
            filename="",
            unique_id="cache/server_data",
            long_abs_path=True,
            remove=True,
        )
        control["scopes"] = []
        _write_control(control)
        return int(control["epoch"])
