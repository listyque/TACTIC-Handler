import QtQuick
import QtQuick.Window
import QtQuick.Controls
import "../../thlib/ui/qml" as TH
import "../../thlib/ui/qml/tactic_frame" as Frame
import "selection.ui.mjs" as UI

ApplicationWindow {
    id: root
    required property var applicationRoot
    required property var selectionModel
    property int selectionRevision: 0
    readonly property var records: {
        const revision = root.selectionRevision;
        return root.selectionModel.records();
    }
    property string batchName: "Selection"
    property string preview: ""
    property bool modal: false
    signal disposeRequested
    onClosing: root.disposeRequested()
    readonly property string language: typeof localizationController === "undefined" ? Qt.uiLanguage : localizationController.current_language
    title: qsTr("Frame tool example")
    width: 640
    height: 580
    minimumWidth: 420
    minimumHeight: 400
    transientParent: root.applicationRoot
    modality: root.modal ? Qt.WindowModal : Qt.NonModal
    color: toolTheme.workspace

    Connections {
        target: root.selectionModel
        function onContentReplaced() {
            root.selectionRevision++;
        }
        function onRowsRemoved() {
            root.selectionRevision++;
        }
        function onRowsInserted() {
            root.selectionRevision++;
        }
        function onDataChanged() {
            root.selectionRevision++;
        }
    }
    TH.Theme {
        id: toolTheme
        dark: root.applicationRoot.dark
        styleName: root.applicationRoot.applicationThemeStyleName
        baseColor: root.applicationRoot.applicationThemeBaseColor
        accentColor: root.applicationRoot.applicationThemeAccentColor
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: toolTheme
        models: ({
                selection: root.selectionModel
            })
        scene: UI.describe({
            name: root.batchName,
            rows: root.records,
            preview: root.preview
        }, width, height, root.language)
        describeRow: UI.row
        onEvent: action => {
            if (action.type === "name") {
                root.batchName = action.value;
                root.preview = "";
            } else if (action.type === "clear") {
                root.selectionModel.clear();
                root.preview = "";
            } else if (action.type === "preview") {
                const selection = {
                    name: root.batchName.trim(),
                    ids: root.records.map(row => row.id)
                };
                root.preview = JSON.stringify(selection);
                console.log(root.preview);
            }
        }
    }
}
