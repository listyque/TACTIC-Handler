import "../tactic_frame/core/foundation.mjs" as Foundation
import "../tactic_frame/core/interaction.mjs" as Interaction
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Templates as T
import "." as Controls

Basic.TextField {
    id: control

    required property var theme
    property bool errorState: false
    property bool tableCell: false
    property var contextMenu: null
    readonly property var paint: Interaction.fieldVisual({
        enabled: enabled,
        focused: activeFocus,
        error: errorState,
        tableCell: tableCell
    })

    // The Basic style installs its own TextEditingContextMenu. This control
    // provides the shared themed menu below, so the style menu must stay disabled.
    T.ContextMenu.menu: null

    implicitHeight: theme.controlHeight
    leftPadding: tableCell ? 8 : Foundation.controls.field.padding
    rightPadding: tableCell ? 8 : Foundation.controls.field.padding
    passwordCharacter: "\u2022"
    selectByMouse: true
    persistentSelection: true
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
        radius: control.tableCell ? 0 : theme.fieldRadius
        color: control.paint.background === "transparent" ? "transparent" : theme[control.paint.background]
        border.width: control.paint.borderWidth
        border.color: theme[control.paint.border]

        Behavior on border.color {
            ColorAnimation {
                duration: theme.motionFast
            }
        }
    }

    MouseArea {
        id: textCursorArea
        objectName: "textFieldCursorArea"
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        hoverEnabled: true
        cursorShape: control.enabled ? Qt.IBeamCursor : Qt.ArrowCursor
        onPressed: mouse => {
            if (!control.contextMenu)
                control.contextMenu = contextMenuComponent.createObject(control);
            control.contextMenu.openForEditor(control, mouse.x, mouse.y, control.positionAt(mouse.x));
        }
    }

    Component {
        id: contextMenuComponent
        Controls.TextContextMenu {
            theme: control.theme
            editor: control
            readOnly: control.readOnly
            allowCopy: control.echoMode === TextInput.Normal
        }
    }
}
