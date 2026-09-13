import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property int modelRevision: 0

    function refresh() {
        repositoryEditorController.begin_edit()
    }

    Component.onCompleted: refresh()

    Connections {
        target: repositoryEditorModel

        function onDataChanged() { root.modelRevision += 1 }
        function onContentReplaced() { root.modelRevision += 1 }
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: contentColumn.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: scroll
        }

        ColumnLayout {
            id: contentColumn
            x: 22
            y: 20
            width: Math.max(0, scroll.availableWidth - 44)
            spacing: 22

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Repository storage")
                description: qsTr("Snapshots, previews, check-in, check-out and synchronization depend on a valid repository path.")
                iconName: "database"

                Controls.SettingsRow {
                    theme: root.theme
                    title: repositoryEditorController.configuration_required
                        ? qsTr("Repository is not configured")
                        : repositoryEditorController.current_title.length
                            ? repositoryEditorController.current_title
                            : qsTr("Repository configuration is loading")
                    description: repositoryEditorController.current_path.length
                        ? repositoryEditorController.current_path
                        : qsTr("Set a writable path for the default repository before working with files.")

                    Controls.StatusChip {
                        theme: root.theme
                        text: repositoryEditorController.configuration_required
                            ? qsTr("Setup required")
                            : repositoryEditorController.configuration_loaded
                                ? qsTr("Configured") : qsTr("Loading")
                        iconName: repositoryEditorController.configuration_required
                            ? "warning" : repositoryEditorController.configuration_loaded
                                ? "check-circle" : "schedule"
                        accentColor: repositoryEditorController.configuration_required
                            ? root.theme.red : repositoryEditorController.configuration_loaded
                                ? root.theme.green : root.theme.secondaryText
                    }
                }

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Repository definitions")
                    description: qsTr("Configure Windows and Linux paths, enabled repositories, the default destination, custom locations and project mappings.")
                    showDivider: false

                    Controls.Button {
                        objectName: "openRepositoryEditorButton"
                        theme: root.theme
                        text: qsTr("Open Repository Editor")
                        icon.name: "database"
                        highlighted: repositoryEditorController.configuration_required
                        onClicked: windowModel.show_window("repository_editor")
                    }
                    Controls.Button {
                        theme: root.theme
                        text: repositoryEditorController.busy
                            ? qsTr("Checking…") : qsTr("Check paths")
                        icon.name: "check-circle"
                        flat: true
                        enabled: repositoryEditorController.active_count > 0
                            && !repositoryEditorController.busy
                        onClicked: repositoryEditorController.check_paths()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Active repositories")
                description: qsTr("The default repository is used when an operation does not choose another destination explicitly.")
                iconName: "folder-open"

                Repeater {
                    model: repositoryEditorModel

                    delegate: Item {
                        id: repositoryRow
                        required property int index
                        required property string title
                        required property string code
                        required property string windowsPath
                        required property string linuxPath
                        required property bool active
                        required property bool isDefault
                        required property string status
                        required property string statusText

                        Layout.fillWidth: true
                        implicitHeight: active ? rowContent.implicitHeight : 0
                        visible: active

                        Controls.SettingsRow {
                            id: rowContent
                            anchors.left: parent.left
                            anchors.right: parent.right
                            theme: root.theme
                            title: repositoryRow.title
                            description: {
                                root.modelRevision
                                const path = Qt.platform.os === "windows"
                                    ? repositoryRow.windowsPath
                                    : repositoryRow.linuxPath
                                return path.length
                                    ? path : qsTr("No path for this platform")
                            }
                            showDivider: repositoryRow.index
                                < repositoryEditorModel.count() - 1

                            Controls.StatusChip {
                                theme: root.theme
                                text: repositoryRow.isDefault
                                    ? qsTr("Default") : repositoryRow.code
                                iconName: repositoryRow.isDefault
                                    ? "star" : "folder-open"
                                accentColor: repositoryRow.isDefault
                                    ? root.theme.action
                                    : root.theme.secondaryText
                            }
                            Controls.StatusChip {
                                visible: repositoryRow.status !== "unchecked"
                                theme: root.theme
                                text: qsTr(repositoryRow.statusText)
                                iconName: repositoryRow.status === "available"
                                    ? "check-circle" : "warning"
                                accentColor:
                                    repositoryRow.status === "available"
                                    ? root.theme.green : root.theme.red
                            }
                        }
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: repositoryEditorController.active_count === 0
                    text: qsTr("No repositories are enabled.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                }
            }

            Label {
                Layout.fillWidth: true
                visible: repositoryEditorController.message.length > 0
                text: repositoryEditorController.message
                color: text.indexOf("saved") >= 0
                    ? root.theme.green : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
            }

            Item { Layout.preferredHeight: 8 }
        }
    }
}
