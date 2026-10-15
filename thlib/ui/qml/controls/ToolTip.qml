import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import QtQuick.Window
import Qt5Compat.GraphicalEffects
import "." as Controls

Loader {
    id: root

    required property var theme
    property string text: ""
    property int delay: Foundation.controls.tooltip.delay
    property int timeout: Foundation.controls.tooltip.timeout
    property int margins: Foundation.controls.tooltip.margin

    anchors.fill: parent
    visible: false
    active: visible
    onLoaded: Qt.callLater(function () {
        if (root.visible && root.item)
            root.item.visible = true;
    })
    sourceComponent: QtControls.ToolTip {
        id: control

        readonly property point anchorOrigin: root.mapToItem(null, 0, 0)

        parent: root
        x: Math.round((root.width - width) / 2)
        y: {
            const window = root.Window.window;
            const below = anchorOrigin.y + root.height + root.margins + height;
            if (window && below > window.height - root.margins && anchorOrigin.y >= height + root.margins * 2)
                return -height - root.margins;
            return root.height + root.margins;
        }
        visible: false
        text: root.text
        delay: root.delay
        timeout: root.timeout
        margins: root.margins
        padding: 0

        enter: Transition {
            enabled: root.theme.popupAnimationsEnabled
            NumberAnimation {
                property: "opacity"
                from: 0
                to: 1
                duration: root.theme.popupMotionFast
                easing.type: Easing.OutQuad
            }
        }
        exit: Transition {
            enabled: root.theme.popupAnimationsEnabled
            NumberAnimation {
                property: "opacity"
                from: 1
                to: 0
                duration: root.theme.popupMotionFast
                easing.type: Easing.InQuad
            }
        }

        contentItem: Label {
            leftPadding: Foundation.controls.tooltip.paddingX
            rightPadding: Foundation.controls.tooltip.paddingX
            topPadding: Foundation.controls.tooltip.paddingY
            bottomPadding: Foundation.controls.tooltip.paddingY
            text: control.text
            color: root.theme.tooltipSurface
            font.family: root.theme.fontFamily
            font.pixelSize: Foundation.textStyles.body
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
