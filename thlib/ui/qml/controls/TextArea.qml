import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Templates as T
import "." as Controls

Basic.TextArea {
    id: control

    required property var theme
    property bool errorState: false
    property bool emphasizedOutline: false
    property color idleOutlineColor: theme.outline
    property color activeOutlineColor: theme.action

    // The Basic style installs its own TextEditingContextMenu. This control
    // provides the shared themed menu below, so the style menu must stay disabled.
    T.ContextMenu.menu: null

    leftPadding: Foundation.controls.field.padding
    rightPadding: Foundation.controls.field.padding
    topPadding: Foundation.controls.field.areaPadding
    bottomPadding: Foundation.controls.field.areaPadding
    selectByMouse: true
    persistentSelection: true
    wrapMode: TextEdit.Wrap
    color: enabled ? theme.primaryText : theme.disabledText
    placeholderTextColor: theme.secondaryText
    selectionColor: theme.action
    selectedTextColor: theme.selectedText
    font: Qt.font({
        family: theme.fontFamily,
        hintingPreference: Font.PreferVerticalHinting,
        pixelSize: Foundation.textStyles.body
    })

    background: Rectangle {
        radius: theme.surfaceRadius
        color: theme.surfaceContainerHigh
        border.width: control.activeFocus || control.emphasizedOutline ? 2 : 1
        border.color: control.errorState ? theme.error : control.activeFocus || control.emphasizedOutline ? control.activeOutlineColor : control.idleOutlineColor

        Behavior on border.color {
            ColorAnimation {
                duration: theme.motionFast
            }
        }
    }

    MouseArea {
        objectName: "textAreaCursorArea"
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        hoverEnabled: true
        cursorShape: control.enabled ? Qt.IBeamCursor : Qt.ArrowCursor
        onPressed: mouse => {
            contextMenu.openForEditor(control, mouse.x, mouse.y, control.positionAt(mouse.x, mouse.y));
        }
    }

    Controls.TextContextMenu {
        id: contextMenu
        theme: control.theme
        editor: control
        readOnly: control.readOnly
    }
}
