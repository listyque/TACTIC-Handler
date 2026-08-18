import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Templates as T

Basic.TextField {
    id: control

    required property var theme
    property bool errorState: false

    // The Basic style installs its own TextEditingContextMenu. This control
    // provides the shared MD3 menu below, so the style menu must stay disabled.
    T.ContextMenu.menu: null

    implicitHeight: theme.controlHeight
    leftPadding: 12
    rightPadding: 12
    selectByMouse: true
    color: enabled ? theme.primaryText : theme.disabledText
    placeholderTextColor: theme.secondaryText
    selectionColor: theme.action
    selectedTextColor: theme.selectedText
    font.family: theme.fontFamily
    font.pointSize: Typography.body

    background: Rectangle {
        radius: theme.fieldRadius
        color: theme.surfaceContainerHigh
        border.width: control.activeFocus ? 2 : 1
        border.color: control.errorState
            ? theme.error
            : control.activeFocus ? theme.action : theme.outline

        Behavior on border.color {
            ColorAnimation { duration: theme.motionFast }
        }
    }

    MouseArea {
        id: textCursorArea
        objectName: "md3TextFieldCursorArea"
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        hoverEnabled: true
        cursorShape: control.enabled
            ? Qt.IBeamCursor : Qt.ArrowCursor
        onPressed: mouse => {
            control.cursorPosition = control.positionAt(mouse.x)
            contextMenu.openAt(control, mouse.x, mouse.y)
        }
    }

    Md3TextContextMenu {
        id: contextMenu
        theme: control.theme
        editor: control
        readOnly: control.readOnly
        allowCopy: control.echoMode === TextInput.Normal
    }
}
