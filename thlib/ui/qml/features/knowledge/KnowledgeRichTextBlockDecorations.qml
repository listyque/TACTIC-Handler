pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../.."

Item {
    id: root

    required property var theme
    required property var editor
    required property var documentController
    readonly property var layoutDependencies: [editor.width, editor.contentHeight, documentController.layoutRevision, documentController.blockDecorations]

    enabled: false
    Accessible.ignored: true

    Repeater {
        id: decorationRepeater
        objectName: "knowledgeBlockDecorationRepeater"
        model: root.documentController.blockDecorations || []

        delegate: Rectangle {
            id: decoration

            required property var modelData
            required property int index
            readonly property var dependencies: root.layoutDependencies
            readonly property bool codeBlock: modelData.kind === "code"
            readonly property bool pullQuote: modelData.kind === "pull-quote"
            readonly property rect startRect: {
                return dependencies.length >= 0 ? root.editor.positionToRectangle(Number(modelData.start || 0)) : Qt.rect(0, 0, 0, 0);
            }
            readonly property rect endRect: {
                return dependencies.length >= 0 ? root.editor.positionToRectangle(Number(modelData.end || modelData.start || 0)) : Qt.rect(0, 0, 0, 0);
            }
            readonly property var nextDecoration: index + 1 < root.documentController.blockDecorations.length ? root.documentController.blockDecorations[index + 1] : null
            readonly property rect nextStartRect: {
                return dependencies.length >= 0 && nextDecoration ? root.editor.positionToRectangle(Number(nextDecoration.start || 0)) : Qt.rect(0, 0, 0, 0);
            }
            readonly property real nextY: nextDecoration ? Math.max(0, nextStartRect.y - (nextDecoration.kind === "code" ? 38 : 10)) : 0
            readonly property real desiredHeight: Math.max(codeBlock ? 64 : 46, endRect.y + endRect.height + 12 - y)

            objectName: "knowledgeEditorBlockDecoration-" + index
            x: 0
            y: Math.max(0, startRect.y - (codeBlock ? 38 : 10))
            width: root.editor.width
            height: nextDecoration ? Math.max(1, Math.min(desiredHeight, nextY - y - 1)) : desiredHeight
            radius: root.theme.surfaceRadius
            color: codeBlock ? root.theme.surfaceContainerLow : root.theme.surfaceContainerHighest
            border.width: codeBlock || pullQuote ? 1 : 0
            border.color: codeBlock ? root.theme.outlineVariant : root.theme.action

            Rectangle {
                visible: decoration.modelData.kind === "quote"
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 4
                radius: 2
                color: root.theme.action
            }

            Label {
                objectName: "knowledgeQuoteMark-" + decoration.index
                visible: !decoration.codeBlock
                anchors.left: parent.left
                anchors.leftMargin: decoration.pullQuote ? 16 : 11
                anchors.top: parent.top
                anchors.topMargin: 4
                text: "“"
                color: root.theme.action
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.title * 1.5
                font.weight: Font.Bold
            }

            Label {
                visible: decoration.pullQuote
                anchors.right: parent.right
                anchors.rightMargin: 16
                anchors.bottom: parent.bottom
                text: "”"
                color: root.theme.action
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.title * 1.5
                font.weight: Font.Bold
            }

            RowLayout {
                objectName: "knowledgeCodeHeader-" + decoration.index
                visible: decoration.codeBlock
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                height: 34
                spacing: 7

                Controls.MaterialIcon {
                    name: decoration.modelData.language === "python" ? "script-python" : "code-block"
                    size: 16
                    color: root.theme.secondaryText
                }
                Label {
                    objectName: "knowledgeEditorCodeLanguage-" + decoration.index
                    text: String(decoration.modelData.language || "").length ? String(decoration.modelData.language).charAt(0).toUpperCase() + String(decoration.modelData.language).slice(1) : qsTr("Code")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
                Item {
                    Layout.fillWidth: true
                }
            }
        }
    }
}
