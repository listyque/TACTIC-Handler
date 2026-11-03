"""Standalone, repeatable native setup wizard; launch with TH Setup.exe."""

from __future__ import annotations

import os
from pathlib import Path
import sys

from PySide6.QtCore import (
    QObject,
    Property,
    QStandardPaths,
    QTimer,
    QUrl,
    Signal,
    Slot,
    QLocale,
)
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from thlib.environment import env_inst, env_mode
from thlib.ui.setup_service import SetupSession, apply_setup, read_initial
from thlib.ui.setup_package import read_setup_defaults, default_repository


class SetupController(QObject):
    stateChanged = Signal()

    def __init__(self, root: Path, parent=None):
        super().__init__(parent)
        self.root = root
        self.session = SetupSession()
        self._closed = False
        self._worker = None
        self._catalog_key = None
        self._presets = read_setup_defaults(root)
        initial = read_initial()
        has_presets = (root.parent / "setup-defaults.json").is_file()
        self._app = None
        self._translator = None
        self._engine = None
        self._state = {
            **initial,
            "server": self._presets["server"],
            "login": "",
            "step": 0,
            "busy": False,
            "error": "",
            "projects": [],
            "shelves": [],
            "shelf": "",
            "plugins": [],
            "pluginCatalog": [],
            "maya": [],
            "mayaProfiles": [],
            "shortcuts": self._presets["shortcuts"],
            "language": self._presets["language"] or initial["language"],
            "darkTheme": (
                self._presets["dark_theme"] if has_presets else initial["darkTheme"]
            ),
            "closeToTray": (
                self._presets["close_to_tray"]
                if has_presets
                else initial["closeToTray"]
            ),
        }
        if not self._state["repository"]:
            self._state["repository"] = str(default_repository(root))
        if self._presets["project"]:
            self._state["project"] = self._presets["project"]

    def attach_localization(self, app, translator, engine):
        self._app, self._translator, self._engine = app, translator, engine
        self._apply_language(self._state["language"])

    def _apply_language(self, language: str):
        if self._app is None or self._translator is None:
            return
        self._app.removeTranslator(self._translator)
        if language == "ru":
            self._app.installTranslator(self._translator)
        QLocale.setDefault(QLocale("ru_RU" if language == "ru" else "en_US"))
        if self._engine is not None:
            self._engine.retranslate()

    @Property("QVariantMap", notify=stateChanged)
    def state(self):
        return dict(self._state)

    @Slot(str, str)
    def edit(self, key, value):
        if self._state["busy"]:
            return
        if key == "language" and value in {"en", "ru"}:
            self._state["language"] = value
            self._apply_language(value)
            self.stateChanged.emit()
        elif key in {
            "server",
            "login",
            "project",
            "repository",
            "repositoryAlias",
            "shelf",
        }:
            self._state[key] = value
            self.stateChanged.emit()

    @Slot(str, str, bool)
    def toggle(self, key, identity, enabled):
        if self._state["busy"]:
            return
        if key in {"plugins", "mayaProfiles"}:
            selected = set(self._state[key])
            selected.add(identity) if enabled else selected.discard(identity)
            self._state[key] = sorted(selected)
            if key == "plugins" and identity == "maya" and not enabled:
                self._state["mayaProfiles"] = []
        elif key in {"shortcuts", "darkTheme", "closeToTray"}:
            self._state[key] = bool(enabled)
        self.stateChanged.emit()

    @Slot()
    def browse(self):
        folder = QFileDialog.getExistingDirectory(
            None, self.tr("Repository folder"), self._state["repository"]
        )
        if folder:
            self.edit("repository", folder)

    @Slot(str)
    def sign_in(self, password):
        if self._state["busy"]:
            return
        address, login = self._state["server"], self._state["login"]
        self._run("login", lambda: self.session.authenticate(address, login, password))

    @Slot()
    def next(self):
        if self._state["busy"]:
            return
        step = self._state["step"]
        self._state["error"] = ""
        if step == 1:
            project, repository = (
                self._state["project"],
                Path(self._state["repository"]).expanduser(),
            )
            default_missing = (
                repository == default_repository(self.root) and not repository.exists()
            )
            if not repository.is_absolute() or (
                not repository.is_dir() and not default_missing
            ):
                self._state["error"] = self.tr(
                    "Choose an existing repository folder accessible from this computer"
                )
            elif project not in {row["code"] for row in self._state["projects"]}:
                self._state["error"] = self.tr("Sign in and select a project first")
            else:
                self._run("project", lambda: self._load_project(project))
                return
        elif step == 2:
            self._state["step"] = 3
        elif step == 3:
            values = dict(self._state)
            desktop = Path(
                QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
            )
            self._run(
                "apply", lambda: apply_setup(self.session, self.root, values, desktop)
            )
            return
        self.stateChanged.emit()

    def _load_project(self, project):
        from tactic_handler_dcc import maya_integration
        from tactic_handler_dcc.connectors import plugin_catalog
        from thlib.ui.dcc_plugins import read_disabled_plugins

        return {
            "shelves": self.session.load_project(project),
            "maya": maya_integration.discover(),
            "pluginCatalog": plugin_catalog(),
            "disabled": read_disabled_plugins(),
        }

    @Slot()
    def back(self):
        if not self._state["busy"] and 0 < self._state["step"] < 4:
            self._state["step"] -= 1
            self._state["error"] = ""
            self.stateChanged.emit()

    def _run(self, operation, function):
        if self._closed or self._state["busy"]:
            return
        self._state.update(busy=True, error="")
        self.stateChanged.emit()
        worker = env_inst.local_pool.add_task(lambda: (operation, function()))
        if worker is None:
            self._failed("The local worker pool is shutting down")
            return
        self._worker = worker
        worker.result.connect(self._finished)
        worker.error.connect(self._failed)
        worker.start()

    @Slot(object)
    def _finished(self, result):
        if self._closed:
            return
        operation, value = result
        self._state["busy"] = False
        self._worker = None
        if operation == "login":
            self._state.update(projects=value, step=1)
            if self._state["project"] not in {row["code"] for row in value}:
                self._state["project"] = value[0]["code"] if value else ""
        elif operation == "project":
            key = (self.session.url, self.session.login, self._state["project"])
            same_project = key == self._catalog_key
            shelf_ids = {row["id"] for row in value["shelves"]}
            plugin_ids = {row["id"] for row in value["pluginCatalog"]}
            profile_ids = {
                row["id"]
                for row in value["maya"]
                if row["supported"] and not row["pids"]
            }
            if same_project:
                shelf = (
                    self._state["shelf"] if self._state["shelf"] in shelf_ids else ""
                )
                plugins = [
                    identity
                    for identity in self._state["plugins"]
                    if identity in plugin_ids
                ]
                profiles = [
                    identity
                    for identity in self._state["mayaProfiles"]
                    if identity in profile_ids
                ]
            else:
                shelf = value["shelves"][0]["id"] if value["shelves"] else ""
                if self._presets["shelf"]:
                    shelf = next(
                        (
                            row["id"]
                            for row in value["shelves"]
                            if self._presets["shelf"] in {row["id"], row["title"]}
                        ),
                        shelf,
                    )
                plugins = [
                    row["id"]
                    for row in value["pluginCatalog"]
                    if row["id"] not in value["disabled"]
                ]
                profiles = []
                if self._presets["plugins"] is not None:
                    plugins = [
                        identity
                        for identity in self._presets["plugins"]
                        if identity in plugin_ids
                    ]
            self._state.update(
                {key: value[key] for key in ("shelves", "maya", "pluginCatalog")}
            )
            self._state.update(
                step=2,
                shelf=shelf,
                plugins=plugins,
                mayaProfiles=profiles,
            )
            self._catalog_key = key
        elif operation == "apply":
            self._state["step"] = 4
        self.stateChanged.emit()

    @Slot(object)
    def _failed(self, error):
        if self._closed:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        message = str(
            payload.get("exception", payload) if isinstance(payload, dict) else payload
        )
        ticket = getattr(self.session.server, "login_ticket", "")
        if ticket:
            message = message.replace(ticket, "[redacted]")
        self._worker = None
        self._state.update(busy=False, error=self.tr(message))
        self.stateChanged.emit()

    def shutdown(self):
        self._closed = True


