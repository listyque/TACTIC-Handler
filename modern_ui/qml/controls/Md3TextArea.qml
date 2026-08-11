import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Templates as T

Basic.TextArea {
    id: control

    required property var theme
    property bool errorState: false
    property bool emphasizedOutline: false
    property color idleOutlineColor: theme.outline
    property color activeOutlineColor: theme.action

    // The Basic style installs its own TextEditingContextMenu. This control
    // provides the shared MD3 menu below, so the style menu must stay disabled.
    T.ContextMenu.menu: null

    leftPadding: 12
    rightPadding: 12
    topPadding: 10
    bottomPadding: 10
    selectByMouse: true
    wrapMode: TextEdit.Wrap
    color: enabled ? theme.primaryText : theme.disabledText
    placeholderTextColor: theme.secondaryText
    selectionColor: theme.action
    selectedTextColor: theme.selectedText
    font.family: theme.fontFamily
    font.pixelSize: 10

    background: Rectangle {
        radius: theme.surfaceRadius
        color: theme.surfaceContainerHigh
        border.width: control.activeFocus || control.emphasizedOutline ? 2 : 1
        border.color: control.errorState
            ? theme.error
            : control.activeFocus || control.emphasizedOutline
                ? control.activeOutlineColor : control.idleOutlineColor

        Behavior on border.color {
            ColorAnimation { duration: theme.motionFast }
        }
    }

    MouseArea {
        objectName: "md3TextAreaCursorArea"
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        hoverEnabled: true
        cursorShape: control.enabled
            ? Qt.IBeamCursor : Qt.ArrowCursor
        onPressed: mouse => {
            control.cursorPosition = control.positionAt(mouse.x, mouse.y)
            contextMenu.openAt(control, mouse.x, mouse.y)
        }
    }

    Md3TextContextMenu {
        id: contextMenu
        theme: control.theme
        editor: control
        readOnly: control.readOnly
    }
}
