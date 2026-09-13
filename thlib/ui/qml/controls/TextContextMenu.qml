import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Controls.Popup {
    id: root

    property var editor: null
    property bool readOnly: false
    property bool allowCopy: true
    property string pendingCommand: ""
    property int focusedActionIndex: -1

    width: 166 + 2 * effectiveShadowMargin
    padding: 5
    usePopupWindow: true
    modal: true
    dim: false
    focus: true
    settledClosePolicy: Controls.Popup.CloseOnEscape
        | Controls.Popup.CloseOnPressOutside
    readonly property real calculatedContentHeight: {
        let total = 0
        for (let index = 0; index < actions.length; ++index) {
            if (index > 0)
                total += 1
            total += actions[index].separator ? 7 : 32
        }
        return total
    }
    implicitHeight: calculatedContentHeight + topPadding + bottomPadding
    onClosed: flushPendingCommand()
    onOpened: Qt.callLater(root.focusFirstAction)

    readonly property var actions: readOnly ? [
        {"title": "Copy", "icon": "content_copy", "command": "copy",
         "enabled": allowCopy},
        {"separator": true},
        {"title": "Select all", "icon": "select_all", "command": "select_all"}
    ] : [
        {"title": "Cut", "icon": "content_cut", "command": "cut",
         "enabled": allowCopy},
        {"title": "Copy", "icon": "content_copy", "command": "copy",
         "enabled": allowCopy},
        {"title": "Paste", "icon": "content_paste", "command": "paste"},
        {"separator": true},
        {"title": "Select all", "icon": "select_all", "command": "select_all"}
    ]

    function openAt(sourceItem, localX, localY) {
        if (!sourceItem || !root.parent)
            return
        if (root.usePopupWindow) {
            root.reopenAtItem(sourceItem, localX, localY, true)
            return
        }
        const point = sourceItem.mapToItem(root.parent, localX, localY)
        root.x = Math.max(
                4,
                Math.min(root.parent.width - root.width - 4, point.x)
            )
        root.y = Math.max(
                4,
                Math.min(root.parent.height - root.height - 4, point.y)
            )
        root.open()
    }

    function openForEditor(sourceItem, localX, localY, characterPosition) {
        if (!editor)
            return
        const selectionFrom = Math.min(
            editor.selectionStart, editor.selectionEnd)
        const selectionTo = Math.max(
            editor.selectionStart, editor.selectionEnd)
        const hasSelection = selectionFrom !== selectionTo
        const clickedSelection = hasSelection
            && characterPosition >= selectionFrom
            && characterPosition <= selectionTo
        if (!clickedSelection)
            editor.cursorPosition = characterPosition
        openAt(sourceItem, localX, localY)
    }

    function trigger(command) {
        if (!editor)
            return
        pendingCommand = command
        Qt.callLater(function() {
            if (root.opened)
                root.close()
            else
                root.flushPendingCommand()
        })
    }

    function flushPendingCommand() {
        const command = pendingCommand
        pendingCommand = ""
        if (!editor || !command)
            return
        Qt.callLater(function() {
            if (command === "cut")
                editor.cut()
            else if (command === "copy")
                editor.copy()
            else if (command === "paste")
                editor.paste()
            else if (command === "select_all")
                editor.selectAll()
        })
    }

    function focusFirstAction() {
        focusedActionIndex = -1
        for (let index = 0; index < actionRepeater.count; ++index) {
            const row = actionRepeater.itemAt(index)
            if (row && row.actionTarget && row.actionTarget.enabled) {
                focusedActionIndex = index
                row.actionTarget.forceActiveFocus(Qt.PopupFocusReason)
                return
            }
        }
    }

    function focusRelativeAction(step) {
        if (actionRepeater.count <= 0)
            return
        let index = focusedActionIndex
        for (let offset = 0; offset < actionRepeater.count; ++offset) {
            index = (index + step + actionRepeater.count)
                % actionRepeater.count
            const row = actionRepeater.itemAt(index)
            if (row && row.actionTarget && row.actionTarget.enabled) {
                focusedActionIndex = index
                row.actionTarget.forceActiveFocus(Qt.TabFocusReason)
                return
            }
        }
    }

    function activateFocusedAction() {
        const row = actionRepeater.itemAt(focusedActionIndex)
        if (row && row.actionTarget && row.actionTarget.enabled)
            Qt.callLater(row.actionTarget.click)
    }

    Shortcut {
        sequence: "Down"
        context: Qt.WindowShortcut
        enabled: root.visible
        onActivated: root.focusRelativeAction(1)
    }
    Shortcut {
        sequence: "Up"
        context: Qt.WindowShortcut
        enabled: root.visible
        onActivated: root.focusRelativeAction(-1)
    }
    Shortcut {
        sequence: "Space"
        context: Qt.WindowShortcut
        enabled: root.visible && root.focusedActionIndex >= 0
        onActivated: root.activateFocusedAction()
    }
    Shortcut {
        sequence: "Return"
        context: Qt.WindowShortcut
        enabled: root.visible && root.focusedActionIndex >= 0
        onActivated: root.activateFocusedAction()
    }
    Shortcut {
        sequence: "Enter"
        context: Qt.WindowShortcut
        enabled: root.visible && root.focusedActionIndex >= 0
        onActivated: root.activateFocusedAction()
    }
    Shortcut {
        sequence: "Esc"
        context: Qt.WindowShortcut
        enabled: root.visible
        onActivated: root.close()
    }

    contentItem: Column {
        id: actionsColumn
        width: root.availableWidth
        spacing: 1

        Repeater {
            id: actionRepeater
            model: root.actions
            delegate: Item {
                id: actionRow
                required property var modelData
                required property int index
                readonly property alias actionTarget: actionActivation
                width: actionsColumn.width
                height: modelData.separator ? 7 : 32

                Rectangle {
                    visible: !!actionRow.modelData.separator
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width
                    height: 1
                    color: root.theme.separator
                }
                Rectangle {
                    visible: !actionRow.modelData.separator
                    anchors.fill: parent
                    radius: root.theme.itemRadius
                    color: root.theme.primaryText
                    opacity: actionActivation.pressed ? 0.12
                        : actionActivation.activeFocus ? 0.10
                        : actionHover.hovered ? 0.08 : 0
                }
                RowLayout {
                    visible: !actionRow.modelData.separator
                    anchors.fill: parent
                    anchors.leftMargin: 9
                    anchors.rightMargin: 8
                    spacing: 8
                    Controls.MaterialIcon {
                        name: actionRow.modelData.icon || "info"
                        size: 16
                        color: actionRow.modelData.enabled === false
                            ? root.theme.disabledText : root.theme.secondaryText
                    }
                    Label {
                        Layout.fillWidth: true
                        text: actionRow.modelData.title || ""
                        color: actionRow.modelData.enabled === false
                            ? root.theme.disabledText : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.bodyLarge
                    }
                }
                Controls.PopupAction {
                    id: actionActivation
                    anchors.fill: parent
                    enabled: !actionRow.modelData.separator
                        && actionRow.modelData.enabled !== false
                    hoverEnabled: true
                    focusPolicy: Qt.StrongFocus
                    background: null
                    contentItem: null
                    onActiveFocusChanged: {
                        if (activeFocus)
                            root.focusedActionIndex = actionRow.index
                    }
                    onClicked: root.trigger(actionRow.modelData.command)
                    HoverHandler {
                        id: actionHover
                        enabled: actionActivation.enabled
                        cursorShape: Qt.PointingHandCursor
                    }
                }
            }
        }
    }
}
