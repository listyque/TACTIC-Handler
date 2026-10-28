"""Exercise the real Main.qml: first custom page, dock focus loss and section rail."""
from pathlib import Path
import json
import os
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch


def main():
    with tempfile.TemporaryDirectory(prefix="handler-shell-lifecycle-") as directory:
        os.environ.update({
            "QT_QPA_PLATFORM": os.environ.get("QT_QPA_PLATFORM", "offscreen"),
            "TACTIC_QML_SMOKE_OFFLINE": "1",
            "TACTIC_QML_TEST_SETTINGS_DIR": directory,
            "XDG_CACHE_HOME": str(Path(directory) / "cache"),
            "XDG_CONFIG_HOME": str(Path(directory) / "config"),
        })
        from PySide6.QtCore import QObject, QTimer, QMetaObject
        from PySide6.QtQml import QQmlEngine
        from PySide6.QtWidgets import QApplication
        from PySide6.QtTest import QTest
        from thlib.ui import application
        from thlib.ui.models import NavigationEntry
        from tests.profile_ui_responsiveness import frame
        from tests.test_sidebar_editor_qml import SidebarEditorQmlTests

        errors = []
        results = []

        def exercise(app):
            try:
                window = next(window for window in app.allWindows()
                              if window.title().startswith("TACTIC-Handler"))
                context = QQmlEngine.contextForObject(window)
                controller = context.contextProperty("appController")
                services = context.contextProperty("tableServicesController")
                host = window.findChild(QObject, "dockHost")
                empty = window.findChild(QObject, "workspaceNoSearchType")
                warnings = []
                context.engine().warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
                controller._current_project_code = "shell_fixture"
                controller.navigation_model.replace([NavigationEntry(
                    key="dashboard", title="Overview", glyph="dashboard", group="Project",
                    command="open_sidebar_item", search_type="sthpw/project", layout_view="dashboard.lifecycle",
                )])
                document = dict(layoutView="dashboard.lifecycle", targetSearchKey="sthpw/project?code=shell_fixture",
                                layoutRecord={}, layoutNodes=[dict(kind="heading", text="Lifecycle dashboard")])

                def read(operation, loaded, **kwargs):
                    loaded(document)
                    if kwargs.get("settled"):
                        kwargs["settled"]()

                def wait_for(predicate):
                    deadline = time.monotonic() + 3
                    while not predicate():
                        if time.monotonic() > deadline:
                            raise AssertionError("Main workspace transition timed out")
                        QTest.qWait(5)
                    frame(window)

                assert not host.property("workspaceActive")
                with patch("thlib.tactic_classes.server_start", return_value=SimpleNamespace(query=lambda *args, **kwargs: [])), \
                        patch.object(services, "_run", side_effect=read):
                    for index in range(3):
                        controller.select_navigation("dashboard", "Overview", "open_sidebar_item")
                        wait_for(lambda: bool(host.property("workspaceActive")))
                        assert services.workspaceLayout.active
                        assert not empty.property("visible")
                        grip = next((item for item in SidebarEditorQmlTests.descendants(window.contentItem())
                                     if item.objectName() == "dockTitleDrag_results"), None)
                        assert grip is not None and not grip.property("visible"), (
                            "Search grip covers the dashboard", grip,
                            host.property("resultsDragHandleVisible"), warnings
                        )
                        invoked = QMetaObject.invokeMethod(host, "cancelActiveGesture")
                        assert invoked
                        # Exercise the GUI/render synchronization that previously deadlocked.
                        QTest.qWait(20)
                        visible = SidebarEditorQmlTests.descendants(window.contentItem())
                        assert any(item.property("text") == "Lifecycle dashboard" for item in visible)
                        assert not warnings, warnings
                        results.append(dict(customPageActive=True, searchGripVisible=False, noSearchTypeVisible=False))
                        proof = os.environ.get("TACTIC_SHELL_PROOF_DIR")
                        if proof and index == 0:
                            target = Path(proof)
                            target.mkdir(parents=True, exist_ok=True)
                            saved = window.grabWindow().save(str(target / "main-custom-layout.png"))
                            assert saved
                        controller.close_section("dashboard")
                        wait_for(lambda: not host.property("workspaceActive"))
                        assert empty.property("visible")
                assert not warnings, warnings
                print(json.dumps(dict(cycles=results, warnings=warnings)), flush=True)
            except Exception as error:
                errors.append(error)
            finally:
                app.quit()

        class TestApplication:
            instance = staticmethod(QApplication.instance)
            sendPostedEvents = staticmethod(QApplication.sendPostedEvents)

            def __new__(cls, *args):
                app = QApplication(*args)
                QTimer.singleShot(250, lambda: exercise(app))
                return app

        application.QApplication = TestApplication
        result = application.main()
        if errors:
            raise errors[0]
        return result


if __name__ == "__main__":
    raise SystemExit(main())
