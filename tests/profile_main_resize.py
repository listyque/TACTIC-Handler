"""Profile the real offline Main.qml while resizing: python -m tests.profile_main_resize."""

from __future__ import annotations

import json
import os
import statistics
import tempfile
import time
from pathlib import Path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tactic-main-resize-") as directory:
        os.environ.update({
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "TACTIC_QML_SMOKE_OFFLINE": "1",
            "TACTIC_QML_TEST_SETTINGS_DIR": directory,
            "XDG_CACHE_HOME": str(Path(directory) / "cache"),
            "XDG_CONFIG_HOME": str(Path(directory) / "config"),
        })
        if os.name == "nt":
            os.environ["LOCALAPPDATA"] = directory
            os.environ["APPDATA"] = directory
            os.environ["QT_QPA_FONTDIR"] = str(
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
            )

        from PySide6.QtCore import QEventLoop, QObject, QTimer, Qt
        from PySide6.QtWidgets import QApplication
        from thlib.ui import application

        errors = []

        def measure(app):
            window = next(
                item for item in app.allWindows()
                if item.title().startswith("TACTIC-Handler")
            )
            top_bar = window.findChild(QObject, "topAppBar")
            if top_bar is None:
                raise RuntimeError("Main.qml top bar was not created")

            samples = []
            for width, height in (
                (1400, 900), (1400, 720), (900, 720),
                (640, 560), (900, 900), (1400, 900),
            ):
                loop = QEventLoop()
                timer = QTimer()
                timer.setSingleShot(True)
                timed_out = []
                timer.timeout.connect(lambda: timed_out.append(True))
                timer.timeout.connect(loop.quit)
                window.frameSwapped.connect(loop.quit, Qt.QueuedConnection)
                start = time.perf_counter()
                window.setWidth(width)
                window.setHeight(height)
                window.update()
                timer.start(2000)
                loop.exec()
                timer.stop()
                window.frameSwapped.disconnect(loop.quit)
                if timed_out:
                    raise RuntimeError(f"No frame after resize to {width}x{height}")
                if (window.width(), window.height()) != (width, height):
                    raise RuntimeError(
                        f"Window did not resize to {width}x{height}"
                    )
                elapsed = (time.perf_counter() - start) * 1000
                samples.append({
                    "width": width,
                    "height": height,
                    "frameMs": round(elapsed, 2),
                    "topPadding": window.property("topPadding"),
                    "topBarY": top_bar.property("y"),
                })
            print(json.dumps({
                "medianFrameMs": round(statistics.median(
                    row["frameMs"] for row in samples[1:]
                ), 2),
                "samples": samples,
            }))

        def finish_measurement(app):
            try:
                measure(app)
            except Exception as error:
                errors.append(error)
            finally:
                app.quit()

        class ProfilingApplication:
            instance = staticmethod(QApplication.instance)
            sendPostedEvents = staticmethod(QApplication.sendPostedEvents)

            def __new__(cls, *args):
                app = QApplication(*args)
                QTimer.singleShot(250, lambda: finish_measurement(app))
                return app

        application.QApplication = ProfilingApplication
        result = application.main()
        if errors:
            raise errors[0]
        return result


if __name__ == "__main__":
    raise SystemExit(main())
