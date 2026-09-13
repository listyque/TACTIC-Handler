"""QTextDocument formatting bridge for the native QML knowledge editor."""

from __future__ import annotations

import re

import shiboken6

from PySide6.QtCore import (
    QObject,
    QPointF,
    Property,
    QRectF,
    Signal,
    Slot,
    Qt,
    QUrl,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextDocumentFragment,
    QTextFormat,
    QTextImageFormat,
    QTextLength,
    QTextListFormat,
    QTextTableFormat,
)
from PySide6.QtQuick import QQuickTextDocument

from .rich_text import (
    markdown_from_rich_html,
    plain_text_from_html,
    sanitize_rich_html,
)


_IMAGE_MINIMUM_SIZE = 24.0
_IMAGE_MAXIMUM_SIZE = 4096.0
_IMAGE_CONFIGURED_WIDTH = int(QTextFormat.UserProperty) + 1
_IMAGE_CONFIGURED_HEIGHT = int(QTextFormat.UserProperty) + 2
_IMAGE_STORAGE_SOURCE = int(QTextFormat.UserProperty) + 3
_IMAGE_CONTENT_WIDTH = int(QTextFormat.UserProperty) + 4
_IMAGE_MAXIMUM_WIDTH = int(QTextFormat.Property.ImageMaxWidth)

