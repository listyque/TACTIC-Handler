import QtQuick
import QtQuick.Window
import QtQuick.Dialogs
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/support/help/help.ui.mjs" as UI
import "../../../tactic_frame/features/support/help/help.state.mjs" as State

Item {
    id: root
    objectName: "applicationHelpView"
    required property var theme
    readonly property bool presented: !!Window.window && Window.window.visible
    onPresentedChanged: helpController.set_active(presented)
    property var ui: State.initial()
    readonly property string language: localizationController.current_language
    readonly property var article: helpController.article || ({})
    readonly property var frameData: ({
            articles: helpController.topics,
            busy: false,
            canDownload: true,
            currentFile: article.filePath || "",
            style: theme.style
        })
    readonly property var scene: UI.describe(ui, frameData, width, height, language)

    function row(list, record) {
        return UI.topicRow(ui, record, list.width - 16, language);
    }
    function findTopicList(item) {
        if (item.objectName === "helpTopicList")
            return item;
        for (let child of item.children) {
            const found = root.findTopicList(child);
            if (found)
                return found;
        }
        return null;
    }
    function reveal(id, focus) {
        const records = scene.topicRows;
        const index = records.findIndex(record => record.id === id);
        const list = findTopicList(frame);
        if (list && index >= 0)
            list.contentY = State.revealOffset(list.contentY, index, list.height, records.length);
        if (focus)
            frame.focusControl("helpTopic_" + id);
    }
    function dispatch(action) {
        if (["select", "open", "close"].indexOf(action.type) >= 0 && documentPane)
            documentPane.capture();
        const result = State.transition(ui, helpController.topics, action);
        if (documentPane && ["open", "select", "loaded"].indexOf(action.type) >= 0) {
            documentPane.prepare();
            Qt.callLater(documentPane.restore);
        }
        ui = result.model;
        for (const command of result.commands) {
            if (command.type === "selectArticle")
                helpController.select(command.id);
            else if (command.type === "reload")
                helpController.reload();
            else if (command.type === "openFile")
                helpController.open_current_file();
            else if (command.type === "download")
                exportDialog.open();
            else if (command.type === "close")
                windowModel.close_window("help");
            else if (command.type === "reveal")
                Qt.callLater(function () {
                    root.reveal(command.id, false);
                });
            else if (command.type === "focusTopic")
                Qt.callLater(function () {
                    root.reveal(command.id, true);
                });
            else if (command.type === "focusArticle" && documentPane)
                Qt.callLater(documentPane.focusArticle);
        }
    }
    property var documentPane: null
    Component.onCompleted: {
        helpController.set_active(presented);
        dispatch({
            type: "loaded"
        });
        dispatch({
            type: "open",
            id: windowModel.helpTopic
        });
    }
    Connections {
        target: windowModel
        function onHelpRequested(topic) {
            root.dispatch({
                type: "open",
                id: topic
            });
        }
    }
    Connections {
        target: helpController
        function onTopicsChanged() {
            root.dispatch({
                type: "loaded"
            });
        }
    }
    Frame.FrameView {
        id: frame
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        models: ({
                helpTopics: root.scene.topicRows
            })
        describeRow: root.row
        views: ({
                document: documentComponent,
                busy: busyComponent
            })
        onEvent: action => root.dispatch(action)
    }
    FileDialog {
        id: exportDialog
        title: qsTr("Download article")
        fileMode: FileDialog.SaveFile
        nameFilters: ["Markdown (*.md)"]
        onAccepted: helpController.save_current_file(selectedFile)
    }
    Component {
        id: busyComponent
        Controls.BusyIndicator {
            uiTheme: root.theme
            running: root.frameData.busy
        }
    }
    Component {
        id: documentComponent
        Controls.DocumentPane {
            id: pane
            theme: root.theme
            documentKey: root.ui.selected
            baseUrl: root.article.fileUrl || ""
            text: root.article.body || ""
            summary: root.article.summary || ""
            error: helpController.error
            scrollOffset: State.offset(root.ui, root.ui.selected)
            presented: root.presented && (!root.scene.compact || !root.ui.topicsVisible)
            onScrollChanged: (id, offset) => root.dispatch({
                    type: "scroll",
                    id: id,
                    value: offset
                })
            onFormatRequested: (document, style) => helpController.format_document(document, style)
            onLinkActivated: link => {
                const topic = State.topicFromLink(link);
                if (topic)
                    root.dispatch({
                        type: "select",
                        id: topic
                    });
                else
                    Qt.openUrlExternally(link);
            }
            Component.onCompleted: root.documentPane = pane
            Component.onDestruction: root.documentPane = null
        }
    }
}
