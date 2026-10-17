import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/objects/description.ui.mjs" as UI
import "features/objects" as Objects

Item {
    id: root
    required property var theme
    property string value: ""
    property string targetTitle: ""
    property string targetKind: ""
    property string errorText: ""
    property bool managed: true
    property bool editing: false
    property bool pinned: false
    property bool dirty: false
    property bool saving: false
    property bool canSave: true
    property bool editorEnabled: true
    property bool compact: false
    property bool showTargetHeader: true
    property bool internalTextChange: false
    property var editorItem: null
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            managed: managed,
            enabled: editorEnabled,
            editing: editing,
            pinned: pinned,
            dirty: dirty,
            saving: saving,
            canSave: canSave,
            compact: compact,
            header: showTargetHeader,
            title: targetTitle,
            kind: targetKind,
            error: errorText
        })
    signal editRequested
    signal valueEdited(string value)
    signal saveRequested
    signal cancelRequested
    signal pinRequested
    signal unpinRequested
    signal editingFinished(string value)

    function syncText() {
        if (editorItem)
            editorItem.syncText();
    }
    function dispatch(action) {
        if (action.type === "edit") {
            editRequested();
            Qt.callLater(function () {
                if (editorItem)
                    editorItem.focusEditor();
            });
        } else if (action.type === "cancel")
            cancelRequested();
        else if (action.type === "save")
            saveRequested();
        else if (action.type === "pin")
            pinRequested();
        else if (action.type === "unpin")
            unpinRequested();
    }
    Keys.onEscapePressed: event => {
        if (root.managed && root.editing && !root.saving) {
            root.cancelRequested();
            event.accepted = true;
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        views: ({
                value: valueComponent
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: valueComponent
        Objects.DescriptionValue {
            theme: root.theme
            model: UI.presentation(root.frameModel, root.language)
            value: root.value
            html: typeof appController !== "undefined" && typeof appController.rich_text_html === "function" ? appController.rich_text_html(root.value) : root.value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            onValueEdited: value => root.valueEdited(value)
            onEditingFinished: value => root.editingFinished(value)
            onLinkActivated: link => {
                if (typeof appController !== "undefined" && typeof appController.open_rich_link === "function")
                    appController.open_rich_link(link);
            }
            Component.onCompleted: root.editorItem = this
            Component.onDestruction: if (root.editorItem === this)
                root.editorItem = null
        }
    }
}
