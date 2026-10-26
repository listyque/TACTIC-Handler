import QtQuick
import QtQuick.Controls.Basic as Basic
import "../../controls" as Controls
import "../../tactic_frame/features/scripts/request.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var frameNode: ({})
    property var previews: ({})
    property string language: Qt.uiLanguage
    property bool toolsExpanded: false
    signal action(var value)
    readonly property var chips: UI.contextItems(frameNode.context || {}, language)
    readonly property var toolGeometry: UI.messageGeometry(width, "assistant", 20, [])

    Item {
        anchors.fill: parent
        visible: root.frameNode.view === "context"
        Flickable {
            width: parent.width - 36
            height: 36
            contentWidth: chipRow.width
            clip: true
            flickableDirection: Flickable.HorizontalFlick
            Basic.ScrollBar.horizontal: Controls.ScrollBar {
                theme: root.theme
            }
            Row {
                id: chipRow
                spacing: 6
                Repeater {
                    model: root.chips
                    Rectangle {
                        required property var modelData
                        width: modelData.width
                        height: 28
                        radius: 8
                        color: root.theme.surfaceContainer
                        border.color: root.theme.outlineVariant
                        Controls.MaterialIcon {
                            x: 10
                            anchors.verticalCenter: parent.verticalCenter
                            name: parent.modelData.icon
                            size: 16
                            color: root.theme.secondaryText
                        }
                        Text {
                            x: 34
                            width: parent.width - 44
                            anchors.verticalCenter: parent.verticalCenter
                            text: parent.modelData.value
                            font.family: root.theme.fontFamily
                            font.pixelSize: 12
                            color: root.theme.primaryText
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }
        Controls.Button {
            anchors.right: parent.right
            width: 28
            height: 28
            theme: root.theme
            compact: true
            icon.name: root.frameNode.expanded ? "expand-less" : "expand-more"
            Accessible.name: qsTr("Context details")
            onClicked: root.action({
                type: "context"
            })
        }
        Flickable {
            y: 40
            width: parent.width
            height: Math.max(0, parent.height - y)
            visible: !!root.frameNode.expanded
            clip: true
            contentHeight: contextText.height
            Basic.ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }
            TextEdit {
                id: contextText
                x: 8
                width: parent.width - 24
                text: [root.frameNode.context?.page, root.frameNode.context?.view].concat(root.frameNode.context?.search_keys || []).filter(Boolean).join("\n")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                readOnly: true
                selectByMouse: true
                wrapMode: TextEdit.Wrap
            }
        }
    }

    Flickable {
        id: transcript
        objectName: "agentTranscript"
        anchors.fill: parent
        visible: root.frameNode.view === "transcript"
        clip: true
        contentHeight: messageColumn.height + 24
        boundsBehavior: Flickable.StopAtBounds
        property bool following: true
        onMovementEnded: following = contentHeight - contentY - height < 60
        onContentHeightChanged: if (following)
            contentY = Math.max(0, contentHeight - height)
        Basic.ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
        }
        Column {
            id: messageColumn
            y: 12
            width: parent.width
            spacing: UI.metrics.messageGap
            Text {
                visible: !(root.frameNode.messages || []).length
                width: parent.width - 40
                x: 20
                height: visible ? 140 : 0
                text: qsTr("What would you like to change?") + "\n\n" + qsTr("Describe the task. Attach files or paste an image.")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.Wrap
            }
            Repeater {
                model: root.frameNode.messages || []
                Item {
                    id: message
                    required property var modelData
                    width: messageColumn.width
                    height: geometry.height
                    readonly property var geometry: UI.messageGeometry(width, modelData.role, body.implicitHeight, modelData.attachments || [])
                    Rectangle {
                        objectName: message.modelData.role === "assistant" ? "agentAssistantMessage" : "agentUserMessage"
                        x: message.geometry.x
                        width: message.geometry.width
                        height: parent.height
                        radius: 12
                        border.width: 0
                        color: message.modelData.role === "user" ? root.theme.surfaceContainerHigh : "transparent"
                        TextEdit {
                            id: body
                            x: message.geometry.padding
                            y: message.geometry.padding
                            width: parent.width - 2 * message.geometry.padding
                            text: UI.safeMarkdown(message.modelData.text)
                            textFormat: TextEdit.MarkdownText
                            readOnly: true
                            selectByMouse: true
                            wrapMode: TextEdit.Wrap
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 13
                            onLinkActivated: link => {
                                if (/^https?:\/\//i.test(link))
                                    Qt.openUrlExternally(link);
                            }
                        }
                        Column {
                            x: message.geometry.padding
                            y: body.y + Math.max(20, body.implicitHeight)
                            width: body.width
                            Repeater {
                                model: message.modelData.attachments || []
                                Item {
                                    required property var modelData
                                    height: UI.attachmentHeight(modelData)
                                    width: parent.width
                                    Image {
                                        width: Math.min(320, parent.width)
                                        height: parent.height - UI.metrics.attachmentHeight
                                        source: root.previews[parent.modelData.attachment_id] || ""
                                        sourceSize: Qt.size(320, 180)
                                        fillMode: Image.PreserveAspectFit
                                        horizontalAlignment: Image.AlignLeft
                                    }
                                    Controls.Button {
                                        y: parent.height - height
                                        theme: root.theme
                                        height: UI.metrics.attachmentHeight
                                        width: parent.width
                                        text: parent.modelData.name
                                        icon.name: "attach-file"
                                        onClicked: root.action({
                                            type: "download",
                                            value: parent.modelData.attachment_id
                                        })
                                    }
                                }
                            }
                        }
                    }
                }
            }
            Controls.Button {
                objectName: "agentOperationDetails"
                x: root.toolGeometry.x
                width: root.toolGeometry.width
                height: visible ? 28 : 0
                visible: !!root.frameNode.events?.length
                theme: root.theme
                text: root.frameNode.active ? qsTr("Working with TACTIC tools…") : qsTr("Operation details")
                icon.name: root.toolsExpanded ? "expand-less" : "expand-more"
                onClicked: root.toolsExpanded = !root.toolsExpanded
            }
            Text {
                objectName: "agentOperationEvents"
                x: root.toolGeometry.x
                width: root.toolGeometry.width
                visible: root.toolsExpanded || !!root.frameNode.active
                text: (root.frameNode.events || []).join("\n")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }
            Item {
                objectName: "agentRequestStatusRow"
                x: root.toolGeometry.x
                width: root.toolGeometry.width
                height: visible ? Math.max(20, statusText.implicitHeight) : 0
                visible: !!root.frameNode.status
                Controls.MaterialIcon {
                    objectName: "agentRequestStatusIcon"
                    name: root.frameNode.status?.icon || "chat"
                    size: 18
                    color: root.theme[root.frameNode.status?.color || "secondaryText"]
                }
                Text {
                    id: statusText
                    objectName: "agentRequestStatus"
                    x: 26
                    width: parent.width - x
                    text: root.frameNode.status?.text || ""
                    color: root.theme[root.frameNode.status?.color || "secondaryText"]
                    font.family: root.theme.fontFamily
                    font.pixelSize: 12
                    lineHeight: 20
                    lineHeightMode: Text.FixedHeight
                    wrapMode: Text.Wrap
                }
            }
        }
    }

    Flickable {
        anchors.fill: parent
        visible: root.frameNode.view === "attachments"
        clip: true
        contentWidth: files.width
        flickableDirection: Flickable.HorizontalFlick
        Basic.ScrollBar.horizontal: Controls.ScrollBar {
            theme: root.theme
        }
        Row {
            id: files
            spacing: 8
            Repeater {
                model: root.frameNode.files || []
                Rectangle {
                    required property var modelData
                    width: 210
                    height: 36
                    radius: 8
                    color: root.theme.surfaceContainer
                    border.color: root.theme.outlineVariant
                    Image {
                        x: 4
                        y: 4
                        width: 28
                        height: 28
                        source: root.previews[parent.modelData.attachment_id] || ""
                        fillMode: Image.PreserveAspectFit
                    }
                    Text {
                        x: 38
                        width: 140
                        anchors.verticalCenter: parent.verticalCenter
                        text: parent.modelData.name
                        elide: Text.ElideRight
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                    }
                    Controls.Button {
                        x: 180
                        y: 5
                        width: 26
                        height: 26
                        theme: root.theme
                        compact: true
                        icon.name: "close"
                        Accessible.name: qsTr("Remove attachment")
                        onClicked: root.action({
                            type: "remove",
                            value: parent.modelData.attachment_id
                        })
                    }
                }
            }
        }
    }
}
