"""Real native/browser input smoke. Requires node, Playwright and an Edge channel.

Set BATCH_PLAYWRIGHT to the installed Playwright module URL. Screenshots and
measurements are written only to the explicitly supplied evidence directory.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import Property, QObject, Signal, QPointF, QCoreApplication, QEvent
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from batch_render_fixture import BatchCase, Root, episode
from plugins.batch_render.web import BatchWebServer
from plugins.batch_render.window import _create_window
from thlib.ui.icon_font import fontawesome_assets, material_design_icon_assets
import thlib.ui.source_editor


class Locale(QObject):
    changed = Signal()
    value = "en"
    current_language = Property(str, lambda self: self.value, notify=changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args()
    args.evidence.mkdir(parents=True, exist_ok=True)
    case = BatchCase(); case.setUpClass(); case.setUp()
    c = case.controller
    c._clock.stop()
    first = episode("episode", 12)
    first["jobs"][5]["state"] = "skipped"
    first["jobs"][0]["state"] = "completed"
    first["title"] = "Episode with a deliberately long project title"
    c._entries = [first, episode("other", 4)]
    c._publish_queue()
    c.episodes.replace([dict(searchKey=f"catalog-{i}",code=f"EP{i}",title=f"Episode {i} with a long descriptive project title",subtitle="Project description remains project data",renderStatus="Подготовлен",previewUrl="",statusColor="#79aeaa",selected=False,queued=False,statusChoices=[]) for i in range(100)])
    engine = QQmlEngine(); warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    locale = Locale()
    engine.rootContext().setContextProperty("localizationController", locale)
    solid, family, regular, regular_family = fontawesome_assets(ROOT)
    material, material_family = material_design_icon_assets(ROOT)
    for key, value in dict(fontAwesomeSolidGlyphs=solid,fontAwesomeSolidFontFamily=family,fontAwesomeRegularGlyphs=regular,fontAwesomeRegularFontFamily=regular_family,materialDesignGlyphs=material,materialDesignFontFamily=material_family).items():
        engine.rootContext().setContextProperty(key, value)
    parent = Root()
    component, window = _create_window(engine, ROOT, parent, c)
    window.show(); QTest.qWait(100)
    server = BatchWebServer(c._web_dispatch,host="127.0.0.1",port=0)
    original = c._web_action
    measurements = {}
    def fixture_action(request):
        if request.get("action") != "fixture-view":
            return original(request)
        locale.value = request["language"]; locale.changed.emit()
        window.setWidth(request["width"]); window.setHeight(request["height"])
        QTest.qWait(30)
        label = f"{locale.value}-{request['width']}"
        window.grabWindow().save(str(args.evidence / ("native-"+label+".png")))
        def descendants(item):
            for child in item.childItems():
                yield child
                yield from descendants(child)
        names = {"batchQueueRow_0","batchQueueRow_1","batchQueuePreview_0","batchQueuePreview_1","batchEpisodeRow_0","batchEpisodePreview_0","batchQueueTitle_0","batchQueueTitle_1"}
        rows = {}
        for item in descendants(window.contentItem()):
            if item.objectName() in names:
                point=item.mapToScene(QPointF())
                rows[item.objectName()] = dict(x=point.x(),y=point.y(),width=item.width(),height=item.height())
        measurements[label] = rows
        return {"ok": True, "native": rows}
    c._web_action = fixture_action
    environment = dict(os.environ, BATCH_WEB_URL=server.start(), BATCH_EVIDENCE=str(args.evidence))
    process = subprocess.Popen(["node",str(Path(__file__).with_name("batch_render_browser_smoke.mjs"))],env=environment,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    try:
        deadline = time.monotonic()+90
        while process.poll() is None and time.monotonic()<deadline:
            case.app.processEvents(); QTest.qWait(5)
        if process.poll() is None:
            process.kill(); raise RuntimeError("Browser smoke exceeded 90 seconds")
        output = process.communicate()[0]
        print(output)
        if process.returncode:
            raise RuntimeError("Browser smoke failed")
        if warnings:
            raise AssertionError(warnings)
        (args.evidence/"native-geometry.json").write_text(json.dumps(measurements,indent=2),encoding="utf-8")
    finally:
        if process.poll() is None: process.kill(); process.communicate()
        server.stop(); window.hide(); window.deleteLater(); component.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        engine.deleteLater();case.doCleanups()


if __name__ == "__main__":
    main()
