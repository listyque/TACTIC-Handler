"""Declared ownership and invalidation rules for retained hot UI data.

These small runtime projections remain with their lifecycle owners. Persistent
raw TACTIC query payloads are instead owned by :mod:`thlib.server_cache`; the
two layers must not persist unsynchronized copies of the same server records.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CachePolicy:
    name: str
    owner: str
    key: str
    ttl_seconds: int | None
    invalidation: str
    explicit_refresh: str
    stale_allowed: bool
    maximum_entries: int


CACHE_POLICIES = (
    CachePolicy(
        name="message_history",
        owner="MessagesController",
        key="server + login + conversation code",
        ttl_seconds=None,
        invalidation=(
            "login/server change, conversation deletion, message mutation, "
            "or a newer server timestamp"
        ),
        explicit_refresh="MessagesController.refresh_current",
        stale_allowed=True,
        maximum_entries=12,
    ),
    CachePolicy(
        name="skey_preview",
        owner="SearchKeyPreviewResolver",
        key="server + login + code-based skey",
        ttl_seconds=None,
        invalidation="scope change by key; individual retry after an error",
        explicit_refresh="SearchKeyPreviewResolver.retry",
        stale_allowed=True,
        maximum_entries=768,
    ),
    CachePolicy(
        name="project_preview",
        owner="ProjectModel",
        key="project code",
        ttl_seconds=None,
        invalidation="project list replacement or repository preview refresh",
        explicit_refresh="ProjectModel.refresh_previews",
        stale_allowed=True,
        maximum_entries=256,
    ),
    CachePolicy(
        name="search_tab_session",
        owner="ApplicationController.NavigationMixin",
        key="project code + section key + tab id",
        ttl_seconds=None,
        invalidation="configuration clear, project schema reload, or user edit",
        explicit_refresh="ApplicationController.flush_search_cache",
        stale_allowed=True,
        maximum_entries=128,
    ),
    CachePolicy(
        name="result_controls",
        owner="WorkspaceItemModel.PresentationMixin",
        key="loaded node id + task/process payload",
        ttl_seconds=None,
        invalidation="node replacement, task/detail refresh, or model reset",
        explicit_refresh="ApplicationController.refresh_selected_item",
        stale_allowed=False,
        maximum_entries=5000,
    ),
)


def cache_policy(name: str) -> CachePolicy:
    return next(policy for policy in CACHE_POLICIES if policy.name == name)
