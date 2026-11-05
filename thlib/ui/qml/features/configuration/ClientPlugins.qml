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
    property string selectedPlugin: ""
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
                        objectName: "clientPluginSelect_" + modelData.code
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        theme: root.theme
                        text: modelData.title + (modelData.version ? " · " + modelData.version : "")
                        description: modelData.error || (!modelData.allowed ? qsTr("Your groups cannot run this plugin") : modelData.running ? qsTr("Running version: %1").arg(modelData.runningVersion) : modelData.description || qsTr("Runs in TACTIC Handler"))
                        selected: root.selectedPlugin === modelData.code
                        wrapTitle: true
                        enabled: !root.controller.busy
                        onClicked: root.selectedPlugin = modelData.code
                    }
                    Controls.Button {
                        objectName: "clientPluginLaunch_" + modelData.code
                        theme: root.theme
                        text: modelData.running ? qsTr("Show window") : qsTr("Launch")
                        enabled: !root.controller.busy && modelData.allowed && modelData.enabled && !modelData.error
                        Accessible.name: (modelData.running ? qsTr("Show %1") : qsTr("Launch %1")).arg(modelData.title)
                        onClicked: {
                            root.selectedPlugin = modelData.code
                            root.controller.open_plugin(modelData.code)
                        }
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
                    Layout.fillWidth: true
                    wrapText: true
                    text: qsTr("Start %1 automatically").arg(modelData.title)
                    checked: modelData.autostart
                    enabled: !root.controller.busy && modelData.enabled && modelData.allowed && !modelData.error
                    onToggled: root.controller.set_autostart(modelData.code, checked)
                }
                Controls.SectionLabel {
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("Only this plugin, after sign-in and project selection. Other plugins have their own setting.")
                    wrapMode: Text.Wrap
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: root.theme.outlineVariant
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
            text: root.controller.error || root.controller.message || qsTr("Enabled makes a plugin available; it does not launch it. Use Launch here or the main-window plugin actions. Active queues keep their version.")
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
