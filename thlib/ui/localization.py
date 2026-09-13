"""Runtime localization for the QML application."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QLocale,
    QObject,
    Property,
    QTranslator,
    Signal,
    Slot,
)

LANGUAGES = (
    {"value": "en", "sourceLabel": "English"},
    {"value": "ru", "sourceLabel": "Russian"},
)
_LANGUAGE_CODES = {record["value"] for record in LANGUAGES}


def normalize_language(value: object) -> str:
    code = str(value or "en").strip().lower().replace("-", "_")
    code = code.split("_", 1)[0]
    return code if code in _LANGUAGE_CODES else "en"


class CatalogTranslator(QTranslator):
    """Small source-text catalog compatible with QML ``qsTr`` calls."""

    def __init__(self, catalog_path: Path, parent: QObject | None = None):
        super().__init__(parent)
        self._messages: dict[str, str] = {}
        if catalog_path.is_file():
            with catalog_path.open("r", encoding="utf-8") as stream:
                values = json.load(stream)
            self._messages = {
                str(source): str(target)
                for source, target in dict(values).items()
                if str(source) and str(target)
            }

    def isEmpty(self) -> bool:  # noqa: N802 - Qt virtual method
        return not self._messages

    def translate(
        self,
        context: str,
        source_text: str,
        disambiguation: str | None = None,
        n: int = -1,
    ) -> str:
        del context, disambiguation, n
        source_text = str(source_text or "")
        # QML uses the return value directly for a Python QTranslator
        # subclass.  Returning an empty string therefore blanks menus and
        # tooltips instead of falling back as a compiled .qm catalog would.
        return self._messages.get(source_text, source_text)


class LocalizationController(QObject):
    """Owns the selected locale and asks the live QML engine to retranslate."""

    languageChanged = Signal()

    def __init__(
        self,
        qt_application,
        settings_owner,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._qt_application = qt_application
        self._settings_owner = settings_owner
        self._settings = settings_owner._settings
        self._language = normalize_language(
            self._settings.get("appearance/language", "en")
        )
        self._engine = None
        self._translator: CatalogTranslator | None = None
        self._install_language(self._language)

    def attach_engine(self, engine) -> None:
        self._engine = engine

    def _install_language(self, language: str) -> None:
        if self._translator is not None:
            self._qt_application.removeTranslator(self._translator)
            self._translator.deleteLater()
            self._translator = None
        if language != "en":
            catalog = Path(__file__).parent / "translations" / f"{language}.json"
            translator = CatalogTranslator(catalog, self)
            self._qt_application.installTranslator(translator)
            self._translator = translator
        QLocale.setDefault(QLocale("ru_RU" if language == "ru" else "en_US"))

    @Property(str, notify=languageChanged)
    def current_language(self) -> str:
        return self._language

    @Property("QVariantList", notify=languageChanged)
    def language_options(self) -> list[dict]:
        return [
            {
                "value": record["value"],
                "label": QCoreApplication.translate(
                    "Localization", record["sourceLabel"]
                ),
            }
            for record in LANGUAGES
        ]

    @Slot(str)
    def set_language(self, language: str) -> None:
        language = normalize_language(language)
        if language == self._language:
            return
        self._language = language
        self._settings["appearance/language"] = language
        self._settings_owner._write_settings()
        self._install_language(language)
        if self._engine is not None:
            self._engine.retranslate()
        self.languageChanged.emit()

    @Slot(str, result=str)
    def translate(self, source_text: str) -> str:
        return QCoreApplication.translate("TacticHandler", str(source_text or ""))
