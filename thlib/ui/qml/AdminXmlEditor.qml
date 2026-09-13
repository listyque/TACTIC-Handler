import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.EditorPanel {
    id: root

    property string sourceText: ""
    property bool readOnly: false
    property string buttonText: qsTr("Apply to draft")
    signal applied(string text)

    title: qsTr("Native XML")
    iconName: "code"

    Flickable {
        id: editorScroll
        objectName: "adminNativeDocumentViewport"
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: 100
        clip: true
        contentWidth: width
        contentHeight: editor.implicitHeight
        boundsBehavior: Flickable.StopAtBounds

        Controls.TextArea {
            id: editor
            objectName: "adminNativeDocumentText"
            width: Math.max(0, editorScroll.width - editorBar.reservedExtent - 4)
            height: Math.max(editorScroll.height, implicitHeight)
            theme: root.theme
            text: root.sourceText
            wrapMode: TextEdit.Wrap
            readOnly: root.readOnly
            selectByMouse: true
            font.family: "Consolas"
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: editorBar
            theme: root.theme
            flickableTarget: editorScroll
        }
    }
    GridLayout {
        Layout.fillWidth: true
        visible: !root.readOnly
        columns: width >= applyHint.implicitWidth + applyButton.implicitWidth + columnSpacing ? 2 : 1
        columnSpacing: 12
        rowSpacing: 8
        Label {
            id: applyHint
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: qsTr("Apply updates the draft. Save sends it to the server.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
        Controls.Button {
            id: applyButton
            objectName: "adminApplyNativeDocument"
            Layout.alignment: Qt.AlignRight
            theme: root.theme
            text: root.buttonText
            icon.name: "check"
            enabled: editor.text !== root.sourceText
            onClicked: root.applied(editor.text)
        }
    }
}
