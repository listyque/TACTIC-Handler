import QtQuick
import QtQuick.Dialogs
import "../tactic_frame" as Frame
import "../tactic_frame/controls/forms/file.ui.mjs" as UI

Frame.FrameView {
    id: root
    property string value: ""
    property bool editable: true
    signal valueEdited(var value)
    implicitHeight: 44
    scene: UI.describe(value, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language, editable)
    onEvent: action => {
        if (action.type === "choose")
            fileDialog.open();
        else if (action.type === "clear")
            root.valueEdited("");
    }
    FileDialog {
        id: fileDialog
        title: qsTr("Choose file")
        fileMode: FileDialog.OpenFile
        onAccepted: root.valueEdited(selectedFile)
    }
}
