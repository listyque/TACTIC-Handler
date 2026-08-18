import QtQuick
import QtQuick.Controls.Basic as Basic

Basic.TabButton {
    id: control

    required property var theme
    property bool indicatorVisible: true
    implicitHeight: 48
    implicitWidth: Math.max(112, visual.labelImplicitWidth + 34)
    padding: 0

    contentItem: WorkspaceTabVisual {
        id: visual
        theme: control.theme
        title: control.text
        current: control.checked
        hovered: control.hovered
        pressed: control.down
        indicatorVisible: control.indicatorVisible
    }

    background: Item {}

    onPressedChanged: {
        if (pressed)
            visual.burst(width / 2, height / 2)
    }

    HoverHandler {
        cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}
