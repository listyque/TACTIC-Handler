"""Capture the native QML editor on isolated data; no WebEngine or live writes."""
import json,os,sys
from pathlib import Path
os.environ.update(QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',QT_FONT_DPI='96')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QUrl,QCoreApplication,QEvent,QPointF
from PySide6.QtQml import QQmlEngine,QQmlComponent
from tests.test_layout_editor import LayoutEditorTests
from tests.profile_ui_responsiveness import frame
from tests.test_sidebar_editor_qml import SidebarEditorQmlTests
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.localization import CatalogTranslator
output=Path(sys.argv[-1]);output.mkdir(parents=True,exist_ok=True)
LayoutEditorTests.setUpClass();fixture=LayoutEditorTests();fixture.setUp();fixture.loaded();host=fixture.host
engine=QQmlEngine();warnings=[];engine.warnings.connect(lambda rows:warnings.extend(row.toString() for row in rows));icons=qml_icon_bindings(ROOT,fixture.app)
for key,value in icons.items():engine.rootContext().setContextProperty(key,value)
engine.rootContext().setContextProperty('testHost',host)
component=QQmlComponent(engine)
component.setData(('import QtQuick\nimport QtQuick.Controls\nimport "'+(ROOT/'thlib/ui/qml').as_uri()+'" as TH\nApplicationWindow {id:root;color:theme.workspace;width:1190;height:903;visible:true;property string language:"en";property alias dark:theme.dark;TH.Theme{id:theme;dark:true;clickAnimationsEnabled:false;hoverAnimationsEnabled:false;fadeAnimationsEnabled:false;popupAnimationsEnabled:false} TH.LayoutEditorView{anchors.fill:parent;theme:theme;controller:testHost;language:root.language}}').encode(),QUrl.fromLocalFile(str(output/'native-layout-fixture.qml')))
assert component.isReady(),[error.toString() for error in component.errors()]
window=component.create();assert window, warnings+[error.toString() for error in component.errors()]
translator=CatalogTranslator(ROOT/'thlib/ui/translations/ru.json');captures=[]
try:
 for language,dark,width,height in [('en',True,1190,903),('ru',True,850,700),('en',False,1190,903),('ru',False,850,700)]:
  fixture.app.removeTranslator(translator)
  if language=='ru':fixture.app.installTranslator(translator)
  window.resize(width,height);window.setProperty('language',language);window.setProperty('dark',dark);engine.retranslate();frame(window)
  parts={}
  for item in SidebarEditorQmlTests.descendants(window.contentItem()):
   if item.objectName() in ('layoutElementsList','layoutGrid','layoutProperty_title') and item.isVisible():
    point=item.mapToScene(QPointF());parts[item.objectName()]=dict(x=point.x(),y=point.y(),width=item.width(),height=item.height())
  assert parts,'native editor must contain actual controls'
  image=f'{language}-'+('dark' if dark else 'light')+f'-{width}-handler.png';assert window.grabWindow().save(str(output/image))
  captures.append(dict(language=language,dark=dark,width=width,height=height,parts=parts,pixelRatio=window.devicePixelRatio()))
 assert not warnings,warnings
 assert not any(name.startswith('PySide6.QtWebEngine') for name in sys.modules)
 (output/'handler-measurements.json').write_text(json.dumps(captures,indent=2),encoding='utf8')
 print('Native QML Layout: four theme/language/size captures, no WebEngine')
finally:
 fixture.app.removeTranslator(translator);window.close();window.deleteLater();engine.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);fixture.doCleanups()
