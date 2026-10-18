"""Offline production hosts and shared compositions for B14 input/capture."""

from datetime import date
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Property, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QJSValue
from PySide6.QtQuick import QQuickItem, QQuickWindow
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests.test_knowledge_base import _KnowledgeStub, _AttachmentStub, _PreviewStub
from tests.test_work_hours import _Application
from thlib.environment import env_mode
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.rich_text_document import RichTextDocumentController
from thlib.ui.work_hours import WorkHoursController
from thlib.ui.workspace_models.records import RecordListModel

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"
PANELS = (
    "initializeState",
    "initializeConfirm",
    "editor",
    "viewer",
    "format",
    "navigation",
    "entry",
    "hourEditor",
    "summary",
    "reportRow",
)
PRODUCTION = (
    "uninitialized",
    "reader",
    "articleEditor",
    "create",
    "section",
    "catalog",
    "error",
    "timesheet",
    "reports",
    "cost",
    "hourDialog",
)


class Knowledge(_KnowledgeStub):
    def __init__(self):
        self._initialized = True
        super().__init__()

    @Property(bool, notify=_KnowledgeStub.stateChanged)
    def initialized(self):
        return self._initialized

    @Property(bool, notify=_KnowledgeStub.stateChanged)
    def canInitialize(self):
        return True


class Locale(QObject):
    def __init__(self, language, parent):
        super().__init__(parent)
        self.language = language

    @Property(str, constant=True)
    def current_language(self):
        return self.language


def projection(screen, locked=False):
    model = dict(
        kind="article",
        title="Publishing guide",
        description="Production notes",
        back=True,
        creating=False,
        step=1,
        selectionCount=2,
        metadataExpanded=False,
        dirty=True,
        draft=False,
        localDraft=False,
        busy=locked,
        disabled=locked,
        canEdit=True,
        tocCount=3,
        tocVisible=True,
        resourceCount=2,
        resourcesVisible=False,
        minutes=2,
    )
    if screen in ("initializeState", "initializeConfirm"):
        model.update(
            title="Knowledge Base is not initialized",
            message="Initialize the collaboration schema before writing project documentation.",
            icon="file",
            canInitialize=True,
            project="demo",
        )
    elif screen == "format":
        model.update(mode="visual", checked=dict(bold=True))
    elif screen == "navigation":
        model.update(
            identity="guide",
            kind="section",
            depth=0,
            hasChildren=True,
            expanded=True,
            localDraft=True,
        )
    elif screen == "entry":
        model.update(
            id="hour-1",
            taskTitle="Robot Arm",
            process="Model",
            loginLabel="Robin",
            day="2026-10-14",
            hours=2.5,
            status="approved",
            description="Model review",
            canApprove=True,
            selectable=True,
            selected=True,
        )
    elif screen == "hourEditor":
        model.update(
            day="2026-10-14",
            hours="2.5",
            category="regular",
            login="robin",
            canManage=True,
            users=[dict(value="robin", label="Robin")],
            error="",
        )
    elif screen == "summary":
        model.update(logged=12.5, approved=10, pending=2.5, overtime=1)
    elif screen == "reportRow":
        model.update(label="Robin", valueLabel="12.5 h", share=0.65)
    return model


