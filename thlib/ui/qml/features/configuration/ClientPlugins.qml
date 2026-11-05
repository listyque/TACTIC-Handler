import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import "../../controls" as Controls
import "../../tactic_frame/core/foundation.mjs" as Foundation

Item {
    id: root
    required property var theme
    required property var controller
    property string pendingArchive: ""
    ColumnLayout {
        anchors.fill: parent
        spacing: Foundation.spacing.compact
        Controls.SectionLabel {
            Layout.fillWidth: true
            theme: root.theme
            text: qsTr("Desktop tools supplied by this project's TACTIC server. Updates apply on the next plugin launch.")
            wrapMode: Text.Wrap
        }
        RowLayout {
            Layout.fillWidth: true
            Controls.Button {
                objectName: "clientPluginsRefresh"
                theme: root.theme
                text: qsTr("Refresh")
                enabled: !root.controller.busy
                onClicked: root.controller.refresh()
            }
            Controls.Button {
                objectName: "clientPluginsPublish"
                theme: root.theme
                text: qsTr("Publish ZIP…")
                visible: root.controller.canPublish
                enabled: !root.controller.busy
                onClicked: root.controller.choose_publish()
            }
            Item { Layout.fillWidth: true }
            Controls.BusyIndicator { uiTheme: root.theme; running: root.controller.busy }
        }
        ListView {
            id: plugins
            objectName: "clientPluginsList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 140
            model: root.controller.rows
            spacing: Foundation.spacing.compact
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            delegate: ColumnLayout {
                required property var modelData
                width: plugins.width - Foundation.controls.scrollBar.extent - Foundation.spacing.compact
                spacing: Foundation.spacing.compact
                RowLayout {
                    Layout.fillWidth: true
                    Controls.EditorListItem {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        theme: root.theme
                        text: modelData.title + (modelData.version ? " · " + modelData.version : "")
                        description: modelData.error || (!modelData.allowed ? qsTr("Your groups cannot run this plugin") : modelData.running ? qsTr("Running version: %1").arg(modelData.runningVersion) : modelData.description || qsTr("Runs in TACTIC Handler"))
                        enabled: !root.controller.busy && modelData.allowed && modelData.enabled && !modelData.error
                        onClicked: root.controller.open_plugin(modelData.code)
                    }
                    Controls.CheckBox {
                        objectName: "clientPluginEnabled_" + modelData.code
                        theme: root.theme
                        text: qsTr("Enabled")
                        checked: modelData.enabled
                        enabled: !root.controller.busy
                        onToggled: root.controller.set_enabled(modelData.code, checked)
                    }
                }
                Controls.CheckBox {
                    objectName: "clientPluginAutostart_" + modelData.code
                    theme: root.theme
                    text: qsTr("Open when Handler starts")
                    checked: modelData.autostart
                    enabled: !root.controller.busy && modelData.enabled && modelData.allowed && !modelData.error
                    onToggled: root.controller.set_autostart(modelData.code, checked)
                }
            }
            QQC.ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
            Controls.SectionLabel {
                anchors.centerIn: parent
                width: Math.max(0, parent.width - 24)
                theme: root.theme
                visible: plugins.count === 0 && !root.controller.busy
                text: qsTr("No client plugins are active in this project")
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
            }
        }
        RowLayout {
            visible: root.controller.canPublish
            Layout.fillWidth: true
            Controls.SectionLabel { theme: root.theme; text: qsTr("Release version") }
            Controls.TextField {
                id: version
                objectName: "clientPluginBuildVersion"
                theme: root.theme
                Layout.fillWidth: true
                text: "1.0.0"
                enabled: !root.controller.busy
            }
            Controls.Button {
                objectName: "clientPluginBuild"
                theme: root.theme
                text: qsTr("Build ZIP…")
                enabled: !root.controller.busy && !!version.text
                onClicked: root.controller.build(version.text)
            }
        }
        Controls.SelectableText {
            Layout.fillWidth: true
            theme: root.theme
            text: root.controller.error || root.controller.message || qsTr("Click a plugin to open it. Active render queues keep their current version.")
        }
    }
    Connections {
        target: root.controller
        function onPublishRequested(path) {
            root.pendingArchive = path;
            confirmation.open();
        }
    }
    Controls.Dialog {
        id: confirmation
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(520, root.width - 24)
        modal: true
        title: qsTr("Publish client plugin")
        standardButtons: QQC.Dialog.Ok | QQC.Dialog.Cancel
        contentItem: Controls.SelectableText {
            theme: root.theme
            text: qsTr("Make this ZIP the active client plugin release for the current server and project? Running queues keep their version.\n%1").arg(root.pendingArchive)
        }
        onAccepted: root.controller.publish(root.pendingArchive)
    }
    Component.onCompleted: root.controller.refresh()
}
