import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 2
        anchors.rightMargin: 6
        spacing: 3

        Rectangle {
            id: shelfMode
            objectName: "scriptShelfMode"
            Layout.preferredWidth: 26
            Layout.preferredHeight: 46
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerHigh
            border.width: 1
            border.color: root.theme.outlineVariant

            Column {
                anchors.fill: parent
                anchors.margins: 2
                spacing: 0

                Repeater {
                    model: root.controller.activeModeOptions

                    delegate: Controls.CompactIconButton {
                        required property var modelData
                        readonly property bool selected:
                            String(modelData.value || "")
                                === root.controller.activeMode

                        objectName: "scriptShelfMode_" + modelData.value
                        width: 22
                        height: 21
                        theme: root.theme
                        iconName: String(modelData.icon || "")
                        iconSize: 13
                        iconColor: selected
                            ? root.theme.selectedText
                            : root.theme.secondaryText
                        backgroundColor: selected
                            ? root.theme.selected : "transparent"
                        enabled: modelData.enabled !== false
                        toolTip: String(modelData.label || "")
                        onClicked: root.controller.set_active_mode(
                            String(modelData.value || "")
                        )
                    }
                }
            }
        }

        ListView {
            id: shelfButtons
            objectName: "scriptShelfButtons"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.bottomMargin: shelfScrollBar.visible
                ? shelfScrollBar.reservedExtent : 0
            orientation: ListView.Horizontal
            spacing: 4
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: root.controller.model

            WheelHandler {
                target: null
                blocking: true
                enabled: shelfButtons.contentWidth > shelfButtons.width
                onWheel: function(event) {
                    const pixelDelta = Math.abs(event.pixelDelta.x)
                            > Math.abs(event.pixelDelta.y)
                        ? event.pixelDelta.x : event.pixelDelta.y
                    const angleDelta = Math.abs(event.angleDelta.x)
                            > Math.abs(event.angleDelta.y)
                        ? event.angleDelta.x : event.angleDelta.y
                    const delta = pixelDelta !== 0
                        ? pixelDelta : angleDelta / 2
                    const minimumX = shelfButtons.originX
                    const maximumX = Math.max(
                        minimumX,
                        minimumX + shelfButtons.contentWidth
                            - shelfButtons.width
                    )
                    shelfButtons.contentX = Math.max(
                        minimumX,
                        Math.min(maximumX, shelfButtons.contentX - delta)
                    )
                    event.accepted = true
                }
            }

            delegate: Controls.Button {
                id: shelfButton

                required property string buttonId
                required property string title
                required property string description
                required property string iconName
                required property string script
                required property bool available
                required property bool running

                objectName: "scriptShelfAction_" + buttonId
                width: 40
                height: 40
                anchors.verticalCenter: parent ? parent.verticalCenter : undefined
                theme: root.theme
                compact: true
                topPadding: 0
                bottomPadding: 0
                flat: true
                enabled: available && !root.controller.executionBusy
                toolTip: !available
                    ? qsTr("Script is unavailable: ") + script
                    : description.length > 0 ? description : title
                onClicked: root.controller.run(buttonId)

                contentItem: Item {
                    Controls.MaterialIcon {
                        objectName: "scriptShelfActionIcon"
                        x: Math.round((parent.width - width) / 2)
                        y: 1
                        name: shelfButton.running
                            ? "hourglass-empty" : shelfButton.iconName
                        size: 16
                        color: shelfButton.contentColor
                    }

                    Label {
                        id: buttonLabel
                        objectName: "scriptShelfActionLabel"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 1
                        text: shelfButton.title
                        color: shelfButton.contentColor
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        horizontalAlignment: Text.AlignHCenter
                        maximumLineCount: 1
                        elide: Text.ElideRight
                    }
                }

                background: Rectangle {
                    radius: root.theme.itemRadius
                    color: shelfButton.down
                        ? root.theme.selected
                        : shelfButton.hovered
                            ? root.theme.rowHover : "transparent"
                }
            }

            ScrollBar.horizontal: Controls.ScrollBar {
                id: shelfScrollBar
                objectName: "scriptShelfScrollBar"
                theme: root.theme
                flickableTarget: shelfButtons
            }
        }

        Label {
            visible: shelfButtons.count === 0 && !root.controller.busy
            text: qsTr("No shelf buttons")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
        }

        Controls.BusyIndicator {
            Layout.preferredWidth: 18
            Layout.preferredHeight: 18
            uiTheme: root.theme
            running: root.controller.busy
        }

        Controls.CompactIconButton {
            objectName: "exportDccShelfButton"
            visible: root.controller.canExportDccShelf
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24
            theme: root.theme
            iconName: root.controller.dccShelfBusy
                ? "hourglass-empty" : "upload"
            round: true
            enabled: !root.controller.dccShelfBusy
            toolTip: qsTr("Create this shelf in the selected DCC")
            onClicked: {
                dccShelfName.text = root.controller.dccShelfName
                exportDccShelfDialog.open()
            }
        }

        Controls.CompactIconButton {
            objectName: "editScriptShelfButton"
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24
            theme: root.theme
            iconName: "edit"
            round: true
            toolTip: qsTr("Edit script shelf")
            onClicked: root.controller.open_editor()
        }
    }

    Controls.Dialog {
        id: exportDccShelfDialog
        objectName: "exportDccShelfDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(390, parent.width - 24)
        theme: root.theme
        modal: true
        title: qsTr("Create or update DCC shelf")
        onOpened: {
            dccShelfName.forceActiveFocus()
            dccShelfName.selectAll()
        }
        onAccepted: root.controller.export_dcc_shelf(
            dccShelfName.text
        )

        contentItem: ColumnLayout {
            spacing: 8

            Controls.TextField {
                id: dccShelfName
                objectName: "dccShelfNameField"
                Layout.fillWidth: true
                theme: root.theme
                maximumLength: 64
                placeholderText: qsTr("DCC shelf name")
                Keys.onReturnPressed: {
                    if (text.trim().length > 0)
                        exportDccShelfDialog.accept()
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr(
                    "A shelf with this name will be updated in the selected DCC."
                )
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
            }
        }

        footer: DialogButtonBox {
            background: Item {}

            Controls.Button {
                objectName: "confirmExportDccShelfButton"
                theme: root.theme
                text: qsTr("Create or update")
                highlighted: true
                enabled: dccShelfName.text.trim().length > 0
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }

            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }
}
