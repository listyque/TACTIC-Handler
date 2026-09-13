import QtQuick
import "." as Controls

TextEdit {
    id: root

    required property var theme
    property bool richText: false
    property var contextMenu: null

    function openContextMenu(localX, localY) {
        if (!contextMenu) {
            contextMenu = contextMenuComponent.createObject(root, {
                "theme": root.theme,
                "editor": root,
                "readOnly": true
            })
        }
        if (contextMenu) {
            contextMenu.openForEditor(
                root,
                localX,
                localY,
                root.positionAt(localX, localY)
            )
        }
    }

    textFormat: richText ? TextEdit.RichText : TextEdit.PlainText
    color: theme.primaryText
    selectionColor: theme.action
    selectedTextColor: theme.selectedText
    font.family: theme.fontFamily
    font.pointSize: Controls.Typography.body
    wrapMode: TextEdit.Wrap
    readOnly: true
    selectByMouse: true
    persistentSelection: true
    activeFocusOnTab: true
    padding: 0

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        cursorShape: root.hoveredLink.length
            ? Qt.PointingHandCursor : Qt.IBeamCursor
        onPressed: mouse => root.openContextMenu(mouse.x, mouse.y)
    }

    Component {
        id: contextMenuComponent

        Controls.TextContextMenu {
            objectName: "selectableTextContextMenu"
            onClosed: {
                const closedMenu = root.contextMenu
                root.contextMenu = null
                if (closedMenu)
                    closedMenu.destroy()
            }
        }
    }

    Component.onDestruction: if (contextMenu) contextMenu.destroy()
}
