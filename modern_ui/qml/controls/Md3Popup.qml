import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

Popup {
    id: control

    required property var theme
    property real surfaceRadius: theme.menuRadius

    padding: 6
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnReleaseOutside

    background: Item {
        DropShadow {
            anchors.fill: surface
            source: surface
            horizontalOffset: 0
            verticalOffset: 4
            radius: 10
            samples: 21
            color: control.theme.popupShadow
            transparentBorder: true
        }
        Rectangle {
            id: surface
            anchors.fill: parent
            radius: control.surfaceRadius
            color: control.theme.surfaceContainerHigh
            border.width: 1
            border.color: control.theme.outlineVariant
        }
    }
}
