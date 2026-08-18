import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Md3Popup {
    id: root

    property var editor: null
    property bool readOnly: false
    property bool allowCopy: true

    width: 166
    padding: 5
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnReleaseOutside
    implicitHeight: actionsColumn.implicitHeight + topPadding + bottomPadding

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
        const point = sourceItem.mapToItem(root.parent, localX, localY)
        root.x = Math.max(4, Math.min(root.parent.width - root.width - 4, point.x))
        root.y = Math.max(4, Math.min(root.parent.height - root.height - 4, point.y))
        root.open()
    }

    function trigger(command) {
        if (!editor)
            return
        root.close()
        if (command === "cut")
            editor.cut()
        else if (command === "copy")
            editor.copy()
        else if (command === "paste")
            editor.paste()
        else if (command === "select_all")
            editor.selectAll()
    }

    contentItem: Column {
        id: actionsColumn
        width: root.availableWidth
        spacing: 1

        Repeater {
            model: root.actions
            delegate: Item {
                id: actionRow
                required property var modelData
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
                    opacity: actionMouse.pressed ? 0.12
                        : actionMouse.containsMouse ? 0.08 : 0
                }
                RowLayout {
                    visible: !actionRow.modelData.separator
                    anchors.fill: parent
                    anchors.leftMargin: 9
                    anchors.rightMargin: 8
                    spacing: 8
                    MaterialIcon {
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
                MouseArea {
                    id: actionMouse
                    visible: !actionRow.modelData.separator
                        && actionRow.modelData.enabled !== false
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.trigger(actionRow.modelData.command)
                }
            }
        }
    }
}
