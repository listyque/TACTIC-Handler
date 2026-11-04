import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../controls" as Controls

Item {
    id: root
    required property var theme
    property real maximumBlockHeight: 260
    readonly property real contentHeight: content.implicitHeight
    readonly property var syntaxColors: ({
            keyword: String(theme.syntaxKeyword),
            string: String(theme.syntaxString),
            comment: String(theme.syntaxComment),
            number: String(theme.syntaxNumber),
            type: String(theme.syntaxType),
            function: String(theme.syntaxFunction),
            definition: String(theme.syntaxDefinition),
            decorator: String(theme.syntaxDefinition),
            self: String(theme.syntaxSelf),
            module: String(theme.syntaxSelf)
        })
    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 14
        Repeater {
            model: debugLog.error_request_blocks
            delegate: ColumnLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: 7

                Label {
                    Layout.fillWidth: true
                    text: modelData.name ? qsTr("Multiline argument") + ": " + modelData.name : qsTr("REQUEST")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(root.maximumBlockHeight, commandText.implicitHeight + 30)
                    radius: 12
                    color: root.theme.workspace
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    ScrollView {
                        objectName: "errorRequestScrollView"
                        anchors.fill: parent
                        anchors.margins: 7
                        clip: true
                        ScrollBar.vertical: Controls.ScrollBar {
                            objectName: "errorRequestVerticalScrollBar"
                            theme: root.theme
                        }
                        ScrollBar.horizontal: Controls.ScrollBar {
                            objectName: "errorRequestHorizontalScrollBar"
                            theme: root.theme
                        }

                        Controls.TextArea {
                            id: commandText
                            objectName: "errorRequestCode"
                            theme: root.theme
                            rightPadding: 24
                            bottomPadding: 22
                            readOnly: true
                            selectByMouse: true
                            textFormat: TextEdit.PlainText
                            wrapMode: TextEdit.NoWrap
                            text: modelData.text
                            font.family: "Consolas"
                            font.pointSize: Controls.Typography.label
                            background: Item {}
                            Component.onCompleted: debugLog.attach_request_document(textDocument, root.syntaxColors)
                            Connections {
                                target: root
                                function onSyntaxColorsChanged() {
                                    debugLog.attach_request_document(commandText.textDocument, root.syntaxColors);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
