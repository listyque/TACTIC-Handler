import QtQuick
import QtQuick.Window
import QtQuick.Dialogs
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/files/object_checkin.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var owner: tableServicesController.appendEditor
    readonly property var inputWindow: root.Window.window
    onInputWindowChanged: root.owner.attach_window(inputWindow)
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    function requestClose() {
        owner.request_close();
        return !owner.isOpen;
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        focus: true
        scene: width > 0 && height > 0 ? UI.describe(root.owner.model, width, height, root.language) : {
            nodes: []
        }
        models: ({
                files: root.owner.fileModel
            })
        describeRow: (list, row, index) => UI.fileRow(row, list.width - 16, root.language)
        Keys.onEscapePressed: event => {
            root.owner.request_close();
            event.accepted = true;
        }
        onEvent: (action, value) => {
            if (action.type === "choose")
                files.open();
            else
                root.owner.activate(action, value);
        }
        DropArea {
            anchors.fill: parent
            onDropped: drop => {
                if (drop.hasUrls)
                    root.owner.add_files(drop.urls);
            }
        }
    }
    FileDialog {
        id: files
        title: qsTr("Choose files for check-in")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.owner.add_files(selectedFiles)
    }
}
