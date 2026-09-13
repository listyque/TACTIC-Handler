import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Column {
    id: root
    objectName: "workspaceLayoutPresetMenuSection"
    required property var theme
    property var controller: null
    property var viewport: null
    property string pendingDeleteView: ""
    property string pendingDeleteTitle: ""
    signal closeMenuRequested()

    width: parent ? parent.width : 280
    spacing: 2

    function focusFirstAction() {
        const targets = keyboardTargets()
        if (targets.length)
            targets[0].forceActiveFocus(Qt.PopupFocusReason)
    }

    function keyboardTargets() {
        const targets = []
        for (let i = 0; i < presetRepeater.count; ++i)
            targets.push(...presetRepeater.itemAt(i).actionTargets)
        targets.push(savePresetButton, refreshButton)
        return targets.filter(target => target.visible && target.enabled)
    }

    function moveFocus(step) {
        const targets = keyboardTargets()
        if (!targets.length)
            return
        const current = targets.indexOf(root.Window.window.activeFocusItem)
        const index = current < 0 ? (step > 0 ? 0 : targets.length - 1)
            : (current + step + targets.length) % targets.length
        const target = targets[index]
        target.forceActiveFocus(Qt.TabFocusReason)
        if (root.viewport) {
            const top = target.mapToItem(root, 0, 0).y
            if (top < root.viewport.contentY)
                root.viewport.contentY = top
            else if (top + target.height > root.viewport.contentY + root.viewport.height)
                root.viewport.contentY = top + target.height - root.viewport.height
        }
    }

    Keys.onDownPressed: moveFocus(1)
    Keys.onUpPressed: moveFocus(-1)

    Item {
        width: parent.width
        height: 9
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width
            height: 1
            color: root.theme.separator
        }
    }

    RowLayout {
        width: parent.width
        height: 30
        spacing: 6

        Label {
            Layout.fillWidth: true
            leftPadding: 12
            text: qsTr("Layout presets")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }
        Controls.CompactIconButton {
            id: refreshButton
            Layout.rightMargin: 6
            theme: root.theme
            iconName: "refresh"
            toolTip: qsTr("Refresh layout presets")
            enabled: root.controller && !root.controller.busy
            onClicked: root.controller.refresh()
        }
    }

    Label {
        visible: root.controller && presetRepeater.count === 0
        width: parent.width
        leftPadding: 12
        rightPadding: 12
        topPadding: 6
        bottomPadding: 8
        text: qsTr("No saved layouts yet")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        wrapMode: Text.WordWrap
    }

    Repeater {
        id: presetRepeater
        model: root.controller ? root.controller.model : null
        delegate: Item {
            id: presetRow
            readonly property var actionTargets: [applyAction, replaceButton, deleteButton]
            required property string code
            required property string view
            required property string title
            required property int panelCount
            required property int assignedCount
            required property bool valid
            required property string error

            width: parent.width
            height: root.theme.compactControlHeight + 8

            Rectangle {
                anchors.fill: parent
                radius: root.theme.itemRadius
                color: root.theme.primaryText
                opacity: applyAction.pressed ? 0.12
                    : applyHover.hovered ? 0.08 : 0
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 6
                spacing: 8

                Controls.MaterialIcon {
                    name: presetRow.valid
                        ? "dashboard_customize" : "warning"
                    size: 18
                    color: presetRow.valid
                        ? root.theme.action : root.theme.error
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: presetRow.title
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: presetRow.valid
                            ? qsTr("%1 panels · %2 sidebar items")
                                .arg(presetRow.panelCount)
                                .arg(presetRow.assignedCount)
                            : qsTr("Invalid layout preset")
                        color: presetRow.valid
                            ? root.theme.secondaryText : root.theme.error
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }
                Controls.CompactIconButton {
                    id: replaceButton
                    visible: root.controller && root.controller.canManage
                    theme: root.theme
                    iconName: "save"
                    toolTip: qsTr("Replace with current layout")
                    enabled: !root.controller.busy
                    onClicked: root.controller.update(presetRow.view)
                }
                Controls.CompactIconButton {
                    id: deleteButton
                    visible: root.controller && root.controller.canManage
                    theme: root.theme
                    iconName: "delete"
                    iconColor: enabled
                        ? root.theme.error : root.theme.disabledText
                    toolTip: presetRow.assignedCount > 0
                        ? qsTr("Remove this preset from sidebar items first")
                        : qsTr("Delete layout preset")
                    enabled: !root.controller.busy
                        && presetRow.assignedCount === 0
                    onClicked: {
                        root.pendingDeleteView = presetRow.view
                        root.pendingDeleteTitle = presetRow.title
                        deleteDialog.open()
                    }
                }
            }
            Controls.PopupAction {
                id: applyAction
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.rightMargin: root.controller
                        && root.controller.canManage ? 64 : 0
                enabled: presetRow.valid && root.controller
                    && !root.controller.busy
                hoverEnabled: true
                focusPolicy: Qt.StrongFocus
                onActiveFocusChanged: {
                    if (!activeFocus || !root.viewport)
                        return
                    if (presetRow.y < root.viewport.contentY)
                        root.viewport.contentY = presetRow.y
                    else if (presetRow.y + presetRow.height > root.viewport.contentY + root.viewport.height)
                        root.viewport.contentY = presetRow.y + presetRow.height - root.viewport.height
                }
                background: null
                contentItem: null
                onClicked: {
                    root.controller.apply_preset(presetRow.view)
                    root.closeMenuRequested()
                }
                HoverHandler {
                    id: applyHover
                    cursorShape: applyAction.enabled
                        ? Qt.PointingHandCursor : Qt.ArrowCursor
                }
            }
        }
    }

    Controls.Button {
        id: savePresetButton
        objectName: "saveWorkspaceLayoutPreset"
        visible: root.controller && root.controller.canManage
        width: parent.width
        theme: root.theme
        flat: true
        icon.name: "add"
        text: qsTr("Save current layout…")
        enabled: !root.controller.busy
        onClicked: {
            root.closeMenuRequested()
            saveDialog.open()
            presetName.forceActiveFocus()
        }
    }

    Label {
        visible: root.controller && root.controller.error.length > 0
        width: parent.width
        leftPadding: 12
        rightPadding: 12
        topPadding: 4
        bottomPadding: 6
        text: root.controller ? root.controller.error : ""
        color: root.theme.error
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.caption
        wrapMode: Text.WordWrap
    }

    Controls.Dialog {
        id: saveDialog
        parent: Overlay.overlay
        theme: root.theme
        title: qsTr("Save workspace layout")
        modal: true
        anchors.centerIn: parent
        width: 400
        onAccepted: {
            root.controller.save_as(presetName.text)
            presetName.clear()
        }
        contentItem: Controls.TextField {
            id: presetName
            width: 352
            theme: root.theme
            placeholderText: qsTr("Layout preset name")
            Accessible.name: qsTr("Layout preset name")
            Keys.onReturnPressed: {
                if (text.trim().length > 0)
                    saveDialog.accept()
            }
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Save")
                highlighted: true
                enabled: presetName.text.trim().length > 0
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

    Controls.Dialog {
        id: deleteDialog
        parent: Overlay.overlay
        theme: root.theme
        title: qsTr("Delete layout preset?")
        modal: true
        anchors.centerIn: parent
        width: 420
        onAccepted: root.controller.delete_preset(
            root.pendingDeleteView
        )
        contentItem: Label {
            width: 372
            text: qsTr("The server layout preset “%1” will be deleted.")
                .arg(root.pendingDeleteTitle)
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                destructive: true
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
