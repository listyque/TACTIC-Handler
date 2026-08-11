"""Public WorkspaceItemModel model."""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, Qt

from .results_types import WorkspaceNode
from .results_records import RecordsMixin
from .results_presentation import PresentationMixin
from .results_tree_state import TreeStateMixin
from .results_loading import LoadingMixin
from .results_navigation import NavigationMixin


class WorkspaceItemModel(
        RecordsMixin,
        PresentationMixin,
        TreeStateMixin,
        LoadingMixin,
        NavigationMixin,
        QAbstractListModel):
    SearchKeyRole = Qt.UserRole + 1

    CodeRole = Qt.UserRole + 2

    TitleRole = Qt.UserRole + 3

    SubtitleRole = Qt.UserRole + 4

    StatusRole = Qt.UserRole + 5

    AccentRole = Qt.UserRole + 6

    CommentsRole = Qt.UserRole + 7

    TasksRole = Qt.UserRole + 8

    ValuesRole = Qt.UserRole + 9

    NodeIdRole = Qt.UserRole + 10

    NodeTypeRole = Qt.UserRole + 11

    DepthRole = Qt.UserRole + 12

    ExpandedRole = Qt.UserRole + 13

    HasChildrenRole = Qt.UserRole + 14

    ContextRole = Qt.UserRole + 15

    VersionRole = Qt.UserRole + 16

    FilePathRole = Qt.UserRole + 17

    FileSizeRole = Qt.UserRole + 18

    ChipsRole = Qt.UserRole + 19

    ParentIdRole = Qt.UserRole + 20

    ProcessRole = Qt.UserRole + 21

    AuthorRole = Qt.UserRole + 22

    TimestampRole = Qt.UserRole + 23

    RevisionRole = Qt.UserRole + 24

    RepositoryRole = Qt.UserRole + 25

    PreviewUrlRole = Qt.UserRole + 26

    RelationshipRole = Qt.UserRole + 27

    WatchStateRole = Qt.UserRole + 28

    FileExistsRole = Qt.UserRole + 29

    IsLatestRole = Qt.UserRole + 30

    IsVersionlessRole = Qt.UserRole + 31

    IsMultipleRole = Qt.UserRole + 32

    NeedsSyncRole = Qt.UserRole + 33

    ChildCountRole = Qt.UserRole + 34

    ControlsRole = Qt.UserRole + 35

    ProgressRole = Qt.UserRole + 36

    LoadingRole = Qt.UserRole + 37

    RepositoryColorRole = Qt.UserRole + 38

    PreviewRevealedRole = Qt.UserRole + 39

    PreviewRequestedRole = Qt.UserRole + 40

    def __init__(self) -> None:
        super().__init__()
        self._roots: list[WorkspaceNode] = []
        self._items: list[WorkspaceNode] = []
        self._row_by_node_id: dict[str, int] = {}
        self._nodes: dict[str, WorkspaceNode] = {}
        self._stype = None
        self._process_ignore: dict = {}
        self.repository_sync = None
        self._pending_preview_paths: dict[str, str] = {}
        self._failed_preview_tokens: set[str] = set()
        self._role_attributes = {
            self.SearchKeyRole: "search_key",
            self.CodeRole: "code",
            self.TitleRole: "title",
            self.SubtitleRole: "subtitle",
            self.StatusRole: "status",
            self.AccentRole: "accent",
            self.CommentsRole: "comments",
            self.TasksRole: "tasks",
            self.ValuesRole: "values",
            self.NodeIdRole: "node_id",
            self.NodeTypeRole: "node_type",
            self.DepthRole: "depth",
            self.ExpandedRole: "expanded",
            self.HasChildrenRole: "has_children",
            self.ContextRole: "context",
            self.VersionRole: "version",
            self.FilePathRole: "file_path",
            self.FileSizeRole: "file_size",
            self.ChipsRole: "chips",
            self.ParentIdRole: "parent_id",
            self.ProcessRole: "process",
            self.AuthorRole: "author",
            self.TimestampRole: "timestamp",
            self.RevisionRole: "revision",
            self.RepositoryRole: "repository",
            self.RelationshipRole: "relationship",
            self.WatchStateRole: "watch_state",
            self.FileExistsRole: "file_exists",
            self.IsLatestRole: "is_latest",
            self.IsVersionlessRole: "is_versionless",
            self.IsMultipleRole: "is_multiple",
            self.NeedsSyncRole: "needs_sync",
            self.ChildCountRole: "child_count",
            self.ProgressRole: "progress_items",
            self.LoadingRole: "loading",
            self.RepositoryColorRole: "repository_color",
            self.PreviewRevealedRole: "preview_revealed",
            self.PreviewRequestedRole: "preview_requested",
        }