class Surface:
    def __init__(
        self,
        screen,
        width=900,
        height=650,
        *,
        qml=None,
        style="md3",
        dark=True,
        language="en",
        locked=False,
    ):
        self.app = gui_test_application()
        self.screen = screen
        self.window = None
        self.view = None
        self.controller = None
        self.temporary = tempfile.TemporaryDirectory()
        self.previous_path = env_mode.current_path
        env_mode.current_path = self.temporary.name
        self.engine = QQmlEngine()
        self.components = []
        self.objects = []
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        self.qml = Path(qml or QML)
        self.model = projection(screen, locked)
        self.locale = Locale(language, self.engine)
        context = self.engine.rootContext()
        self.icon_bindings = qml_icon_bindings(
            Path(__file__).resolve().parents[1], self.engine
        )
        for name, value in dict(
            self.icon_bindings, localizationController=self.locale
        ).items():
            context.setContextProperty(name, value)
        self.theme = self.create(
            self.qml / "Theme.qml",
            dict(
                dark=dark,
                styleName=style,
                popupAnimationsEnabled=False,
                clickAnimationsEnabled=False,
            ),
        )
        self.window = QQuickWindow()
        self.window.resize(width, height)
        self.window.setColor(self.theme.property("workspace"))
        if screen in PANELS:
            self.view = self.create(
                Path(__file__).parent / "fixtures/FrameRemainingHarness.qml",
                dict(
                    theme=self.theme,
                    screen=screen,
                    model=self.model,
                    width=width,
                    height=height,
                ),
            )
        elif screen in ("timesheet", "reports", "cost", "hourDialog"):
            self.application = _Application()
            self.controller = WorkHoursController(self.application)
            self.controller._week_start = date(2026, 10, 12)
            self.controller._permissions = dict(manage=True, viewCosts=True)
            self.controller._selected_login = "robin"
            self.users = RecordListModel(
                ("login", "displayName"), [dict(login="robin", displayName="Robin")]
            )
            self.controller.timesheet_entries.replace(
                [
                    dict(
                        entryCode="hour-1",
                        searchKey="sthpw/work_hour?code=hour-1",
                        taskCode="task-1",
                        taskTitle="Robot Arm",
                        process="Model",
                        login="robin",
                        loginLabel="Robin",
                        day="2026-10-14",
                        startTime="",
                        endTime="",
                        regularHours=2.5,
                        overtimeHours=0,
                        totalHours=2.5,
                        category="regular",
                        status="approved",
                        statusLabel="Approved",
                        description="Model review",
                        canEdit=True,
                        canApprove=True,
                        selected=False,
                    )
                ]
            )
            self.controller.report_values.replace(
                [
                    dict(
                        label="Robin",
                        value=12.5,
                        valueLabel="12.5 h",
                        secondary="",
                        accent="",
                        share=0.65,
                    )
                ]
            )
            for name, value in dict(
                workHoursController=self.controller,
                timesheetModel=self.controller.timesheet_entries,
                workReportModel=self.controller.report_descriptors,
                workReportValueModel=self.controller.report_values,
                userListModel=self.users,
            ).items():
                context.setContextProperty(name, value)
            name = dict(
                timesheet="TimesheetView",
                reports="WorkReportsView",
                cost="CostReportsView",
                hourDialog="WorkHourEditorDialog",
            )[screen]
            self.view = self.create(
                self.qml / (name + ".qml"),
                dict(
                    theme=self.theme,
                    **(
                        dict(
                            controller=self.controller, parent=self.window.contentItem()
                        )
                        if screen == "hourDialog"
                        else dict(width=width, height=height)
                    ),
                ),
            )
            if screen == "hourDialog":
                self.view.setProperty("controller", self.controller)
                self.view.setProperty("parent", self.window.contentItem())
                self.view.prepare(
                    dict(
                        entryCode="hour-1",
                        day="2026-10-14",
                        totalHours=2.5,
                        login="robin",
                        description="Model review",
                    )
                )
        else:
            self.controller = Knowledge()
            self.controller._initialized = screen != "uninitialized"
            self.controller._editing = screen in ("articleEditor", "create")
            self.controller._creating = screen == "create"
            self.controller._open_article_pending = screen != "catalog"
            self.controller._document.update(
                contentMarkdown="# Publishing\n\nReview the model before publishing.",
                contentText="Review the model before publishing.",
            )
            if screen == "create":
                self.controller._identity = "local:new"
                self.controller._document.update(title="New article")
            if screen == "section":
                self.controller._document.update(kind="section", title="Production")
                self.controller._table_of_contents = [
                    dict(
                        identity="DOC0001",
                        title="Publishing guide",
                        kind="article",
                        level=1,
                    )
                ]
            if screen == "catalog":
                self.controller._identity = ""
            if screen == "error":
                self.controller._error = (
                    "The article could not be loaded. Please retry."
                )
            self.upload = _AttachmentStub()
            self.preview = _PreviewStub()
            self.rich = RichTextDocumentController(self.engine)
            self.navigation = RecordListModel(
                (
                    "identity",
                    "title",
                    "description",
                    "excerpt",
                    "kind",
                    "parentCode",
                    "sortOrder",
                    "updatedBy",
                    "timestamp",
                    "searchKey",
                    "depth",
                    "hasChildren",
                    "expanded",
                    "draft",
                    "localDraft",
                ),
                [
                    dict(
                        identity="SEC0001",
                        title="Production",
                        description="Publishing notes",
                        excerpt="",
                        kind="section",
                        parentCode="",
                        sortOrder=0,
                        updatedBy="robin",
                        timestamp="",
                        searchKey="",
                        depth=0,
                        hasChildren=True,
                        expanded=True,
                        draft=False,
                        localDraft=False,
                    ),
                    dict(
                        identity="DOC0001",
                        title="Publishing guide",
                        description="Model review",
                        excerpt="",
                        kind="article",
                        parentCode="SEC0001",
                        sortOrder=1,
                        updatedBy="robin",
                        timestamp="",
                        searchKey="",
                        depth=1,
                        hasChildren=False,
                        expanded=True,
                        draft=False,
                        localDraft=False,
                    ),
                ],
            )
            self.staging = RecordListModel(
                (
                    "token",
                    "title",
                    "path",
                    "size",
                    "fileType",
                    "previewUrl",
                    "status",
                    "progress",
                    "error",
                    "snapshotKey",
                    "uploadTarget",
                )
            )
            for name, value in dict(
                knowledgeController=self.controller,
                knowledgeNavigationModel=self.navigation,
                knowledgeAttachments=self.upload,
                knowledgeAttachmentDraftModel=self.staging,
                knowledgeRichText=self.rich,
                skeyPreviewResolver=self.preview,
            ).items():
                context.setContextProperty(name, value)
            self.view = self.create(
                self.qml / "KnowledgeBaseView.qml",
                dict(theme=self.theme, width=width, height=height),
            )
        if isinstance(self.view, QQuickItem):
            self.view.setParentItem(self.window.contentItem())
        self.window.show()
        frame(self.window)
        if screen == "hourDialog":
            self.view.open()
            frame(self.window)
        assert not self.warnings, self.warnings

    def create(self, path, properties):
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(path)))
        self.components.append(component)
        obj = component.createWithInitialProperties(properties)
        assert obj is not None, [error.toString() for error in component.errors()]
        self.objects.append(obj)
        return obj

    def close(self):
        if self.controller and hasattr(self.controller, "shutdown"):
            self.controller.shutdown()
        if self.window:
            self.window.close()
        if self.view:
            self.view.deleteLater()
        if self.window:
            self.window.deleteLater()
        for obj in self.objects:
            if obj is not self.view:
                obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        env_mode.current_path = self.previous_path
        self.temporary.cleanup()
