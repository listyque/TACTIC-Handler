import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme

    property var availableRepositories: {
        if (!watchFoldersController.editorOpen)
            return []
        const selected = watchFoldersController.editor.repositories || []
        const result = []
        const repositories = watchFoldersController.repositories || []
        for (let index = 0; index < repositories.length; ++index) {
            if (selected.indexOf(repositories[index].value) < 0)
                result.push(repositories[index])
        }
        result.push({ label: qsTr("All Repos"), value: "__all__" })
        return result
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: qsTr("Relative Watch Path:")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
            }
            Controls.TextField {
                theme: root.theme
                Layout.fillWidth: true
                text: watchFoldersController.editor.path || ""
                onTextEdited: watchFoldersController.set_editor_value(
                    "path", text
                )
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Controls.ComboBox {
                id: repositoryCombo
                theme: root.theme
                Layout.fillWidth: true
                model: root.availableRepositories
                textRole: "label"
                valueRole: "value"
                translateDisplayText: false
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Add")
                icon.name: "add"
                enabled: repositoryCombo.currentIndex >= 0
                onClicked: {
                    const value = repositoryCombo.currentValue
                    if (value === "__all__") {
                        const repositories = watchFoldersController.repositories
                        for (let index = 0; index < repositories.length; ++index)
                            watchFoldersController.toggle_editor_repository(
                                repositories[index].value, true
                            )
                    } else {
                        watchFoldersController.toggle_editor_repository(
                            value, true
                        )
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant
            radius: root.theme.itemRadius

            ListView {
                id: selectedRepositories
                anchors.fill: parent
                anchors.margins: 6
                clip: true
                model: watchFoldersController.repositories
                boundsBehavior: Flickable.StopAtBounds

                delegate: Item {
                    required property var modelData
                    readonly property bool isSelected: (
                        watchFoldersController.editor.repositories || []
                    ).indexOf(modelData.value) >= 0
                    width: selectedRepositories.width
                    height: isSelected ? 40 : 0
                    visible: isSelected

                    Controls.ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        normalColor: root.theme.row
                        cornerRadius: root.theme.itemRadius
                        railVisible: false
                        separatorVisible: false
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 6

                        Label {
                            Layout.fillWidth: true
                            text: modelData.label
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            elide: Text.ElideRight
                        }
                        Controls.Button {
                            theme: root.theme
                            compact: true
                            text: qsTr("Remove")
                            icon.name: "delete"
                            destructive: true
                            onClicked:
                                watchFoldersController.toggle_editor_repository(
                                    modelData.value, false
                                )
                        }
                    }
                }
                ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

                Label {
                    anchors.centerIn: parent
                    visible: (
                        watchFoldersController.editor.repositories || []
                    ).length === 0
                    text: qsTr("No repositories selected")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: watchFoldersController.message.length > 0
            text: watchFoldersController.message
            color: root.theme.error
            wrapMode: Text.WordWrap
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: watchFoldersController.cancel_edit()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Save and Close")
                icon.name: "save"
                highlighted: true
                enabled: watchFoldersController.canSaveEditor
                onClicked: watchFoldersController.save_edit()
            }
        }
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        theme: root.theme
        visible: watchFoldersController.busy
        message: qsTr("Preparing watch folder…")
    }
}
