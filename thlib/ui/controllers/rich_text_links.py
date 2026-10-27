"""Shared rich-text link handling exposed to QML presentation surfaces."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QDesktopServices

from ..rich_text import linkify_plain_text


class RichTextLinksMixin:
    """Own application-wide conversion and routing of user-authored links."""

    def attach_rich_text_navigation(self, previews, knowledge=None) -> None:
        self._rich_text_previews = previews
        self._rich_text_knowledge = knowledge

    @Slot(str, result=str)
    def rich_text_html(self, value: str) -> str:
        return linkify_plain_text(value)

    @Slot(str)
    def open_rich_link(self, value: str) -> None:
        value = str(value or "").strip()
        if not value:
            return
        if value.startswith('/') and not value.startswith('//') and not any(char.isspace() or ord(char) < 32 or char == '\\' for char in value):
            from thlib.environment import env_server
            from ..server_address import normalize_tactic_server_url
            value = normalize_tactic_server_url(env_server.get_server()).rstrip('/') + value
        knowledge = getattr(self, "_rich_text_knowledge", None)
        if value.startswith("skey://"):
            if knowledge is not None and knowledge.is_knowledge_key(value):
                knowledge.open_search_key(value)
                return
            previews = getattr(self, "_rich_text_previews", None)
            if previews is not None:
                previews.open(value)
            else:
                self.open_search_key(value)
            return
        if value.startswith("tactic-search://"):
            self.search(value)
            return
        if value.startswith(("http://", "https://", "ftp://")):
            from ..custom_urls import open_custom_url
            if open_custom_url(self, value):
                return
            QDesktopServices.openUrl(QUrl(value))
