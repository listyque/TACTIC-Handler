import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    required property var theme
    required property bool createMode
    property bool versionInitialized: false

    function syncVersion() {
        if (!createMode || versionInitialized
                || !updateController.currentVersion)
            return
        const parts = updateController.currentVersion.split(".")
        if (parts.length === 4) {
            major.value = Number(parts[0])
            minor.value = Number(parts[1])
            build.value = Number(parts[2])
            revision.value = Number(parts[3])
            versionInitialized = true
        }
    }

    onVisibleChanged: if (visible) updateController.load()
    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10
        RowLayout {
            Layout.fillWidth: true
            Rectangle {
                Layout.preferredWidth: 42
                Layout.preferredHeight: 42
                radius: 14
                color: root.theme.secondaryContainer
                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    name: root.createMode ? "inventory_2" : "system_update"
                    size: 21
                    color: root.theme.action
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    text: root.createMode
                        ? qsTr("Create update") : qsTr("Application updates")
                    color: root.theme.primaryText
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Label {
                    text: qsTr("Current version  ") + (updateController.currentVersion || "—")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
            }
            RefreshIconButton {
                theme: root.theme
                toolTip: qsTr("Reload local update history")
                enabled: !updateController.busy
                onClicked: updateController.load()
            }
            Controls.CompactIconButton {
                theme: root.theme
                visible: !root.createMode
                iconName: "cloud_download"
                toolTip: qsTr("Check update source")
                enabled: !updateController.busy
                onClicked: updateController.refresh_remote()
            }
        }

        GridLayout {
            visible: root.createMode
            Layout.fillWidth: true
            columns: 4
            rowSpacing: 5
            columnSpacing: 8
            Label { text: qsTr("Major"); color: root.theme.secondaryText; font.pointSize: Controls.Typography.label }
            Label { text: qsTr("Minor"); color: root.theme.secondaryText; font.pointSize: Controls.Typography.label }
            Label { text: qsTr("Build"); color: root.theme.secondaryText; font.pointSize: Controls.Typography.label }
            Label { text: qsTr("Revision"); color: root.theme.secondaryText; font.pointSize: Controls.Typography.label }
            Controls.SpinBox { id: major; theme: root.theme; Layout.fillWidth: true; from: 0; to: 999 }
            Controls.SpinBox { id: minor; theme: root.theme; Layout.fillWidth: true; from: 0; to: 999 }
            Controls.SpinBox { id: build; theme: root.theme; Layout.fillWidth: true; from: 0; to: 999 }
            Controls.SpinBox { id: revision; theme: root.theme; Layout.fillWidth: true; from: 0; to: 999 }
        }
        Controls.TextArea {
            id: changes
            theme: root.theme
            visible: root.createMode
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            placeholderText: qsTr("Changes")
        }
        Controls.TextArea {
            id: misc
            theme: root.theme
            visible: root.createMode
            Layout.fillWidth: true
            Layout.preferredHeight: 62
            placeholderText: qsTr("Additional information")
        }

        ListView {
            id: versions
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: updateModel
            clip: true
            spacing: 5
            delegate: Rectangle {
                required property int index
                required property string version
                required property string date
                required property string changes
                required property string misc
                required property bool selected
                width: versions.width
                height: 72
                radius: 13
                color: selected ? root.theme.secondaryContainer
                    : root.theme.surfaceContainerLow
                border.width: 1
                border.color: selected ? root.theme.action
                    : root.theme.outlineVariant
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 9
                    spacing: 2
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: version
                            color: root.theme.primaryText
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        Item { Layout.fillWidth: true }
                        Label { text: date; color: root.theme.secondaryText; font.pointSize: Controls.Typography.caption }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: changes || misc || qsTr("No release notes")
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                        elide: Text.ElideRight
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: updateController.select(parent.index)
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: versions
            }
            Label {
                anchors.centerIn: parent
                visible: versions.count === 0 && !updateController.busy
                text: qsTr("No local update metadata")
                color: root.theme.secondaryText
                font.pointSize: Controls.Typography.body
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: updateController.busy || updateController.error.length > 0
            ProgressBar {
                Layout.fillWidth: true
                from: 0
                to: 1
                value: updateController.progress
                indeterminate: updateController.busy
                    && updateController.progress <= 0
            }
            Label {
                Layout.fillWidth: true
                text: updateController.error || updateController.stage
                color: updateController.error ? root.theme.red
                    : root.theme.secondaryText
                font.pointSize: Controls.Typography.label
                wrapMode: Text.WordWrap
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Controls.Button {
                theme: root.theme
                visible: updateController.busy
                text: qsTr("Cancel")
                icon.name: "stop"
                onClicked: updateController.cancel()
            }
            Item { Layout.fillWidth: true }
            Controls.Button {
                theme: root.theme
                visible: root.createMode
                text: qsTr("Create archive")
                icon.name: "archive"
                highlighted: true
                enabled: !updateController.busy
                onClicked: updateController.create_update(
                    major.value, minor.value, build.value, revision.value,
                    changes.text, misc.text)
            }
            Controls.Button {
                theme: root.theme
                visible: !root.createMode
                text: qsTr("Update and restart")
                icon.name: "restart_alt"
                highlighted: true
                enabled: !updateController.busy && versions.count > 0
                onClicked: updateConfirmation.open()
            }
        }
    }

    Controls.Dialog {
        id: updateConfirmation
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: 410
        title: qsTr("Restart for update?")
        contentItem: Label {
            width: 362
            text: qsTr("The existing application update mechanism will close and restart TACTIC-Handler.")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Update and restart")
                highlighted: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onAccepted: updateController.restart_to_update()
    }
    Connections {
        target: updateController
        function onStateChanged() { root.syncVersion() }
    }
}
