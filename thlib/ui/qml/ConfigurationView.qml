import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property string windowId

    function pageTitle(pageId) {
        for (let row = 0; row < configPageModel.count(); ++row) {
            const page = configPageModel.get(row)
            if (page.target === pageId)
                return qsTr(page.title)
        }
        return qsTr("Configuration")
    }

    function pageDescription(pageId) {
        for (let row = 0; row < configPageModel.count(); ++row) {
            const page = configPageModel.get(row)
            if (page.target === pageId)
                return qsTr(page.description || "")
        }
        return ""
    }

    function pageHelpTopic(pageId) {
        for (let row = 0; row < configPageModel.count(); ++row) {
            const page = configPageModel.get(row)
            if (page.target === pageId)
                return page.helpTopic || "configuration"
        }
        return "configuration"
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 216
            Layout.fillHeight: true
            color: root.theme.surfaceContainerLow

            ColumnLayout {
                anchors.fill: parent
                anchors.topMargin: 18
                spacing: 6

                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 20
                    Layout.rightMargin: 16
                    text: qsTr("Configuration")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                }

                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 20
                    Layout.rightMargin: 16
                    text: qsTr("TACTIC-HANDLER  ·  PREFERENCES")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.letterSpacing: 0.7
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    Layout.topMargin: 10
                    Layout.bottomMargin: 6
                    color: root.theme.outlineVariant
                }

                ListView {
                    id: pageList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    leftMargin: 8
                    rightMargin: 8
                    topMargin: 4
                    bottomMargin: 12
                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: pageList
                    }
                    model: configPageModel
                    delegate: Item {
                        id: pageRow
                        required property string title
                        required property string target
                        required property string icon
                        objectName: "configurationPage_" + target
                        width: pageList.width - pageList.leftMargin
                            - pageList.rightMargin
                        height: 48
                        readonly property bool selected:
                            configurationController.current_page === target

                        Rectangle {
                            anchors.fill: parent
                            radius: 14
                            color: pageRow.selected
                                ? root.theme.selected
                                : pageMouse.containsMouse
                                    ? root.theme.rowHover : "transparent"
                        }
                        Rectangle {
                            visible: pageRow.selected
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            width: 3
                            height: 22
                            radius: 2
                            color: root.theme.action
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            spacing: 12
                            Controls.MaterialIcon {
                                name: pageRow.icon
                                size: 18
                                color: pageRow.selected
                                    ? root.theme.action
                                    : root.theme.secondaryText
                            }
                            Label {
                                Layout.fillWidth: true
                                text: qsTr(pageRow.title)
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.bodyLarge
                                font.weight: pageRow.selected
                                    ? Font.DemiBold : Font.Normal
                            }
                            Rectangle {
                                visible: pageRow.selected
                                    && configurationController.current_page_dirty
                                Layout.preferredWidth: 7
                                Layout.preferredHeight: 7
                                radius: 4
                                color: root.theme.action
                            }
                        }
                        MouseArea {
                            id: pageMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked:
                                configurationController.select_page(pageRow.target)
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 76
                color: root.theme.surfaceContainerLow

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 24
                    anchors.rightMargin: 24
                    anchors.topMargin: 13
                    anchors.bottomMargin: 12
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Label {
                            Layout.fillWidth: true
                            text: root.pageTitle(
                                configurationController.current_page
                            )
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 18
                            font.weight: Font.DemiBold
                        }
                        Rectangle {
                            visible:
                                configurationController.current_page_dirty
                            implicitWidth: dirtyLabel.implicitWidth + 20
                            implicitHeight: 25
                            radius: 13
                            color: root.theme.primaryContainer
                            Label {
                                id: dirtyLabel
                                anchors.centerIn: parent
                                text: qsTr("Unsaved")
                                color: root.theme.selectedText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.DemiBold
                            }
                        }
                        Controls.CompactIconButton {
                            objectName: "configurationHelpButton"
                            theme: root.theme
                            iconName: "help"
                            toolTip: qsTr("Help")
                            Accessible.name: toolTip
                            onClicked: windowModel.open_help(
                                root.pageHelpTopic(
                                    configurationController.current_page
                                )
                            )
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.pageDescription(
                            configurationController.current_page
                        )
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: root.theme.outlineVariant
            }

            ConfigurationPage {
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                pageId: configurationController.current_page
                managed: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                color: root.theme.surfaceContainerLow

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 1
                    color: root.theme.outlineVariant
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    spacing: 10

                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Reset")
                        objectName: "configurationReset"
                        flat: true
                        enabled:
                            configurationController.can_reset_current_page
                            && configurationController.current_page_dirty
                        onClicked: configurationController.reset_current()
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Apply")
                        objectName: "configurationApply"
                        flat: true
                        enabled: configurationController.current_page_dirty
                        onClicked: configurationController.apply_current()
                    }
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Save")
                        highlighted: true
                        onClicked: configurationController.save_and_close()
                    }
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Cancel")
                        flat: true
                        onClicked: configurationController.request_close()
                    }
                }
            }
        }
    }

    Controls.Dialog {
        id: unsavedDialog
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(430, root.width - 40)
        modal: true
        padding: 22
        closePolicy: Popup.NoAutoClose

        contentItem: RowLayout {
            spacing: 16

            Rectangle {
                Layout.alignment: Qt.AlignTop
                Layout.preferredWidth: 42
                Layout.preferredHeight: 42
                radius: 21
                color: root.theme.primaryContainer
                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    name: "edit_note"
                    size: 21
                    color: root.theme.selectedText
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 5
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Unsaved changes")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Save changes before closing Configuration?")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                }
            }
        }

        footer: DialogButtonBox {
            leftPadding: 14
            rightPadding: 14
            bottomPadding: 14
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Save")
                highlighted: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
                onClicked: {
                    unsavedDialog.close()
                    configurationController.save_and_close()
                }
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Discard")
                destructive: true
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.DestructiveRole
                onClicked: {
                    unsavedDialog.close()
                    configurationController.discard_and_close()
                }
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                onClicked: unsavedDialog.close()
            }
        }
    }

    Connections {
        target: configurationController

        function onConfirmationRequested() {
            unsavedDialog.open()
        }
    }
}
