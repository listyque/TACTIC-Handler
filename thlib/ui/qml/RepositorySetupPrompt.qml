import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var applicationController
    required property var configurationController
    required property var repositoryController
    required property var windows
    required property bool smokeMode
    property bool shownThisSession: false

    function evaluate() {
        if (root.smokeMode || root.shownThisSession
                || !root.repositoryController.configuration_loaded
                || !root.repositoryController.configuration_required)
            return
        root.shownThisSession = true
        setupDialog.open()
    }

    function refreshAfterConnection() {
        if (root.applicationController.server_state !== "online")
            return
        root.repositoryController.begin_edit()
        Qt.callLater(root.evaluate)
    }

    Component.onCompleted: {
        refreshAfterConnection()
        Qt.callLater(root.evaluate)
    }

    Connections {
        target: root.applicationController

        function onServer_state_changed() {
            root.refreshAfterConnection()
        }
    }

    Connections {
        target: root.repositoryController

        function onConfigurationChanged() {
            Qt.callLater(root.evaluate)
            if (!root.repositoryController.configuration_required
                    && setupDialog.opened)
                setupDialog.close()
        }
    }

    Controls.Dialog {
        id: setupDialog
        objectName: "repositorySetupPrompt"
        theme: root.theme
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(480, root.width - 40)
        title: qsTr("Configure repository storage")
        closePolicy: Popup.NoAutoClose

        contentItem: RowLayout {
            spacing: 16

            Rectangle {
                Layout.alignment: Qt.AlignTop
                Layout.preferredWidth: 44
                Layout.preferredHeight: 44
                radius: 14
                color: root.theme.errorContainer

                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    name: "database"
                    size: 22
                    color: root.theme.red
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Label {
                    Layout.fillWidth: true
                    text: qsTr("Repository storage is not configured")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("TACTIC-Handler needs a repository path for snapshots, previews, check-in, check-out and synchronization. Configure it now to avoid missing files.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                }
            }
        }

        footer: Controls.DialogActions {
            theme: root.theme

            Controls.Button {
                theme: root.theme
                text: qsTr("Later")
                flat: true
                onClicked: setupDialog.close()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Configure repositories")
                icon.name: "database"
                highlighted: true
                onClicked: {
                    setupDialog.close()
                    root.configurationController.select_page("repository")
                    root.windows.show_window("configuration")
                }
            }
        }
    }
}
