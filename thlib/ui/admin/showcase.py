"""Private local models for the component workbench; no application user data."""
from pathlib import Path

from PySide6.QtCore import QObject, Property, Slot

from thlib.ui.emoji import EmojiCatalog
from thlib.ui.workspace_models.records import RecordListModel


class ShowcaseServices(QObject):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._users = RecordListModel((
            'login', 'displayName', 'initials', 'avatarUrl', 'avatarColor',
            'groups', 'primaryGroup', 'current', 'retired'))
        self._users.setParent(self)
        self._emoji = EmojiCatalog(Path(__file__).resolve().parents[3], self)

    @Property(QObject, constant=True)
    def users(self) -> RecordListModel:
        return self._users

    @Property(QObject, constant=True)
    def emoji(self) -> EmojiCatalog:
        return self._emoji

    @Slot('QVariantList')
    def setUsers(self, rows: list[dict[str, object]]) -> None:
        self._users.replace(rows)