_MARKDOWN_IMAGE = re.compile(
    r"(?P<image>!\[(?:\\.|[^\]])*\]\((?:\\.|[^)\n])+\))"
    r"(?:\{(?P<attributes>[^}\n]+)\})?"
)
_MARKDOWN_UNDERLINE = re.compile(
    r"<u>(?P<content>.*?)</u>", re.IGNORECASE | re.DOTALL
)
_MARKDOWN_ALIGNMENT = re.compile(
    r"[ \t]+\{align=(?P<alignment>center|right|justify)\}[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
_UNDERLINE_START = "\ue100"
_UNDERLINE_END = "\ue101"
_ALIGNMENT_MARKERS = {
    "center": "\ue110",
    "right": "\ue111",
    "justify": "\ue112",
}


class RichTextDocumentController(QObject):
    """Apply semantic formatting without embedding a browser engine."""

    stateChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._document_source: QObject | None = None
        self._selection_start = 0
        self._selection_end = 0
        self._cursor_position = 0
        self._selected_image_position = -1
        self._selected_image_width = 0.0
        self._selected_image_height = 0.0
        self._selected_image_ratio = 0.0
        self._selected_image_configured_width = 0.0
        self._selected_image_configured_height = 0.0
        self._selected_image_natural_width = 0.0
        self._selected_image_natural_height = 0.0
        self._selected_image_content_width = False
        self._refreshing_image_layout = False
        self._last_image_maximum_width = 560.0
        self._typing_format: QTextCharFormat | None = None
        self._typing_position = -1
        self._applying_typing_format = False
        self._format_state = self._default_format_state()

    @Property(bool, notify=stateChanged)
    def attached(self) -> bool:
        return self._live_document() is not None

    @Property(bool, notify=stateChanged)
    def imageSelected(self) -> bool:
        return self._selected_image_position >= 0

    @Property(int, notify=stateChanged)
    def selectedImagePosition(self) -> int:
        return self._selected_image_position

    @Property(float, notify=stateChanged)
    def selectedImageWidth(self) -> float:
        return self._selected_image_width

    @Property(float, notify=stateChanged)
    def selectedImageHeight(self) -> float:
        return self._selected_image_height

    @Property(QRectF, notify=stateChanged)
    def selectedImageRect(self) -> QRectF:
        """Return the selected inline image bounds in document coordinates."""
        selected = self._selected_image_cursor()
        document = self._live_document()
        if selected is None or document is None:
            return QRectF()
        _cursor, image, image_position = selected
        return self._image_rect(document, image, image_position)

    @staticmethod
    def _image_rect(
        document: QTextDocument,
        image: QTextImageFormat,
        image_position: int,
    ) -> QRectF:
        block = document.findBlock(image_position)
        block_rect = document.documentLayout().blockBoundingRect(block)
        layout = block.layout()
        if not block.isValid() or layout is None:
            return QRectF()
        relative_position = image_position - block.position()
        line = layout.lineForTextPosition(relative_position)
        if not line.isValid():
            return QRectF()
        cursor_x = line.cursorToX(relative_position)
        if isinstance(cursor_x, tuple):
            cursor_x = cursor_x[0]
        line_origin_x = line.cursorToX(0)
        if isinstance(line_origin_x, tuple):
            line_origin_x = line_origin_x[0]
        # QTextLine.cursorToX() includes the paragraph-alignment offset even
        # though QQuick TextEdit paints inline images from the line-content
        # origin. Remove that offset while preserving any text before the
        # image on the same line.
        cursor_x = float(cursor_x) - float(line_origin_x)
        width = max(1.0, float(image.width()))
        height = max(1.0, float(image.height()))
        return QRectF(
            block_rect.x() + cursor_x,
            block_rect.y() + line.y() + max(0.0, line.ascent() - height),
            width,
            height,
        )

    @Property(float, notify=stateChanged)
    def selectedImageConfiguredWidth(self) -> float:
        return self._selected_image_configured_width

    @Property(float, notify=stateChanged)
    def selectedImageConfiguredHeight(self) -> float:
        return self._selected_image_configured_height

    @Property(float, notify=stateChanged)
    def selectedImageNaturalWidth(self) -> float:
        return self._selected_image_natural_width

    @Property(float, notify=stateChanged)
    def selectedImageNaturalHeight(self) -> float:
        return self._selected_image_natural_height

    @Property(bool, notify=stateChanged)
    def selectedImageProportional(self) -> bool:
        return self.imageSelected and self._selected_image_ratio > 0.0

    @Property(bool, notify=stateChanged)
    def selectedImageContentWidth(self) -> bool:
        return self.imageSelected and self._selected_image_content_width

    @Property("QVariantMap", notify=stateChanged)
    def formatState(self) -> dict:
        return dict(self._format_state)

    @staticmethod
    def _default_format_state() -> dict:
        return {
            "bold": False,
            "italic": False,
            "underline": False,
            "strike": False,
            "smallText": False,
            "heading": 0,
            "quote": False,
            "pullQuote": False,
            "codeBlock": False,
            "listStyle": "",
            "alignment": "left",
        }

    def _read_format_state(self) -> dict:
        cursor = self._cursor()
        if cursor is None:
            return self._default_format_state()
        character = (
            self._typing_format
            if not cursor.hasSelection() and self._typing_format is not None
            else cursor.charFormat()
        )
        block = cursor.blockFormat()
        quote_level = int(
            block.property(QTextFormat.BlockQuoteLevel) or 0
        )
        code_block = bool(block.property(QTextFormat.BlockCodeFence))
        alignment = block.alignment()
        current_list = cursor.currentList()
        list_style = current_list.format().style() if current_list else None
        checklist = block.marker() in {
            QTextBlockFormat.MarkerType.Checked,
            QTextBlockFormat.MarkerType.Unchecked,
        }
        return {
            "bold": character.fontWeight() >= QFont.DemiBold,
            "italic": character.fontItalic(),
            "underline": character.fontUnderline(),
            "strike": character.fontStrikeOut(),
            "smallText": 0.0 < character.fontPointSize() <= 9.0,
            "heading": block.headingLevel(),
            "quote": quote_level > 0 and alignment != Qt.AlignHCenter,
            "pullQuote": quote_level > 0 and alignment == Qt.AlignHCenter,
            "codeBlock": code_block,
            "listStyle": (
                "checklist" if checklist
                else "ordered"
                if list_style == QTextListFormat.ListDecimal
                else "bullet"
                if list_style == QTextListFormat.ListDisc
                else ""
            ),
            "alignment": (
                "center" if alignment == Qt.AlignHCenter
                else "right" if alignment == Qt.AlignRight
                else "justify" if alignment == Qt.AlignJustify
                else "left"
            ),
        }

    def _refresh_format_state(self) -> bool:
        state = self._read_format_state()
        if state == self._format_state:
            return False
        self._format_state = state
        return True

    def _emit_format_state_changed(self) -> None:
        self._refresh_format_state()
        self.stateChanged.emit()

    @staticmethod
    def _valid_object(value: QObject | None) -> bool:
        return bool(value is not None and shiboken6.isValid(value))

    @staticmethod
    def _source_from_wrapper(
        wrapper: QObject | None,
    ) -> QObject | None:
        if not isinstance(wrapper, (QTextDocument, QQuickTextDocument)):
            return None
        return wrapper if shiboken6.isValid(wrapper) else None

    @classmethod
    def _document_for_source(
        cls, source: QObject | None,
    ) -> QTextDocument | None:
        if not cls._valid_object(source):
            return None
        if isinstance(source, QTextDocument):
            return source
        getter = getattr(source, "textDocument", None)
        if not callable(getter):
            return None
        try:
            document = getter()
        except RuntimeError:
            return None
        return (
            document
            if isinstance(document, QTextDocument)
            and shiboken6.isValid(document)
            else None
        )

    def _reset_selection(self) -> None:
        self._selection_start = 0
        self._selection_end = 0
        self._cursor_position = 0
        self._typing_format = None
        self._typing_position = -1
        self._format_state = self._default_format_state()
        self._reset_image_selection()

    def _reset_image_selection(self) -> None:
        self._selected_image_position = -1
        self._selected_image_width = 0.0
        self._selected_image_height = 0.0
        self._selected_image_ratio = 0.0
        self._selected_image_configured_width = 0.0
        self._selected_image_configured_height = 0.0
        self._selected_image_natural_width = 0.0
        self._selected_image_natural_height = 0.0
        self._selected_image_content_width = False

    def _release_document(self, *, disconnect: bool) -> bool:
        source = self._document_source
        if source is None:
            return False
        document = self._document_for_source(source)
        self._document_source = None
        self._reset_selection()
        if disconnect and self._valid_object(source):
            try:
                source.destroyed.disconnect(self._document_destroyed)
            except (RuntimeError, TypeError):
                pass
        if disconnect and document is not None:
            try:
                document.contentsChange.disconnect(
                    self._document_contents_changed
                )
            except (RuntimeError, TypeError):
                pass
            try:
                document.documentLayout().documentSizeChanged.disconnect(
                    self._document_layout_changed
                )
            except (RuntimeError, TypeError):
                pass
        return True

    def _document_destroyed(self, *_args) -> None:
        # The destroyed signal is emitted while the QQuickTextDocument wrapper
        # is already being torn down. Never call textDocument() from here.
        if self._document_source is None:
            return
        self._document_source = None
        self._reset_selection()
        self.stateChanged.emit()

    def _live_document(self) -> QTextDocument | None:
        source = self._document_source
        document = self._document_for_source(source)
        if document is not None:
            return document
        if self._release_document(disconnect=False):
            self.stateChanged.emit()
        return None

    @Slot(QQuickTextDocument)
    def attach(self, wrapper: QObject | None) -> None:
        source = self._source_from_wrapper(wrapper)
        if (
            source is self._document_source
            and self._live_document() is not None
        ):
            return
        self._release_document(disconnect=True)
        self._document_source = source
        self._reset_selection()
        if source is not None:
            source.destroyed.connect(self._document_destroyed)
            document = self._document_for_source(source)
            if document is not None:
                document.contentsChange.connect(
                    self._document_contents_changed
                )
                document.documentLayout().documentSizeChanged.connect(
                    self._document_layout_changed
                )
        self._refresh_format_state()
        self.stateChanged.emit()

    def _document_layout_changed(self, *_args) -> None:
        if self._refreshing_image_layout:
            return
        selected = self._selected_image_cursor()
        document = self._live_document()
        if selected is None or document is None:
            return
        cursor, image, image_position = selected
        natural_width, natural_height = self._image_resource_dimensions(
            document, image
        )
        if self._selected_image_height > 0.0:
            if (
                natural_width == self._selected_image_natural_width
                and natural_height == self._selected_image_natural_height
            ):
                return
            self._selected_image_natural_width = natural_width
            self._selected_image_natural_height = natural_height
            self.stateChanged.emit()
            return
        previous = (
            self._selected_image_width,
            self._selected_image_height,
            self._selected_image_natural_width,
            self._selected_image_natural_height,
        )
        self._refreshing_image_layout = True
        try:
            image, metrics, changed = self._fit_image_format(
                document,
                image,
                max(_IMAGE_MINIMUM_SIZE, self._selected_image_width),
            )
            if changed:
                cursor.setCharFormat(image)
            self._apply_selected_image_metrics(image_position, metrics)
        finally:
            self._refreshing_image_layout = False
        current = (
            self._selected_image_width,
            self._selected_image_height,
            self._selected_image_natural_width,
            self._selected_image_natural_height,
        )
        if changed or current != previous:
            self.stateChanged.emit()

    @Slot()
    def detach(self) -> None:
        if self._release_document(disconnect=True):
            self.stateChanged.emit()

    @Slot(int, int, int)
    def sync_selection(self, cursor_position: int, start: int, end: int) -> None:
        next_position = max(0, int(cursor_position))
        next_start = max(0, int(start))
        next_end = max(0, int(end))
        changed = (
            next_position,
            next_start,
            next_end,
        ) != (
            self._cursor_position,
            self._selection_start,
            self._selection_end,
        )
        self._cursor_position = next_position
        self._selection_start = next_start
        self._selection_end = next_end
        if self._typing_format is not None and (
            next_start != next_end or next_position != self._typing_position
        ):
            self._typing_format = None
            self._typing_position = -1
            changed = True
        format_changed = self._refresh_format_state()
        image_position = self._selected_image_position
        if image_position < 0:
            if changed or format_changed:
                self.stateChanged.emit()
            return
        selection_start = min(self._selection_start, self._selection_end)
        selection_end = max(self._selection_start, self._selection_end)
        if (
            selection_start == image_position
            and selection_end == image_position + 1
        ):
            if changed or format_changed:
                self.stateChanged.emit()
            return
        self._reset_image_selection()
        self.stateChanged.emit()

    def _document_contents_changed(
        self, position: int, removed: int, added: int,
    ) -> None:
        if self._typing_format is None or self._applying_typing_format:
            return
        position = int(position)
        removed = int(removed)
        added = int(added)
        if (
            removed > 0
            and added == 0
            and position + removed == self._typing_position
        ):
            self._typing_position = position
            self._emit_format_state_changed()
            return
        if position != self._typing_position:
            self._typing_format = None
            self._typing_position = -1
            self._emit_format_state_changed()
            return
        self._typing_position = position + added
        if added <= 0:
            self._emit_format_state_changed()
            return
        document = self._live_document()
        if document is None:
            return
        end = position + added
        if position < 0 or end > document.characterCount() - 1:
            self._typing_format = None
            self._typing_position = -1
            self._emit_format_state_changed()
            return
        cursor = QTextCursor(document)
        cursor.setPosition(position)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self._applying_typing_format = True
        try:
            cursor.mergeCharFormat(self._typing_format)
        finally:
            self._applying_typing_format = False
        self._emit_format_state_changed()

    def _image_cursor_at(
        self, position: int,
    ) -> tuple[QTextCursor, QTextImageFormat, int] | None:
        document = self._live_document()
        if document is None:
            return None
        maximum = max(0, document.characterCount() - 1)
        requested = max(0, min(int(position), maximum))
        for image_position in (
            requested, requested + 1, requested - 1,
        ):
            selected = self._image_cursor_at_exact(image_position)
            if selected is not None:
                return selected
        return None

    def _selected_image_cursor(
        self,
    ) -> tuple[QTextCursor, QTextImageFormat, int] | None:
        if self._selected_image_position < 0:
            return None
        return self._image_cursor_at_exact(self._selected_image_position)

    def _image_cursor_at_exact(
        self, image_position: int,
    ) -> tuple[QTextCursor, QTextImageFormat, int] | None:
        document = self._live_document()
        if document is None:
            return None
        maximum = max(0, document.characterCount() - 1)
        position = int(image_position)
        if (
                not 0 <= position < maximum
                or document.characterAt(position) != "\ufffc"
        ):
            return None
        probe = QTextCursor(document)
        probe.setPosition(position + 1)
        formatting = probe.charFormat()
        if not formatting.isImageFormat():
            return None
        cursor = QTextCursor(document)
        cursor.setPosition(position)
        cursor.setPosition(position + 1, QTextCursor.KeepAnchor)
        return cursor, formatting.toImageFormat(), position

    @staticmethod
    def _image_cursors(document: QTextDocument):
        cursors = []
        block = document.begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                iterator += 1
                if not fragment.isValid():
                    continue
                formatting = fragment.charFormat()
                if not formatting.isImageFormat():
                    continue
                start = fragment.position()
                stop = start + fragment.length()
                for image_position in range(start, stop):
                    cursor = QTextCursor(document)
                    cursor.setPosition(image_position)
                    cursor.setPosition(
                        image_position + 1, QTextCursor.KeepAnchor
                    )
                    cursors.append((
                        cursor,
                        formatting.toImageFormat(),
                        image_position,
                    ))
            block = block.next()
        yield from cursors

    @staticmethod
    def _format_property(image: QTextImageFormat, key: int) -> float:
        try:
            return max(0.0, float(image.property(key) or 0.0))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _image_resource_dimensions(
        document: QTextDocument,
        image: QTextImageFormat,
    ) -> tuple[float, float]:
        source = str(image.name() or "").strip()
        if not source:
            return 0.0, 0.0
        try:
            resource = document.resource(
                QTextDocument.ImageResource, QUrl(source)
            )
        except (RuntimeError, TypeError):
            return 0.0, 0.0
        dimensions = []
        for name in ("width", "height"):
            value = getattr(resource, name, 0.0)
            try:
                value = value() if callable(value) else value
                dimensions.append(max(0.0, float(value or 0.0)))
            except (RuntimeError, TypeError, ValueError):
                dimensions.append(0.0)
        return dimensions[0], dimensions[1]

    @classmethod
    def _configured_image_dimensions(
        cls,
        image: QTextImageFormat,
        natural_width: float,
        natural_height: float,
    ) -> tuple[float, float]:
        width = cls._format_property(image, _IMAGE_CONFIGURED_WIDTH)
        height = cls._format_property(image, _IMAGE_CONFIGURED_HEIGHT)
        if width <= 0.0:
            width = max(0.0, float(image.width())) or natural_width
        if height <= 0.0:
            height = max(0.0, float(image.height()))
        if (
            height <= 0.0
            and width > 0.0
            and natural_width > 0.0
            and natural_height > 0.0
        ):
            height = width * natural_height / natural_width
        return width, height

    @staticmethod
    def _image_uses_content_width(image: QTextImageFormat) -> bool:
        if image.hasProperty(_IMAGE_CONTENT_WIDTH):
            return bool(image.property(_IMAGE_CONTENT_WIDTH))
        maximum_width = image.maximumWidth()
        return (
            maximum_width.type() == QTextLength.PercentageLength
            and maximum_width.rawValue() >= 99.99
        )

    def _fit_image_format(
        self,
        document: QTextDocument,
        image: QTextImageFormat,
        maximum_width: float,
    ) -> tuple[QTextImageFormat, dict, bool]:
        limit = max(
            _IMAGE_MINIMUM_SIZE,
            min(float(maximum_width or 560.0), _IMAGE_MAXIMUM_SIZE),
        )
        natural_width, natural_height = self._image_resource_dimensions(
            document, image
        )
        configured_width, configured_height = (
            self._configured_image_dimensions(
                image, natural_width, natural_height
            )
        )
        if configured_width <= 0.0:
            configured_width = limit
        ratio = (
            configured_height / configured_width
            if configured_width > 0.0 and configured_height > 0.0
            else 0.0
        )
        content_width = self._image_uses_content_width(image)
        displayed_width = limit if content_width else min(
            configured_width, limit
        )
        displayed_height = (
            displayed_width * ratio if ratio > 0.0 else 0.0
        )
        changed = any((
            not image.hasProperty(_IMAGE_CONFIGURED_WIDTH),
            abs(self._format_property(
                image, _IMAGE_CONFIGURED_WIDTH
            ) - configured_width) > 0.01,
            abs(float(image.width()) - displayed_width) > 0.01,
            not content_width and image.hasProperty(_IMAGE_MAXIMUM_WIDTH),
        ))
        if configured_height > 0.0:
            changed = changed or any((
                not image.hasProperty(_IMAGE_CONFIGURED_HEIGHT),
                abs(self._format_property(
                    image, _IMAGE_CONFIGURED_HEIGHT
                ) - configured_height) > 0.01,
                abs(float(image.height()) - displayed_height) > 0.01,
        ))
        image.setProperty(_IMAGE_CONFIGURED_WIDTH, configured_width)
        if not content_width:
            # QTextDocument serializes a VariableLength zero as
            # ``style="max-width:"``. Qt Quick can then retain the old texture
            # even while the format reports new dimensions.
            image.clearProperty(_IMAGE_MAXIMUM_WIDTH)
        image.setWidth(displayed_width)
        if configured_height > 0.0:
            image.setProperty(_IMAGE_CONFIGURED_HEIGHT, configured_height)
            image.setHeight(displayed_height)
        metrics = {
            "configured_width": configured_width,
            "configured_height": configured_height,
            "displayed_width": displayed_width,
            "displayed_height": displayed_height,
            "natural_width": natural_width,
            "natural_height": natural_height,
            "ratio": ratio,
            "content_width": content_width,
        }
        return image, metrics, changed

    def _apply_selected_image_metrics(
        self,
        image_position: int,
        metrics: dict,
    ) -> None:
        self._selected_image_position = image_position
        self._selected_image_width = metrics["displayed_width"]
        self._selected_image_height = metrics["displayed_height"]
        self._selected_image_configured_width = metrics["configured_width"]
        self._selected_image_configured_height = metrics["configured_height"]
        self._selected_image_natural_width = metrics["natural_width"]
        self._selected_image_natural_height = metrics["natural_height"]
        self._selected_image_ratio = metrics["ratio"]
        self._selected_image_content_width = metrics["content_width"]

    @Slot(float, result=bool)
    def fit_images_to_width(self, maximum_width: float) -> bool:
        self._last_image_maximum_width = max(
            _IMAGE_MINIMUM_SIZE, float(maximum_width or 560.0)
        )
        document = self._live_document()
        if document is None:
            return False
        changed = False
        selected_metrics = None
        for cursor, image, image_position in self._image_cursors(document):
            image, metrics, image_changed = self._fit_image_format(
                document, image, maximum_width
            )
            if image_changed:
                cursor.setCharFormat(image)
                changed = True
            if image_position == self._selected_image_position:
                selected_metrics = (image_position, metrics)
        if selected_metrics is not None:
            self._apply_selected_image_metrics(*selected_metrics)
        if changed or selected_metrics is not None:
            self.stateChanged.emit()
        return changed

    @Slot(int, float, result=bool)
    def select_image_at(self, position: int, maximum_width: float) -> bool:
        selected = self._image_cursor_at(position)
        if selected is None:
            if self._selected_image_position >= 0:
                self._reset_image_selection()
                self.stateChanged.emit()
            return False
        return self._select_image_cursor(selected, maximum_width)

    def _select_image_cursor(
        self,
        selected: tuple[QTextCursor, QTextImageFormat, int],
        maximum_width: float,
    ) -> bool:
        cursor, image, image_position = selected
        document = self._live_document()
        if document is None:
            return False
        self._last_image_maximum_width = max(
            _IMAGE_MINIMUM_SIZE, float(maximum_width or 560.0)
        )
        image, metrics, changed = self._fit_image_format(
            document, image, maximum_width
        )
        if changed:
            cursor.setCharFormat(image)
        self._apply_selected_image_metrics(image_position, metrics)
        self.stateChanged.emit()
        return True

    @Slot(int, float, result=bool)
    def try_select_image_at(
        self, position: int, maximum_width: float,
    ) -> bool:
        """Select an adjacent image without clearing an existing selection."""
        selected = self._image_cursor_at(position)
        return bool(
            selected is not None
            and self._select_image_cursor(selected, maximum_width)
        )

    @Slot(float, float, float, result=bool)
    def select_image_at_point(
        self,
        x: float,
        y: float,
        maximum_width: float,
    ) -> bool:
        """Select the inline image painted at a document-space point.

        A QML ``TextEdit.positionAt()`` returns a caret boundary. For a large
        inline image that boundary can legally be before or after the object,
        so deriving image selection from the caret is unreliable. The text
        document layout owns the painted geometry and exposes the exact image
        hit test used here.
        """
        document = self._live_document()
        if document is None:
            return False
        point = QPointF(max(0.0, float(x)), max(0.0, float(y)))
        layout = document.documentLayout()
        if not str(layout.imageAt(point) or ""):
            return False
        position = layout.hitTest(point, Qt.FuzzyHit)
        if position < 0:
            return False
        return self.try_select_image_at(position, maximum_width)

    @Slot()
    def clear_image_selection(self) -> None:
        if self._selected_image_position < 0:
            return
        self._reset_image_selection()
        self.stateChanged.emit()

    @Slot(float, float)
    def begin_image_resize(
        self, displayed_width: float, displayed_height: float,
    ) -> None:
        width = max(0.0, float(displayed_width))
        height = max(0.0, float(displayed_height))
        if width > 0.0 and height > 0.0:
            self._selected_image_ratio = height / width

    @Slot(float, float, result=bool)
    def resize_selected_image(
        self, requested_width: float, maximum_width: float,
    ) -> bool:
        selected = self._selected_image_cursor()
        if selected is None:
            self._reset_image_selection()
            self.stateChanged.emit()
            return False
        cursor, image, image_position = selected
        limit = max(
            _IMAGE_MINIMUM_SIZE,
            min(float(maximum_width or 560.0), _IMAGE_MAXIMUM_SIZE),
        )
        width = max(
            _IMAGE_MINIMUM_SIZE, min(float(requested_width), limit)
        )
        ratio = self._selected_image_ratio
        if ratio <= 0.0:
            stored_width = float(image.width())
            stored_height = float(image.height())
            if stored_width > 0.0 and stored_height > 0.0:
                ratio = stored_height / stored_width
        image.setWidth(width)
        image.clearProperty(_IMAGE_MAXIMUM_WIDTH)
        image.setProperty(_IMAGE_CONFIGURED_WIDTH, width)
        height = 0.0
        if ratio > 0.0:
            height = max(1.0, width * ratio)
            image.setHeight(height)
            image.setProperty(_IMAGE_CONFIGURED_HEIGHT, height)
        cursor.setCharFormat(image)
        self._selected_image_position = image_position
        self._selected_image_width = width
        self._selected_image_height = height
        self._selected_image_configured_width = width
        self._selected_image_configured_height = height
        self._selected_image_ratio = ratio
        self._selected_image_content_width = False
        self.stateChanged.emit()
        return True

    @Slot(bool, float, result=bool)
    def set_selected_image_content_width(
        self,
        enabled: bool,
        maximum_width: float,
    ) -> bool:
        selected = self._selected_image_cursor()
        document = self._live_document()
        if selected is None or document is None:
            return False
        cursor, image, image_position = selected
        if enabled:
            image.setMaximumWidth(QTextLength(
                QTextLength.PercentageLength, 100.0
            ))
        else:
            image.clearProperty(_IMAGE_MAXIMUM_WIDTH)
        image.setProperty(_IMAGE_CONTENT_WIDTH, bool(enabled))
        image, metrics, _changed = self._fit_image_format(
            document, image, maximum_width
        )
        cursor.setCharFormat(image)
        self._apply_selected_image_metrics(image_position, metrics)
        self.stateChanged.emit()
        return True

    @Slot(int, result=bool)
    def move_selected_image(self, target_position: int) -> bool:
        """Move the selected image fragment to a document insertion point."""
        selected = self._selected_image_cursor()
        document = self._live_document()
        if selected is None or document is None:
            return False
        source_cursor, _image, source_position = selected
        maximum = max(0, document.characterCount() - 1)
        target = max(0, min(int(target_position), maximum))
        if source_position <= target <= source_position + 1:
            return False

        fragment = QTextDocumentFragment(source_cursor)
        displayed_width = max(
            _IMAGE_MINIMUM_SIZE, self._selected_image_width or 560.0
        )
        source_cursor.beginEditBlock()
        try:
            source_cursor.removeSelectedText()
            if target > source_position:
                target -= 1
            insertion_cursor = QTextCursor(document)
            insertion_cursor.setPosition(target)
            insertion_cursor.insertFragment(fragment)
        finally:
            source_cursor.endEditBlock()

        moved = self._image_cursor_at_exact(target)
        if moved is None:
            self._reset_image_selection()
            self.stateChanged.emit()
            return False
        moved_cursor, moved_image, image_position = moved
        moved_image, metrics, changed = self._fit_image_format(
            document, moved_image, displayed_width
        )
        if changed:
            moved_cursor.setCharFormat(moved_image)
        self._apply_selected_image_metrics(image_position, metrics)
        self._cursor_position = image_position + 1
        self._selection_start = image_position
        self._selection_end = image_position + 1
        self.stateChanged.emit()
        return True

    def _cursor(self) -> QTextCursor | None:
        document = self._live_document()
        if document is None:
            return None
        try:
            cursor = QTextCursor(document)
        except RuntimeError:
            if self._release_document(disconnect=False):
                self.stateChanged.emit()
            return None
        start = min(self._selection_start, self._selection_end)
        end = max(self._selection_start, self._selection_end)
        character_count = max(0, document.characterCount() - 1)
        cursor.setPosition(min(start, character_count))
        if end > start:
            cursor.setPosition(
                min(end, character_count),
                QTextCursor.KeepAnchor,
            )
        else:
            cursor.setPosition(
                min(self._cursor_position, character_count)
            )
        return cursor

    def _merge_character_format(self, formatting: QTextCharFormat) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        if cursor.hasSelection():
            self._typing_format = None
            self._typing_position = -1
            cursor.mergeCharFormat(formatting)
        else:
            current = QTextCharFormat(
                self._typing_format or cursor.charFormat()
            )
            current.merge(formatting)
            self._typing_format = current
            self._typing_position = cursor.position()
        self._emit_format_state_changed()

    @Slot()
    def toggle_bold(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        current = (
            self._typing_format
            if not cursor.hasSelection() and self._typing_format is not None
            else cursor.charFormat()
        )
        formatting = QTextCharFormat()
        formatting.setFontWeight(
            QFont.Normal
            if current.fontWeight() >= QFont.DemiBold else QFont.Bold
        )
        self._merge_character_format(formatting)

    @Slot()
    def toggle_italic(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        current = (
            self._typing_format
            if not cursor.hasSelection() and self._typing_format is not None
            else cursor.charFormat()
        )
        formatting = QTextCharFormat()
        formatting.setFontItalic(not current.fontItalic())
        self._merge_character_format(formatting)

    @Slot()
    def toggle_underline(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        current = (
            self._typing_format
            if not cursor.hasSelection() and self._typing_format is not None
            else cursor.charFormat()
        )
        formatting = QTextCharFormat()
        formatting.setFontUnderline(not current.fontUnderline())
        self._merge_character_format(formatting)

    @Slot()
    def toggle_strike(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        current = (
            self._typing_format
            if not cursor.hasSelection() and self._typing_format is not None
            else cursor.charFormat()
        )
        formatting = QTextCharFormat()
        formatting.setFontStrikeOut(not current.fontStrikeOut())
        self._merge_character_format(formatting)

    def _restore_default_font(self, cursor: QTextCursor) -> None:
        document = self._live_document()
        if document is None:
            return
        target = QTextCursor(cursor)
        if not target.hasSelection():
            target.select(QTextCursor.BlockUnderCursor)
        default = document.defaultFont()
        formatting = QTextCharFormat()
        formatting.setFontFamilies(
            default.families() or [default.family()]
        )
        formatting.setFontFixedPitch(default.fixedPitch())
        if default.pointSizeF() > 0.0:
            formatting.setFontPointSize(default.pointSizeF())
        formatting.setFontWeight(default.weight())
        target.mergeCharFormat(formatting)

    @Slot(int)
    def set_heading(self, level: int) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        level = max(0, min(6, int(level)))
        current = cursor.blockFormat()
        if level and current.headingLevel() == level:
            level = 0
        code_block = bool(current.property(QTextFormat.BlockCodeFence))
        block = QTextBlockFormat()
        block.setHeadingLevel(level)
        cursor.setBlockFormat(block)
        if code_block:
            self._restore_default_font(cursor)
        formatting = QTextCharFormat()
        formatting.setFontWeight(QFont.Bold if level else QFont.Normal)
        formatting.setFontPointSize(
            {
                1: 24.0,
                2: 19.0,
                3: 16.0,
                4: 14.0,
                5: 12.0,
                6: 11.0,
            }.get(level, 11.0)
        )
        cursor.mergeCharFormat(formatting)
        self._emit_format_state_changed()

    @Slot(str)
    def set_alignment(self, value: str) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        alignment = {
            "center": Qt.AlignHCenter,
            "right": Qt.AlignRight,
            "justify": Qt.AlignJustify,
        }.get(str(value or "").casefold(), Qt.AlignLeft)
        block = cursor.blockFormat()
        block.setAlignment(alignment)
        cursor.mergeBlockFormat(block)
        self._emit_format_state_changed()

    @staticmethod
    def _remove_selected_lists(cursor: QTextCursor) -> None:
        document = cursor.document()
        block = document.findBlock(cursor.selectionStart())
        end = max(cursor.selectionStart() + 1, cursor.selectionEnd())
        while block.isValid() and block.position() < end:
            next_block = block.next()
            current = block.textList()
            if current is not None:
                current.remove(block)
            formatting = block.blockFormat()
            formatting.setMarker(QTextBlockFormat.MarkerType.NoMarker)
            QTextCursor(block).setBlockFormat(formatting)
            block = next_block

    @Slot(str)
    def toggle_list(self, value: str) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        current = cursor.currentList()
        wanted = (
            QTextListFormat.ListDecimal
            if str(value or "").casefold() == "ordered"
            else QTextListFormat.ListDisc
        )
        if current and current.format().style() == wanted:
            self._remove_selected_lists(cursor)
        else:
            formatting = QTextListFormat()
            formatting.setStyle(wanted)
            formatting.setIndent(max(1, cursor.blockFormat().indent() + 1))
            cursor.createList(formatting)
        self._emit_format_state_changed()

    @Slot()
    def toggle_check_list(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        block = cursor.blockFormat()
        current = cursor.currentList()
        checked = block.marker() in {
            QTextBlockFormat.MarkerType.Checked,
            QTextBlockFormat.MarkerType.Unchecked,
        }
        if current and checked:
            self._remove_selected_lists(cursor)
        else:
            if not current or current.format().style() != QTextListFormat.ListDisc:
                formatting = QTextListFormat()
                formatting.setStyle(QTextListFormat.ListDisc)
                formatting.setIndent(max(1, block.indent() + 1))
                cursor.createList(formatting)
                block = cursor.blockFormat()
            block.setMarker(QTextBlockFormat.MarkerType.Unchecked)
            cursor.setBlockFormat(block)
        self._emit_format_state_changed()

    @Slot(str)
    def set_quote(self, style: str) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        current = cursor.blockFormat()
        pull_quote = str(style or "").casefold() == "pull"
        current_is_pull = current.alignment() == Qt.AlignHCenter
        if (
            current.property(QTextFormat.BlockQuoteLevel)
            and pull_quote == current_is_pull
        ):
            cursor.setBlockFormat(QTextBlockFormat())
            self._emit_format_state_changed()
            return
        code_block = bool(current.property(QTextFormat.BlockCodeFence))
        formatting = QTextBlockFormat()
        formatting.setProperty(QTextFormat.BlockQuoteLevel, 1)
        formatting.setLeftMargin(40.0)
        formatting.setRightMargin(40.0)
        formatting.setTopMargin(6.0)
        formatting.setBottomMargin(6.0)
        formatting.setBackground(QColor(128, 128, 128, 32))
        formatting.setAlignment(
            Qt.AlignHCenter if pull_quote else Qt.AlignLeft
        )
        cursor.setBlockFormat(formatting)
        if code_block or current.headingLevel():
            self._restore_default_font(cursor)
        self._emit_format_state_changed()

    @Slot()
    def set_code_block(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        current = cursor.blockFormat()
        if current.property(QTextFormat.BlockCodeFence):
            cursor.setBlockFormat(QTextBlockFormat())
            self._restore_default_font(cursor)
            self._emit_format_state_changed()
            return
        formatting = QTextBlockFormat()
        formatting.setNonBreakableLines(True)
        formatting.setProperty(QTextFormat.BlockCodeFence, "`")
        formatting.setLeftMargin(14.0)
        formatting.setRightMargin(14.0)
        formatting.setTopMargin(8.0)
        formatting.setBottomMargin(8.0)
        formatting.setBackground(QColor(128, 128, 128, 32))
        cursor.setBlockFormat(formatting)
        if current.headingLevel():
            self._restore_default_font(cursor)
        if not cursor.hasSelection():
            cursor.select(QTextCursor.BlockUnderCursor)
        character = QTextCharFormat()
        character.setFontFamilies(["monospace"])
        character.setFontFixedPitch(True)
        cursor.mergeCharFormat(character)
        self._emit_format_state_changed()

    @Slot()
    def set_small_text(self) -> None:
        cursor = self._cursor()
        document = self._live_document()
        if cursor is None or document is None:
            return
        current = (
            self._typing_format
            if not cursor.hasSelection() and self._typing_format is not None
            else cursor.charFormat()
        )
        formatting = QTextCharFormat()
        formatting.setFontPointSize(
            document.defaultFont().pointSizeF()
            if 0.0 < current.fontPointSize() <= 9.0 else 9.0
        )
        self._merge_character_format(formatting)

    @Slot()
    def insert_divider(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        if cursor.hasSelection():
            cursor.removeSelectedText()
        cursor.insertHtml("<hr>")
        self._cursor_position = cursor.position()
        self._selection_start = self._selection_end = self._cursor_position
        self._emit_format_state_changed()

    @Slot()
    def insert_table(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        if cursor.hasSelection():
            cursor.removeSelectedText()
        formatting = QTextTableFormat()
        formatting.setBorder(1.0)
        formatting.setCellPadding(5.0)
        formatting.setHeaderRowCount(1)
        formatting.setWidth(QTextLength(QTextLength.PercentageLength, 100.0))
        formatting.setColumnWidthConstraints([
            QTextLength(QTextLength.PercentageLength, 100.0 / 3.0)
            for _column in range(3)
        ])
        table = cursor.insertTable(3, 3, formatting)
        first_cell = table.cellAt(0, 0).firstCursorPosition()
        self._cursor_position = first_cell.position()
        self._selection_start = self._selection_end = self._cursor_position
        self._emit_format_state_changed()

    @staticmethod
    def _supported_link_target(target: str) -> bool:
        return (
            bool(target)
            and QUrl(target).scheme().casefold()
            in {"ftp", "http", "https", "skey", "tactic-search"}
        )

    @staticmethod
    def _link_character_format(
        document: QTextDocument,
        position: int,
    ) -> QTextCharFormat | None:
        maximum = max(0, document.characterCount() - 1)
        if not 0 <= position < maximum:
            return None
        cursor = QTextCursor(document)
        cursor.setPosition(position)
        cursor.setPosition(position + 1, QTextCursor.KeepAnchor)
        formatting = cursor.charFormat()
        if not formatting.isAnchor() or not formatting.anchorHref():
            return None
        return QTextCharFormat(formatting)

    @classmethod
    def _link_span_at(
        cls,
        document: QTextDocument,
        position: int,
        expected_target: str = "",
    ) -> tuple[int, int, str, str] | None:
        maximum = max(0, document.characterCount() - 1)
        requested = max(0, min(int(position), maximum))
        expected_target = str(expected_target or "").strip()
        match = None
        for candidate in (requested, requested - 1, requested + 1):
            formatting = cls._link_character_format(document, candidate)
            if formatting is None:
                continue
            target = str(formatting.anchorHref() or "")
            if expected_target and target != expected_target:
                continue
            match = candidate, target
            break
        if match is None:
            return None
        character_position, target = match
        start = character_position
        while start > 0:
            formatting = cls._link_character_format(document, start - 1)
            if formatting is None or formatting.anchorHref() != target:
                break
            start -= 1
        end = character_position + 1
        while end < maximum:
            formatting = cls._link_character_format(document, end)
            if formatting is None or formatting.anchorHref() != target:
                break
            end += 1
        cursor = QTextCursor(document)
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        label = cursor.selectedText().replace("\u2029", "\n")
        if "\ufffc" in label:
            return None
        return start, end, target, label

    @Slot(int, result="QVariantMap")
    @Slot(int, str, result="QVariantMap")
    def link_at(self, position: int, expected_target: str = "") -> dict:
        document = self._live_document()
        if document is None:
            return {}
        details = self._link_span_at(
            document, position, expected_target
        )
        if details is None:
            return {}
        start, end, target, label = details
        return {
            "start": start,
            "end": end,
            "target": target,
            "label": label,
        }

    @Slot(str, str)
    def insert_link(self, target: str, label: str = "") -> None:
        cursor = self._cursor()
        target = str(target or "").strip()
        if cursor is None or not self._supported_link_target(target):
            return
        text = str(label or "").strip() or cursor.selectedText() or target
        formatting = QTextCharFormat(cursor.charFormat())
        formatting.setAnchor(True)
        formatting.setAnchorHref(target)
        formatting.setFontUnderline(True)
        if cursor.hasSelection():
            cursor.insertText(text, formatting)
        else:
            cursor.insertText(text, formatting)
        self._cursor_position = cursor.position()
        self._selection_start = self._selection_end = self._cursor_position
        self._emit_format_state_changed()

    @Slot(int, int, str, str, result=bool)
    def update_link(
        self,
        start: int,
        end: int,
        target: str,
        label: str = "",
    ) -> bool:
        document = self._live_document()
        target = str(target or "").strip()
        if document is None or not self._supported_link_target(target):
            return False
        details = self._link_span_at(document, start)
        if details is None or details[0] != start or details[1] != end:
            return False
        _start, _end, _previous_target, previous_label = details
        cursor = QTextCursor(document)
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        formatting = QTextCharFormat(cursor.charFormat())
        formatting.setAnchor(True)
        formatting.setAnchorHref(target)
        formatting.setFontUnderline(True)
        cursor.insertText(str(label or "").strip() or previous_label, formatting)
        self._cursor_position = cursor.position()
        self._selection_start = self._selection_end = self._cursor_position
        self._emit_format_state_changed()
        return True

    @Slot(str, str)
    @Slot(str, str, float)
    @Slot(str, str, float, str)
    def insert_image(
        self,
        source: str,
        title: str = "",
        maximum_width: float = 560.0,
        display_source: str = "",
    ) -> None:
        cursor = self._cursor()
        source = str(source or "").strip()
        if (
            cursor is None
            or not source
            or QUrl(source).scheme().casefold() not in {"http", "https"}
        ):
            return
        image = QTextImageFormat()
        display_source = str(display_source or "").strip()
        display_url = QUrl(display_source)
        if display_url.scheme().casefold() not in {"file", "http", "https"}:
            display_source = source
        image.setName(QUrl(display_source or source).toString())
        if display_source and display_source != source:
            image.setProperty(_IMAGE_STORAGE_SOURCE, source)
        image.setToolTip(str(title or ""))
        image.setProperty(_IMAGE_CONTENT_WIDTH, False)
        image.setWidth(max(
            _IMAGE_MINIMUM_SIZE,
            min(float(maximum_width or 560.0), _IMAGE_MAXIMUM_SIZE),
        ))
        cursor.insertImage(image)
        self._cursor_position = cursor.position()
        self._selection_start = self._selection_end = self._cursor_position
        image_position = max(0, cursor.position() - 1)
        if not self.select_image_at(image_position, maximum_width):
            self._selected_image_position = image_position
            self._selected_image_width = float(image.width())
            self._selected_image_configured_width = float(image.width())
            self.stateChanged.emit()

    @Slot("QVariantMap", result=bool)
    def apply_image_display_sources(self, sources) -> bool:
        """Use bounded editor previews without changing stored image URLs."""
        document = self._live_document()
        if document is None:
            return False
        mapping = {
            str(source or "").strip(): str(display or "").strip()
            for source, display in dict(sources or {}).items()
            if str(source or "").strip()
        }
        changed = False
        for cursor, image, _position in self._image_cursors(document):
            stored_source = str(
                image.property(_IMAGE_STORAGE_SOURCE) or image.name() or ""
            ).strip()
            display_source = mapping.get(stored_source, stored_source)
            display_url = QUrl(display_source)
            if display_url.scheme().casefold() not in {
                "file", "http", "https",
            }:
                display_source = stored_source
            if str(image.name() or "") == display_source:
                continue
            image.setProperty(_IMAGE_STORAGE_SOURCE, stored_source)
            image.setName(display_source)
            cursor.setCharFormat(image)
            changed = True
        if changed:
            self.stateChanged.emit()
        return changed

    @Slot("QVariantList", result=bool)
    def apply_image_storage_sources(self, sources) -> bool:
        document = self._live_document()
        if document is None:
            return False
        values = [str(source or "").strip() for source in list(sources or [])]
        changed = False
        for index, (cursor, image, _position) in enumerate(
            self._image_cursors(document)
        ):
            if index >= len(values) or not values[index]:
                break
            if image.property(_IMAGE_STORAGE_SOURCE) == values[index]:
                continue
            image.setProperty(_IMAGE_STORAGE_SOURCE, values[index])
            cursor.setCharFormat(image)
            changed = True
        if changed:
            self.stateChanged.emit()
        return changed

    @Slot(str)
    def insert_html(self, value: str) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        cursor.insertHtml(sanitize_rich_html(value))
        self._cursor_position = cursor.position()
        self._selection_start = self._selection_end = self._cursor_position
        self.stateChanged.emit()

    @Slot()
    def clear_format(self) -> None:
        cursor = self._cursor()
        if cursor is None:
            return
        cursor.setCharFormat(QTextCharFormat())
        block = QTextBlockFormat()
        cursor.setBlockFormat(block)
        self._emit_format_state_changed()

    @Slot()
    def undo(self) -> None:
        document = self._live_document()
        if document is not None:
            document.undo()
            self._emit_format_state_changed()

    @Slot()
    def redo(self) -> None:
        document = self._live_document()
        if document is not None:
            document.redo()
            self._emit_format_state_changed()

    @Slot(result=str)
    def html(self) -> str:
        document = self._live_document()
        if document is None:
            return ""
        storage_document = document.clone()
        for cursor, image, _position in self._image_cursors(storage_document):
            storage_source = str(
                image.property(_IMAGE_STORAGE_SOURCE) or ""
            ).strip()
            if storage_source:
                image.setName(storage_source)
                image.clearProperty(_IMAGE_STORAGE_SOURCE)
            configured_width = self._format_property(
                image, _IMAGE_CONFIGURED_WIDTH
            )
            configured_height = self._format_property(
                image, _IMAGE_CONFIGURED_HEIGHT
            )
            if configured_width > 0.0:
                image.setWidth(configured_width)
            if configured_height > 0.0:
                image.setHeight(configured_height)
            if self._image_uses_content_width(image):
                image.setMaximumWidth(QTextLength(
                    QTextLength.PercentageLength, 100.0
                ))
            else:
                image.clearProperty(_IMAGE_MAXIMUM_WIDTH)
            cursor.setCharFormat(image)
        return sanitize_rich_html(storage_document.toHtml(), linkify=True)

    @Slot(str, result=str)
    def html_from_markdown(self, value: str) -> str:
        return rich_html_from_markdown(value)

    @Slot(result=str)
    def markdown(self) -> str:
        return markdown_from_rich_html(self.html())

    @Slot(result=str)
    def plain_text(self) -> str:
        document = self._live_document()
        if document is None:
            return ""
        value = document.toPlainText().strip()
        return value or plain_text_from_html(document.toHtml())


def _markdown_source(value: str) -> tuple[str, list[dict]]:
    image_specs = []

    def image(match: re.Match) -> str:
        attributes = {
            name.casefold(): raw_value
            for name, raw_value in re.findall(
                r"([a-zA-Z]+)\s*=\s*([^\s}]+)",
                str(match.group("attributes") or ""),
            )
        }
        image_specs.append(attributes)
        return (
            "![Image](" + match.group("image")[4:]
            if match.group("image").startswith("![](")
            else match.group("image")
        )

    source = _MARKDOWN_IMAGE.sub(image, str(value or ""))
    source = _MARKDOWN_UNDERLINE.sub(
        lambda match: (
            _UNDERLINE_START + match.group("content") + _UNDERLINE_END
        ),
        source,
    )
    source = _MARKDOWN_ALIGNMENT.sub(
        lambda match: _ALIGNMENT_MARKERS[match.group("alignment").casefold()],
        source,
    )
    return source, image_specs


def _apply_markdown_images(
    document: QTextDocument,
    image_specs: list[dict],
) -> None:
    for (cursor, image, _position), attributes in zip(
        RichTextDocumentController._image_cursors(document), image_specs
    ):
        width = RichTextDocumentController._format_property(
            image, _IMAGE_CONFIGURED_WIDTH
        )
        height = RichTextDocumentController._format_property(
            image, _IMAGE_CONFIGURED_HEIGHT
        )
        for name in ("width", "height"):
            try:
                value = max(0.0, float(attributes.get(name) or 0.0))
            except (TypeError, ValueError):
                value = 0.0
            if name == "width" and value > 0.0:
                width = value
                image.setWidth(value)
                image.setProperty(_IMAGE_CONFIGURED_WIDTH, value)
            elif name == "height" and value > 0.0:
                height = value
                image.setHeight(value)
                image.setProperty(_IMAGE_CONFIGURED_HEIGHT, value)
        if attributes.get("fit", "").casefold() == "content":
            image.setMaximumWidth(QTextLength(
                QTextLength.PercentageLength, 100.0
            ))
            image.setProperty(_IMAGE_CONTENT_WIDTH, True)
        else:
            image.clearProperty(_IMAGE_MAXIMUM_WIDTH)
            image.setProperty(_IMAGE_CONTENT_WIDTH, False)
        if width > 0.0 and not image.hasProperty(_IMAGE_CONFIGURED_WIDTH):
            image.setProperty(_IMAGE_CONFIGURED_WIDTH, width)
        if height > 0.0 and not image.hasProperty(_IMAGE_CONFIGURED_HEIGHT):
            image.setProperty(_IMAGE_CONFIGURED_HEIGHT, height)
        storage_source = str(
            attributes.get("storage_source") or ""
        ).strip()
        if storage_source:
            image.setProperty(_IMAGE_STORAGE_SOURCE, storage_source)
        cursor.setCharFormat(image)


def _remove_markdown_markers(document: QTextDocument) -> None:
    plain_text = document.toPlainText()
    pairs = []
    offset = 0
    while True:
        start = plain_text.find(_UNDERLINE_START, offset)
        if start < 0:
            break
        end = plain_text.find(_UNDERLINE_END, start + 1)
        if end < 0:
            break
        pairs.append((start, end))
        offset = end + 1
    for start, end in reversed(pairs):
        content = QTextCursor(document)
        content.setPosition(start + 1)
        content.setPosition(end, QTextCursor.KeepAnchor)
        formatting = QTextCharFormat()
        formatting.setFontUnderline(True)
        content.mergeCharFormat(formatting)
        for position in (end, start):
            marker = QTextCursor(document)
            marker.setPosition(position)
            marker.setPosition(position + 1, QTextCursor.KeepAnchor)
            marker.removeSelectedText()

    markers = {value: key for key, value in _ALIGNMENT_MARKERS.items()}
    block = document.begin()
    while block.isValid():
        text = block.text()
        alignment = markers.get(text[-1:] if text else "")
        next_block = block.next()
        if alignment:
            marker = QTextCursor(document)
            marker.setPosition(block.position() + len(text) - 1)
            marker.setPosition(
                block.position() + len(text), QTextCursor.KeepAnchor
            )
            marker.removeSelectedText()
            formatting = marker.blockFormat()
            formatting.setAlignment({
                "center": Qt.AlignHCenter,
                "right": Qt.AlignRight,
                "justify": Qt.AlignJustify,
            }[alignment])
            marker.setBlockFormat(formatting)
        block = next_block


def markdown_document(value: str) -> QTextDocument:
    """Create the editor document for canonical Markdown article text."""
    document = QTextDocument()
    _load_markdown_document(document, value)
    return document


def _load_markdown_document(
    document: QTextDocument,
    value: str,
) -> None:
    source, image_specs = _markdown_source(value)
    document.setMarkdown(source)
    _apply_markdown_images(document, image_specs)
    _remove_markdown_markers(document)
    block = document.begin()
    while block.isValid():
        formatting = block.blockFormat()
        if formatting.property(QTextFormat.BlockQuoteLevel):
            formatting.setTopMargin(6.0)
            formatting.setBottomMargin(6.0)
            formatting.setBackground(QColor(128, 128, 128, 32))
        elif formatting.property(QTextFormat.BlockCodeFence):
            formatting.setLeftMargin(14.0)
            formatting.setRightMargin(14.0)
            formatting.setTopMargin(8.0)
            formatting.setBottomMargin(8.0)
            formatting.setBackground(QColor(128, 128, 128, 32))
        else:
            block = block.next()
            continue
        cursor = QTextCursor(block)
        cursor.setBlockFormat(formatting)
        block = block.next()


def rich_html_from_markdown(value: str) -> str:
    if not str(value or "").strip():
        return ""
    return sanitize_rich_html(markdown_document(value).toHtml(), linkify=True)


def plain_text_from_markdown(value: str) -> str:
    return markdown_document(value).toPlainText().strip()
