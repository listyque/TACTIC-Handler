import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import Qt5Compat.GraphicalEffects
import "." as Controls

Loader {
    id: root

    required property var theme
    property string text: ""
    property int delay: 500
    property int timeout: 5000
    property int margins: 8

    visible: false
    active: visible
    onLoaded: Qt.callLater(function() {
        if (root.visible && root.item)
            root.item.visible = true
    })
    sourceComponent: QtControls.ToolTip {
        id: control

        visible: false
        text: root.text
        delay: root.delay
        timeout: root.timeout
        margins: root.margins
        padding: 0

        enter: Transition {
            enabled: root.theme.popupAnimationsEnabled
            NumberAnimation {
                property: "opacity"; from: 0; to: 1
                duration: root.theme.popupMotionFast
                easing.type: Easing.OutQuad
            }
        }
        exit: Transition {
            enabled: root.theme.popupAnimationsEnabled
            NumberAnimation {
                property: "opacity"; from: 1; to: 0
                duration: root.theme.popupMotionFast
                easing.type: Easing.InQuad
            }
        }

        contentItem: Label {
            leftPadding: 12
            rightPadding: 12
            topPadding: 7
            bottomPadding: 7
            text: control.text
            color: root.theme.tooltipSurface
            font.family: root.theme.fontFamily
            font.pointSize: Typography.body
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
                color: root.theme.popupShadow
                transparentBorder: true
            }
            Rectangle {
                id: tooltipSurface
                anchors.fill: parent
                radius: Math.min(6, root.theme.itemRadius)
                color: root.theme.tooltipText
            }
        }
    }
}
