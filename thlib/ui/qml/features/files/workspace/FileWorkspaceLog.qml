import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/log.ui.mjs" as UI

Item {
    id: root
    objectName: "fileWorkspaceLog"
    required property var theme
    required property var controller
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            native: true,
            expanded: true
        }, width, height, root.language)
        views: ({
                entries: {
                    component: entryList
                }
            })
        onEvent: action => {
            if (action.type === "copy")
                root.controller.copy_log();
            else if (action.type === "clear")
                root.controller.clear_log();
            else if (action.type === "debug")
                root.controller.open_debug_log();
            else if (action.type === "visibility")
                root.controller.set_value("log_visible", false);
        }
    }
    Component {
        id: entryList
        ListView {
            id: entries
            objectName: "fileWorkspaceLogEntries"
            model: root.controller.log_model
            clip: true
            Accessible.role: Accessible.List
            Accessible.name: qsTr("Operation log")
            ScrollBar.vertical: Controls.ScrollBar {
                id: bar
                theme: root.theme
                flickableTarget: entries
            }
            Timer {
                id: tail
                interval: 0
                onTriggered: entries.positionViewAtEnd()
            }
            onCountChanged: if (count)
                tail.restart()
            delegate: Frame.FrameView {
                id: entry
                required property int index
                required property string time
                required property string level
                required property string operation
                required property string message
                required property string path
                property real messageHeight: 18
                width: Math.max(0, entries.width - bar.reservedExtent)
                height: Math.max(16, messageHeight)
                onHeightChanged: if (index === entries.count - 1)
                    tail.restart()
                theme: root.theme
                scene: UI.entry({
                    time: time,
                    level: level,
                    operation: operation,
                    message: message,
                    path: path
                }, width, height)
                views: ({
                        message: {
                            component: messagePort,
                            nodeProps: true
                        }
                    })
                Component {
                    id: messagePort
                    Controls.TextArea {
                        id: messageText
                        property var frameNode: ({
                                text: "",
                                fontSize: 12,
                                weight: 400,
                                color: "primaryText"
                            })
                        objectName: "fileWorkspaceLogMessage"
                        theme: root.theme
                        text: frameNode.text
                        readOnly: true
                        selectByMouse: true
                        wrapMode: TextEdit.Wrap
                        textFormat: TextEdit.PlainText
                        padding: 0
                        font: entry.controlFont(frameNode)
                        color: root.theme[frameNode.color]
                        background: Item {}
                        Timer {
                            id: measure
                            interval: 0
                            onTriggered: entry.messageHeight = Math.max(16, messageText.contentHeight)
                        }
                        onContentHeightChanged: measure.restart()
                        Accessible.name: text
                    }
                }
            }
        }
    }
}
