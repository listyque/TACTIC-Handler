import QtQuick
import QtQuick.Layouts
import "../../thlib/ui/qml/controls" as Controls
import "../../thlib/ui/qml/tactic_frame" as Frame
import "../../thlib/ui/qml/tactic_frame/core/frame.mjs" as Nodes
import "../../thlib/ui/qml/tactic_frame/controls/forms/sections.ui.mjs" as Forms

Rectangle {
    id: root
    required property var theme
    required property var fields
    property string language: "en"
    property string mode: "form"
    property var lastEvent: ({})
    color: theme.workspace

    Frame.FrameView {
        id: form
        objectName: "spacingForm"
        anchors.fill: parent
        visible: root.mode === "form"
        theme: root.theme
        scene: Forms.sections(root.fields, width, root.language, true, root.theme.style)
        onEvent: event => root.lastEvent = event
    }
    Controls.EditorPanel {
        objectName: "spacingPanel"
        x: root.theme.spacing.content
        y: root.theme.spacing.content
        width: parent.width - x * 2
        visible: root.mode === "panel"
        fillContentHeight: false
        theme: root.theme
        title: "General"
        description: "A shared panel and settings row"
        Controls.SettingsRow {
            theme: root.theme
            title: "Name"
            description: "Object name"
            Controls.TextField {
                objectName: "spacingPanelField"
                Layout.preferredWidth: 160
                theme: root.theme
                text: "Robot Arm"
            }
        }
    }
    Controls.EditorListItem {
        objectName: "spacingListRow"
        x: root.theme.spacing.content
        y: 200
        width: parent.width - x * 2
        visible: root.mode === "panel"
        theme: root.theme
        text: "Robot Arm"
        description: "Object name"
    }
    Controls.Dialog {
        id: dialog
        objectName: "spacingDialog"
        x: 40
        y: 40
        width: Math.min(440, root.width - 80)
        height: 220
        theme: root.theme
        title: "Confirmation"
        contentItem: Rectangle {
            objectName: "spacingDialogBody"
            color: root.theme.surfaceContainerLow
            Controls.Button {
                theme: root.theme
                text: "Apply"
                onClicked: dialog.close()
            }
        }
    }
    function openDialog() { dialog.open(); }
}
