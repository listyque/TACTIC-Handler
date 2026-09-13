from __future__ import annotations

import os
import json
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import time
from types import ModuleType
import unittest
from unittest.mock import patch

import shiboken6

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
if os.name == "nt":
    os.environ.setdefault(
        "QT_QPA_FONTDIR", str(Path(os.environ["WINDIR"]) / "Fonts")
    )

from PySide6.QtCore import (
    QCoreApplication, QEvent, QObject, QPoint,
    QPointF, Property, Qt, QUrl, Signal, Slot,
    qInstallMessageHandler,
)
from PySide6.QtGui import (
    QFont, QGuiApplication, QImage, QTextCursor, QTextDocument,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.rich_text import (
    fit_rich_html_images,
    headings_from_html,
    linkify_plain_text,
    markdown_from_rich_html,
    plain_text_from_html,
    rich_text_blocks,
    sanitize_rich_html,
)
from thlib.ui.rich_text_document import (
    RichTextDocumentController,
    plain_text_from_markdown,
    rich_html_from_markdown,
)
from thlib.ui.knowledge import KnowledgeController
from thlib.ui.knowledge_api import knowledge_request
from thlib.ui.localization import CatalogTranslator
from thlib.ui.message_attachments import AttachmentUploadController
from thlib.ui.workspace_models.records import RecordListModel
from thlib import tactic_query
from tests.qt_application import gui_test_application
from tests.support.async_scenarios import DeferredPool


class _KnowledgeStub(QObject):
    stateChanged = Signal()
    editorDocumentChanged = Signal()

    def __init__(self):
        super().__init__()
        self._document = {
            "title": "Pipeline guide",
            "description": "How to publish",
            "kind": "article",
            "parentCode": "",
            "contentMarkdown": "# Publish\n\nUse skey://demo/assets?code=A1",
            "contentText": "Publish Use asset A1",
        }
        self._editing = False
        self._creating = False
        self._local_draft = False
        self._organization_dirty = False
        self._dirty = True
        self._error = ""
        self._identity = "DOC0001"
        self._navigation_identity = self._identity
        self._open_article_pending = False
        self.article_open_acknowledgements = 0
        self._table_of_contents = None
        self._article_metadata = {
            "author": "admin",
            "authorDisplay": "Admin Pretty Name",
            "createdLabel": "30 August 2026, 10:00:00",
            "updatedLabel": "31 August 2026, 12:00:00",
        }
        self._history_model = RecordListModel((
            "revisionId", "timestampPretty", "timestampFull", "actor",
            "actorDisplay", "summary", "current", "selected",
        ), [{
            "revisionId": "TX2",
            "timestampPretty": "Just now",
            "timestampFull": "31 August 2026, 12:00:00",
            "actor": "admin",
            "actorDisplay": "Admin Pretty Name",
            "summary": "Changed: Content",
            "current": True,
            "selected": False,
        }, {
            "revisionId": "TX1",
            "timestampPretty": "Yesterday",
            "timestampFull": "30 August 2026, 10:00:00",
            "actor": "artist",
            "actorDisplay": "Anna Artist",
            "summary": "Article created",
            "current": False,
            "selected": False,
        }])
        self._history_preview = {}
        self.history_load_calls = 0
        self.history_preview_calls = []
        self._parent_section = {
            "identity": "", "title": "", "description": "",
        }
        self._references = []
        self._linked_objects = []
        self._uploaded_attachments = RecordListModel((
            "token", "snapshotKey", "title", "extension", "sizeText",
            "previewUrl", "webUrl", "isImage",
        ))
        self._selected_link_candidates = []
        self.selected_identities = []
        self.create_calls = []
        self.delete_calls = 0
        self.copied_attachment_tokens = []
        self.removed_attachment_tokens = []
        self.opened_links = []
        self.opened_references = []
        self.move_calls = []
        self.toggle_calls = []
        self.save_calls = 0
        self.save_draft_calls = 0
        self.unlinked_object_keys = []
        self.display_width_requests = []
        self.image_source_candidates = {}

    @Property(bool, notify=stateChanged)
    def initialized(self): return True

    @Property(bool, notify=stateChanged)
    def canInitialize(self): return False

    @Property(str, notify=stateChanged)
    def projectCode(self): return "demo"

    @Property(bool, notify=stateChanged)
    def canEdit(self): return True

    @Property(bool, notify=stateChanged)
    def editing(self): return self._editing

    @Property(bool, notify=stateChanged)
    def creating(self): return self._creating

    @Property(bool, notify=stateChanged)
    def draft(self): return bool(self._document.get("draft"))

    @Property(bool, notify=stateChanged)
    def localDraft(self): return self._local_draft

    @Property(QObject, constant=True)
    def uploadedAttachmentModel(self): return self._uploaded_attachments

    @Property(bool, notify=stateChanged)
    def organizationDirty(self): return self._organization_dirty

    @Property(bool, notify=stateChanged)
    def dirty(self): return self._dirty

    @Property(bool, notify=stateChanged)
    def busy(self): return False

    @Property(str, notify=stateChanged)
    def error(self): return self._error

    @Property(str, notify=stateChanged)
    def query(self): return ""

    @Property(str, notify=stateChanged)
    def identity(self): return self._identity

    @Property(str, notify=stateChanged)
    def navigationIdentity(self): return self._navigation_identity

    @Property(bool, notify=stateChanged)
    def openArticlePending(self): return self._open_article_pending

    @Slot()
    def acknowledge_article_open(self):
        if not self._open_article_pending:
            return
        self._open_article_pending = False
        self.article_open_acknowledgements += 1
        self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def displayHtml(self):
        return rich_html_from_markdown(self._document["contentMarkdown"])

    @Slot(float, result=str)
    def display_html_for_width(self, maximum_width):
        self.display_width_requests.append(float(maximum_width))
        return rich_html_from_markdown(self._document["contentMarkdown"])

    @Property("QVariantMap", notify=stateChanged)
    def document(self): return dict(self._document)

    @Property(str, notify=editorDocumentChanged)
    def editorMarkdown(self):
        return str(self._document.get("contentMarkdown") or "")

    @Property(str, notify=editorDocumentChanged)
    def editorHtml(self):
        return KnowledgeController._editor_document(self.editorMarkdown)[0]

    @Property("QVariantList", notify=editorDocumentChanged)
    def editorImageStorageSources(self):
        return KnowledgeController._editor_document(self.editorMarkdown)[1]

    @Property(int, notify=stateChanged)
    def readingMinutes(self): return 3

    @Property("QVariantMap", notify=stateChanged)
    def articleMetadata(self): return dict(self._article_metadata)

    @Property(QObject, constant=True)
    def historyModel(self): return self._history_model

    @Property(bool, notify=stateChanged)
    def historyLoaded(self): return True

    @Property(bool, notify=stateChanged)
    def historyLoading(self): return False

    @Property(int, notify=stateChanged)
    def historyCount(self): return self._history_model.rowCount()

    @Property(bool, notify=stateChanged)
    def historyPreviewActive(self): return bool(self._history_preview)

    @Property("QVariantMap", notify=stateChanged)
    def historyPreview(self): return dict(self._history_preview)

    @Property("QVariantMap", notify=stateChanged)
    def viewerDocument(self):
        return dict(self._history_preview.get("document") or self._document)

    @Property("QVariantMap", notify=stateChanged)
    def viewerArticleMetadata(self):
        return dict(
            self._history_preview.get("articleMetadata")
            or self._article_metadata
        )

    @Property("QVariantList", notify=stateChanged)
    def viewerTableOfContents(self):
        document = self.viewerDocument
        if document.get("kind") == "section":
            return self.tableOfContents
        return headings_from_html(rich_html_from_markdown(
            document.get("contentMarkdown") or ""
        ))

    @Property(int, notify=stateChanged)
    def viewerReadingMinutes(self): return 3

    @Slot(float, result=str)
    def viewer_html_for_width(self, maximum_width):
        self.display_width_requests.append(float(maximum_width))
        return rich_html_from_markdown(
            self.viewerDocument.get("contentMarkdown") or ""
        )

    @Slot(float, result="QVariantList")
    def viewer_blocks_for_width(self, maximum_width):
        self.display_width_requests.append(float(maximum_width))
        blocks = rich_text_blocks(
            rich_html_from_markdown(
                self.viewerDocument.get("contentMarkdown") or ""
            ),
            maximum_width,
        )
        for block in blocks:
            if block.get("kind") == "image":
                source = str(block.get("source") or "")
                block["sources"] = list(
                    self.image_source_candidates.get(source, [source])
                )
        return blocks

    @Slot(result="QVariantList")
    def viewer_blocks(self):
        self.display_width_requests.append("intrinsic")
        blocks = rich_text_blocks(
            rich_html_from_markdown(
                self.viewerDocument.get("contentMarkdown") or ""
            )
        )
        for block in blocks:
            if block.get("kind") == "image":
                source = str(block.get("source") or "")
                block["sources"] = list(
                    self.image_source_candidates.get(source, [source])
                )
        return blocks

    @Slot(result=bool)
    def load_history(self):
        self.history_load_calls += 1
        return True

    @Slot(str, result=bool)
    def preview_history_revision(self, revision_id):
        self.history_preview_calls.append(str(revision_id))
        if revision_id == "TX1":
            self._history_preview = {
                "revisionId": "TX1",
                "timestampFull": "30 August 2026, 10:00:00",
                "actorDisplay": "Anna Artist",
                "document": dict(
                    self._document,
                    title="Earlier pipeline guide",
                    contentMarkdown="# Earlier guide",
                ),
                "articleMetadata": dict(self._article_metadata),
            }
            self.stateChanged.emit()
        return True

    @Slot()
    def clear_history_preview(self):
        self._history_preview = {}
        self.stateChanged.emit()

    @Property("QVariantList", notify=stateChanged)
    def references(self): return list(self._references)

    @Property("QVariantList", notify=stateChanged)
    def linkedObjects(self): return list(self._linked_objects)

    @Property("QVariantList", notify=stateChanged)
    def selectedLinkCandidates(self):
        return list(self._selected_link_candidates)

    @Property("QVariantMap", notify=stateChanged)
    def parentSection(self):
        return dict(self._parent_section)

    @Property("QVariantList", notify=stateChanged)
    def linkableSelectedObjects(self):
        linked = set(self._document.get("linkedSearchKeys") or [])
        return [
            dict(record) for record in self._selected_link_candidates
            if record.get("searchKey") not in linked
        ]

    @Property("QVariantList", notify=stateChanged)
    def tableOfContents(self):
        if self._table_of_contents is not None:
            return list(self._table_of_contents)
        return headings_from_html(rich_html_from_markdown(
            self._document["contentMarkdown"]
        ))

    @Slot()
    def begin_edit(self):
        self._editing = True
        self.stateChanged.emit()

    @Slot(str)
    def set_query(self, _value): pass

    @Slot(str)
    def select(self, value):
        self._identity = str(value)
        self._navigation_identity = self._identity
        self.selected_identities.append(self._identity)
        self.stateChanged.emit()

    @Slot(str)
    def toggle_section(self, value):
        self.toggle_calls.append(str(value))

    @Slot(str, str, str, result=bool)
    def move_entry(self, source, target, placement):
        self.move_calls.append((source, target, placement))
        self._organization_dirty = True
        self.stateChanged.emit()
        return True

    @Slot()
    def save_organization(self): self._organization_dirty = False

    @Slot()
    def discard_organization(self): self._organization_dirty = False

    @Slot(str, str)
    def create(self, kind, parent):
        self.create_calls.append((kind, parent))

    @Slot(result=int)
    def link_selected_objects(self):
        records = self.linkableSelectedObjects
        linked = list(self._document.get("linkedSearchKeys") or [])
        linked.extend(record["searchKey"] for record in records)
        self._document["linkedSearchKeys"] = linked
        self._linked_objects.extend({
            "searchKey": record["searchKey"],
            "status": "ready",
            "kind": "sobject",
            "title": str(record.get("title") or record["searchKey"]),
            "description": str(record.get("description") or ""),
            "previewUrl": "",
        } for record in records)
        self.stateChanged.emit()
        return len(records)

    @Slot(str, result=bool)
    def unlink_object(self, search_key):
        search_key = str(search_key or "")
        linked = list(self._document.get("linkedSearchKeys") or [])
        if search_key not in linked:
            return False
        self._document["linkedSearchKeys"] = [
            value for value in linked if value != search_key
        ]
        self._linked_objects = [
            record for record in self._linked_objects
            if record.get("searchKey") != search_key
        ]
        self.unlinked_object_keys.append(search_key)
        self.stateChanged.emit()
        return True

    @Slot()
    def reload(self): pass

    @Slot()
    def initialize(self): pass

    @Slot()
    def copy_search_key(self): pass

    @Slot(str)
    def open_link(self, value):
        self.opened_links.append(str(value))

    @Slot(str)
    def open_reference(self, value):
        self.opened_references.append(str(value))

    @Slot(str, "QVariant")
    def set_field(self, name, value): self._document[name] = value

    @Slot(str)
    def set_content(self, markdown):
        self._document["contentMarkdown"] = markdown
        self._document["contentText"] = plain_text_from_markdown(markdown)

    @Slot()
    def save(self): self.save_calls += 1

    @Slot()
    def save_draft(self): self.save_draft_calls += 1

    @Slot()
    def discard(self): pass

    @Slot()
    def delete_selected(self): self.delete_calls += 1

    @Slot()
    def dismiss_error(self):
        self._error = ""
        self.stateChanged.emit()

    @Slot(result=bool)
    def upload_attachments(self): return False

    @Slot(result=bool)
    def stash_current_draft(self):
        self._local_draft = True
        self._editing = False
        self.stateChanged.emit()
        return True

    @Slot(result=bool)
    def checkpoint_current_draft(self):
        self._local_draft = True
        self.stateChanged.emit()
        return True

    @Slot(str)
    def copy_attachment_web_url(self, token):
        self.copied_attachment_tokens.append(str(token))

    @Slot(str)
    def remove_attachment(self, token):
        self.removed_attachment_tokens.append(str(token))


class _AttachmentStub(QObject):
    stateChanged = Signal()
    uploaded = Signal(object)
    failed = Signal(str, str)

    def __init__(self, count=0):
        super().__init__()
        self._count = count

    @Property(int, notify=stateChanged)
    def count(self): return self._count

    @Property(bool, notify=stateChanged)
    def busy(self): return False

    @Property(float, notify=stateChanged)
    def progress(self): return 0.0

    @Property(str, notify=stateChanged)
    def error(self): return ""

    @Slot("QVariantList")
    def add_files(self, _values): pass

    @Slot()
    def add_clipboard_image(self): pass

    @Slot(int)
    def remove(self, _index): pass

    @Slot()
    def clear(self): pass

    @Slot()
    def cancel(self): pass

    def activate_context(self, _value): return True

    def retarget_context(self, _value): return True

    def shutdown(self): pass


class _ApplicationStub(QObject):
    project_changed = Signal(str, str)
    selected_node_changed = Signal()

    def __init__(self):
        super().__init__()
        self.current_project_code = "demo"
        self.debug_log = None
        self.selected_result_records = []


class _PreviewStub(QObject):
    @Slot(str)
    def retry(self, _value): pass


class _RichTextInteractionProbe(RichTextDocumentController):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selection_sync_calls = 0
        self.link_lookup_calls = 0
        self.image_fit_calls = []

    @Slot(int, int, int)
    def sync_selection(self, cursor_position, start, end):
        self.selection_sync_calls += 1
        super().sync_selection(cursor_position, start, end)

    @Slot(int, result="QVariantMap")
    @Slot(int, str, result="QVariantMap")
    def link_at(self, position, expected_target=""):
        self.link_lookup_calls += 1
        return super().link_at(position, expected_target)

    @Slot(float, result=bool)
    def fit_images_to_width(self, maximum_width):
        self.image_fit_calls.append(float(maximum_width))
        return super().fit_images_to_width(maximum_width)


class KnowledgeBaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = gui_test_application()
        cls.qml = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        fonts = cls.qml.parent / "assets" / "fonts"

        def glyphs(name):
            values = json.loads((fonts / name).read_text(encoding="utf-8"))
            return {
                key: chr(int(codepoint, 16))
                for key, codepoint in values.items()
            }

        cls.solid_glyphs = glyphs(
            "fontawesome5-solid-webfont-charmap.json"
        )
        cls.regular_glyphs = glyphs(
            "fontawesome5-regular-webfont-charmap.json"
        )
        cls.material_glyphs = glyphs(
            "materialdesignicons-webfont-charmap.json"
        )

    def configure_icon_context(self, context):
        context.setContextProperty(
            "fontAwesomeSolidGlyphs", self.solid_glyphs
        )
        context.setContextProperty(
            "fontAwesomeRegularGlyphs", self.regular_glyphs
        )
        context.setContextProperty(
            "materialDesignIconGlyphs", self.material_glyphs
        )

    def test_plain_text_linkification_supports_all_public_schemes(self):
        value = (
            "Object skey://demo/assets?code=A1, web https://example.test, "
            "file ftp://files.example.test/a.mov and tactic-search://demo/preset."
        )
        result = linkify_plain_text(value)
        for target in (
            "skey://demo/assets?code=A1",
            "https://example.test",
            "ftp://files.example.test/a.mov",
            "tactic-search://demo/preset",
        ):
            self.assertIn(f'href="{target}"', result)
        self.assertIn("</a>,", result)

    def test_rich_text_is_sanitized_and_remains_searchable(self):
        source = (
            '<h2 onclick="steal()">Guide</h2>'
            '<script>bad()</script><p>Open '
            '<a href="javascript:bad()">unsafe</a> and '
            'skey://demo/assets?code=A1</p>'
        )
        result = sanitize_rich_html(source)
        self.assertNotIn("onclick", result)
        self.assertNotIn("script", result)
        self.assertNotIn("javascript", result)
        self.assertIn('href="skey://demo/assets?code=A1"', result)
        self.assertEqual(
            plain_text_from_html(result),
            "Guide\nOpen unsafe and skey://demo/assets?code=A1",
        )

    def test_rich_text_headings_build_a_stable_outline(self):
        self.assertEqual(headings_from_html(
            "<h1>Publish</h1><p>Body</p><h2>Checks</h2>"
            "<h2>Checks</h2><h3>Final output</h3>"
            "<h5>Details</h5><h6>Footnote</h6>"
        ), [
            {"title": "Publish", "level": 1, "occurrence": 0},
            {"title": "Checks", "level": 2, "occurrence": 0},
            {"title": "Checks", "level": 2, "occurrence": 1},
            {"title": "Final output", "level": 3, "occurrence": 0},
            {"title": "Details", "level": 5, "occurrence": 0},
            {"title": "Footnote", "level": 6, "occurrence": 0},
        ])

    def test_markdown_is_canonical_and_preserves_visual_editor_features(self):
        source = (
            "# Publish\n\nPlain **bold** *italic* ~~old~~ "
            "<u>underlined</u> and "
            "[Asset](skey://demo/assets?code=A1).\n\n"
            "![Board](https://example.invalid/board.png \"Preview\")"
            "{width=320 height=180 fit=content}\n\n"
            "Centered {align=center}"
        )

        rich_html = rich_html_from_markdown(source)
        stored = markdown_from_rich_html(rich_html)

        self.assertIn("font-weight: 700", rich_html)
        self.assertIn("text-decoration: underline", rich_html)
        self.assertIn('href="skey://demo/assets?code=A1"', rich_html)
        self.assertIn('width="320"', rich_html)
        self.assertIn("max-width: 100%", rich_html)
        self.assertIn("**bold**", stored)
        self.assertIn("<u>underlined</u>", stored)
        self.assertIn("{width=320 height=180 fit=content}", stored)
        self.assertIn("Centered {align=center}", stored)
        self.assertEqual(
            plain_text_from_markdown(source).splitlines()[0], "Publish"
        )

    def test_editor_switches_between_visual_and_markdown_source(self):
        engine = QQmlEngine()
        controller = _KnowledgeStub()
        controller._editing = True
        controller._document["contentMarkdown"] = (
            "# Publish\n\n**Ready** for review\n\n"
            "```python\nprint('ready')\n```"
        )
        rich_text = RichTextDocumentController(engine)
        attachments = _AttachmentStub()
        context = engine.rootContext()
        self.configure_icon_context(context)
        context.setContextProperty(
            "knowledgeAttachments", attachments
        )
        context.setContextProperty(
            "knowledgeAttachmentDraftModel", RecordListModel((
                "token", "title", "path", "size", "fileType",
                "previewUrl", "status", "progress", "error",
                "snapshotKey", "uploadTarget",
            ))
        )
        context.setContextProperty("knowledgeRichText", rich_text)
        context.setContextProperty("skeyPreviewResolver", _PreviewStub())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleEditor.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "width": 900,
            "height": 700,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(900, 700)
        view.setParentItem(window.contentItem())
        window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(window))
        self.application.processEvents()

        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        source_editor = view.findChild(QObject, "knowledgeMarkdownEditor")
        toolbar = view.findChild(QObject, "knowledgeRichTextToolbar")
        self.assertIsNotNone(source_editor)
        self.assertIsNotNone(toolbar)
        markdown_mode = visual_child(
            toolbar, "knowledgeContentMode-markdown"
        )
        visual_mode = visual_child(
            toolbar, "knowledgeContentMode-visual"
        )
        self.assertIsNotNone(markdown_mode)
        self.assertIsNotNone(visual_mode)
        self.assertTrue(markdown_mode.property("visible"))
        text_style = visual_child(toolbar, "knowledgeTextStyle")
        style_menu = view.findChild(QObject, "knowledgeTextStyleMenu")
        list_menu = view.findChild(QObject, "knowledgeListStyleMenu")
        self.assertIsNotNone(text_style)
        self.assertIsNotNone(style_menu)
        self.assertIsNotNone(list_menu)
        self.assertEqual(
            {
                action.get("command")
                for action in style_menu.property("actions").toVariant()
                if action.get("command")
            },
            {f"heading:{level}" for level in range(7)} | {
                "quote", "pullquote", "code-block", "small-text", "divider",
            },
        )
        self.assertEqual(
            {
                action.get("command")
                for action in list_menu.property("actions").toVariant()
            },
            {"bullet", "number", "checklist"},
        )
        table_action = visual_child(
            toolbar, "knowledgeToolbarAction-table"
        )
        self.assertIsNotNone(table_action)
        self.assertEqual(table_action.property("iconName"), "table-view")
        markdown_point = markdown_mode.mapToScene(QPointF(
            markdown_mode.width() / 2,
            markdown_mode.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=markdown_point.toPoint()
        )
        self.application.processEvents()
        self.assertEqual(view.property("contentMode"), "markdown")
        self.assertTrue(source_editor.property("visible"))
        self.assertEqual(
            source_editor.property("text"),
            "# Publish\n\n**Ready** for review\n\n"
            "```python\nprint('ready')\n```",
            rich_text.html(),
        )

        source_editor.setProperty("text", "# Changed\n\n**Body** plain")
        QTest.qWait(400)
        self.assertTrue(controller.localDraft)
        self.assertEqual(
            controller._document["contentMarkdown"],
            "# Changed\n\n**Body** plain",
        )
        visual_point = visual_mode.mapToScene(QPointF(
            visual_mode.width() / 2,
            visual_mode.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=visual_point.toPoint()
        )
        self.application.processEvents()
        self.assertEqual(view.property("contentMode"), "visual")
        self.assertEqual(
            controller._document["contentMarkdown"],
            "# Changed\n\n**Body** plain",
        )
        self.assertIn("font-weight: 700", rich_text.html())

        editor = view.findChild(QObject, "knowledgeRichTextEditor")
        bold_action = visual_child(
            toolbar, "knowledgeToolbarAction-bold"
        )
        self.assertIsNotNone(editor)
        self.assertIsNotNone(bold_action)
        bold_action.setProperty("duplicateWindow", 0)
        document = rich_text._live_document()
        insertion_position = document.toPlainText().index("plain") + 2
        editor.forceActiveFocus()
        editor.setProperty("cursorPosition", insertion_position)
        QTest.qWait(120)
        self.assertFalse(bold_action.property("formatChecked"))
        bold_point = bold_action.mapToScene(QPointF(
            bold_action.width() / 2,
            bold_action.height() / 2,
        ))
        QTest.mouseClick(window, Qt.LeftButton, pos=bold_point.toPoint())
        self.application.processEvents()
        self.assertTrue(bold_action.property("formatChecked"))
        QTest.keyClick(window, Qt.Key_X)
        self.application.processEvents()
        self.assertTrue(bold_action.property("formatChecked"))
        QTest.mouseClick(window, Qt.LeftButton, pos=bold_point.toPoint())
        self.application.processEvents()
        self.assertFalse(bold_action.property("formatChecked"))
        QTest.keyClick(window, Qt.Key_Y)
        self.application.processEvents()
        bold_character = QTextCursor(document)
        bold_character.setPosition(insertion_position)
        bold_character.setPosition(
            insertion_position + 1, QTextCursor.KeepAnchor
        )
        plain_character = QTextCursor(document)
        plain_character.setPosition(insertion_position + 1)
        plain_character.setPosition(
            insertion_position + 2, QTextCursor.KeepAnchor
        )
        self.assertGreaterEqual(
            bold_character.charFormat().fontWeight(), QFont.DemiBold
        )
        self.assertLess(
            plain_character.charFormat().fontWeight(), QFont.DemiBold,
            document.toHtml(),
        )
        self.assertFalse(bold_action.property("formatChecked"))
        body_position = document.toPlainText().index("Body") + 1
        body_rect = editor.positionToRectangle(body_position)
        body_point = editor.mapToScene(QPointF(
            body_rect.x() + 1,
            body_rect.y() + body_rect.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=body_point.toPoint()
        )
        QTest.qWait(120)
        self.assertTrue(bold_action.property("formatChecked"))
        plain_rect = editor.positionToRectangle(insertion_position + 2)
        plain_point = editor.mapToScene(QPointF(
            plain_rect.x() + plain_rect.width() + 1,
            plain_rect.y() + plain_rect.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=plain_point.toPoint()
        )
        QTest.qWait(120)
        self.assertFalse(bold_action.property("formatChecked"))

        style_menu.triggered.emit("heading:4")
        self.application.processEvents()
        self.assertEqual(rich_text.formatState["heading"], 4)
        self.assertTrue(next(
            action["checked"]
            for action in style_menu.property("actions").toVariant()
            if action.get("command") == "heading:4"
        ))
        style_menu.triggered.emit("heading:4")
        self.application.processEvents()
        self.assertEqual(rich_text.formatState["heading"], 0)

        table_point = table_action.mapToScene(QPointF(
            table_action.width() / 2,
            table_action.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=table_point.toPoint()
        )
        self.application.processEvents()
        self.assertIn("| --- | --- | --- |", rich_text.markdown())

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        theme.deleteLater()
        engine.deleteLater()
        self.application.processEvents()

    def test_native_document_bridge_formats_without_web_engine(self):
        document = QTextDocument()
        document.setPlainText("select me")
        bridge = RichTextDocumentController()
        bridge.attach(document)
        bridge.sync_selection(9, 0, 9)
        bridge.toggle_bold()
        bridge.insert_link("skey://demo/assets?code=A1", "Asset")
        self.assertIn("font-weight", bridge.html())
        self.assertIn("skey://demo/assets?code=A1", bridge.html())
        bridge.insert_link("javascript:alert(1)", "Unsafe")
        self.assertNotIn("javascript", bridge.html())

        bridge.sync_selection(0, 0, 0)
        bridge.set_heading(6)
        self.assertIn("<h6", bridge.html())
        bridge.set_heading(6)
        self.assertNotIn("<h6", bridge.html())

    def test_visual_format_state_follows_selection_and_typed_text(self):
        document = QTextDocument()
        document.setPlainText("plain bold")
        bridge = RichTextDocumentController()
        bridge.attach(document)

        bridge.sync_selection(10, 6, 10)
        bridge.toggle_bold()
        self.assertTrue(bridge.formatState["bold"])
        bridge.sync_selection(2, 2, 2)
        self.assertFalse(bridge.formatState["bold"])
        bridge.sync_selection(8, 8, 8)
        self.assertTrue(bridge.formatState["bold"])

        document.clear()
        bridge.sync_selection(0, 0, 0)
        bridge.toggle_bold()
        self.assertTrue(bridge.formatState["bold"])
        cursor = QTextCursor(document)
        cursor.insertText("B")
        bridge.sync_selection(1, 1, 1)
        self.assertTrue(bridge.formatState["bold"])
        bridge.toggle_bold()
        cursor.setPosition(1)
        cursor.insertText("n")
        bold = QTextCursor(document)
        bold.setPosition(0)
        bold.setPosition(1, QTextCursor.KeepAnchor)
        normal = QTextCursor(document)
        normal.setPosition(1)
        normal.setPosition(2, QTextCursor.KeepAnchor)
        self.assertGreaterEqual(bold.charFormat().fontWeight(), QFont.DemiBold)
        self.assertLess(normal.charFormat().fontWeight(), QFont.DemiBold)
        self.assertFalse(bridge.formatState["bold"])

    def test_stale_typing_change_does_not_address_past_document_end(self):
        document = QTextDocument()
        bridge = RichTextDocumentController()
        bridge.attach(document)
        bridge.sync_selection(0, 0, 0)
        bridge.toggle_bold()
        messages = []
        previous_handler = qInstallMessageHandler(
            lambda _kind, _context, message: messages.append(str(message))
        )
        try:
            bridge._document_contents_changed(0, 0, 1)
        finally:
            qInstallMessageHandler(previous_handler)

        self.assertFalse(any(
            "QTextCursor::setPosition" in message for message in messages
        ))
        self.assertIsNone(bridge._typing_format)
        self.assertEqual(bridge._typing_position, -1)

    def test_native_document_bridge_inserts_markdown_blocks(self):
        document = QTextDocument()
        bridge = RichTextDocumentController()
        bridge.attach(document)

        document.setPlainText("Quoted")
        bridge.sync_selection(6, 0, 6)
        bridge.set_quote("pull")
        self.assertEqual(bridge.markdown(), "> Quoted {align=center}")
        self.assertTrue(bridge.formatState["pullQuote"])
        self.assertIn("background-color", bridge.html())
        self.assertIn(
            "background-color", rich_html_from_markdown("> Reopened")
        )
        bridge.set_quote("pull")
        self.assertFalse(bridge.formatState["pullQuote"])
        self.assertEqual(bridge.markdown(), "Quoted")

        document.setPlainText("Switch")
        bridge.sync_selection(6, 0, 6)
        bridge.set_heading(4)
        bridge.set_quote("quote")
        self.assertEqual(bridge.markdown(), "> Switch")

        document.setPlainText("Code")
        bridge.sync_selection(4, 0, 4)
        bridge.set_code_block()
        self.assertEqual(bridge.markdown(), "```\nCode\n```")
        self.assertTrue(bridge.formatState["codeBlock"])
        self.assertIn("background-color", bridge.html())
        bridge.set_code_block()
        self.assertFalse(bridge.formatState["codeBlock"])
        self.assertEqual(bridge.markdown(), "Code")

        font = QFont(document.defaultFont())
        font.setPointSizeF(11.0)
        document.setDefaultFont(font)
        document.setPlainText("Small")
        bridge.sync_selection(5, 0, 5)
        bridge.set_small_text()
        self.assertEqual(bridge.markdown(), "<small>Small</small>")
        bridge.set_small_text()
        self.assertFalse(bridge.formatState["smallText"])
        self.assertEqual(bridge.markdown(), "Small")

        document.setPlainText("Task")
        bridge.sync_selection(4, 0, 4)
        bridge.toggle_check_list()
        self.assertEqual(bridge.markdown(), "- [ ] Task")
        blocks = rich_text_blocks(rich_html_from_markdown(bridge.markdown()))
        self.assertEqual(blocks[0]["listCheckState"], 0)
        bridge.toggle_check_list()
        self.assertEqual(bridge.markdown(), "Task")
        self.assertEqual(bridge.formatState["listStyle"], "")

        document.setPlainText("List")
        bridge.sync_selection(4, 0, 4)
        bridge.toggle_list("bullet")
        self.assertEqual(bridge.formatState["listStyle"], "bullet")
        bridge.toggle_list("bullet")
        self.assertEqual(bridge.markdown(), "List")
        self.assertEqual(bridge.formatState["listStyle"], "")

        document.clear()
        bridge.sync_selection(0, 0, 0)
        bridge.insert_divider()
        self.assertEqual(bridge.markdown(), "---")

        document.clear()
        bridge.sync_selection(0, 0, 0)
        bridge.insert_table()
        self.assertIn("| --- | --- | --- |", bridge.markdown())

    def test_existing_link_can_be_discovered_and_edited_atomically(self):
        document = QTextDocument()
        document.setHtml(
            '<p>Open <a href="https://example.test/old">Old label</a> now</p>'
        )
        bridge = RichTextDocumentController()
        bridge.attach(document)
        link_start = document.toPlainText().index("Old label")

        details = bridge.link_at(
            link_start + 2, "https://example.test/old"
        )

        self.assertEqual(details, {
            "start": link_start,
            "end": link_start + len("Old label"),
            "target": "https://example.test/old",
            "label": "Old label",
        })
        self.assertTrue(bridge.update_link(
            details["start"], details["end"],
            "skey://demo/assets?code=HERO", "Hero asset",
        ))
        edited = bridge.html()
        self.assertIn('href="skey://demo/assets?code=HERO"', edited)
        self.assertIn("Hero asset", edited)
        self.assertNotIn("Old label", edited)
        self.assertFalse(bridge.update_link(
            details["start"], details["end"],
            "javascript:alert(1)", "Unsafe",
        ))

    def test_native_image_insert_and_resize_use_bounded_html_dimensions(self):
        document = QTextDocument()
        bridge = RichTextDocumentController()
        bridge.attach(document)

        bridge.insert_image(
            "https://example.com/large.png", "Large image", 320.0
        )
        self.assertIn('width="320"', bridge.html())
        self.assertTrue(bridge.imageSelected)
        self.assertEqual(bridge.selectedImageWidth, 320.0)

        bridge.begin_image_resize(320.0, 180.0)
        self.assertTrue(bridge.resize_selected_image(160.0, 640.0))
        resized = bridge.html()
        self.assertIn('width="160"', resized)
        self.assertIn('height="90"', resized)

        self.assertTrue(bridge.resize_selected_image(900.0, 640.0))
        self.assertIn('width="640"', bridge.html())

        self.assertTrue(bridge.resize_selected_image(32.0, 640.0))
        self.assertIn('width="32"', bridge.html())

    def test_editor_image_preview_keeps_the_permanent_storage_url(self):
        document = QTextDocument()
        bridge = RichTextDocumentController()
        bridge.attach(document)
        permanent = "https://example.test/article/original.png"
        preview = "https://example.test/article/preview.png"

        bridge.insert_image(permanent, "Board", 320.0, preview)

        self.assertIn(preview, document.toHtml())
        stored = bridge.html()
        self.assertIn(permanent, stored)
        self.assertNotIn(preview, stored)

        reopened = QTextDocument()
        reopened.setHtml(stored)
        reopened_bridge = RichTextDocumentController()
        reopened_bridge.attach(reopened)
        self.assertTrue(reopened_bridge.apply_image_display_sources({
            permanent: preview,
        }))
        self.assertIn(preview, reopened.toHtml())
        self.assertIn(permanent, reopened_bridge.html())

    def test_toolbar_format_state_does_not_reenter_the_live_document(self):
        document = QTextDocument()
        document.setHtml("<p><b>Bold</b> text</p>")
        bridge = RichTextDocumentController()
        bridge.attach(document)
        bridge.sync_selection(2, 2, 2)

        with patch.object(
            bridge,
            "_cursor",
            side_effect=AssertionError("QML binding reentered QTextDocument"),
        ):
            self.assertTrue(bridge.formatState["bold"])

        bridge.detach()

    def test_native_image_is_inserted_at_the_synced_text_caret(self):
        document = QTextDocument()
        document.setPlainText("BeforeAfter")
        bridge = RichTextDocumentController()
        bridge.attach(document)
        bridge.sync_selection(6, 6, 6)

        bridge.insert_image(
            "https://example.com/at-caret.png", "At caret", 240.0
        )

        self.assertEqual(bridge.selectedImagePosition, 6)
        rich_html = bridge.html()
        self.assertLess(rich_html.index("Before"), rich_html.index("at-caret.png"))
        self.assertLess(rich_html.index("at-caret.png"), rich_html.index("After"))

    def test_native_image_hit_testing_uses_its_painted_document_bounds(self):
        document = QTextDocument()
        source = QUrl("https://example.com/hit-test.png")
        document.addResource(
            QTextDocument.ImageResource,
            source,
            QImage(320, 180, QImage.Format_ARGB32),
        )
        document.setHtml(
            '<p>Before</p><p><img src="https://example.com/hit-test.png" '
            'width="320" height="180"></p>'
        )
        document.setTextWidth(600.0)
        bridge = RichTextDocumentController()
        bridge.attach(document)
        image_position = next(bridge._image_cursors(document))[2]
        self.assertTrue(bridge.select_image_at(image_position, 560.0))
        image_center = bridge.selectedImageRect.center()
        bridge.clear_image_selection()

        self.assertTrue(bridge.select_image_at_point(
            image_center.x(), image_center.y(), 560.0
        ))
        self.assertEqual(bridge.selectedImagePosition, image_position)

    def test_native_image_move_preserves_fragment_and_is_undoable(self):
        document = QTextDocument()
        document.setHtml(
            '<p>Before <img src="https://example.com/move.png" '
            'width="320" height="180"> after</p>'
        )
        bridge = RichTextDocumentController()
        bridge.attach(document)
        source_position = next(bridge._image_cursors(document))[2]
        self.assertTrue(bridge.select_image_at(source_position, 560.0))

        self.assertTrue(bridge.move_selected_image(0))

        self.assertEqual(bridge.selectedImagePosition, 0)
        moved_html = bridge.html()
        self.assertLess(moved_html.index("move.png"), moved_html.index("Before"))
        self.assertIn('width="320"', moved_html)
        self.assertIn('height="180"', moved_html)

        document.undo()
        restored_html = bridge.html()
        self.assertLess(restored_html.index("Before"), restored_html.index("move.png"))

    def test_existing_image_keeps_article_size_while_editor_fits_it(self):
        document = QTextDocument()
        source = QUrl("https://example.com/large.png")
        document.addResource(
            QTextDocument.ImageResource,
            source,
            QImage(1200, 675, QImage.Format_ARGB32),
        )
        document.setHtml(
            '<p><img src="https://example.com/large.png" '
            'width="1200" height="675"></p>'
        )
        bridge = RichTextDocumentController()
        bridge.attach(document)

        self.assertTrue(bridge.select_image_at(0, 560.0))
        self.assertEqual(bridge.selectedImagePosition, 0)
        self.assertEqual(bridge.selectedImageWidth, 560.0)
        self.assertEqual(bridge.selectedImageHeight, 315.0)
        self.assertEqual(bridge.selectedImageConfiguredWidth, 1200.0)
        self.assertEqual(bridge.selectedImageConfiguredHeight, 675.0)
        self.assertEqual(bridge.selectedImageNaturalWidth, 1200.0)
        self.assertEqual(bridge.selectedImageNaturalHeight, 675.0)
        self.assertTrue(bridge.selectedImageProportional)
        self.assertIn('width="1200"', bridge.html())
        self.assertIn('height="675"', bridge.html())

        self.assertTrue(bridge.resize_selected_image(320.0, 560.0))
        self.assertIn('width="320"', bridge.html())
        self.assertIn('height="180"', bridge.html())
        self.assertNotIn("max-width:", document.toHtml())

        bridge.clear_image_selection()
        self.assertFalse(bridge.imageSelected)

    def test_image_content_width_mode_persists_and_restores_fixed_size(self):
        document = QTextDocument()
        document.setHtml(
            '<p><img src="https://example.com/stretch.png" '
            'width="320" height="180"></p>'
        )
        bridge = RichTextDocumentController()
        bridge.attach(document)
        self.assertTrue(bridge.select_image_at(0, 560.0))
        self.assertFalse(bridge.selectedImageContentWidth)

        self.assertTrue(bridge.set_selected_image_content_width(
            True, 560.0
        ))
        self.assertTrue(bridge.selectedImageContentWidth)
        self.assertEqual(bridge.selectedImageWidth, 560.0)
        self.assertEqual(bridge.selectedImageHeight, 315.0)
        stored_html = bridge.html()
        self.assertIn("max-width: 100%", stored_html)

        fitted_html = fit_rich_html_images(stored_html, 480.0)
        self.assertIn('width="480"', fitted_html)
        self.assertIn('height="270"', fitted_html)

        reopened_document = QTextDocument()
        reopened_document.setHtml(stored_html)
        reopened = RichTextDocumentController()
        reopened.attach(reopened_document)
        self.assertTrue(reopened.select_image_at(0, 400.0))
        self.assertTrue(reopened.selectedImageContentWidth)
        self.assertEqual(reopened.selectedImageWidth, 400.0)
        self.assertEqual(reopened.selectedImageHeight, 225.0)

        self.assertTrue(bridge.set_selected_image_content_width(
            False, 560.0
        ))
        self.assertFalse(bridge.selectedImageContentWidth)
        self.assertEqual(bridge.selectedImageWidth, 320.0)
        self.assertEqual(bridge.selectedImageHeight, 180.0)
        self.assertNotIn("max-width:", document.toHtml())

    def test_editor_image_frame_survives_unrelated_controller_updates(self):
        engine = QQmlEngine()
        controller = _KnowledgeStub()
        controller._editing = True
        controller._document["contentMarkdown"] = markdown_from_rich_html(
            '<p><a href="https://example.test/old">Old label</a></p>'
            '<p><img src="https://example.com/large.png" '
            'width="320" height="180"></p><p>Body text</p>'
        )
        attachments = _AttachmentStub()
        attachment_model = RecordListModel((
            "token", "title", "path", "size", "fileType", "previewUrl",
            "status", "progress", "error", "snapshotKey", "uploadTarget",
        ))
        rich_text = _RichTextInteractionProbe(engine)
        context = engine.rootContext()
        self.configure_icon_context(context)
        context.setContextProperty("knowledgeAttachments", attachments)
        context.setContextProperty(
            "knowledgeAttachmentDraftModel", attachment_model
        )
        context.setContextProperty("knowledgeRichText", rich_text)
        context.setContextProperty("skeyPreviewResolver", _PreviewStub())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleEditor.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "width": 900,
            "height": 700,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(900, 700)
        view.setParentItem(window.contentItem())
        window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(window))
        self.application.processEvents()

        editor = view.findChild(QObject, "knowledgeRichTextEditor")
        frame = view.findChild(QObject, "knowledgeSelectedImageFrame")
        resize_handle = view.findChild(
            QObject, "knowledgeImageResizeHandle"
        )
        content_width = view.findChild(
            QObject, "knowledgeImageContentWidth"
        )
        fixed_width = view.findChild(QObject, "knowledgeImageFixedWidth")
        edit_link = view.findChild(QObject, "knowledgeEditHoveredLink")
        link_target = view.findChild(QObject, "knowledgeLinkTarget")
        link_label = view.findChild(QObject, "knowledgeLinkLabel")
        link_apply = view.findChild(QObject, "knowledgeLinkApply")
        self.assertIsNotNone(editor)
        self.assertIsNotNone(frame)
        self.assertIsNotNone(resize_handle)
        self.assertIsNotNone(content_width)
        self.assertIsNotNone(fixed_width)
        self.assertIsNotNone(edit_link)
        self.assertIsNotNone(link_target)
        self.assertIsNotNone(link_label)
        self.assertIsNotNone(link_apply)
        fit_calls = len(rich_text.image_fit_calls)
        view.setProperty("resizeActive", True)
        for width in (820, 760, 700, 900):
            view.setWidth(width)
            self.application.processEvents()
        self.assertEqual(len(rich_text.image_fit_calls), fit_calls)
        view.setProperty("resizeActive", False)
        self.application.processEvents()
        self.assertEqual(len(rich_text.image_fit_calls), fit_calls + 1)
        rich_text.fit_images_to_width(view.property("imageMaximumWidth"))
        image_position = next(rich_text._image_cursors(
            rich_text._live_document()
        ))[2]
        self.assertTrue(rich_text.select_image_at(
            image_position, 560.0
        ))
        self.application.processEvents()
        image_rect = rich_text.selectedImageRect
        self.assertAlmostEqual(
            frame.x(), editor.property("leftPadding") + image_rect.x(),
            delta=0.5,
        )
        self.assertAlmostEqual(
            frame.y(), editor.property("topPadding") + image_rect.y(),
            delta=0.5,
        )
        self.assertAlmostEqual(frame.width(), image_rect.width(), delta=0.5)
        self.assertAlmostEqual(frame.height(), image_rect.height(), delta=0.5)

        self.assertFalse(content_width.property("checked"))
        self.assertTrue(fixed_width.property("visible"))
        toggle_point = content_width.mapToScene(QPointF(
            content_width.width() / 2,
            content_width.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=toggle_point.toPoint()
        )
        self.application.processEvents()
        self.assertTrue(rich_text.selectedImageContentWidth)
        self.assertEqual(
            rich_text.selectedImageWidth,
            view.property("imageMaximumWidth"),
        )
        self.assertFalse(fixed_width.property("visible"))
        self.assertFalse(resize_handle.property("visible"))
        toggle_point = content_width.mapToScene(QPointF(
            content_width.width() / 2,
            content_width.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=toggle_point.toPoint()
        )
        self.application.processEvents()
        self.assertFalse(rich_text.selectedImageContentWidth)
        self.assertEqual(rich_text.selectedImageWidth, 320.0)
        self.assertTrue(fixed_width.property("visible"))
        self.assertTrue(resize_handle.property("visible"))

        self.assertTrue(rich_text.resize_selected_image(240.0, 560.0))
        edited_html = rich_text.html()
        selected_position = rich_text.selectedImagePosition
        selected_width = rich_text.selectedImageWidth
        controller.stateChanged.emit()
        self.application.processEvents()

        self.assertTrue(rich_text.imageSelected)
        self.assertEqual(rich_text.selectedImagePosition, selected_position)
        self.assertEqual(rich_text.selectedImageWidth, selected_width)
        self.assertEqual(rich_text.html(), edited_html)

        rich_text.clear_image_selection()
        for local_y in range(12, 90, 6):
            for local_x in range(14, 130, 6):
                link_point = editor.mapToScene(QPointF(
                    local_x, local_y
                )).toPoint()
                QTest.mouseMove(window, link_point)
                self.application.processEvents()
                if edit_link.property("visible"):
                    break
            if edit_link.property("visible"):
                break
        self.assertTrue(edit_link.property("visible"))
        edit_point = edit_link.mapToScene(QPointF(
            edit_link.width() / 2,
            edit_link.height() / 2,
        )).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, pos=edit_point)
        self.application.processEvents()
        self.assertEqual(
            link_target.property("text"), "https://example.test/old"
        )
        self.assertEqual(link_label.property("text"), "Old label")
        self.assertEqual(link_apply.property("text"), "Save link")
        link_target.setProperty("text", "skey://demo/assets?code=HERO")
        link_label.setProperty("text", "Hero asset")
        apply_point = link_apply.mapToScene(QPointF(
            link_apply.width() / 2,
            link_apply.height() / 2,
        )).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, pos=apply_point)
        self.application.processEvents()
        updated_html = rich_text.html()
        self.assertIn('href="skey://demo/assets?code=HERO"', updated_html)
        self.assertIn("Hero asset", updated_html)

        document = rich_text._live_document()
        body_position = document.toPlainText().index("Body text")
        body_rect = editor.positionToRectangle(body_position)
        selection_start = editor.mapToScene(QPointF(
            body_rect.x() + 2,
            body_rect.y() + body_rect.height() / 2,
        )).toPoint()
        selection_end = selection_start + QPoint(70, 0)
        sync_calls = rich_text.selection_sync_calls
        link_calls = rich_text.link_lookup_calls
        QTest.mousePress(window, Qt.LeftButton, pos=selection_start)
        for offset in range(10, 71, 10):
            QTest.mouseMove(
                window, selection_start + QPoint(offset, 0), delay=2
            )
        QTest.mouseRelease(window, Qt.LeftButton, pos=selection_end)
        self.application.processEvents()
        self.assertIn("text", editor.property("selectedText"))
        self.assertEqual(rich_text.selection_sync_calls, sync_calls)
        self.assertEqual(rich_text.link_lookup_calls, link_calls)

        window.hide()
        view.setParentItem(None)
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()

    def test_editor_resize_changes_the_rendered_image_geometry(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        image_path = Path(temporary.name) / "editor-resize.png"
        source_image = QImage(330, 320, QImage.Format_ARGB32)
        source_image.fill(0xFFFF00FF)
        self.assertTrue(source_image.save(str(image_path)))

        controller = _KnowledgeStub()
        controller._editing = True
        remote_source = "https://example.invalid/editor-resize.png"
        controller._document["contentMarkdown"] = markdown_from_rich_html(
            (
                '<p>Before image</p>'
                '<p align="center"><img src="%s" width="560" '
                'height="543"></p>'
                '<p>After image</p>'
            ) % remote_source
        )
        controller._uploaded_attachments.replace([{
            "token": "editor-resize",
            "snapshotKey": "skey://sthpw/snapshot?code=SNAP_RESIZE",
            "title": "editor-resize.png",
            "extension": "PNG",
            "sizeText": "2 KB",
            "previewUrl": QUrl.fromLocalFile(str(image_path)).toString(),
            "webUrl": remote_source,
            "isImage": True,
        }])
        attachments = _AttachmentStub()
        attachment_model = RecordListModel((
            "token", "title", "path", "size", "fileType", "previewUrl",
            "status", "progress", "error", "snapshotKey", "uploadTarget",
        ))
        rich_text = RichTextDocumentController()
        engine = QQmlEngine()
        context = engine.rootContext()
        self.configure_icon_context(context)
        context.setContextProperty("knowledgeAttachments", attachments)
        context.setContextProperty(
            "knowledgeAttachmentDraftModel", attachment_model
        )
        context.setContextProperty("knowledgeRichText", rich_text)
        context.setContextProperty("skeyPreviewResolver", _PreviewStub())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleEditor.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "width": 900,
            "height": 700,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(900, 700)
        view.setParentItem(window.contentItem())
        window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(window))
        QTest.qWait(80)

        live_document = rich_text._live_document()
        live_image = next(rich_text._image_cursors(live_document))[1]
        self.assertIn(
            "knowledge_image_placeholder.svg", str(live_image.name())
        )
        self.assertNotIn(remote_source, str(live_image.name()))
        self.assertIn(remote_source, rich_text.markdown())

        def rendered_image_bounds():
            deadline = time.monotonic() + 3.0
            points = []
            while not points and time.monotonic() < deadline:
                capture = window.grabWindow()
                points = [
                    (x, y)
                    for y in range(capture.height())
                    for x in range(capture.width())
                    if (
                        capture.pixelColor(x, y).red() > 245
                        and capture.pixelColor(x, y).green() < 10
                        and capture.pixelColor(x, y).blue() > 245
                    )
                ]
                if not points:
                    QTest.qWait(10)
            self.assertTrue(points)
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            return (
                min(xs), min(ys), max(xs) + 1, max(ys) + 1,
                capture.devicePixelRatio(),
            )

        before = rendered_image_bounds()
        document = rich_text._live_document()
        image_position = next(rich_text._image_cursors(document))[2]
        self.assertGreater(image_position, 0)
        self.assertTrue(rich_text.select_image_at(
            image_position, view.property("imageMaximumWidth")
        ))
        self.assertEqual(rich_text.selectedImagePosition, image_position)
        resize_handle = view.findChild(
            QObject, "knowledgeImageResizeHandle"
        )
        self.assertIsNotNone(resize_handle)
        handle_point = resize_handle.mapToScene(QPointF(
            resize_handle.width() / 2,
            resize_handle.height() / 2,
        )).toPoint()
        QTest.mousePress(window, Qt.LeftButton, pos=handle_point)
        QTest.mouseMove(
            window, handle_point + QPoint(-287, 0), delay=30
        )
        QTest.mouseRelease(
            window, Qt.LeftButton,
            pos=handle_point + QPoint(-287, 0),
        )
        self.application.processEvents()
        self.assertAlmostEqual(rich_text.selectedImageWidth, 273.0, delta=2)
        self.assertIn("width=273", controller._document["contentMarkdown"])
        QTest.qWait(40)
        rich_text.clear_image_selection()
        self.application.processEvents()
        after = rendered_image_bounds()
        device_ratio = after[4]
        image_point = QPoint(
            round((after[0] + after[2]) / (2 * device_ratio)),
            round((after[1] + after[3]) / (2 * device_ratio)),
        )
        QTest.mouseClick(window, Qt.LeftButton, pos=image_point)
        self.application.processEvents()
        self.assertTrue(rich_text.imageSelected)
        image_frame = view.findChild(
            QObject, "knowledgeSelectedImageFrame"
        )
        self.assertIsNotNone(image_frame)
        frame_origin = image_frame.mapToScene(QPointF(0, 0))
        frame_width = image_frame.width()
        frame_height = image_frame.height()

        self.assertGreater(before[2] - before[0], 500)
        self.assertAlmostEqual(
            (after[2] - after[0]) / device_ratio,
            rich_text.selectedImageWidth,
            delta=2,
        )
        self.assertAlmostEqual(
            (after[3] - after[1]) / device_ratio,
            rich_text.selectedImageHeight,
            delta=2,
        )
        self.assertAlmostEqual(
            frame_width, rich_text.selectedImageWidth, delta=1
        )
        self.assertAlmostEqual(
            frame_height, rich_text.selectedImageHeight, delta=1
        )
        self.assertAlmostEqual(
            after[0] / device_ratio, frame_origin.x(), delta=2
        )
        self.assertAlmostEqual(
            after[1] / device_ratio, frame_origin.y(), delta=2
        )
        self.assertNotIn("max-width:", document.toHtml())

        stretch_width = 560.0
        self.assertTrue(rich_text.set_selected_image_content_width(
            True, stretch_width
        ))
        editor = view.findChild(QObject, "knowledgeRichTextEditor")
        editor.setProperty("cursorPosition", image_position + 1)
        rich_text.clear_image_selection()
        self.application.processEvents()
        stretched = rendered_image_bounds()
        self.assertAlmostEqual(
            (stretched[2] - stretched[0]) / stretched[4],
            stretch_width,
            delta=2,
        )

        self.assertTrue(rich_text.select_image_at(
            image_position, stretch_width
        ))
        self.assertTrue(rich_text.set_selected_image_content_width(
            False, stretch_width
        ))
        rich_text.clear_image_selection()
        self.application.processEvents()
        fixed_again = rendered_image_bounds()
        self.assertAlmostEqual(
            (fixed_again[2] - fixed_again[0]) / fixed_again[4],
            273.0,
            delta=2,
        )
        self.assertNotIn("max-width:", document.toHtml())

        window.hide()
        view.setParentItem(None)
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()

    def test_article_view_shrinks_oversized_images_without_upscaling(self):
        source = (
            '<p><img src="https://example.com/large.png" '
            'width="1200" height="675"></p>'
        )

        fitted = fit_rich_html_images(source, 500.0)
        unchanged = fit_rich_html_images(source, 1600.0)

        self.assertIn('width="500"', fitted)
        self.assertIn('height="281.25"', fitted)
        self.assertIn('width="1200"', unchanged)
        self.assertIn('height="675"', unchanged)

    def test_article_view_separates_images_into_responsive_native_blocks(self):
        blocks = rich_text_blocks(
            '<h1>Before</h1><p><strong>Lead</strong>'
            '<img src="https://example.com/large.png" '
            'width="1200" height="675" alt="Board">tail</p>',
            500.0,
        )

        self.assertEqual(
            [block["kind"] for block in blocks],
            ["html", "html", "image", "html"],
        )
        self.assertIn("Before", blocks[0]["plainText"])
        self.assertEqual(blocks[2]["source"], "https://example.com/large.png")
        self.assertEqual(blocks[2]["width"], 500.0)
        self.assertEqual(blocks[2]["height"], 281.25)
        self.assertEqual(blocks[2]["alt"], "Board")
        self.assertIn("tail", blocks[3]["plainText"])

    def test_article_view_uses_small_plain_blocks_until_markup_is_needed(self):
        blocks = rich_text_blocks(
            '<h2 style="margin-left: 0px">'
            '<span style="font-size: x-large; font-weight: 700">'
            'Fast heading</span></h2>'
            '<p style="margin-left: 0px">Plain paragraph</p>'
            '<p><strong>Formatted</strong> paragraph</p>'
            '<p>Open https://example.test/docs</p>'
        )

        self.assertEqual(len(blocks), 4)
        self.assertTrue(blocks[0]["lightweight"])
        self.assertEqual(blocks[0]["headingLevel"], 2)
        self.assertTrue(blocks[1]["lightweight"])
        self.assertFalse(blocks[2]["lightweight"])
        self.assertFalse(blocks[3]["lightweight"])
        self.assertIn('href="https://example.test/docs"', blocks[3]["html"])

    def test_article_view_flattens_plain_lists_into_lightweight_rows(self):
        blocks = rich_text_blocks(
            '<ol start="3"><li>Third</li><li>Fourth'
            '<ul><li>Nested bullet</li></ul></li></ol>'
        )

        self.assertEqual(
            [block["kind"] for block in blocks],
            ["list-item", "list-item", "list-item"],
        )
        self.assertEqual(
            [block["listIndex"] for block in blocks], [3, 4, 1]
        )
        self.assertEqual(
            [block["listLevel"] for block in blocks], [0, 0, 1]
        )
        self.assertEqual(
            [block["listOrdered"] for block in blocks],
            [True, True, False],
        )
        self.assertTrue(all(block["lightweight"] for block in blocks))

    def test_plain_numbered_list_qml_rows_do_not_use_rich_text_layout(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        controller = _KnowledgeStub()
        controller._document["contentMarkdown"] = (
            "1. First item\n2. Second item"
        )
        engine = QQmlEngine()
        self.configure_icon_context(engine.rootContext())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleContent.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "contentWidth": 500.0,
            "width": 500.0,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        self.application.processEvents()

        first = visual_child(view, "knowledgeArticleTextContent-0")
        second = visual_child(view, "knowledgeArticleTextContent-1")
        first_marker = visual_child(view, "knowledgeArticleListMarker-0")
        second_marker = visual_child(view, "knowledgeArticleListMarker-1")
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertIsNotNone(first_marker)
        self.assertIsNotNone(second_marker)
        self.assertFalse(first.property("richText"))
        self.assertFalse(second.property("richText"))
        self.assertEqual(first.property("text"), "First item")
        self.assertEqual(second.property("text"), "Second item")
        self.assertEqual(first_marker.property("text"), "1.")
        self.assertEqual(second_marker.property("text"), "2.")

        view.setProperty("contentWidth", 280.0)
        view.setWidth(280.0)
        self.application.processEvents()
        self.assertLessEqual(first.width(), 242.0)
        self.assertLessEqual(second.width(), 242.0)

        view.deleteLater()
        theme.deleteLater()
        self.application.processEvents()

    def test_intrinsic_article_blocks_preserve_responsive_image_intent(self):
        blocks = rich_text_blocks(
            '<p><img src="https://example.com/large.png" '
            'width="1200" height="675" style="max-width: 100%"></p>'
        )

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["width"], 1200.0)
        self.assertEqual(blocks[0]["height"], 675.0)
        self.assertTrue(blocks[0]["contentWidth"])

    def test_native_article_image_uses_fallback_and_tracks_content_width(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        image_path = Path(temporary.name) / "article.png"
        source_image = QImage(1200, 675, QImage.Format_ARGB32)
        source_image.fill(Qt.red)
        self.assertTrue(source_image.save(str(image_path)))
        local_source = QUrl.fromLocalFile(str(image_path)).toString()
        missing_source = QUrl.fromLocalFile(
            str(Path(temporary.name) / "missing.png")
        ).toString()

        controller = _KnowledgeStub()
        remote_source = "https://example.invalid/article.png"
        controller._document["contentMarkdown"] = (
            f"![Board]({remote_source}){{width=1200 height=675}}"
        )
        controller.image_source_candidates[remote_source] = [
            missing_source, local_source,
        ]
        engine = QQmlEngine()
        self.configure_icon_context(engine.rootContext())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleContent.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "contentWidth": 500.0,
            "width": 500.0,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(500, 400)
        view.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(100)

        article_image = visual_child(view, "knowledgeArticleImage-0")
        image_block = visual_child(view, "knowledgeArticleImageBlock-0")
        self.assertIsNotNone(article_image)
        self.assertIsNotNone(image_block)
        if not image_block.property("imageReady"):
            QTest.qWait(250)
        self.assertTrue(image_block.property("imageReady"))
        self.assertEqual(
            image_block.property("activeImageSource"), local_source
        )
        self.assertEqual(article_image.property("sourceSize").width(), 1280)
        self.assertEqual(article_image.property("sourceSize").height(), 1280)
        self.assertFalse(article_image.property("mipmap"))
        self.assertLessEqual(article_image.width(), 500.0)
        self.assertAlmostEqual(
            article_image.height() / article_image.width(),
            675.0 / 1200.0,
            places=2,
        )
        image_point = article_image.mapToScene(QPointF(
            article_image.width() / 2,
            article_image.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=image_point.toPoint()
        )
        self.application.processEvents()
        self.assertEqual(controller.opened_links, [remote_source])

        decoded_size = article_image.property("sourceSize")
        for width in range(500, 279, -11):
            view.setProperty("contentWidth", float(width))
            view.setWidth(float(width))
            window.resize(width, 400)
            self.application.processEvents()
        resized_article_image = visual_child(
            view, "knowledgeArticleImage-0"
        )
        self.assertIs(resized_article_image, article_image)
        self.assertEqual(
            resized_article_image.property("sourceSize"), decoded_size
        )
        self.assertEqual(
            resized_article_image.property("source").toString(), local_source
        )
        self.assertTrue(image_block.property("imageReady"))
        self.assertLessEqual(resized_article_image.width(), 280.0)

        controller._document["contentMarkdown"] = ""
        controller.stateChanged.emit()
        self.application.processEvents()
        controller._document["contentMarkdown"] = "Restored article"
        controller.stateChanged.emit()
        self.application.processEvents()
        restored_text = visual_child(view, "knowledgeArticleTextContent-0")
        self.assertIsNotNone(restored_text)
        self.assertIn("Restored article", restored_text.property("text"))
        self.assertFalse(restored_text.property("richText"))

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        theme.deleteLater()
        self.application.processEvents()

    def test_article_resize_reuses_multiple_bounded_image_textures(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        controller = _KnowledgeStub()
        image_markup = []
        for index, color in enumerate((Qt.red, Qt.green, Qt.blue)):
            image_path = Path(temporary.name) / f"article-{index}.png"
            source_image = QImage(3000, 1688, QImage.Format_ARGB32)
            source_image.fill(color)
            self.assertTrue(source_image.save(str(image_path)))
            remote_source = f"https://example.invalid/article-{index}.png"
            controller.image_source_candidates[remote_source] = [
                QUrl.fromLocalFile(str(image_path)).toString()
            ]
            image_markup.append(
                f'<p>Image {index}</p><img src="{remote_source}" '
                'width="3000" height="1688" style="max-width: 100%">'
            )
        controller._document["contentMarkdown"] = markdown_from_rich_html(
            "".join(image_markup)
        )

        engine = QQmlEngine()
        self.configure_icon_context(engine.rootContext())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleContent.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "contentWidth": 900.0,
            "width": 900.0,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(900, 700)
        view.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(200)

        images = [
            visual_child(view, f"knowledgeArticleImage-{index * 2 + 1}")
            for index in range(3)
        ]
        blocks = [
            visual_child(view, f"knowledgeArticleImageBlock-{index * 2 + 1}")
            for index in range(3)
        ]
        self.assertTrue(all(images))
        self.assertTrue(all(blocks))
        if not all(block.property("imageReady") for block in blocks):
            QTest.qWait(400)
        self.assertTrue(all(block.property("imageReady") for block in blocks))

        source_sizes = [image.property("sourceSize") for image in images]
        sources = [image.property("source").toString() for image in images]
        source_changes = [QSignalSpy(image.sourceChanged) for image in images]
        status_changes = [QSignalSpy(image.statusChanged) for image in images]
        for image, source_size in zip(images, source_sizes):
            self.assertEqual(source_size.width(), 1280)
            self.assertEqual(source_size.height(), 1280)
            self.assertFalse(image.property("mipmap"))

        for width in range(900, 419, -13):
            view.setProperty("contentWidth", float(width))
            view.setWidth(float(width))
            window.resize(width, 700)
            self.application.processEvents()
        view.setProperty("contentWidth", 420.0)
        view.setWidth(420.0)
        window.resize(420, 700)
        self.application.processEvents()

        for index, image in enumerate(images):
            self.assertIs(
                visual_child(
                    view, f"knowledgeArticleImage-{index * 2 + 1}"
                ),
                image,
            )
            self.assertEqual(image.property("sourceSize"), source_sizes[index])
            self.assertEqual(image.property("source").toString(), sources[index])
            self.assertEqual(source_changes[index].count(), 0)
            self.assertEqual(status_changes[index].count(), 0)
            self.assertLessEqual(image.width(), 420.0)

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        theme.deleteLater()
        engine.deleteLater()
        self.application.processEvents()

    def test_deleted_text_document_is_released_before_formatting(self):
        document = QTextDocument()
        document.setPlainText("temporary editor")
        bridge = RichTextDocumentController()
        bridge.attach(document)
        self.assertTrue(bridge.attached)

        shiboken6.delete(document)
        self.application.processEvents()

        self.assertFalse(bridge.attached)
        bridge.set_heading(2)
        bridge.toggle_bold()
        bridge.undo()
        self.assertEqual(bridge.html(), "")

    def test_hidden_knowledge_controller_only_requests_the_workspace_link_index(self):
        application = _ApplicationStub()
        attachments = _AttachmentStub()
        controller = KnowledgeController(
            application,
            attachments=attachments,
            rich_text_document=RichTextDocumentController(),
        )
        calls = []
        controller._run = lambda action, **_kwargs: calls.append(action)

        controller.set_visible(False)
        application.project_changed.emit("other", "Other")
        self.assertEqual(calls, ["link_index"])

        application.current_project_code = "other"
        controller.set_visible(True)
        self.assertEqual(calls, ["link_index", "list"])

        controller.set_visible(False)
        application.project_changed.emit("third", "Third")
        self.assertEqual(calls, ["link_index", "list", "link_index"])

    def test_background_link_index_hands_off_to_catalog_when_dock_opens(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        calls = []
        controller._run = lambda action, **_kwargs: calls.append(action)
        controller._worker = object()

        controller.set_visible(True)
        self.assertEqual(calls, [])

        controller._worker = None
        controller._link_index_ready({})
        self.assertEqual(calls, ["list"])

    def test_layout_hide_retains_knowledge_load_and_warm_article(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        pool = DeferredPool()
        navigation = controller.navigation
        from thlib.environment import env_inst

        with patch.object(env_inst, "server_pool", pool):
            controller.set_visible(True)
            self.assertEqual(len(pool.workers), 1)
            catalog_worker = pool.workers[0]
            generation = controller._generation

            # Section A hides Knowledge while the Section B catalog request
            # is running.  The request remains authoritative and completes
            # into the retained controller/model while hidden.
            controller.set_visible(False)
            self.assertIs(controller._worker, catalog_worker)
            self.assertTrue(controller.busy)
            self.assertFalse(catalog_worker.cancelled)
            self.assertEqual(controller._generation, generation)

            catalog_worker.resolve({
                "initialized": True,
                "canEdit": True,
                "canInitialize": False,
                "query": "",
                "catalog": [{
                    "identity": "DOC0001",
                    "title": "Pipeline guide",
                    "description": "How to publish",
                    "excerpt": "Warm cached article",
                    "kind": "article",
                    "parentCode": "",
                    "sortOrder": 10,
                    "searchKey": (
                        "skey://demo/th_knowledge_article?code=DOC0001"
                    ),
                }],
            })
            self.assertIs(controller.navigation, navigation)
            self.assertEqual(controller.navigation.count(), 1)
            self.assertEqual(len(pool.workers), 2)

            article_worker = pool.workers[1]
            self.assertFalse(article_worker.cancelled)
            article_worker.resolve({
                "initialized": True,
                "canEdit": True,
                "canInitialize": False,
                "identity": "DOC0001",
                "searchKey": (
                    "skey://demo/th_knowledge_article?code=DOC0001"
                ),
                "revision": "revision-1",
                "document": {
                    "title": "Pipeline guide",
                    "description": "How to publish",
                    "kind": "article",
                    "parentCode": "",
                    "contentMarkdown": "Warm cached article",
                    "contentText": "Warm cached article",
                    "sortOrder": 10,
                },
                "sectionContents": [],
            })
            self.assertFalse(controller.busy)
            self.assertEqual(controller.document["title"], "Pipeline guide")

            request_count = len(pool.workers)
            for visible in (True, False, True, False, True):
                controller.set_visible(visible)

        self.assertIs(controller.navigation, navigation)
        self.assertEqual(controller.navigation.count(), 1)
        self.assertEqual(controller.identity, "DOC0001")
        self.assertEqual(len(pool.workers), request_count)

    def test_project_change_and_shutdown_cancel_knowledge_loads(self):
        application = _ApplicationStub()
        controller = KnowledgeController(
            application,
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        pool = DeferredPool()
        from thlib.environment import env_inst

        with patch.object(env_inst, "server_pool", pool):
            controller.set_visible(True)
            project_worker = pool.workers[-1]

            application.current_project_code = "other"
            application.project_changed.emit("other", "Other")

            self.assertTrue(project_worker.cancelled)
            replacement_worker = pool.workers[-1]
            self.assertIsNot(replacement_worker, project_worker)
            self.assertIs(controller._worker, replacement_worker)

            controller.shutdown()

        self.assertTrue(replacement_worker.cancelled)
        self.assertIsNone(controller._worker)

    def test_hidden_schema_bootstrap_refreshes_the_workspace_link_index(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        calls = []
        controller._run = lambda action, **_kwargs: calls.append(action)

        controller.apply_schema_initialization()

        self.assertTrue(controller.initialized)
        self.assertEqual(calls, ["link_index"])

    def test_reopening_retained_article_reprojects_cached_link_previews(self):
        class CachedPreviews(QObject):
            previewReady = Signal(str, object)
            previewsReady = Signal(object)

            @staticmethod
            def records_for_text(_value):
                return []

            @staticmethod
            def records_for_keys(search_keys):
                return [{
                    "searchKey": search_keys[0],
                    "status": "ready",
                    "kind": "sobject",
                    "title": "Hero asset",
                    "description": "Resolved while the dock was hidden",
                    "previewUrl": "image://preview/hero",
                }]

        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
            skey_previews=CachedPreviews(),
        )
        controller._loaded = True
        controller._document = {
            "kind": "article",
            "contentMarkdown": "Hero",
            "linkedSearchKeys": ["skey://demo/assets?code=HERO"],
        }
        controller._linked_objects = [{
            "searchKey": "skey://demo/assets?code=HERO",
            "status": "loading",
            "title": "HERO",
        }]

        controller.set_visible(True)

        self.assertEqual(controller.linkedObjects[0]["title"], "Hero asset")
        self.assertEqual(
            controller.linkedObjects[0]["description"],
            "Resolved while the dock was hidden",
        )

    def test_collapsing_a_section_removes_its_articles_from_navigation(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._catalog = [{
            "identity": "17", "title": "Characters", "description": "",
            "excerpt": "", "kind": "section", "parentCode": "",
            "sortOrder": 0,
        }, {
            "identity": "18", "title": "Niki", "description": "",
            "excerpt": "", "kind": "article", "parentCode": "17",
            "sortOrder": 0,
        }]

        controller._rebuild_navigation()
        self.assertEqual(controller.navigation.rowCount(), 2)
        self.assertEqual(controller.navigation.records()[1]["depth"], 1)

        controller.toggle_section("17")
        self.assertEqual(controller.navigation.rowCount(), 1)
        self.assertEqual(
            controller.navigation.records()[0]["identity"], "17"
        )

    def test_drag_move_reparents_and_reorders_locally_until_saved(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller._project_code = "demo"
        controller._catalog = [{
            "identity": "SEC1", "title": "Characters", "kind": "section",
            "parentCode": "", "sortOrder": 10,
        }, {
            "identity": "SEC2", "title": "Shots", "kind": "section",
            "parentCode": "", "sortOrder": 20,
        }, {
            "identity": "DOC1", "title": "Hero", "kind": "article",
            "parentCode": "", "sortOrder": 30,
        }, {
            "identity": "DOC2", "title": "Villain", "kind": "article",
            "parentCode": "SEC1", "sortOrder": 10,
        }]
        controller._rebuild_navigation()

        self.assertTrue(controller.move_entry("DOC1", "SEC1", "inside"))

        moved = controller._catalog_record("DOC1")
        self.assertEqual(moved["parentCode"], "SEC1")
        self.assertEqual(moved["sortOrder"], 20)
        self.assertTrue(controller.organizationDirty)
        self.assertEqual(
            [record["identity"] for record in controller.navigation.records()],
            ["SEC1", "DOC2", "DOC1", "SEC2"],
        )

        requests = []
        controller._run = lambda action, **kwargs: requests.append((
            action, kwargs.get("organization"),
        ))
        controller.save_organization()

        self.assertEqual(requests[0][0], "organize")
        changed = {
            entry["identity"]: entry for entry in requests[0][1]
        }
        self.assertEqual(changed["DOC1"]["parentCode"], "SEC1")
        self.assertEqual(changed["DOC1"]["sortOrder"], 20)

    def test_dragged_section_cannot_be_nested_in_its_descendant(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller._catalog = [{
            "identity": "SEC1", "title": "Characters", "kind": "section",
            "parentCode": "", "sortOrder": 10,
        }, {
            "identity": "SEC2", "title": "Heroes", "kind": "section",
            "parentCode": "SEC1", "sortOrder": 10,
        }]

        self.assertFalse(controller.move_entry("SEC1", "SEC2", "inside"))
        self.assertFalse(controller.organizationDirty)
        self.assertIn("inside its child", controller.error)

    def test_discard_organization_restores_parent_and_order(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller._catalog = [{
            "identity": "A", "title": "Alpha", "kind": "article",
            "parentCode": "", "sortOrder": 10,
        }, {
            "identity": "B", "title": "Beta", "kind": "article",
            "parentCode": "", "sortOrder": 20,
        }]

        self.assertTrue(controller.move_entry("B", "A", "before"))
        self.assertEqual(
            [record["identity"] for record in controller.navigation.records()],
            ["B", "A"],
        )

        controller.discard_organization()

        self.assertFalse(controller.organizationDirty)
        self.assertEqual(
            [record["identity"] for record in controller.navigation.records()],
            ["A", "B"],
        )

    def test_navigation_selection_responds_before_article_load_finishes(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._project_code = "demo"
        controller._catalog = [{
            "identity": "18",
            "title": "Niki",
            "description": "Character documentation",
            "kind": "article",
            "parentCode": "17",
            "sortOrder": 10,
            "searchKey": "skey://demo/th_knowledge_article?code=18",
        }]
        calls = []
        controller._run = lambda action, **kwargs: calls.append((
            action, kwargs.get("identity"),
        ))

        controller.select("18")

        self.assertEqual(controller.navigationIdentity, "18")
        self.assertEqual(controller.identity, "18")
        self.assertEqual(controller.document["title"], "Niki")
        self.assertEqual(controller.document["description"], "Character documentation")
        self.assertEqual(calls, [("load", "18")])

    def test_navigation_stashes_unsaved_article_as_local_draft(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._project_code = "demo"
        controller._can_edit = True
        controller._catalog = [{
            "identity": "DOC1", "title": "Hero", "description": "",
            "kind": "article", "parentCode": "", "sortOrder": 10,
            "searchKey": "skey://demo/th_knowledge_article?code=DOC1",
            "draft": False, "localDraft": False,
        }, {
            "identity": "DOC2", "title": "Villain", "description": "",
            "kind": "article", "parentCode": "", "sortOrder": 20,
            "searchKey": "skey://demo/th_knowledge_article?code=DOC2",
            "draft": False, "localDraft": False,
        }]
        controller._identity = "DOC1"
        controller._navigation_identity = "DOC1"
        controller._search_key = (
            "skey://demo/th_knowledge_article?code=DOC1"
        )
        controller._document = {
            "title": "Hero — local edit",
            "description": "",
            "kind": "article",
            "parentCode": "",
            "contentMarkdown": "Unsaved body",
            "contentText": "Unsaved body",
            "linkedSearchKeys": [],
            "sortOrder": 10,
            "draft": False,
        }
        controller._original = dict(
            controller._document,
            title="Hero",
            contentMarkdown="Published body",
            contentText="Published body",
        )
        controller._document_complete = True
        controller._editing = True
        controller._rebuild_navigation()
        calls = []
        controller._run = lambda action, **kwargs: calls.append((
            action, kwargs.get("identity"),
        ))

        controller.select("DOC2")

        self.assertEqual(calls, [("load", "DOC2")])
        draft_record = controller._catalog_record("DOC1")
        self.assertTrue(draft_record["localDraft"])
        self.assertEqual(draft_record["title"], "Hero — local edit")
        self.assertEqual(controller.error, "")

        controller.select("DOC1")

        self.assertEqual(calls, [("load", "DOC2")])
        self.assertTrue(controller.localDraft)
        self.assertTrue(controller.editing)
        self.assertEqual(
            controller.document["contentMarkdown"], "Unsaved body"
        )

    def test_article_checkpoint_persists_and_restores_local_draft(self):
        class ConfigQueue:
            def __init__(self):
                self.calls = []

            def submit(self, payload, **location):
                self.calls.append((deepcopy(payload), dict(location)))
                return True

        queue = ConfigQueue()
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
            config_queue=queue,
        )
        controller._ensure_project_context()
        controller._identity = "DOC1"
        controller._search_key = (
            "skey://demo/th_knowledge_article?code=DOC1"
        )
        controller._document = {
            "title": "Recovered article",
            "description": "",
            "kind": "article",
            "parentCode": "",
            "contentMarkdown": "Work that must survive a crash",
            "contentText": "Work that must survive a crash",
            "linkedSearchKeys": [],
            "sortOrder": 10,
            "draft": False,
        }
        controller._original = dict(
            controller._document,
            contentMarkdown="Published body",
            contentText="Published body",
        )
        controller._document_complete = True
        controller._editing = True

        self.assertTrue(controller.checkpoint_current_draft())

        payload, location = queue.calls[-1]
        self.assertEqual(
            payload["projects"]["demo"]["DOC1"]["document"]
            ["contentMarkdown"],
            "Work that must survive a crash",
        )
        self.assertEqual(location, {
            "filename": "drafts",
            "unique_id": "cache/knowledge",
            "long_abs_path": True,
        })
        restored = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
            draft_state=payload,
        )
        restored._ensure_project_context()
        self.assertTrue(restored._restore_local_draft("DOC1"))
        self.assertEqual(
            restored.document["contentMarkdown"],
            "Work that must survive a crash",
        )

    def test_selected_section_presents_catalog_outline_before_load_finishes(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._project_code = "demo"
        controller._catalog = [{
            "identity": "17", "title": "Characters",
            "description": "Character documentation", "kind": "section",
            "parentCode": "", "sortOrder": 0,
            "searchKey": "skey://demo/th_knowledge_article?code=17",
        }, {
            "identity": "18", "title": "Niki",
            "description": "Hero character", "kind": "article",
            "parentCode": "17", "sortOrder": 0,
            "searchKey": "skey://demo/th_knowledge_article?code=18",
        }]
        calls = []
        controller._run = lambda action, **kwargs: calls.append((
            action, kwargs.get("identity"),
        ))

        controller.select("17")

        self.assertEqual(controller.identity, "17")
        self.assertEqual(controller.document["kind"], "section")
        self.assertEqual(controller.document["title"], "Characters")
        self.assertEqual(controller.tableOfContents, [{
            "identity": "18",
            "title": "Niki",
            "description": "Hero character",
            "kind": "article",
            "level": 1,
        }])
        self.assertEqual(calls, [("load", "17")])

    def test_navigation_recovers_project_context_before_loading(self):
        application = _ApplicationStub()
        controller = KnowledgeController(
            application,
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        calls = []

        def record_run(action, **kwargs):
            self.assertEqual(controller.projectCode, "demo")
            calls.append((action, kwargs.get("identity")))
            return True

        original_run = controller._run
        controller._run = record_run
        try:
            controller.select("18")
        finally:
            controller._run = original_run

        self.assertEqual(controller.navigationIdentity, "18")
        self.assertEqual(calls, [("load", "18")])

    def test_create_recovers_project_context_and_stays_local_until_needed(self):
        application = _ApplicationStub()
        controller = KnowledgeController(
            application,
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        calls = []

        def record_run(action, **kwargs):
            self.assertEqual(controller.projectCode, "demo")
            calls.append((action, kwargs.get("document")))
            return True

        original_run = controller._run
        controller._run = record_run
        try:
            controller.create("article", "")
        finally:
            controller._run = original_run

        self.assertEqual(calls, [])
        self.assertEqual(controller.document["kind"], "article")
        self.assertTrue(controller.creating)
        self.assertFalse(controller.draft)
        self.assertTrue(controller.localDraft)
        self.assertTrue(controller.identity.startswith("local:"))
        self.assertEqual(controller.navigation.rowCount(), 1)

    def test_saving_a_new_local_draft_creates_its_server_entry(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller.create("article", "")
        requests = []
        controller._run = lambda action, **kwargs: (
            requests.append((action, kwargs)) or True
        )

        controller.save()

        self.assertEqual(len(requests), 1)
        action, request = requests[0]
        self.assertEqual(action, "save")
        self.assertEqual(request["identity"], "")
        self.assertEqual(request["document"]["title"], "Untitled article")

    def test_saving_as_draft_uses_a_distinct_server_operation(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller.create("article", "")
        requests = []
        controller._run = lambda action, **kwargs: (
            requests.append((action, kwargs)) or True
        )

        controller.save_draft()

        self.assertEqual(len(requests), 1)
        action, request = requests[0]
        self.assertEqual(action, "save_draft")
        self.assertEqual(request["identity"], "")
        self.assertIs(request["handler"].__self__, controller)
        self.assertIs(
            request["handler"].__func__,
            controller._draft_save_ready.__func__,
        )

    def test_saved_server_draft_stays_in_the_editor(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller.create("article", "")
        previous_identity = controller.identity

        controller._draft_save_ready({
            "identity": "DOC0001",
            "searchKey": (
                "skey://demo/th_knowledge_article?code=DOC0001"
            ),
            "revision": "draft-revision",
            "document": dict(controller.document, draft=True),
            "catalog": [{
                "identity": "DOC0001",
                "title": "Untitled article",
                "description": "",
                "kind": "article",
                "parentCode": "",
                "sortOrder": 0,
                "searchKey": (
                    "skey://demo/th_knowledge_article?code=DOC0001"
                ),
                "draft": True,
            }],
            "attachmentSnapshots": [],
            "sectionContents": [],
        })

        self.assertNotEqual(controller.identity, previous_identity)
        self.assertEqual(controller.identity, "DOC0001")
        self.assertTrue(controller.draft)
        self.assertTrue(controller.editing)
        self.assertTrue(controller.creating)
        self.assertFalse(controller.localDraft)
        self.assertFalse(controller.dirty)

    def test_saving_a_local_section_retargets_its_local_children(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller.create("section", "")
        local_section = controller.identity
        controller.create("article", local_section)
        local_article = controller.identity
        controller.select(local_section)

        controller._save_ready({
            "identity": "SEC0001",
            "searchKey": "skey://demo/article?code=SEC0001",
            "revision": "revision-1",
            "document": {
                "title": "New section", "description": "",
                "kind": "section", "parentCode": "",
                "contentMarkdown": "", "contentText": "",
                "linkedSearchKeys": [], "sortOrder": 0,
                "draft": False,
            },
            "catalog": [{
                "identity": "SEC0001", "title": "New section",
                "description": "", "kind": "section",
                "parentCode": "", "sortOrder": 0,
                "searchKey": "skey://demo/article?code=SEC0001",
            }],
            "attachmentSnapshots": [],
            "sectionContents": [],
        })

        child_record = controller._catalog_record(local_article)
        self.assertTrue(child_record["localDraft"])
        self.assertEqual(child_record["parentCode"], "SEC0001")
        controller.select(local_article)
        self.assertEqual(controller.document["parentCode"], "SEC0001")

    def test_discarding_an_existing_local_draft_restores_catalog_entry(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._project_code = "demo"
        controller._can_edit = True
        controller._replace_catalog([{
            "identity": "DOC1", "title": "Published title",
            "description": "", "kind": "article", "parentCode": "",
            "sortOrder": 10, "searchKey": "skey://demo/article?code=DOC1",
        }])
        controller._identity = "DOC1"
        controller._navigation_identity = "DOC1"
        controller._document = {
            "title": "Local title", "description": "",
            "kind": "article", "parentCode": "",
            "contentMarkdown": "Local body",
            "contentText": "Local body", "linkedSearchKeys": [],
            "sortOrder": 10, "draft": False,
        }
        controller._original = dict(
            controller._document,
            title="Published title",
            contentMarkdown="Published body",
            contentText="Published body",
        )
        controller._editing = True
        controller.stash_current_draft()

        controller.discard()

        self.assertFalse(controller.localDraft)
        self.assertFalse(controller.editing)
        self.assertEqual(
            controller._catalog_record("DOC1")["title"],
            "Published title",
        )

    def test_editor_links_selected_sobjects_without_duplicates(self):
        application = _ApplicationStub()
        application.selected_result_records = [{
            "type": "sobject",
            "searchKey": "demo/assets?code=HERO",
            "title": "Hero",
        }, {
            "type": "process",
            "searchKey": "demo/assets?code=HERO&process=model",
            "title": "Model",
        }, {
            "type": "sobject",
            "searchKey": "skey://demo/assets?code=HERO",
            "title": "Duplicate Hero",
        }, {
            "type": "sobject",
            "searchKey": "skey://demo/assets?code=VILLAIN",
            "title": "Villain",
        }]
        controller = KnowledgeController(
            application,
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller._editing = True
        controller._document = {
            "kind": "article",
            "linkedSearchKeys": [],
        }
        controller._original = dict(controller._document)

        linked_count = controller.link_selected_objects()

        self.assertEqual(linked_count, 2)
        self.assertEqual(controller.document["linkedSearchKeys"], [
            "skey://demo/assets?code=HERO",
            "skey://demo/assets?code=VILLAIN",
        ])
        self.assertEqual(controller.linkableSelectedObjects, [])

    def test_editor_unlinks_only_the_requested_sobject(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller._editing = True
        controller._document = {
            "kind": "article",
            "linkedSearchKeys": [
                "skey://demo/assets?code=HERO",
                "demo/assets?code=VILLAIN",
            ],
        }
        controller._original = deepcopy(controller._document)
        controller._update_linked_objects()

        removed = controller.unlink_object(
            "demo/assets?code=HERO"
        )

        self.assertTrue(removed)
        self.assertEqual(controller.document["linkedSearchKeys"], [
            "skey://demo/assets?code=VILLAIN",
        ])
        self.assertEqual(
            [record["searchKey"] for record in controller.linkedObjects],
            ["skey://demo/assets?code=VILLAIN"],
        )
        self.assertTrue(controller.dirty)
        self.assertFalse(controller.unlink_object(
            "demo/assets?code=MISSING"
        ))

    def test_create_supersedes_a_search_request_and_starts_unlinked(self):
        class ReadWorker:
            def __init__(self):
                self.cancelled = False

            def cancel(self):
                self.cancelled = True

        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        worker = ReadWorker()
        controller._worker = worker
        controller._worker_action = "list"
        controller._busy = True
        controller._query = "characters"
        documents = []

        def record_run(action, **kwargs):
            documents.append((action, kwargs["document"]))
            return True

        controller._run = record_run

        controller.create("article", "")

        self.assertTrue(worker.cancelled)
        self.assertEqual(controller.query, "")
        self.assertEqual(documents, [])
        self.assertEqual(controller.document["linkedSearchKeys"], [])
        self.assertTrue(controller.creating)

        reloads = []
        controller._run = lambda action, **_kwargs: reloads.append(action)
        controller.discard()
        self.assertEqual(reloads, ["list"])

    def test_first_attachment_reserves_hidden_draft_before_upload(self):
        class PendingAttachments(_AttachmentStub):
            def __init__(self):
                super().__init__()
                self.targets = []
                self.retargeted = []

            @Property(int, notify=_AttachmentStub.stateChanged)
            def count(self): return 1

            def begin_named_target(
                    self, search_key, context, description, owner_code):
                self.targets.append((
                    search_key, context, description, owner_code,
                ))
                return True

            def retarget_context(self, value):
                self.retargeted.append(value)
                return True

        attachments = PendingAttachments()
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=attachments,
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller.create("article", "")
        requests = []
        controller._run = lambda action, **kwargs: (
            requests.append((action, kwargs)) or True
        )

        self.assertTrue(controller.upload_attachments())
        self.assertEqual(requests[0][0], "reserve")
        self.assertFalse(requests[0][1]["document"]["draft"])

        requests[0][1]["handler"]({
            "identity": "4",
            "searchKey": "skey://demo/th_knowledge_article?code=DOC0002",
            "revision": "draft-revision",
            "document": dict(controller.document, draft=True),
            "attachmentSnapshots": [],
            "sectionContents": [],
        })

        self.assertEqual(attachments.targets, [(
            "skey://demo/th_knowledge_article?code=DOC0002",
            "attachment/knowledge",
            "Knowledge Base attachment",
            "DOC0002",
        )])
        self.assertEqual(attachments.retargeted, [
            "skey://demo/th_knowledge_article?code=DOC0002"
        ])
        self.assertTrue(controller.draft)

    def test_named_attachment_payload_uses_owner_code_and_opaque_token(self):
        first = AttachmentUploadController._target_payload(
            "demo/th_knowledge_article?code=DOC0002",
            "attachment/knowledge",
            "Knowledge Base attachment",
            {
                "path": "C:/uploads/статья.png",
                "fileType": "preview",
                "token": "a1b2c3d4e5f6",
            },
            "DOC0002",
        )
        second = AttachmentUploadController._target_payload(
            "demo/th_knowledge_article?code=DOC0002",
            "attachment/knowledge",
            "Knowledge Base attachment",
            {
                "path": "C:/other/статья.png",
                "fileType": "preview",
                "token": "f6e5d4c3b2a1",
            },
            "DOC0002",
        )

        self.assertEqual(
            first["explicitFilename"], "DOC0002_a1b2c3d4e5f6"
        )
        self.assertEqual(
            first["context"],
            "attachment/knowledge/DOC0002_a1b2c3d4e5f6",
        )
        self.assertEqual(
            first["filesDict"][0][0], "DOC0002_a1b2c3d4e5f6"
        )
        self.assertNotEqual(
            first["explicitFilename"], second["explicitFilename"]
        )
        self.assertNotIn("статья", first["explicitFilename"])

    def test_article_file_staging_previews_images_and_keeps_other_files(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        engine = QQmlEngine()
        self.configure_icon_context(engine.rootContext())
        with tempfile.TemporaryDirectory() as directory, patch(
            "thlib.ui.message_attachments.env_read_config",
            return_value={},
        ), patch("thlib.ui.message_attachments.env_write_config"):
            image_path = Path(directory) / "article image.png"
            image = QImage(12, 8, QImage.Format.Format_ARGB32)
            image.fill(0xff336699)
            self.assertTrue(image.save(str(image_path)))
            file_path = Path(directory) / "article notes.txt"
            file_path.write_text("notes", encoding="utf-8")

            upload_controller = AttachmentUploadController(
                _ApplicationStub(), draft_namespace="knowledge-test"
            )
            upload_controller.activate_context("knowledge:new:test")
            upload_controller.add_files([
                QUrl.fromLocalFile(str(image_path)),
                QUrl.fromLocalFile(str(file_path)),
            ])
            self.assertEqual(upload_controller.count, 2)
            self.assertEqual(
                upload_controller.model._records[1]["fileType"], "file"
            )

            theme_component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
            )
            theme = theme_component.createWithInitialProperties({"dark": True})
            component = QQmlComponent(
                engine,
                QUrl.fromLocalFile(str(
                    self.qml / "AttachmentStagingPanel.qml"
                )),
            )
            panel = component.createWithInitialProperties({
                "theme": theme,
                "controller": upload_controller,
                "attachmentModel": upload_controller.model,
                "width": 260,
                "height": 190,
            })
            self.assertIsNotNone(panel, "\n".join(
                error.toString() for error in component.errors()
            ))
            window = QQuickWindow()
            window.resize(260, 190)
            panel.setParentItem(window.contentItem())
            window.show()
            self.assertTrue(QTest.qWaitForWindowExposed(window))
            self.application.processEvents()

            repeater = panel.findChild(QObject, "attachmentStagingRepeater")
            image_preview = visual_child(
                panel, "attachmentStagingPreview-0"
            )
            file_preview = visual_child(
                panel, "attachmentStagingPreview-1"
            )
            scroll_bar = panel.findChild(
                QObject, "attachmentStagingHorizontalScrollBar"
            )
            self.assertEqual(repeater.property("count"), 2)
            self.assertTrue(
                image_preview.property("source").toString().startswith("file:")
            )
            self.assertEqual(file_preview.property("source").toString(), "")
            self.assertEqual(file_preview.property("fallbackText"), "TXT")
            self.assertTrue(scroll_bar.property("hasOverflow"))
            self.assertTrue(scroll_bar.property("visible"))

            panel.deleteLater()
            theme.deleteLater()
            window.close()

    def test_attachment_upload_retries_unversioned_path_collision(self):
        application = _ApplicationStub()
        with patch(
            "thlib.ui.message_attachments.env_read_config",
            return_value={},
        ):
            controller = AttachmentUploadController(
                application, draft_namespace="knowledge-test"
            )
        payloads = []

        def execute(payload, _repository, **_kwargs):
            payloads.append(deepcopy(payload))
            if len(payloads) == 1:
                raise RuntimeError(
                    "This path [/opt/tactic/assets/demo/"
                    "DOC0002_token.png] already exists"
                )
            return {"__search_key__": "sthpw/snapshot?code=SNAP0002"}

        record = {
            "token": "token",
            "title": "статья.png",
            "path": "C:/uploads/статья.png",
            "fileType": "preview",
        }
        with patch(
            "thlib.checkin_operation.execute_checkin_payload",
            side_effect=execute,
        ):
            result = controller._upload_all(
                "demo/th_knowledge_article?code=DOC0002",
                "attachment/knowledge",
                "Knowledge Base attachment",
                [record],
                {},
                "target",
                {},
                "DOC0002",
            )

        self.assertEqual(
            result["snapshots"]["token"],
            "sthpw/snapshot?code=SNAP0002",
        )
        self.assertEqual(
            payloads[0]["explicitFilename"], "DOC0002_token"
        )
        self.assertEqual(
            payloads[1]["explicitFilename"], "DOC0002_token_2"
        )
        self.assertEqual(
            payloads[1]["filesDict"][0][0], "DOC0002_token_2"
        )

    def test_uploaded_attachment_model_uses_native_file_web_paths(self):
        class PreviewFile:
            @staticmethod
            def get_full_web_path():
                return "http://tactic/assets/demo/guide_web.png"

        class FileObject:
            @staticmethod
            def get_type(): return "main"
            @staticmethod
            def get_filename_with_ext(): return "DOC0002.png"
            @staticmethod
            def get_metadata(): return {"filename": "guide.png"}
            @staticmethod
            def get_ext(): return "png"
            @staticmethod
            def get_full_web_path():
                return "http://tactic/assets/demo/guide.png"
            @staticmethod
            def get_web_preview(): return PreviewFile()
            @staticmethod
            def is_previewable(): return True
            @staticmethod
            def get_file_size(): return 2048

        class SnapshotObject:
            def __init__(self, _value): pass
            @staticmethod
            def get_search_key(): return "sthpw/snapshot?code=SNAP0001"
            @staticmethod
            def get_files_objects(): return [FileObject()]

        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        import thlib.tactic_classes as tc
        with patch.object(tc, "Snapshot", SnapshotObject):
            controller._replace_attachment_snapshots([{"code": "SNAP0001"}])

        records = controller.uploaded_attachments.records()
        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["webUrl"],
            "http://tactic/assets/demo/guide.png",
        )
        self.assertEqual(
            records[0]["previewUrl"],
            "http://tactic/assets/demo/guide_web.png",
        )
        self.assertTrue(records[0]["isImage"])
        self.assertEqual(records[0]["title"], "guide.png")
        self.assertIn("2.00", records[0]["sizeText"])
        controller._document = {
            "kind": "article",
            "contentMarkdown": markdown_from_rich_html(
                '<p><img src="http://tactic/assets/demo/guide.png" '
                'width="900"></p>'
            ),
        }
        image_block = controller.viewer_blocks_for_width(500.0)[0]
        self.assertEqual(image_block["kind"], "image")
        self.assertEqual(image_block["width"], 500.0)
        self.assertEqual(image_block["sources"], [
            "http://tactic/assets/demo/guide_web.png",
            "http://tactic/assets/demo/guide.png",
        ])
        controller.copy_attachment_web_url(records[0]["token"])
        self.assertEqual(
            QGuiApplication.clipboard().text(),
            "http://tactic/assets/demo/guide.png",
        )
    def test_attachment_library_stays_compact_and_confirms_copy_link(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        engine = QQmlEngine()
        self.configure_icon_context(engine.rootContext())
        controller = _KnowledgeStub()
        controller._uploaded_attachments.replace([
            {
                "token": "attachment-1",
                "snapshotKey": "skey://sthpw/snapshot?code=SNAP0001",
                "title": "guide.png",
                "extension": "PNG",
                "sizeText": "2 KB",
                "previewUrl": "",
                "webUrl": "http://tactic/assets/guide.png",
                "isImage": True,
            },
            {
                "token": "attachment-2",
                "snapshotKey": "skey://sthpw/snapshot?code=SNAP0002",
                "title": "reference.png",
                "extension": "PNG",
                "sizeText": "4 KB",
                "previewUrl": "",
                "webUrl": "http://tactic/assets/reference.png",
                "isImage": True,
            },
        ])
        upload_controller = _AttachmentStub(count=1)
        staging_model = RecordListModel((
            "token", "title", "path", "size", "fileType", "previewUrl",
            "status", "progress", "error", "snapshotKey", "uploadTarget",
        ))
        document_controller = RichTextDocumentController(engine)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeAttachmentLibrary.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "uploadController": upload_controller,
            "stagingModel": staging_model,
            "uploadedModel": controller.uploadedAttachmentModel,
            "documentController": document_controller,
            "width": 260,
            "height": 460,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(260, 460)
        view.setParentItem(window.contentItem())
        window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(window))
        self.application.processEvents()

        primary_upload = visual_child(view, "knowledgeUploadAttachments")
        duplicate_upload = visual_child(view, "attachmentChooseFiles")
        clipboard_upload = visual_child(view, "attachmentClipboardImage")
        clear_uploads = visual_child(view, "attachmentClearAll")
        first_attachment = visual_child(
            view, "knowledgeUploadedAttachment-0"
        )
        second_attachment = visual_child(
            view, "knowledgeUploadedAttachment-1"
        )
        copy_link = visual_child(
            first_attachment, "knowledgeCopyAttachmentLink"
        )
        insert_link = visual_child(
            first_attachment, "knowledgeInsertAttachment"
        )
        delete_file = visual_child(
            first_attachment, "knowledgeDeleteAttachment"
        )
        self.assertIsNotNone(primary_upload)
        self.assertTrue(primary_upload.property("visible"))
        self.assertIsNotNone(duplicate_upload)
        self.assertFalse(duplicate_upload.property("visible"))
        self.assertIsNotNone(clipboard_upload)
        self.assertTrue(clipboard_upload.property("visible"))
        self.assertIsNotNone(clear_uploads)
        self.assertTrue(clear_uploads.property("visible"))
        self.assertIsNotNone(copy_link)
        self.assertIsNotNone(insert_link)
        self.assertIsNotNone(delete_file)
        self.assertIsNotNone(first_attachment)
        self.assertIsNotNone(second_attachment)
        self.assertEqual(copy_link.property("iconName"), "content-copy")
        self.assertEqual(delete_file.property("iconName"), "delete")
        self.assertTrue(copy_link.property("visible"))
        insert_position = insert_link.mapToItem(view, QPointF(0, 0))
        copy_position = copy_link.mapToItem(view, QPointF(0, 0))
        delete_position = delete_file.mapToItem(view, QPointF(0, 0))
        self.assertLessEqual(first_attachment.height(), 64.5)
        self.assertLessEqual(second_attachment.height(), 64.5)
        first_position = first_attachment.mapToItem(view, QPointF(0, 0))
        second_position = second_attachment.mapToItem(view, QPointF(0, 0))
        self.assertGreaterEqual(
            second_position.y(),
            first_position.y() + first_attachment.height() - 0.5,
        )
        self.assertLessEqual(
            insert_position.x() + insert_link.width(),
            copy_position.x() + 0.5,
        )
        self.assertLessEqual(
            abs(delete_position.y() - copy_position.y()), 0.5
        )
        self.assertLessEqual(
            delete_position.x() + delete_file.width(),
            view.width(),
        )
        window.resize(760, 460)
        view.setWidth(760)
        self.application.processEvents()
        first_position = first_attachment.mapToItem(view, QPointF(0, 0))
        second_position = second_attachment.mapToItem(view, QPointF(0, 0))
        self.assertGreaterEqual(
            second_position.y(),
            first_position.y() + first_attachment.height() - 0.5,
        )
        self.assertLessEqual(first_attachment.height(), 64.5)
        self.assertLessEqual(second_attachment.height(), 64.5)
        copy_point = copy_link.mapToScene(QPointF(
            copy_link.width() / 2, copy_link.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=copy_point.toPoint()
        )
        self.application.processEvents()
        self.assertEqual(
            controller.copied_attachment_tokens, ["attachment-1"]
        )
        self.assertEqual(copy_link.property("iconName"), "check")

        delete_dialog = view.findChild(
            QObject, "knowledgeDeleteAttachmentDialog"
        )
        delete_confirm = view.findChild(
            QObject, "knowledgeDeleteAttachmentConfirm"
        )
        self.assertIsNotNone(delete_dialog)
        self.assertIsNotNone(delete_confirm)
        delete_point = delete_file.mapToScene(QPointF(
            delete_file.width() / 2, delete_file.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=delete_point.toPoint()
        )
        self.application.processEvents()
        self.assertTrue(delete_dialog.property("visible"))
        confirm_point = delete_confirm.mapToScene(QPointF(
            delete_confirm.width() / 2, delete_confirm.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=confirm_point.toPoint()
        )
        self.application.processEvents()
        self.assertEqual(
            controller.removed_attachment_tokens, ["attachment-1"]
        )

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        theme.deleteLater()
        engine.deleteLater()
        self.application.processEvents()

    def test_article_viewer_lists_attachments_and_opens_file_cards(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        image_path = Path(temporary.name) / "guide.png"
        image = QImage(320, 180, QImage.Format_ARGB32)
        image.fill(Qt.blue)
        self.assertTrue(image.save(str(image_path)))

        controller = _KnowledgeStub()
        web_url = "https://example.test/guide.png"
        controller._uploaded_attachments.replace([{
            "token": "attachment-1",
            "snapshotKey": "skey://sthpw/snapshot?code=SNAP0001",
            "title": "guide.png",
            "extension": "PNG",
            "sizeText": "12 KB",
            "previewUrl": QUrl.fromLocalFile(str(image_path)).toString(),
            "webUrl": web_url,
            "isImage": True,
        }])
        controller._references = [{
            "searchKey": "skey://demo/assets?code=A1",
            "title": "Asset A1",
            "status": "ready",
        }]
        engine = QQmlEngine()
        engine.rootContext().setContextProperty(
            "skeyPreviewResolver", _PreviewStub()
        )
        self.configure_icon_context(engine.rootContext())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleViewer.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "width": 900,
            "height": 720,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(900, 720)
        view.setParentItem(window.contentItem())
        window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(window))
        self.application.processEvents()

        attachment_list = visual_child(
            view, "knowledgeViewerAttachments"
        )
        reference_list = visual_child(
            view, "knowledgeViewerReferences"
        )
        resources_toggle = visual_child(
            view, "knowledgeToggleResources"
        )
        resource_panel = visual_child(
            view, "knowledgeViewerResources"
        )
        attachment_card = visual_child(
            view, "knowledgeViewerAttachment-0"
        )
        article_text = visual_child(
            view, "knowledgeArticleTextContent-0"
        )
        self.assertIsNotNone(attachment_list)
        self.assertIsNotNone(reference_list)
        self.assertIsNotNone(resources_toggle)
        self.assertIsNotNone(resource_panel)
        self.assertTrue(resources_toggle.property("visible"))
        self.assertEqual(resource_panel.property("height"), 0)
        self.assertEqual(resource_panel.property("opacity"), 0)
        toggle_point = resources_toggle.mapToScene(QPointF(
            resources_toggle.width() / 2,
            resources_toggle.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=toggle_point.toPoint()
        )
        QTest.qWait(30)
        self.assertGreater(resource_panel.property("height"), 0)
        self.assertEqual(resource_panel.property("opacity"), 1)
        self.assertTrue(attachment_list.property("visible"))
        self.assertTrue(reference_list.property("visible"))
        self.assertIsNotNone(attachment_card)
        self.assertIsNotNone(article_text)
        self.assertGreater(
            attachment_list.mapToItem(view, QPointF(0, 0)).y(),
            article_text.mapToItem(view, QPointF(0, 0)).y(),
        )

        card_point = attachment_card.mapToScene(QPointF(
            attachment_card.width() / 2,
            attachment_card.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=card_point.toPoint()
        )
        self.application.processEvents()
        self.assertEqual(controller.opened_links, [web_url])

        attachment_card.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Return)
        self.application.processEvents()
        self.assertEqual(controller.opened_links, [web_url, web_url])

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        theme.deleteLater()
        engine.deleteLater()
        self.application.processEvents()

    def test_async_load_completion_publishes_selected_document(self):
        class ImmediateWorker(QObject):
            result = Signal(object)
            error = Signal(object)

            def __init__(self, operation):
                super().__init__()
                self._operation = operation

            def start(self):
                self.result.emit(self._operation())

            def cancel(self):
                return True

        class ImmediatePool:
            is_stopped = False

            def add_task(self, operation):
                return ImmediateWorker(operation)

        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        result = {
            "initialized": True,
            "canEdit": True,
            "canInitialize": True,
            "catalog": [],
            "query": "",
            "identity": "DOC0001",
            "searchKey": (
                "skey://demo/th_knowledge_article?code=DOC0001"
            ),
            "revision": "revision-1",
            "document": {
                "title": "Niki",
                "description": "Character notes",
                "kind": "article",
                "parentCode": "",
                "contentMarkdown": "Niki",
                "contentText": "Niki",
                "sortOrder": 0,
            },
            "sectionContents": [],
        }
        from thlib.environment import env_inst

        with (
            patch.object(env_inst, "server_pool", ImmediatePool()),
            patch(
                "thlib.tactic_classes.execute_procedure_serverside",
                return_value=result,
            ),
        ):
            controller.select("DOC0001")
            self.application.processEvents()

        self.assertEqual(controller.identity, "DOC0001")
        self.assertEqual(controller.document["title"], "Niki")
        self.assertFalse(controller.busy)

    def test_navigation_keeps_latest_click_while_request_is_running(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._worker = object()

        controller.select("19")

        self.assertEqual(controller.navigationIdentity, "19")
        self.assertEqual(controller._pending_identity, "19")

    def test_external_open_requests_article_page_for_same_identity(self):
        class DockModel:
            def __init__(self):
                self.shown = []

            def show_panel(self, panel_id):
                self.shown.append(str(panel_id))

        application = _ApplicationStub()
        application.dock_model = DockModel()
        controller = KnowledgeController(
            application,
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._loaded = True
        controller._catalog = [{
            "identity": "DOC0001",
            "kind": "article",
        }]
        controller._identity = "DOC0001"
        controller._navigation_identity = "DOC0001"
        controller._document = {
            "title": "Guide",
            "kind": "article",
            "contentMarkdown": "Body",
            "linkedSearchKeys": [],
        }
        controller._document_complete = True

        controller.open_identity("DOC0001")

        self.assertEqual(application.dock_model.shown, ["knowledge"])
        self.assertTrue(controller.openArticlePending)
        controller.acknowledge_article_open()
        self.assertFalse(controller.openArticlePending)
        controller.shutdown()

    def test_initialization_server_script_owns_both_feature_schemas(self):
        code = tactic_query.prepare_serverside_script(
            knowledge_request,
            {
                "action": "initialize",
                "project_code": "demo",
                "identity": "",
                "document": None,
                "expected_revision": "",
                "query": "",
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        compile("def execute():\n" + "".join(
            "    " + line for line in code.splitlines(keepends=True)
        ), "<collaboration-initialize>", "exec")
        self.assertIn('(\"sthpw/message\", ((\"metadata\", \"text\"),))', code)
        self.assertIn(
            '(\"sthpw/message_log\", ((\"metadata\", \"text\"),))',
            code,
        )
        self.assertIn('table = \"th_knowledge_article\"', code)
        self.assertIn('api.add_column_to_search_type(', code)

    def test_saved_article_uses_shared_dependency_delete_workflow(self):
        class DeleteController(QObject):
            deletionFinished = Signal(str)

            def __init__(self):
                super().__init__()
                self.calls = []

            def begin_search_keys(self, targets, context="items"):
                self.calls.append((targets, context))
                return True

        application = _ApplicationStub()
        application.sobject_delete = DeleteController()
        controller = KnowledgeController(
            application,
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._can_edit = True
        controller._project_code = "demo"
        controller._identity = "17"
        controller._search_key = (
            "skey://demo/th_knowledge_article?project=demo&id=17"
        )
        controller._document = {
            "kind": "article",
            "title": "Dependency-aware article",
        }

        controller.delete_selected()

        self.assertEqual(application.sobject_delete.calls, [([{
            "searchKey": controller._search_key,
            "title": "Dependency-aware article",
            "projectCode": "demo",
        }], "knowledge")])
        self.assertEqual(controller.identity, "17")

        with patch.object(controller, "reload") as reload_catalog:
            application.sobject_delete.deletionFinished.emit("knowledge")

        self.assertEqual(controller.identity, "")
        reload_catalog.assert_called_once_with()
        controller.shutdown()

    def test_stale_knowledge_completion_preserves_unsaved_text(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._identity = "17"
        controller._editing = True
        controller._document = {
            "title": "Unsaved title",
            "kind": "article",
            "contentMarkdown": "Keep this draft",
        }
        controller._original = {
            "title": "Old title",
            "kind": "article",
            "contentMarkdown": "Old text",
        }

        controller._save_ready({
            "entryMissing": True,
            "missingIdentity": "17",
            "requestedAction": "save",
        })

        self.assertTrue(controller.editing)
        self.assertTrue(controller.localDraft)
        self.assertEqual(controller.document["title"], "Unsaved title")
        self.assertIn("remain as a local draft", controller.error)

    def test_controller_publishes_section_contents_as_its_outline(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        outline = [{
            "identity": "18",
            "title": "Child article",
            "description": "Read this first",
            "kind": "article",
            "level": 1,
        }]

        controller._load_ready({
            "identity": "17",
            "searchKey": "skey://demo/th_knowledge_article?id=17",
            "revision": "revision-1",
            "document": {
                "title": "Characters",
                "description": "Character documentation",
                "kind": "section",
                "contentMarkdown": "",
                "contentText": "",
                "parentCode": "",
                "sortOrder": 0,
            },
            "sectionContents": outline,
        })

        self.assertEqual(controller.tableOfContents, outline)

    def test_knowledge_qml_creates_at_narrow_and_wide_sizes(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        for width in (430, 1100):
            engine = QQmlEngine()
            controller = _KnowledgeStub()
            controller._identity = "SEC0001"
            controller._navigation_identity = "SEC0001"
            controller._editing = width > 500
            if width > 500:
                controller._document["contentMarkdown"] = markdown_from_rich_html(
                    '<p><img src="https://example.com/large.png" '
                    'width="320" height="180"></p><p>Body text</p>'
                )
                controller._document["contentText"] = "Body text"
                controller._uploaded_attachments.replace([{
                    "token": "attachment-1",
                    "snapshotKey": "skey://sthpw/snapshot?code=SNAP0001",
                    "title": "guide.png",
                    "extension": "PNG",
                    "sizeText": "2 KB",
                    "previewUrl": "",
                    "webUrl": "http://tactic/assets/guide.png",
                    "isImage": True,
                }])
            attachments = _AttachmentStub()
            navigation = RecordListModel((
                "identity", "title", "description", "excerpt", "kind",
                "parentCode", "sortOrder", "updatedBy", "timestamp",
                "searchKey", "depth", "hasChildren", "expanded", "draft",
                "localDraft",
            ))
            navigation.replace([{
                "identity": "SEC0001", "title": "Production",
                "description": "Pipeline and publishing guides",
                "excerpt": "", "kind": "section", "parentCode": "",
                "sortOrder": 0, "updatedBy": "admin", "timestamp": "",
                "searchKey": "skey://demo/th_knowledge_article?code=SEC0001",
                "depth": 0, "hasChildren": True, "expanded": True,
                "draft": False,
                "localDraft": False,
            }, {
                "identity": "DOC0001", "title": "Pipeline guide",
                "description": "", "excerpt": "", "kind": "article",
                "parentCode": "", "sortOrder": 0, "updatedBy": "admin",
                "timestamp": "", "searchKey": "skey://demo/th_knowledge_article?code=DOC0001",
                "depth": 0, "hasChildren": False, "expanded": True,
                "draft": False,
                "localDraft": False,
            }])
            attachments_model = RecordListModel((
                "token", "title", "path", "size", "fileType", "previewUrl",
                "status", "progress", "error", "snapshotKey", "uploadTarget",
            ))
            context = engine.rootContext()
            self.configure_icon_context(context)
            context.setContextProperty("knowledgeController", controller)
            context.setContextProperty("knowledgeNavigationModel", navigation)
            context.setContextProperty("knowledgeAttachments", attachments)
            context.setContextProperty("knowledgeAttachmentDraftModel", attachments_model)
            rich_text = RichTextDocumentController(engine)
            context.setContextProperty("knowledgeRichText", rich_text)
            context.setContextProperty("skeyPreviewResolver", _PreviewStub())
            theme_component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml")))
            theme = theme_component.createWithInitialProperties({
                "dark": width < 500
            })
            component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(self.qml / "KnowledgeBaseView.qml")))
            view = component.createWithInitialProperties({
                "theme": theme, "width": width, "height": 760,
            })
            self.assertIsNotNone(view, "\n".join(
                error.toString() for error in component.errors()))
            self.application.processEvents()
            QTest.qWait(30)
            self.assertIsNotNone(view.findChild(QObject, "knowledgeNavigationList"))
            navigation_panel = visual_child(view, "knowledgeNavigation")
            navigation_toggle = visual_child(
                view, "knowledgeToggleNavigation"
            )
            article_loader = visual_child(view, "knowledgeArticleLoader")
            self.assertIsNotNone(navigation_panel)
            self.assertIsNotNone(navigation_toggle)
            self.assertIsNotNone(article_loader)
            self.assertEqual(
                bool(navigation_toggle.property("visible")), width >= 720
            )
            feature_layout = visual_child(view, "knowledgeBaseLayout")
            dock_surface = visual_child(view, "knowledgeDockSurface")
            self.assertIsNotNone(feature_layout)
            self.assertIsNotNone(dock_surface)
            self.assertAlmostEqual(
                feature_layout.y() + feature_layout.height(),
                view.height() - 8,
            )
            self.assertAlmostEqual(dock_surface.height(), view.height())
            expected_corner = max(
                0.0, float(theme.property("surfaceRadius")) - 1.0
            )
            self.assertEqual(dock_surface.property("topLeftRadius"), 0.0)
            self.assertEqual(dock_surface.property("topRightRadius"), 0.0)
            self.assertAlmostEqual(
                dock_surface.property("bottomLeftRadius"), expected_corner
            )
            self.assertAlmostEqual(
                dock_surface.property("bottomRightRadius"), expected_corner
            )
            footer_divider = visual_child(
                dock_surface, "dockWorkspaceFooterDivider"
            )
            self.assertIsNotNone(footer_divider)
            self.assertFalse(footer_divider.property("visible"))
            section_description = visual_child(
                view, "knowledgeSectionDescription-SEC0001"
            )
            section_disclosure = visual_child(
                view, "knowledgeSectionDisclosure-SEC0001"
            )
            self.assertIsNotNone(section_description)
            self.assertIsNotNone(section_disclosure)
            self.assertTrue(section_description.property("visible"))
            self.assertEqual(
                section_description.property("text"),
                "Pipeline and publishing guides",
            )
            self.assertEqual(
                section_disclosure.property("iconName"), "chevron-down"
            )
            if width > 500:
                self.assertIsNotNone(visual_child(
                    view, "knowledgeUploadAttachments"
                ))
                self.assertIsNone(visual_child(
                    view, "knowledgeUploadImage"
                ))
                self.assertIsNone(visual_child(
                    view, "knowledgeUploadFile"
                ))
                self.assertIsNotNone(visual_child(
                    view, "knowledgeInsertAttachment"
                ))
                self.assertIsNotNone(visual_child(
                    view, "knowledgeCopyAttachmentLink"
                ))
                self.assertIsNotNone(visual_child(
                    view, "knowledgeDeleteAttachment"
                ))
            selected_row = visual_child(
                view, "knowledgeNavigationRow-SEC0001"
            )
            selected_title = visual_child(
                view, "knowledgeNavigationTitle-SEC0001"
            )
            self.assertIsNotNone(selected_row, [
                child.objectName()
                for child in view.findChildren(QObject)
                if child.objectName().startswith("knowledgeNavigation")
            ])
            self.assertIsNotNone(selected_title)
            self.assertTrue(selected_row.property("selected"))
            self.assertFalse(selected_row.property("railVisible"))
            self.assertEqual(selected_row.property("borderWidth"), 0)
            self.assertEqual(
                selected_row.property("baseColor"),
                theme.property("surfaceContainerHigh"),
            )
            self.assertNotEqual(
                selected_row.property("baseColor"), theme.property("selected")
            )
            self.assertEqual(
                selected_title.property("color"),
                theme.property("primaryText"),
            )
            save_order = view.findChild(
                QObject, "knowledgeSaveOrganization"
            )
            discard_order = view.findChild(
                QObject, "knowledgeDiscardOrganization"
            )
            self.assertIsNotNone(save_order)
            self.assertIsNotNone(discard_order)
            self.assertFalse(save_order.property("visible"))
            self.assertFalse(discard_order.property("visible"))
            controller._organization_dirty = True
            controller.stateChanged.emit()
            self.application.processEvents()
            self.assertTrue(save_order.property("visible"))
            self.assertTrue(discard_order.property("visible"))
            controller._organization_dirty = False
            controller.stateChanged.emit()
            self.application.processEvents()
            if width < 500:
                controller._open_article_pending = True
                controller.stateChanged.emit()
                self.application.processEvents()
                self.assertFalse(controller.openArticlePending)
                self.assertEqual(
                    controller.article_open_acknowledgements, 1
                )
                self.assertIsNotNone(visual_child(
                    view, "knowledgeViewerBack"
                ))
            if width > 500:
                editor = view.findChild(QObject, "knowledgeRichTextEditor")
                self.assertIsNotNone(editor)
                self.assertTrue(rich_text.attached)
                toolbar = view.findChild(
                    QObject, "knowledgeRichTextToolbar"
                )
                text_style = visual_child(toolbar, "knowledgeTextStyle")
                list_style = visual_child(toolbar, "knowledgeListStyle")
                content_mode = visual_child(
                    toolbar, "knowledgeContentMode"
                )
                first_action = visual_child(
                    toolbar, "knowledgeToolbarAction-undo"
                )
                self.assertIsNotNone(toolbar)
                self.assertIsNotNone(text_style)
                self.assertIsNotNone(list_style)
                self.assertIsNotNone(content_mode)
                self.assertIsNotNone(first_action)
                style_position = text_style.mapToItem(
                    toolbar, QPointF(0, 0)
                )
                action_position = first_action.mapToItem(
                    toolbar, QPointF(0, 0)
                )
                self.assertAlmostEqual(
                    style_position.y(), action_position.y(), delta=0.5
                )
                self.assertLessEqual(
                    style_position.y() + text_style.height(),
                    toolbar.height() + 0.5,
                )
                mode_position = content_mode.mapToItem(
                    toolbar, QPointF(0, 0)
                )
                self.assertTrue(content_mode.property("visible"))
                self.assertEqual(
                    bool(content_mode.property("iconOnly")),
                    toolbar.width() < 460,
                )
                self.assertLessEqual(
                    mode_position.x() + content_mode.width(),
                    toolbar.width() + 0.5,
                )
                self.assertLessEqual(toolbar.height(), 52)
                fontawesome = json.loads((
                    Path(__file__).parents[1]
                    / "thlib/ui/assets/fonts/"
                    "fontawesome5-solid-webfont-charmap.json"
                ).read_text(encoding="utf-8"))
                expected_icons = {
                    "undo": "undo",
                    "redo": "redo",
                    "bold": "bold",
                    "italic": "italic",
                    "link": "link",
                    "attach": "attachments-editor",
                }
                for action, icon_name in expected_icons.items():
                    button = visual_child(
                        toolbar, "knowledgeToolbarAction-" + action
                    )
                    self.assertIsNotNone(button)
                    self.assertEqual(button.property("iconName"), icon_name)
                    glyph = visual_child(button, "materialIconGlyph")
                    self.assertIsNotNone(glyph)
                    resolved_name = str(
                        glyph.property("fontAwesomeName") or ""
                    )
                    self.assertIn(resolved_name, fontawesome)
                    self.assertTrue(str(glyph.property("text") or ""))
                    self.assertFalse(glyph.property("useMaterial"))
                style_label = visual_child(
                    text_style, "knowledgeTextStyleLabel"
                )
                fallback_glyph = visual_child(
                    text_style, "materialIconGlyph"
                )
                self.assertIsNotNone(style_label)
                self.assertEqual(style_label.property("text"), "Aa")
                self.assertIsNotNone(fallback_glyph)
                self.assertFalse(
                    fallback_glyph.parent().property("visible")
                )
                self.assertIsNone(visual_child(
                    toolbar, "knowledgeHeading-H1"
                ))
                kind_icon = view.findChild(
                    QObject, "knowledgeEditorKindIcon"
                )
                self.assertEqual(kind_icon.property("name"), "file")
                kind_glyph = visual_child(kind_icon, "materialIconGlyph")
                self.assertIsNotNone(kind_glyph)
                self.assertEqual(
                    kind_glyph.property("resolvedName"), "file"
                )
                metadata_toggle = visual_child(
                    view, "knowledgeMetadataToggle"
                )
                title_field = visual_child(view, "knowledgeTitleField")
                attachment_library = visual_child(
                    view, "knowledgeAttachmentLibrary"
                )
                editor_surface = visual_child(view, "knowledgeEditorSurface")
                self.assertIsNotNone(metadata_toggle)
                self.assertTrue(metadata_toggle.property("visible"))
                self.assertTrue(metadata_toggle.property("compact"))
                self.assertEqual(
                    metadata_toggle.property("text"),
                    "Show title and summary",
                )
                metadata_glyph = visual_child(
                    metadata_toggle, "materialIconGlyph"
                )
                self.assertIsNotNone(metadata_glyph)
                self.assertEqual(
                    metadata_glyph.property("resolvedName"),
                    "chevron-down",
                )
                self.assertIsNotNone(title_field)
                self.assertFalse(title_field.property("visible"))
                self.assertIsNotNone(attachment_library)
                self.assertFalse(attachment_library.property("visible"))
                self.assertIsNotNone(editor_surface)
                window = QQuickWindow()
                window.resize(width, 760)
                view.setParentItem(window.contentItem())
                window.show()
                self.assertTrue(QTest.qWaitForWindowExposed(window))

                initial_article_x = article_loader.x()
                initial_article_width = article_loader.width()
                toggle_point = navigation_toggle.mapToScene(QPointF(
                    navigation_toggle.width() / 2,
                    navigation_toggle.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=toggle_point.toPoint()
                )
                self.application.processEvents()
                self.assertFalse(navigation_panel.property("visible"))
                self.assertEqual(
                    navigation_toggle.property("iconName"), "chevron-right"
                )
                self.assertLess(article_loader.x(), initial_article_x)
                self.assertGreater(article_loader.width(), initial_article_width)

                navigation_toggle.forceActiveFocus()
                QTest.keyClick(window, Qt.Key_Space)
                self.application.processEvents()
                self.assertTrue(navigation_panel.property("visible"))
                self.assertEqual(
                    navigation_toggle.property("iconName"), "chevron-left"
                )

                metadata_point = metadata_toggle.mapToScene(QPointF(
                    metadata_toggle.width() / 2,
                    metadata_toggle.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton,
                    pos=metadata_point.toPoint(),
                )
                self.application.processEvents()
                self.assertTrue(title_field.property("visible"))
                self.assertEqual(
                    metadata_toggle.property("text"),
                    "Hide title and summary",
                )
                self.assertEqual(
                    metadata_glyph.property("resolvedName"),
                    "chevron-up",
                )
                QTest.mouseClick(
                    window, Qt.LeftButton,
                    pos=metadata_point.toPoint(),
                )
                self.application.processEvents()
                self.assertFalse(title_field.property("visible"))
                self.assertGreaterEqual(editor_surface.height(), 500)

                editor_document = rich_text._live_document()
                editor_document.addResource(
                    QTextDocument.ImageResource,
                    QUrl("https://example.com/large.png"),
                    QImage(1280, 720, QImage.Format_ARGB32),
                )
                editor_document.markContentsDirty(
                    0, editor_document.characterCount()
                )
                self.assertTrue(rich_text.select_image_at(0, 560.0))
                self.application.processEvents()
                image_frame = visual_child(
                    view, "knowledgeSelectedImageFrame"
                )
                resize_handle = visual_child(
                    view, "knowledgeImageResizeHandle"
                )
                image_metrics = visual_child(
                    view, "knowledgeSelectedImageMetrics"
                )
                image_size = visual_child(
                    view, "knowledgeSelectedImageSize"
                )
                image_width_mode = visual_child(
                    view, "knowledgeImageContentWidth"
                )
                image_width_slider = visual_child(
                    view, "knowledgeImageWidthSlider"
                )
                self.assertIsNotNone(image_frame)
                self.assertIsNotNone(resize_handle)
                self.assertIsNotNone(image_metrics)
                self.assertIsNotNone(image_size)
                self.assertIsNotNone(image_width_mode)
                self.assertIsNotNone(image_width_slider)
                self.assertTrue(image_frame.property("visible"))
                self.assertTrue(image_metrics.property("visible"))
                self.assertIn("320 × 180 px", image_size.property("text"))
                self.assertIn("1280 × 720 px", image_size.property("text"))
                self.assertFalse(image_width_mode.property("checked"))
                width_before_key = rich_text.selectedImageWidth
                image_width_slider.forceActiveFocus()
                QTest.keyClick(window, Qt.Key_Left)
                self.application.processEvents()
                self.assertLess(
                    rich_text.selectedImageWidth, width_before_key
                )
                image_point = image_frame.mapToScene(QPointF(
                    image_frame.width() / 2,
                    image_frame.height() / 2,
                ))
                rich_text.clear_image_selection()
                self.application.processEvents()
                self.assertFalse(image_frame.property("visible"))
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=image_point.toPoint()
                )
                self.application.processEvents()
                self.assertTrue(rich_text.imageSelected)
                self.assertTrue(image_frame.property("visible"))

                initial_image_width = rich_text.selectedImageWidth
                handle_point = resize_handle.mapToScene(QPointF(
                    resize_handle.width() / 2,
                    resize_handle.height() / 2,
                )).toPoint()
                QTest.mousePress(
                    window, Qt.LeftButton, pos=handle_point
                )
                QTest.mouseMove(
                    window,
                    handle_point + QPoint(70, 40),
                    delay=30,
                )
                QTest.mouseRelease(
                    window,
                    Qt.LeftButton,
                    pos=handle_point + QPoint(70, 40),
                )
                self.application.processEvents()
                self.assertGreater(
                    rich_text.selectedImageWidth, initial_image_width
                )
                self.assertAlmostEqual(
                    rich_text.selectedImageHeight
                    / rich_text.selectedImageWidth,
                    180.0 / 320.0,
                    places=2,
                )
                self.assertIn(
                    str(round(rich_text.selectedImageWidth)),
                    image_size.property("text"),
                )

                drag_start = image_frame.mapToScene(QPointF(
                    image_frame.width() / 2,
                    image_frame.height() / 2,
                )).toPoint()
                drag_target = editor.mapToScene(QPointF(
                    40,
                    image_frame.y() + image_frame.height() + 48,
                )).toPoint()
                drop_indicator = visual_child(
                    image_frame, "knowledgeImageDropIndicator"
                )
                self.assertIsNotNone(drop_indicator)
                QTest.mousePress(
                    window, Qt.LeftButton, pos=drag_start
                )
                QTest.mouseMove(window, drag_target, delay=30)
                self.application.processEvents()
                self.assertTrue(drop_indicator.property("visible"))
                QTest.mouseRelease(
                    window, Qt.LeftButton, pos=drag_target
                )
                self.application.processEvents()
                self.assertGreater(rich_text.selectedImagePosition, 0)
                self.assertFalse(drop_indicator.property("visible"))

                body_position = rich_text._live_document().toPlainText().index(
                    "Body text"
                )
                body_rect = editor.positionToRectangle(body_position + 2)
                body_point = editor.mapToScene(QPointF(
                    body_rect.x() + 3,
                    body_rect.y() + body_rect.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=body_point.toPoint()
                )
                self.application.processEvents()
                self.assertFalse(rich_text.imageSelected)
                self.assertTrue(editor.property("activeFocus"))
                caret_position = editor.property("cursorPosition")

                attachment_button = visual_child(
                    toolbar, "knowledgeToolbarAction-attach"
                )
                attachment_point = attachment_button.mapToScene(QPointF(
                    attachment_button.width() / 2,
                    attachment_button.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton,
                    pos=attachment_point.toPoint(),
                )
                self.application.processEvents()
                self.assertTrue(attachment_library.property("visible"))
                self.assertEqual(
                    (
                        editor.property("cursorPosition"),
                        editor.property("selectionStart"),
                        editor.property("selectionEnd"),
                    ),
                    (caret_position, caret_position, caret_position),
                )
                insert_attachment = visual_child(
                    attachment_library, "knowledgeInsertAttachment"
                )
                self.assertIsNotNone(insert_attachment)
                insert_point = insert_attachment.mapToScene(QPointF(
                    insert_attachment.width() / 2,
                    insert_attachment.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=insert_point.toPoint()
                )
                self.application.processEvents()
                inserted_html = rich_text.html()
                self.assertEqual(
                    inserted_html.count("guide.png"), 1, inserted_html
                )
                self.assertEqual(
                    rich_text.selectedImagePosition, caret_position
                )
                self.assertEqual(
                    (
                        editor.property("selectionStart"),
                        editor.property("selectionEnd"),
                    ),
                    (caret_position, caret_position + 1),
                )
                inserted_width = rich_text.selectedImageWidth
                image_width_slider.forceActiveFocus()
                QTest.keyClick(window, Qt.Key_Left)
                self.application.processEvents()
                self.assertTrue(rich_text.imageSelected)
                self.assertLess(rich_text.selectedImageWidth, inserted_width)
                close_attachments = visual_child(
                    attachment_library, "knowledgeCloseAttachments"
                )
                self.assertIsNotNone(close_attachments)
                close_point = close_attachments.mapToScene(QPointF(
                    close_attachments.width() / 2,
                    close_attachments.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton,
                    pos=close_point.toPoint(),
                )
                self.application.processEvents()
                self.assertFalse(attachment_library.property("visible"))

                disclosure_point = section_disclosure.mapToScene(QPointF(
                    section_disclosure.width() / 2,
                    section_disclosure.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton,
                    pos=disclosure_point.toPoint(),
                )
                self.application.processEvents()
                self.assertEqual(controller.toggle_calls, ["SEC0001"])
                self.assertEqual(controller.selected_identities, [])

                article_row = visual_child(
                    view, "knowledgeNavigationRow-DOC0001"
                )
                self.assertIsNotNone(article_row)
                article_point = article_row.mapToScene(QPointF(
                    article_row.width() / 2,
                    article_row.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=article_point.toPoint()
                )
                self.application.processEvents()
                self.assertEqual(controller.identity, "DOC0001")
                self.assertTrue(article_row.property("selected"))
                self.assertFalse(article_row.property("railVisible"))
                self.assertEqual(article_row.property("borderWidth"), 0)

                section_point = selected_row.mapToScene(QPointF(
                    selected_row.width() / 2,
                    selected_row.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=section_point.toPoint()
                )
                self.application.processEvents()
                self.assertEqual(controller.navigationIdentity, "SEC0001")
                self.assertTrue(selected_row.property("selected"))
                self.assertFalse(selected_row.property("railVisible"))
                self.assertFalse(article_row.property("selected"))

                archive_action = view.findChild(
                    QObject, "knowledgeArchiveAction"
                )
                self.assertIsNotNone(archive_action)
                self.assertEqual(
                    archive_action.property("text"), "Delete article"
                )
                previous_delete_calls = controller.delete_calls
                archive_action.clicked.emit()
                self.application.processEvents()
                self.assertEqual(
                    controller.delete_calls, previous_delete_calls + 1
                )

                controller._error = "Archive failed"
                controller.stateChanged.emit()
                self.application.processEvents()
                error_text = view.findChild(QObject, "knowledgeErrorText")
                error_dismiss = view.findChild(
                    QObject, "knowledgeErrorDismiss"
                )
                self.assertIsNotNone(error_text)
                self.assertIsNotNone(error_dismiss)
                self.assertNotEqual(
                    error_text.property("color"), theme.property("error")
                )
                dismiss_point = error_dismiss.mapToScene(QPointF(
                    error_dismiss.width() / 2,
                    error_dismiss.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=dismiss_point.toPoint()
                )
                self.application.processEvents()
                self.assertEqual(controller.error, "")

                window.hide()
                view.setParentItem(None)
                window.deleteLater()
            view.deleteLater()
            theme.deleteLater()

    def test_article_surface_survives_ancestor_visibility_cycle(self):
        engine = QQmlEngine()
        controller = _KnowledgeStub()
        navigation = RecordListModel((
            "identity", "title", "description", "excerpt", "kind",
            "parentCode", "sortOrder", "updatedBy", "timestamp",
            "searchKey", "depth", "hasChildren", "expanded", "draft",
            "localDraft",
        ))
        attachment_drafts = RecordListModel((
            "token", "title", "path", "size", "fileType", "previewUrl",
            "status", "progress", "error", "snapshotKey", "uploadTarget",
        ))
        context = engine.rootContext()
        self.configure_icon_context(context)
        context.setContextProperty("knowledgeController", controller)
        context.setContextProperty("knowledgeNavigationModel", navigation)
        context.setContextProperty("knowledgeAttachments", _AttachmentStub())
        context.setContextProperty(
            "knowledgeAttachmentDraftModel", attachment_drafts
        )
        context.setContextProperty(
            "knowledgeRichText", RichTextDocumentController(engine)
        )
        context.setContextProperty("skeyPreviewResolver", _PreviewStub())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(self.qml / "KnowledgeBaseView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme, "width": 1000, "height": 760,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(1000, 760)
        view.setParentItem(window.contentItem())
        window.show()
        self.application.processEvents()

        article_loader = view.findChild(QObject, "knowledgeArticleLoader")
        self.assertIsNotNone(article_loader)
        article = article_loader.property("item")
        self.assertIsNotNone(article)
        article_pointer = shiboken6.getCppPointer(article)[0]
        view.setVisible(False)
        self.application.processEvents()
        self.assertTrue(shiboken6.isValid(article))
        self.assertIsNotNone(article_loader.property("item"))
        self.assertEqual(
            shiboken6.getCppPointer(article_loader.property("item"))[0],
            article_pointer,
        )

        view.setVisible(True)
        self.application.processEvents()
        self.assertEqual(
            shiboken6.getCppPointer(article_loader.property("item"))[0],
            article_pointer,
        )

        controller._editing = True
        controller.stateChanged.emit()
        self.application.processEvents()
        editor = article_loader.property("item")
        self.assertIsNotNone(editor)
        editor_pointer = shiboken6.getCppPointer(editor)[0]
        self.assertNotEqual(editor_pointer, article_pointer)
        view.setVisible(False)
        self.application.processEvents()
        self.assertTrue(shiboken6.isValid(editor))
        self.assertEqual(
            shiboken6.getCppPointer(article_loader.property("item"))[0],
            editor_pointer,
        )
        view.setVisible(True)
        self.application.processEvents()
        self.assertEqual(
            shiboken6.getCppPointer(article_loader.property("item"))[0],
            editor_pointer,
        )

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        theme.deleteLater()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_article_viewer_back_covers_the_complete_narrow_layout(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        engine = QQmlEngine()
        controller = _KnowledgeStub()
        context = engine.rootContext()
        self.configure_icon_context(context)
        context.setContextProperty("skeyPreviewResolver", _PreviewStub())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleViewer.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "width": 640,
            "height": 520,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        back_requests = []
        view.backRequested.connect(lambda: back_requests.append(True))
        window = QQuickWindow()
        try:
            window.resize(640, 520)
            view.setParentItem(window.contentItem())
            window.show()
            self.application.processEvents()

            back = visual_child(view, "knowledgeViewerBack")
            delete_action = visual_child(view, "knowledgeViewerDelete")
            self.assertIsNotNone(back)
            self.assertIsNotNone(delete_action)
            self.assertTrue(back.property("visible"))
            self.assertTrue(delete_action.property("visible"))
            self.assertEqual(
                delete_action.property("text"), "Delete article"
            )
            delete_point = delete_action.mapToScene(QPointF(
                delete_action.width() / 2,
                delete_action.height() / 2,
            ))
            QTest.mouseClick(
                window, Qt.LeftButton, pos=delete_point.toPoint()
            )
            self.application.processEvents()
            self.assertEqual(controller.delete_calls, 1)
            point = back.mapToScene(QPointF(
                back.width() / 2, back.height() / 2,
            ))
            QTest.mouseClick(
                window, Qt.LeftButton, pos=point.toPoint()
            )
            self.application.processEvents()
            self.assertEqual(back_requests, [True])

            view.setWidth(760)
            window.resize(760, 520)
            self.application.processEvents()
            self.assertFalse(back.property("visible"))
        finally:
            window.hide()
            view.setParentItem(None)
            window.deleteLater()
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_mouse_drag_moves_article_into_section(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        messages = []
        previous_handler = qInstallMessageHandler(
            lambda _kind, _context, message: messages.append(str(message))
        )
        engine = QQmlEngine()
        controller = _KnowledgeStub()
        controller._dirty = False
        controller._identity = "DOC0001"
        controller._navigation_identity = "DOC0001"
        navigation = RecordListModel((
            "identity", "title", "description", "excerpt", "kind",
            "parentCode", "sortOrder", "updatedBy", "timestamp",
            "searchKey", "depth", "hasChildren", "expanded", "draft",
            "localDraft",
        ))
        navigation.replace([{
            "identity": "SEC0001", "title": "Production",
            "description": "Pipeline guides", "excerpt": "",
            "kind": "section", "parentCode": "", "sortOrder": 10,
            "updatedBy": "admin", "timestamp": "",
            "searchKey": "skey://demo/th_knowledge_article?code=SEC0001",
            "depth": 0, "hasChildren": False, "expanded": True,
            "draft": False,
            "localDraft": False,
        }, {
            "identity": "DOC0001", "title": "Pipeline guide",
            "description": "", "excerpt": "", "kind": "article",
            "parentCode": "", "sortOrder": 20, "updatedBy": "admin",
            "timestamp": "",
            "searchKey": "skey://demo/th_knowledge_article?code=DOC0001",
            "depth": 0, "hasChildren": False, "expanded": True,
            "draft": False,
            "localDraft": False,
        }])
        context = engine.rootContext()
        self.configure_icon_context(context)
        context.setContextProperty("knowledgeNavigationModel", navigation)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(self.qml / "KnowledgeNavigation.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "width": 420,
            "height": 520,
        })
        window = QQuickWindow()
        try:
            self.assertIsNotNone(view, "\n".join(
                error.toString() for error in component.errors()
            ))
            window.resize(420, 520)
            view.setParentItem(window.contentItem())
            window.show()
            self.application.processEvents()
            QTest.qWait(30)

            section_row = visual_child(
                view, "knowledgeNavigationRow-SEC0001"
            )
            article_row = visual_child(
                view, "knowledgeNavigationRow-DOC0001"
            )
            self.assertIsNotNone(section_row)
            self.assertIsNotNone(article_row)
            start = article_row.mapToScene(QPointF(
                article_row.width() / 2,
                article_row.height() / 2,
            )).toPoint()
            destination = section_row.mapToScene(QPointF(
                section_row.width() / 2,
                section_row.height() / 2,
            )).toPoint()
            QTest.mousePress(window, Qt.LeftButton, pos=start)
            QTest.mouseMove(window, start + QPointF(24, 0).toPoint(), 8)
            QTest.mouseMove(window, destination, 8)
            QTest.mouseRelease(window, Qt.LeftButton, pos=destination)
            self.application.processEvents()

            self.assertEqual(
                controller.move_calls,
                [("DOC0001", "SEC0001", "inside")],
            )
            self.assertEqual(controller.selected_identities, [])
            self.assertTrue(controller.organizationDirty)
        finally:
            window.hide()
            if view is not None:
                view.setParentItem(None)
                view.deleteLater()
            window.deleteLater()
            theme.deleteLater()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            self.application.processEvents()
            qInstallMessageHandler(previous_handler)

        self.assertEqual(messages, [])

    def test_mouse_click_opens_page_with_real_knowledge_controller(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        application = _ApplicationStub()
        attachments = _AttachmentStub()
        rich_text = RichTextDocumentController()
        controller = KnowledgeController(
            application,
            attachments=attachments,
            rich_text_document=rich_text,
        )
        catalog = [{
            "identity": "SEC0001", "title": "Characters",
            "description": "Character documentation", "excerpt": "",
            "kind": "section", "parentCode": "", "sortOrder": 0,
            "updatedBy": "admin", "timestamp": "",
            "searchKey": "skey://demo/th_knowledge_article?code=SEC0001",
        }, {
            "identity": "DOC0001", "title": "Niki",
            "description": "Character notes", "excerpt": "",
            "kind": "article", "parentCode": "SEC0001", "sortOrder": 10,
            "updatedBy": "admin", "timestamp": "",
            "searchKey": "skey://demo/th_knowledge_article?code=DOC0001",
        }]
        controller._catalog = catalog
        controller._initialized = True
        controller._can_edit = True
        controller._rebuild_navigation()

        def complete(action, *, identity="", document=None, handler=None):
            target_identity = identity or "DOC0002"
            target_document = document or {
                "title": "Niki",
                "description": "Character notes",
                "kind": "article",
                "parentCode": "SEC0001",
                "contentMarkdown": "# Niki\n\nCharacter notes",
                "contentText": "Niki Character notes",
                "sortOrder": 10,
            }
            handler({
                "initialized": True,
                "canEdit": True,
                "canInitialize": True,
                "catalog": catalog,
                "query": "",
                "identity": target_identity,
                "searchKey": (
                    "skey://demo/th_knowledge_article?code="
                    + target_identity
                ),
                "revision": action + "-revision",
                "document": target_document,
                "sectionContents": [],
            })
            return True

        pending_requests = []

        def delayed(action, **kwargs):
            pending_requests.append(lambda: complete(action, **kwargs))
            return True

        controller._run = delayed
        engine = QQmlEngine()
        context = engine.rootContext()
        self.configure_icon_context(context)
        context.setContextProperty("knowledgeController", controller)
        context.setContextProperty(
            "knowledgeNavigationModel", controller.navigation
        )
        context.setContextProperty("knowledgeAttachments", attachments)
        context.setContextProperty(
            "knowledgeAttachmentDraftModel", RecordListModel((
                "token", "title", "path", "size", "fileType",
                "previewUrl", "status", "progress", "error",
                "snapshotKey", "uploadTarget",
            ))
        )
        context.setContextProperty("knowledgeRichText", rich_text)
        context.setContextProperty("skeyPreviewResolver", _PreviewStub())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(self.qml / "KnowledgeBaseView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme, "width": 1000, "height": 760,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(1000, 760)
        view.setParentItem(window.contentItem())
        window.show()
        self.application.processEvents()

        article_row = visual_child(
            view, "knowledgeNavigationRow-DOC0001"
        )
        self.assertIsNotNone(article_row)
        article_point = article_row.mapToScene(QPointF(
            article_row.width() / 2, article_row.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=article_point.toPoint()
        )
        self.application.processEvents()
        self.assertEqual(controller.identity, "DOC0001")
        self.assertEqual(controller.document["title"], "Niki")
        self.assertEqual(controller.displayHtml, "")
        viewer_back = visual_child(view, "knowledgeViewerBack")
        self.assertIsNotNone(viewer_back)
        self.assertFalse(viewer_back.property("visible"))
        self.assertIsNotNone(
            visual_child(view, "knowledgeViewerKindIcon")
        )
        self.assertEqual(len(pending_requests), 1)

        pending_requests.pop(0)()
        self.application.processEvents()
        self.assertIn("Character notes", controller.displayHtml)

        create_article = visual_child(view, "knowledgeCreateArticle")
        create_section = visual_child(view, "knowledgeCreateSection")
        self.assertIsNotNone(create_article)
        self.assertIsNotNone(create_section)
        self.assertEqual(create_article.property("iconName"), "create-article")
        controller._busy = True
        controller.stateChanged.emit()
        self.application.processEvents()
        self.assertTrue(create_article.property("enabled"))
        self.assertTrue(create_section.property("enabled"))
        controller._busy = False
        controller.stateChanged.emit()
        self.application.processEvents()
        create_point = create_article.mapToScene(QPointF(
            create_article.width() / 2, create_article.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=create_point.toPoint()
        )
        self.application.processEvents()
        self.assertEqual(pending_requests, [])
        self.assertTrue(controller.identity.startswith("local:"))
        self.assertTrue(controller.editing)
        self.assertTrue(controller.creating)
        self.assertFalse(controller.draft)
        self.assertTrue(controller.localDraft)
        self.assertIsNotNone(
            visual_child(view, "knowledgeArticleEditor")
        )
        creation_parent = visual_child(
            view, "knowledgeCreationParent"
        )
        creation_parent_title = visual_child(
            view, "knowledgeCreationParentTitle"
        )
        self.assertIsNotNone(creation_parent)
        self.assertIsNotNone(creation_parent_title)
        self.assertTrue(creation_parent.property("visible"))
        self.assertEqual(
            creation_parent_title.property("text"), "Characters"
        )
        creation_next = visual_child(view, "knowledgeCreationNext")
        creation_step = visual_child(view, "knowledgeCreationStep")
        title_field = visual_child(view, "knowledgeTitleField")
        editor_toolbar = visual_child(view, "knowledgeRichTextToolbar")
        attachment_library = visual_child(
            view, "knowledgeAttachmentLibrary"
        )
        self.assertIsNotNone(creation_next)
        self.assertTrue(creation_next.property("visible"))
        self.assertEqual(creation_step.property("text"), "Step 1 of 2")
        self.assertTrue(title_field.property("visible"))
        self.assertFalse(editor_toolbar.property("visible"))
        self.assertFalse(attachment_library.property("visible"))
        save_draft = visual_child(view, "knowledgeSaveDraft")
        self.assertIsNotNone(save_draft)
        self.assertTrue(save_draft.property("visible"))
        self.assertEqual(save_draft.property("text"), "Save as draft")

        next_point = creation_next.mapToScene(QPointF(
            creation_next.width() / 2,
            creation_next.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=next_point.toPoint()
        )
        self.application.processEvents()
        self.assertFalse(creation_next.property("visible"))
        self.assertEqual(creation_step.property("text"), "Step 2 of 2")
        self.assertFalse(title_field.property("visible"))
        self.assertTrue(editor_toolbar.property("visible"))
        publish = visual_child(view, "knowledgeSave")
        self.assertIsNotNone(publish)
        self.assertTrue(save_draft.property("visible"))
        self.assertEqual(save_draft.property("text"), "Save as draft")
        self.assertEqual(publish.property("text"), "Publish")
        editor_back = visual_child(view, "knowledgeEditorBack")
        self.assertIsNotNone(editor_back)
        self.assertFalse(editor_back.property("visible"))
        metadata_toggle = visual_child(view, "knowledgeMetadataToggle")
        self.assertIsNotNone(metadata_toggle)
        self.assertTrue(metadata_toggle.property("visible"))
        self.assertEqual(
            metadata_toggle.property("text"),
            "Back to title and summary",
        )
        metadata_glyph = visual_child(
            metadata_toggle, "materialIconGlyph"
        )
        self.assertIsNotNone(metadata_glyph)
        self.assertEqual(
            metadata_glyph.property("resolvedName"), "arrow-left"
        )

        local_identity = controller.identity
        view.setWidth(430)
        window.resize(430, 760)
        self.application.processEvents()
        self.assertTrue(metadata_toggle.property("compact"))
        toolbar_overflow = visual_child(
            editor_toolbar, "knowledgeToolbarOverflow"
        )
        compact_style = visual_child(
            editor_toolbar, "knowledgeTextStyle"
        )
        compact_mode = visual_child(
            editor_toolbar, "knowledgeContentMode"
        )
        compact_action = visual_child(
            editor_toolbar, "knowledgeToolbarAction-bold"
        )
        self.assertIsNotNone(toolbar_overflow)
        self.assertTrue(toolbar_overflow.property("visible"))
        self.assertIsNotNone(compact_style)
        self.assertIsNotNone(compact_mode)
        self.assertTrue(compact_mode.property("visible"))
        self.assertEqual(
            bool(compact_mode.property("iconOnly")),
            editor_toolbar.width() < 460,
        )
        self.assertAlmostEqual(
            compact_style.mapToItem(
                editor_toolbar, QPointF(0, 0)
            ).y(),
            compact_action.mapToItem(
                editor_toolbar, QPointF(0, 0)
            ).y(),
            delta=0.5,
        )
        compact_mode_position = compact_mode.mapToItem(
            editor_toolbar, QPointF(0, 0)
        )
        self.assertLessEqual(
            compact_mode_position.x() + compact_mode.width(),
            editor_toolbar.width() + 0.5,
        )
        self.assertLessEqual(editor_toolbar.height(), 52)
        editor_back = visual_child(view, "knowledgeEditorBack")
        self.assertIsNotNone(editor_back)
        self.assertTrue(editor_back.property("visible"))
        back_point = editor_back.mapToScene(QPointF(
            editor_back.width() / 2,
            editor_back.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=back_point.toPoint()
        )
        self.application.processEvents()
        self.assertFalse(controller.editing)
        self.assertTrue(controller.localDraft)
        self.assertIsNotNone(visual_child(
            view, "knowledgeNavigationRow-" + local_identity
        ))

        window.hide()
        view.setParentItem(None)
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.application.processEvents()

    def test_linked_object_header_presents_and_pages_real_previews(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        messages = []
        previous_handler = qInstallMessageHandler(
            lambda _kind, _context, message: messages.append(str(message))
        )
        engine = QQmlEngine()
        controller = _KnowledgeStub()
        controller._editing = True
        controller._document["linkedSearchKeys"] = [
            "skey://demo/assets?code=HERO",
            "skey://demo/assets?code=VILLAIN",
        ]
        controller._linked_objects = [{
            "searchKey": "skey://demo/assets?code=HERO",
            "title": "Hero asset",
            "description": "Primary character model and rig",
            "subtitle": "demo/assets",
            "previewUrl": "",
            "status": "ready",
        }]
        self.configure_icon_context(engine.rootContext())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeLinkedObjectHeader.qml"
            )),
        )
        view = None
        window = None
        try:
            view = component.createWithInitialProperties({
                "theme": theme,
                "controller": controller,
                "width": 430,
                "height": 88,
            })
            self.assertIsNotNone(view, "\n".join(
                error.toString() for error in component.errors()
            ))
            window = QQuickWindow()
            window.resize(430, 120)
            view.setParentItem(window.contentItem())
            window.show()
            self.application.processEvents()

            preview = visual_child(view, "knowledgeLinkedObjectPreview")
            title = visual_child(view, "knowledgeLinkedObjectTitle")
            description = visual_child(
                view, "knowledgeLinkedObjectDescription"
            )
            counter = visual_child(view, "knowledgeLinkedObjectCounter")
            previous = visual_child(view, "knowledgeLinkedObjectPrevious")
            next_button = visual_child(view, "knowledgeLinkedObjectNext")
            unlink_button = visual_child(
                view, "knowledgeLinkedObjectUnlink"
            )
            self.assertIsNotNone(preview)
            self.assertTrue(preview.property("visible"))
            self.assertGreater(preview.width(), 0)
            self.assertEqual(title.property("text"), "Hero asset")
            self.assertEqual(
                description.property("text"),
                "Primary character model and rig",
            )
            self.assertFalse(counter.property("visible"))
            self.assertFalse(previous.property("visible"))
            self.assertFalse(next_button.property("visible"))
            self.assertIsNotNone(unlink_button)
            self.assertTrue(unlink_button.property("visible"))

            preview_point = preview.mapToScene(QPointF(
                preview.width() / 2,
                preview.height() / 2,
            ))
            QTest.mouseClick(
                window, Qt.LeftButton, pos=preview_point.toPoint()
            )
            self.application.processEvents()
            self.assertEqual(controller.opened_references, [
                "skey://demo/assets?code=HERO",
            ])

            controller._linked_objects.append({
                "searchKey": "skey://demo/assets?code=VILLAIN",
                "title": "Villain asset",
                "description": "Secondary character model",
                "subtitle": "demo/assets",
                "previewUrl": "",
                "status": "ready",
            })
            controller.stateChanged.emit()
            self.application.processEvents()
            self.assertTrue(counter.property("visible"))
            self.assertEqual(counter.property("text"), "1 / 2")
            self.assertFalse(previous.property("enabled"))
            self.assertTrue(next_button.property("enabled"))

            next_point = next_button.mapToScene(QPointF(
                next_button.width() / 2,
                next_button.height() / 2,
            ))
            QTest.mouseClick(
                window, Qt.LeftButton, pos=next_point.toPoint()
            )
            self.application.processEvents()
            self.assertEqual(title.property("text"), "Villain asset")
            self.assertEqual(
                description.property("text"),
                "Secondary character model",
            )
            self.assertEqual(counter.property("text"), "2 / 2")
            self.assertTrue(previous.property("enabled"))
            self.assertFalse(next_button.property("enabled"))

            previous_point = previous.mapToScene(QPointF(
                previous.width() / 2,
                previous.height() / 2,
            ))
            QTest.mouseClick(
                window, Qt.LeftButton, pos=previous_point.toPoint()
            )
            self.application.processEvents()
            self.assertEqual(title.property("text"), "Hero asset")
            self.assertEqual(counter.property("text"), "1 / 2")

            unlink_point = unlink_button.mapToScene(QPointF(
                unlink_button.width() / 2,
                unlink_button.height() / 2,
            ))
            QTest.mouseClick(
                window, Qt.LeftButton, pos=unlink_point.toPoint()
            )
            self.application.processEvents()
            self.assertEqual(controller.unlinked_object_keys, [
                "skey://demo/assets?code=HERO",
            ])
            self.assertEqual(title.property("text"), "Villain asset")
            self.assertFalse(counter.property("visible"))
        finally:
            if window is not None:
                window.hide()
            if view is not None:
                view.setParentItem(None)
                view.deleteLater()
            if window is not None:
                window.deleteLater()
            theme.deleteLater()
            engine.deleteLater()
            self.application.processEvents()
            qInstallMessageHandler(previous_handler)

        self.assertEqual(messages, [])

    def test_editor_links_selection_on_demand_at_narrow_and_wide_sizes(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        messages = []
        previous_handler = qInstallMessageHandler(
            lambda _kind, _context, message: messages.append(str(message))
        )
        try:
            for width in (430, 560, 900):
                with self.subTest(width=width):
                    engine = QQmlEngine()
                    controller = _KnowledgeStub()
                    controller._editing = True
                    controller._creating = True
                    controller._parent_section = {
                        "identity": "SEC0001",
                        "title": "Characters",
                        "description": "Character documentation",
                    }
                    controller._selected_link_candidates = [{
                        "searchKey": "skey://demo/assets?code=HERO",
                        "title": "Hero asset",
                        "description": "Main character",
                    }]
                    attachments = _AttachmentStub()
                    rich_text = RichTextDocumentController(engine)
                    context = engine.rootContext()
                    self.configure_icon_context(context)
                    context.setContextProperty(
                        "knowledgeAttachments", attachments
                    )
                    context.setContextProperty(
                        "knowledgeAttachmentDraftModel", RecordListModel((
                            "token", "title", "path", "size", "fileType",
                            "previewUrl", "status", "progress", "error",
                            "snapshotKey", "uploadTarget",
                        ))
                    )
                    context.setContextProperty("knowledgeRichText", rich_text)
                    context.setContextProperty(
                        "skeyPreviewResolver", _PreviewStub()
                    )
                    theme_component = QQmlComponent(
                        engine,
                        QUrl.fromLocalFile(str(self.qml / "Theme.qml")),
                    )
                    theme = theme_component.createWithInitialProperties({
                        "dark": True
                    })
                    component = QQmlComponent(
                        engine,
                        QUrl.fromLocalFile(str(
                            self.qml / "KnowledgeArticleEditor.qml"
                        )),
                    )
                    view = component.createWithInitialProperties({
                        "theme": theme,
                        "controller": controller,
                        "width": width,
                        "height": 520,
                    })
                    self.assertIsNotNone(view, "\n".join(
                        error.toString() for error in component.errors()
                    ))
                    window = QQuickWindow()
                    window.resize(width, 520)
                    view.setParentItem(window.contentItem())
                    window.show()
                    self.assertTrue(QTest.qWaitForWindowExposed(window))
                    self.application.processEvents()

                    link_button = visual_child(
                        view, "knowledgeLinkSelectedObjects"
                    )
                    back_button = visual_child(
                        view, "knowledgeEditorBack"
                    )
                    editor_header = visual_child(
                        view, "knowledgeEditorHeader"
                    )
                    editor_title = visual_child(
                        view, "knowledgeEditorTitle"
                    )
                    cancel_action = visual_child(
                        view, "knowledgeCancelAction"
                    )
                    editor_overflow = visual_child(
                        view, "knowledgeEditorOverflow"
                    )
                    archive_action = visual_child(
                        view, "knowledgeArchiveAction"
                    )
                    linked_header = visual_child(
                        view, "knowledgeLinkedObjectHeader"
                    )
                    creation_parent = visual_child(
                        view, "knowledgeCreationParent"
                    )
                    creation_parent_title = visual_child(
                        view, "knowledgeCreationParentTitle"
                    )
                    self.assertIsNotNone(link_button)
                    self.assertIsNotNone(back_button)
                    self.assertIsNotNone(editor_header)
                    self.assertIsNotNone(editor_title)
                    self.assertIsNotNone(cancel_action)
                    self.assertIsNone(editor_overflow)
                    self.assertIsNotNone(archive_action)
                    self.assertEqual(
                        bool(back_button.property("visible")),
                        width < 720,
                    )
                    self.assertIsNotNone(linked_header)
                    self.assertIsNotNone(creation_parent)
                    self.assertIsNotNone(creation_parent_title)
                    self.assertTrue(link_button.property("visible"))
                    self.assertTrue(cancel_action.property("visible"))
                    self.assertFalse(archive_action.property("visible"))
                    self.assertFalse(linked_header.property("visible"))
                    self.assertTrue(creation_parent.property("visible"))
                    self.assertEqual(
                        creation_parent_title.property("text"), "Characters"
                    )
                    save_draft = visual_child(
                        view, "knowledgeSaveDraft"
                    )
                    self.assertIsNotNone(save_draft)
                    self.assertTrue(save_draft.property("visible"))
                    self.assertEqual(
                        save_draft.property("text"), "Save as draft"
                    )
                    header_items = [
                        item for item in (
                            back_button,
                            editor_title,
                            link_button,
                            cancel_action,
                            save_draft,
                        ) if item.property("visible")
                    ]
                    positions = []
                    for item in header_items:
                        position = item.mapToItem(
                            editor_header, QPointF(0, 0)
                        )
                        self.assertGreaterEqual(position.x(), -0.5)
                        self.assertLessEqual(
                            position.x() + item.width(),
                            editor_header.width() + 0.5,
                        )
                        positions.append((position.x(), item.width()))
                    positions.sort()
                    for previous, current in zip(
                        positions, positions[1:]
                    ):
                        self.assertGreaterEqual(
                            current[0], previous[0] + previous[1] - 0.5
                        )
                    draft_point = save_draft.mapToScene(QPointF(
                        save_draft.width() / 2,
                        save_draft.height() / 2,
                    ))
                    QTest.mouseClick(
                        window,
                        Qt.LeftButton,
                        pos=draft_point.toPoint(),
                    )
                    self.application.processEvents()
                    self.assertEqual(controller.save_draft_calls, 1)

                    button_point = link_button.mapToScene(QPointF(
                        link_button.width() / 2,
                        link_button.height() / 2,
                    ))
                    QTest.mouseClick(
                        window, Qt.LeftButton, pos=button_point.toPoint()
                    )
                    self.application.processEvents()
                    self.assertEqual(
                        controller.document["linkedSearchKeys"],
                        ["skey://demo/assets?code=HERO"],
                    )
                    self.assertFalse(link_button.property("visible"))
                    self.assertTrue(linked_header.property("visible"))

                    creation_next = visual_child(
                        view, "knowledgeCreationNext"
                    )
                    self.assertIsNotNone(creation_next)
                    next_point = creation_next.mapToScene(QPointF(
                        creation_next.width() / 2,
                        creation_next.height() / 2,
                    ))
                    QTest.mouseClick(
                        window,
                        Qt.LeftButton,
                        pos=next_point.toPoint(),
                    )
                    window.update()
                    self.application.processEvents()
                    self.assertTrue(linked_header.property("visible"))
                    unlink_button = visual_child(
                        view, "knowledgeLinkedObjectUnlink"
                    )
                    self.assertIsNotNone(unlink_button)
                    self.assertTrue(unlink_button.property("visible"))

                    publish = visual_child(view, "knowledgeSave")
                    self.assertIsNotNone(publish)
                    self.assertTrue(save_draft.property("visible"))
                    self.assertEqual(
                        save_draft.property("text"), "Save as draft"
                    )
                    self.assertEqual(publish.property("text"), "Publish")
                    if width == 900:
                        controller._creating = False
                        controller.stateChanged.emit()
                        self.application.processEvents()
                        self.assertTrue(linked_header.property("visible"))
                        self.assertTrue(unlink_button.property("visible"))
                        controller._document["linkedSearchKeys"] = []
                        controller.stateChanged.emit()
                        window.update()
                        self.application.processEvents()
                        window.grabWindow()
                        self.assertTrue(
                            archive_action.property("visible")
                        )
                        header_items = [
                            item for item in (
                                back_button,
                                editor_title,
                                link_button,
                                cancel_action,
                                archive_action,
                                publish,
                            ) if item.property("visible")
                        ]
                        positions = []
                        for item in header_items:
                            position = item.mapToItem(
                                editor_header, QPointF(0, 0)
                            )
                            self.assertGreaterEqual(position.x(), -0.5)
                            self.assertLessEqual(
                                position.x() + item.width(),
                                editor_header.width() + 0.5,
                            )
                            positions.append((position.x(), item.width()))
                        positions.sort()
                        for previous, current in zip(
                            positions, positions[1:]
                        ):
                            self.assertGreaterEqual(
                                current[0],
                                previous[0] + previous[1] - 0.5,
                                positions,
                            )
                        archive_action.clicked.emit()
                        self.application.processEvents()
                        self.assertEqual(controller.delete_calls, 1)
                    if width < 720:
                        controller._creating = False
                        controller.stateChanged.emit()
                        window.update()
                        self.application.processEvents()
                        self.assertTrue(cancel_action.property("visible"))
                        self.assertTrue(archive_action.property("visible"))
                        self.assertTrue(archive_action.property("compact"))
                        lifecycle_actions = [
                            cancel_action, archive_action, publish,
                        ]
                        positions = sorted(
                            (
                                item.mapToItem(
                                    editor_header, QPointF(0, 0)
                                ).x(),
                                item.width(),
                            )
                            for item in lifecycle_actions
                            if item.property("visible")
                        )
                        for position, item_width in positions:
                            self.assertGreaterEqual(position, -0.5)
                            self.assertLessEqual(
                                position + item_width,
                                editor_header.width() + 0.5,
                            )
                        for previous, current in zip(
                            positions, positions[1:]
                        ):
                            self.assertGreaterEqual(
                                current[0],
                                previous[0] + previous[1] - 0.5,
                            )
                        view.setProperty("editorStep", 0)
                        window.update()
                        self.application.processEvents()
                        back_point = back_button.mapToScene(QPointF(
                            back_button.width() / 2,
                            back_button.height() / 2,
                        ))
                        QTest.mouseClick(
                            window,
                            Qt.LeftButton,
                            pos=back_point.toPoint(),
                        )
                        self.application.processEvents()
                        self.assertTrue(controller.localDraft)
                        self.assertFalse(controller.editing)

                    window.hide()
                    view.setParentItem(None)
                    view.deleteLater()
                    window.deleteLater()
                    theme.deleteLater()
                    engine.deleteLater()
                    QCoreApplication.sendPostedEvents(
                        None, QEvent.DeferredDelete
                    )
                    self.application.processEvents()
        finally:
            qInstallMessageHandler(previous_handler)

        self.assertEqual(messages, [])

    def test_query_debounce_uses_supported_qtimer_api(self):
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
        )
        controller._visible = True

        controller.set_query("characters")

        self.assertTrue(controller._search_timer.isActive())
        controller._search_timer.stop()

    def test_article_reading_time_and_metadata_use_presentation_values(self):
        user_model = RecordListModel(
            ("login", "displayName"),
            [{"login": "artist", "displayName": "Anna Artist"}],
        )
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
            user_model=user_model,
        )
        controller._document = {
            "kind": "article",
            "contentText": " ".join("word" for _index in range(401)),
        }
        controller._article_metadata = {
            "author": "artist",
            "createdAt": "2026-08-30 10:00:00",
            "updatedAt": "2026-08-31 12:00:00",
        }

        self.assertEqual(controller.readingMinutes, 3)
        self.assertEqual(controller.articleMetadata["author"], "artist")
        self.assertEqual(
            controller.articleMetadata["authorDisplay"], "Anna Artist"
        )
        self.assertTrue(controller.articleMetadata["createdLabel"])
        self.assertTrue(controller.articleMetadata["updatedLabel"])

        controller._document["kind"] = "section"
        self.assertEqual(controller.readingMinutes, 0)

    def test_article_history_presents_people_and_keeps_current_document(self):
        user_model = RecordListModel(
            ("login", "displayName"),
            [
                {"login": "admin", "displayName": "Admin Pretty Name"},
                {"login": "artist", "displayName": "Anna Artist"},
            ],
        )
        controller = KnowledgeController(
            _ApplicationStub(),
            attachments=_AttachmentStub(),
            rich_text_document=RichTextDocumentController(),
            user_model=user_model,
        )
        controller._identity = "DOC0001"
        controller._document = {
            "title": "Current guide",
            "kind": "article",
            "contentMarkdown": "# Current",
            "contentText": "Current",
        }
        controller._history_ready({
            "identity": "DOC0001",
            "history": [{
                "revisionId": "TX2",
                "timestamp": "2026-08-31 12:00:00",
                "actor": "admin",
                "changedFields": ["content"],
                "action": "update",
                "current": True,
            }, {
                "revisionId": "TX1",
                "timestamp": "2026-08-30 10:00:00",
                "actor": "artist",
                "changedFields": ["name", "content"],
                "action": "create",
                "current": False,
            }],
        })

        self.assertTrue(controller.historyLoaded)
        self.assertEqual(controller.historyCount, 2)
        self.assertEqual(
            controller.history.get(1)["actorDisplay"], "Anna Artist"
        )
        self.assertEqual(
            controller.history.get(1)["summary"], "Article created"
        )
        self.assertEqual(controller.viewerDocument["title"], "Current guide")

        controller._history_revision_ready({
            "identity": "DOC0001",
            "historyRevision": {
                "revisionId": "TX1",
                "timestamp": "2026-08-30 10:00:00",
                "actor": "artist",
                "document": {
                    "title": "Earlier guide",
                    "kind": "article",
                    "contentMarkdown": "# Earlier",
                    "contentText": "Earlier",
                },
                "articleMetadata": {
                    "author": "artist",
                    "createdAt": "2026-08-30 10:00:00",
                    "updatedBy": "artist",
                    "updatedAt": "2026-08-30 10:00:00",
                },
            },
        })

        self.assertTrue(controller.historyPreviewActive)
        self.assertEqual(controller.viewerDocument["title"], "Earlier guide")
        self.assertEqual(
            controller.viewerArticleMetadata["authorDisplay"], "Anna Artist"
        )
        self.assertTrue(controller.history.get(1)["selected"])

        controller.clear_history_preview()

        self.assertFalse(controller.historyPreviewActive)
        self.assertEqual(controller.viewerDocument["title"], "Current guide")

    def test_article_viewer_uses_document_icon_and_heading_outline(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        engine = QQmlEngine()
        controller = _KnowledgeStub()
        controller._document["contentMarkdown"] = markdown_from_rich_html(
            "<h1>Publish</h1>"
            + "".join(f"<p>Preparation line {index}</p>" for index in range(70))
            + "<h2>Final checks</h2><p>Ready.</p>"
        )
        controller._document["contentText"] = "Publish Final checks"
        controller._linked_objects = [{
            "searchKey": "skey://demo/assets?code=HERO",
            "title": "Hero asset",
            "description": "Primary character model and rig",
            "subtitle": "demo/assets",
            "previewUrl": "",
            "status": "ready",
        }]
        engine.rootContext().setContextProperty(
            "skeyPreviewResolver", _PreviewStub()
        )
        self.configure_icon_context(engine.rootContext())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml")))
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleViewer.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "width": 900,
            "height": 620,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(900, 620)
        view.setParentItem(window.contentItem())
        window.show()
        self.application.processEvents()

        kind_icon = visual_child(view, "knowledgeViewerKindIcon")
        kind_surface = visual_child(view, "knowledgeViewerKindSurface")
        outline_toggle = visual_child(
            view, "knowledgeToggleTableOfContents"
        )
        history_button = visual_child(view, "knowledgeChangeHistory")
        history_popup = view.findChild(
            QObject, "knowledgeRevisionHistoryPopup"
        )
        viewer_title = visual_child(view, "knowledgeViewerTitle")
        revision_banner = visual_child(
            view, "knowledgeRevisionPreviewBanner"
        )
        back_to_current = visual_child(
            view, "knowledgeBackToCurrentRevision"
        )
        edit_action = visual_child(view, "knowledgeEdit")
        linked_header = visual_child(view, "knowledgeLinkedObjectHeader")
        side_outline = visual_child(view, "knowledgeSideTableOfContents")
        second_heading = visual_child(view, "knowledgeTocEntry-1")
        article_scroll = visual_child(view, "knowledgeArticleScroll")
        article_scrollbar = visual_child(
            view, "knowledgeArticleScrollBar"
        )
        reading_time = visual_child(view, "knowledgeReadingTime")
        metadata_footer = visual_child(
            view, "knowledgeArticleMetadataFooter"
        )
        article_author = visual_child(view, "knowledgeArticleAuthor")
        article_created = visual_child(view, "knowledgeArticleCreated")
        article_updated = visual_child(view, "knowledgeArticleUpdated")
        self.assertIsNotNone(kind_icon)
        self.assertIsNotNone(kind_surface)
        self.assertIsNotNone(outline_toggle)
        self.assertIsNotNone(history_button)
        self.assertIsNotNone(history_popup)
        self.assertIsNotNone(viewer_title)
        self.assertIsNotNone(revision_banner)
        self.assertIsNotNone(back_to_current)
        self.assertIsNotNone(edit_action)
        self.assertIsNotNone(linked_header)
        self.assertTrue(linked_header.property("visible"))
        self.assertEqual(kind_icon.property("name"), "file")
        self.assertEqual(
            kind_surface.property("color"),
            theme.property("surfaceContainerHigh"),
        )
        self.assertEqual(
            outline_toggle.property("backgroundColor"),
            theme.property("surfaceContainerHigh"),
        )
        self.assertFalse(edit_action.property("highlighted"))
        self.assertTrue(edit_action.property("tonal"))
        kind_glyph = visual_child(kind_icon, "materialIconGlyph")
        self.assertIsNotNone(kind_glyph)
        self.assertEqual(kind_glyph.property("resolvedName"), "file")
        self.assertIsNotNone(side_outline)
        self.assertTrue(side_outline.property("visible"))
        self.assertIsNotNone(second_heading)
        self.assertIsNotNone(article_scrollbar)
        self.assertIsNotNone(reading_time)
        self.assertIsNotNone(metadata_footer)
        self.assertIsNotNone(article_author)
        self.assertIsNotNone(article_created)
        self.assertIsNotNone(article_updated)
        self.assertTrue(reading_time.property("visible"))
        self.assertEqual(reading_time.property("text"), "3 min read")
        self.assertTrue(metadata_footer.property("visible"))
        self.assertEqual(
            article_author.property("text"), "Author: Admin Pretty Name"
        )
        self.assertEqual(
            article_author.property("color").toRgb().rgba(),
            theme.property("disabledText").toRgb().rgba(),
        )
        self.assertEqual(
            article_created.property("color").toRgb().rgba(),
            theme.property("disabledText").toRgb().rgba(),
        )
        self.assertEqual(
            article_updated.property("color").toRgb().rgba(),
            theme.property("disabledText").toRgb().rgba(),
        )
        self.assertEqual(
            article_created.property("text"),
            "Created: 30 August 2026, 10:00:00",
        )
        self.assertEqual(
            article_updated.property("text"),
            "Updated: 31 August 2026, 12:00:00",
        )
        self.assertTrue(article_scrollbar.property("visible"))
        self.assertAlmostEqual(
            article_scroll.property("contentWidth")
            + article_scrollbar.property("reservedExtent"),
            article_scroll.width(),
        )
        self.assertTrue(controller.display_width_requests)
        self.assertEqual(controller.display_width_requests, ["intrinsic"])
        first_article_block = visual_child(view, "knowledgeArticleText")
        self.assertIsNotNone(first_article_block)
        linked_y = linked_header.mapToScene(QPointF(0, 0)).y()
        article_scroll.setProperty("contentY", 120.0)
        self.application.processEvents()
        self.assertLess(
            linked_header.mapToScene(QPointF(0, 0)).y(),
            linked_y - 100.0,
        )
        article_scroll.setProperty("contentY", 0.0)
        self.application.processEvents()

        history_point = history_button.mapToScene(QPointF(
            history_button.width() / 2,
            history_button.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=history_point.toPoint()
        )
        QTest.qWait(80)
        self.assertTrue(history_popup.property("visible"))
        self.assertEqual(controller.history_load_calls, 1)
        popup_window = next((
            candidate for candidate in QGuiApplication.topLevelWindows()
            if candidate is not window and candidate.isVisible()
        ), None)
        self.assertIsNotNone(popup_window)
        previous_revision = visual_child(
            popup_window.contentItem(),
            "knowledgeRevisionHistoryEntry-1",
        )
        self.assertIsNotNone(previous_revision)
        previous_point = previous_revision.mapToScene(QPointF(
            previous_revision.width() / 2,
            previous_revision.height() / 2,
        ))
        QTest.mouseClick(
            popup_window, Qt.LeftButton, pos=previous_point.toPoint()
        )
        QTest.qWait(80)
        self.assertEqual(controller.history_preview_calls, ["TX1"])
        self.assertTrue(revision_banner.property("visible"))
        self.assertEqual(
            viewer_title.property("text"), "Earlier pipeline guide"
        )
        back_point = back_to_current.mapToScene(QPointF(
            back_to_current.width() / 2,
            back_to_current.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=back_point.toPoint()
        )
        self.application.processEvents()
        self.assertFalse(revision_banner.property("visible"))
        self.assertEqual(viewer_title.property("text"), "Pipeline guide")
        QTest.qWait(200)

        toggle_point = outline_toggle.mapToScene(QPointF(
            outline_toggle.width() / 2,
            outline_toggle.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=toggle_point.toPoint()
        )
        self.application.processEvents()
        self.assertFalse(side_outline.property("visible"))
        self.assertEqual(
            outline_toggle.property("toolTip"),
            "Show table of contents",
        )
        QTest.qWait(200)
        QTest.mouseClick(
            window, Qt.LeftButton, pos=toggle_point.toPoint()
        )
        self.application.processEvents()
        self.assertTrue(side_outline.property("visible"))

        second_heading = visual_child(view, "knowledgeTocEntry-1")
        self.assertIsNotNone(second_heading)
        heading_point = second_heading.mapToScene(QPointF(
            second_heading.width() / 2,
            second_heading.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=heading_point.toPoint()
        )
        self.application.processEvents()
        self.assertGreater(article_scroll.property("contentY"), 0)

        first_article_block = visual_child(view, "knowledgeArticleText")
        self.assertIsNotNone(first_article_block)
        block_requests_before_resize = len(controller.display_width_requests)
        for width in range(893, 559, -7):
            view.setWidth(width)
            window.resize(width, 620)
            self.application.processEvents()
        self.assertEqual(
            len(controller.display_width_requests),
            block_requests_before_resize,
        )
        self.assertIs(
            visual_child(view, "knowledgeArticleText"),
            first_article_block,
        )
        inline_outline = visual_child(
            view, "knowledgeInlineTableOfContents"
        )
        metadata_footer = visual_child(
            view, "knowledgeArticleMetadataFooter"
        )
        metadata_labels = [
            visual_child(view, "knowledgeArticleAuthor"),
            visual_child(view, "knowledgeArticleCreated"),
            visual_child(view, "knowledgeArticleUpdated"),
        ]
        self.assertIsNotNone(inline_outline)
        self.assertIsNotNone(metadata_footer)
        self.assertTrue(metadata_footer.property("visible"))
        self.assertAlmostEqual(
            metadata_footer.width(), article_scroll.property("contentWidth")
        )
        for label in metadata_labels:
            self.assertIsNotNone(label)
            self.assertLessEqual(
                label.x() + label.width(), label.parent().width() + 0.5
            )
        self.assertTrue(inline_outline.property("visible"))
        QTest.qWait(200)
        toggle_point = outline_toggle.mapToScene(QPointF(
            outline_toggle.width() / 2,
            outline_toggle.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.LeftButton, pos=toggle_point.toPoint()
        )
        self.application.processEvents()
        self.assertFalse(inline_outline.property("visible"))

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        theme.deleteLater()
        self.application.processEvents()

    def test_inline_outline_uses_full_width_without_scrollbar(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        translator = CatalogTranslator(
            self.qml.parent / "translations" / "ru.json"
        )
        self.application.installTranslator(translator)
        self.addCleanup(self.application.removeTranslator, translator)
        engine = QQmlEngine()
        controller = _KnowledgeStub()
        engine.rootContext().setContextProperty(
            "skeyPreviewResolver", _PreviewStub()
        )
        self.configure_icon_context(engine.rootContext())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleViewer.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "width": 560,
            "height": 620,
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(560, 620)
        view.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(60)

        article_scroll = visual_child(view, "knowledgeArticleScroll")
        article_scrollbar = visual_child(
            view, "knowledgeArticleScrollBar"
        )
        inline_outline = visual_child(
            view, "knowledgeInlineTableOfContents"
        )
        metadata_footer = visual_child(
            view, "knowledgeArticleMetadataFooter"
        )
        metadata_labels = [
            visual_child(view, "knowledgeArticleAuthor"),
            visual_child(view, "knowledgeArticleCreated"),
            visual_child(view, "knowledgeArticleUpdated"),
        ]
        self.assertIsNotNone(article_scroll)
        self.assertIsNotNone(article_scrollbar)
        self.assertIsNotNone(inline_outline)
        self.assertIsNotNone(metadata_footer)
        self.assertTrue(metadata_footer.property("visible"))
        for label in metadata_labels:
            self.assertIsNotNone(label)
            self.assertLessEqual(
                label.x() + label.width(), label.parent().width() + 0.5
            )
        self.assertTrue(inline_outline.property("visible"))
        self.assertFalse(article_scrollbar.property("visible"))
        self.assertAlmostEqual(
            article_scroll.property("contentWidth"),
            article_scroll.width(),
        )
        self.assertAlmostEqual(
            inline_outline.width(),
            article_scroll.width(),
        )

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        theme.deleteLater()
        engine.deleteLater()
        self.application.processEvents()

    def test_selected_section_shows_expanded_indented_overview(self):
        def visual_child(item, object_name):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == object_name:
                    return child
                pending.extend(child.childItems())
            return None

        engine = QQmlEngine()
        controller = _KnowledgeStub()
        controller._identity = "SEC0001"
        controller._document.update({
            "title": "Characters",
            "description": "Character documentation",
            "kind": "section",
            "contentMarkdown": "",
            "contentText": "",
        })
        controller._table_of_contents = [{
            "identity": "DOC0001",
            "title": "Hero character",
            "description": "Model and rig notes",
            "kind": "article",
            "level": 1,
        }, {
            "identity": "SEC0002",
            "title": "Background characters",
            "description": "Secondary cast",
            "kind": "section",
            "level": 1,
        }, {
            "identity": "DOC0002",
            "title": "Nested article",
            "description": "Only visible inside its subsection",
            "kind": "article",
            "level": 2,
        }]
        controller._table_of_contents.extend({
            "identity": f"DOC{index:04d}",
            "title": f"Reference page {index}",
            "description": "Section reference material",
            "kind": "article",
            "level": 1,
        } for index in range(3, 23))
        engine.rootContext().setContextProperty(
            "skeyPreviewResolver", _PreviewStub()
        )
        self.configure_icon_context(engine.rootContext())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "KnowledgeArticleViewer.qml"
            )),
        )
        for width in (900, 560, 430):
            with self.subTest(width=width):
                view = component.createWithInitialProperties({
                    "theme": theme,
                    "controller": controller,
                    "width": width,
                    "height": 620,
                })
                self.assertIsNotNone(view, "\n".join(
                    error.toString() for error in component.errors()
                ))
                window = QQuickWindow()
                window.resize(width, 620)
                view.setParentItem(window.contentItem())
                window.show()
                QTest.qWait(80)

                section_overview = visual_child(
                    view, "knowledgeSectionOverview"
                )
                section_list = visual_child(
                    view, "knowledgeSectionList"
                )
                section_scrollbar = visual_child(
                    view, "knowledgeSectionScrollBar"
                )
                first_entry = visual_child(
                    view, "knowledgeSectionEntry-DOC0001"
                )
                second_entry = visual_child(
                    view, "knowledgeSectionEntry-SEC0002"
                )
                nested_entry = visual_child(
                    view, "knowledgeSectionEntry-DOC0002"
                )
                first_surface = visual_child(
                    view, "knowledgeSectionEntrySurface-DOC0001"
                )
                second_surface = visual_child(
                    view, "knowledgeSectionEntrySurface-SEC0002"
                )
                section_icon = visual_child(
                    view, "knowledgeSectionEntryIcon-SEC0002"
                )
                section_subtitle = visual_child(
                    view, "knowledgeSectionEntrySubtitle-SEC0002"
                )
                self.assertIsNotNone(section_overview)
                self.assertTrue(section_overview.property("visible"))
                self.assertIsNotNone(section_list)
                self.assertIsNotNone(section_scrollbar)
                self.assertTrue(section_scrollbar.property("hasOverflow"))
                self.assertTrue(section_scrollbar.property("visible"))
                self.assertIsNotNone(first_entry)
                self.assertIsNotNone(second_entry)
                self.assertIsNotNone(nested_entry)
                self.assertIsNotNone(first_surface)
                self.assertIsNotNone(second_surface)
                self.assertIsNotNone(section_icon)
                self.assertIsNotNone(section_subtitle)
                self.assertEqual(first_entry.height(), 48)
                self.assertEqual(second_entry.height(), 48)
                self.assertEqual(nested_entry.height(), 48)
                self.assertEqual(first_surface.property("borderWidth"), 0)
                self.assertEqual(second_surface.property("borderWidth"), 0)
                self.assertEqual(section_icon.property("name"), "folder-open")
                self.assertTrue(
                    section_subtitle.property("text").startswith("Section")
                )
                self.assertGreater(second_entry.y(), first_entry.y())
                self.assertGreater(nested_entry.y(), second_entry.y())
                self.assertGreater(second_entry.x(), first_entry.x())
                self.assertGreater(nested_entry.x(), second_entry.x())

                entry_point = first_entry.mapToScene(QPointF(
                    first_entry.width() / 2,
                    first_entry.height() / 2,
                ))
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=entry_point.toPoint()
                )
                self.application.processEvents()

                window.hide()
                view.setParentItem(None)
                view.deleteLater()
                window.deleteLater()

        self.assertEqual(
            controller.selected_identities,
            ["DOC0001", "DOC0001", "DOC0001"],
        )
        theme.deleteLater()
        self.application.processEvents()

    def test_shared_initialization_warning_names_both_schema_changes(self):
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml")))
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "CollaborationInitializationState.qml"
            )),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "width": 720,
            "height": 600,
            "canInitialize": True,
            "featureTitle": "First run",
            "featureMessage": "Initialize collaboration features.",
            "projectCode": "demo",
        })
        self.assertIsNotNone(view, "\n".join(
            error.toString() for error in component.errors()
        ))
        window = QQuickWindow()
        window.resize(720, 600)
        view.setParentItem(window.contentItem())
        window.show()
        self.application.processEvents()

        button = view.findChild(QObject, "collaborationInitializeButton")
        confirmation = view.findChild(
            QObject, "collaborationInitializationConfirmation"
        )
        self.assertIsNotNone(button)
        self.assertIsNotNone(confirmation)
        point = button.mapToScene(QPointF(
            button.width() / 2,
            button.height() / 2,
        ))
        QTest.mouseClick(window, Qt.LeftButton, pos=point.toPoint())
        self.application.processEvents()

        self.assertTrue(confirmation.property("visible"))
        messages = view.findChild(QObject, "collaborationMessagesChange")
        knowledge = view.findChild(QObject, "collaborationKnowledgeChange")
        preservation = view.findChild(
            QObject, "collaborationPreservationNotice"
        )
        self.assertIn("sthpw/message_log", messages.property("text"))
        self.assertIn("metadata", messages.property("text"))
        self.assertIn("PROJECT/th_knowledge_article", knowledge.property("text"))
        self.assertIn("content_text", knowledge.property("text"))
        self.assertIn("Nothing is deleted", preservation.property("text"))

        window.hide()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        theme.deleteLater()
        self.application.processEvents()


if __name__ == "__main__":
    unittest.main()