def main(*, builder=False) -> int:
    from thlib.ui.localization import CatalogTranslator
    from thlib.ui.icon_font import qml_icon_bindings
    from thlib.ui.window_appearance import WindowAppearanceController
    from thlib.ui.single_instance import SingleInstanceGuard, instance_server_name

    root = Path(__file__).resolve().parents[2]
    settings = (
        os.environ.get("TACTIC_QML_TEST_SETTINGS_DIR")
        or os.environ.get("TACTIC_HANDLER_SETTINGS_DIR")
        or str(root)
    )
    env_mode.set_current_path(str(Path(settings).resolve()))
    QQuickStyle.setStyle("Material")
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("TH Setup Builder" if builder else "TACTIC Handler Setup")
    app.setWindowIcon(QIcon(str(root / "thlib/ui/assets/tactic_favicon.ico")))
    translator = CatalogTranslator(root / "thlib/ui/translations/ru.json", app)
    if QLocale.system().name().startswith("ru") or "--ru" in sys.argv:
        app.installTranslator(translator)
    # Hold the same ownership lock as TH until setup exits; no competing settings writes.
    guard = SingleInstanceGuard(
        instance_server_name(
            "TacticHandler_SetupBuilder" if builder else "TacticHandler_Client",
            settings,
        ),
        app,
    )
    if not guard.start():
        QMessageBox.information(
            None,
            app.applicationName(),
            app.translate(
                "Setup",
                "Setup Builder is already open."
                if builder
                else "Close TACTIC Handler, including its tray icon, and run Setup again.",
            ),
        )
        return 0
    env_inst.ui_super = app
    env_inst.start_pools()
    if builder:
        from .setup_builder import SetupBuilderController

        controller = SetupBuilderController(root)
    else:
        controller = SetupController(root)
        if "--ru" in sys.argv:
            controller._state["language"] = "ru"
    engine = QQmlApplicationEngine()
    if not builder:
        controller.attach_localization(app, translator, engine)
    appearance = WindowAppearanceController(controller)
    engine.rootContext().setContextProperty("windowAppearanceController", appearance)
    for name, value in qml_icon_bindings(root, controller).items():
        engine.rootContext().setContextProperty(name, value)
    engine.setInitialProperties({"controller": controller})
    view = "SetupBuilder.qml" if builder else "SetupWizard.qml"
    engine.load(QUrl.fromLocalFile(str(root / "thlib/ui/qml/features/setup" / view)))
    if "--smoke" in sys.argv:
        QTimer.singleShot(800, app.quit)
    try:
        return app.exec() if engine.rootObjects() else 1
    finally:
        controller.shutdown()
        env_inst.exit_pools()
        guard.close()


if __name__ == "__main__":
    raise SystemExit(main(builder="--builder" in sys.argv))
