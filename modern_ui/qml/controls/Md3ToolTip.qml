import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

ToolTip {
    id: control

    required property var theme

    delay: 500
    timeout: 5000
    margins: 8
    padding: 0

    contentItem: Label {
        leftPadding: 12
        rightPadding: 12
        topPadding: 7
        bottomPadding: 7
        text: control.text
        color: control.theme.tooltipSurface
        font.family: control.theme.fontFamily
        font.pixelSize: 10
        lineHeight: 1.1
        wrapMode: Text.Wrap
        maximumLineCount: 5
        elide: Text.ElideRight
    }

    background: Item {
        implicitWidth: 28
        implicitHeight: 28

        DropShadow {
            anchors.fill: tooltipSurface
            source: tooltipSurface
            horizontalOffset: 0
            verticalOffset: 3
            radius: 8
            samples: 17
            color: control.theme.popupShadow
            transparentBorder: true
        }
        Rectangle {
            id: tooltipSurface
            anchors.fill: parent
            radius: Math.min(6, control.theme.itemRadius)
            color: control.theme.tooltipText
        }
    }
}
