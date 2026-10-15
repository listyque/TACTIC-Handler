import QtQuick
import QtQuick.Controls
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var cell
    property real maximumHeight: 300

    Column {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: Math.min(root.height, root.maximumHeight)

        Label {
            id: diagnostic
            visible: Boolean(root.cell.diagnostic)
            width: parent.width
            text: qsTr("XML Parse Error") + ": " + String(root.cell.diagnostic || "")
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.Wrap
        }
        Flickable {
            id: viewport
            width: parent.width
            height: Math.max(0, parent.height - (diagnostic.visible ? diagnostic.height : 0))
            clip: true
            contentWidth: Math.max(width, reader.implicitWidth)
            contentHeight: reader.implicitHeight

            Controls.TextArea {
                id: reader
                objectName: "tableStructuredText"
                theme: root.theme
                width: viewport.contentWidth
                height: implicitHeight
                text: String(root.cell.text || "")
                textFormat: TextEdit.PlainText
                wrapMode: TextEdit.NoWrap
                readOnly: true
                background: null
                leftPadding: 0
                rightPadding: 0
                topPadding: 0
                bottomPadding: 0
                font.family: "Consolas"
                font.pointSize: Controls.Typography.body
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: viewport
            }
            ScrollBar.horizontal: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: viewport
            }
        }
    }
}
