import QtQuick
import QtQuick.Shapes
import Qt5Compat.GraphicalEffects

Item {
    required property var popup
    Item {
        id: surfaceSource
        anchors.fill: parent

        Shape {
            id: anchorPointer
            objectName: "popupAnchorPointer"
            visible: popup.anchorPointerVisible
            width: popup.anchorPointerWidth
            height: popup.anchorPointerHeight
            x: popup.anchorPointerCenter - width / 2
            y: popup.anchorPointerEdge === "top"
                ? popup.effectiveShadowMargin
                : popup.height - popup.effectiveShadowMargin - height
            antialiasing: true
            ShapePath {
                fillColor: popup.surfaceColor
                strokeColor: "transparent"
                strokeWidth: 0
                startX: 0
                startY: popup.anchorPointerEdge === "top"
                    ? anchorPointer.height : 0
                PathLine {
                    x: anchorPointer.width / 2
                    y: popup.anchorPointerEdge === "top"
                        ? 0 : anchorPointer.height
                }
                PathLine {
                    x: anchorPointer.width
                    y: popup.anchorPointerEdge === "top"
                        ? anchorPointer.height : 0
                }
                PathLine {
                    x: 0
                    y: popup.anchorPointerEdge === "top"
                        ? anchorPointer.height : 0
                }
            }
            ShapePath {
                fillColor: "transparent"
                strokeColor: popup.surfaceBorderColor
                strokeWidth: popup.surfaceBorderWidth
                capStyle: ShapePath.RoundCap
                joinStyle: ShapePath.RoundJoin
                startX: 0
                startY: popup.anchorPointerEdge === "top"
                    ? anchorPointer.height : 0
                PathLine {
                    x: anchorPointer.width / 2
                    y: popup.anchorPointerEdge === "top"
                        ? 0 : anchorPointer.height
                }
                PathLine {
                    x: anchorPointer.width
                    y: popup.anchorPointerEdge === "top"
                        ? anchorPointer.height : 0
                }
            }
        }
        Rectangle {
            id: surface
            objectName: "popupSurface"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.leftMargin: popup.effectiveShadowMargin
            anchors.rightMargin: popup.effectiveShadowMargin
            anchors.topMargin: popup.effectiveShadowMargin
                + (popup.anchorPointerVisible
                    && popup.anchorPointerEdge === "top"
                    ? popup.anchorPointerInset : 0)
            anchors.bottomMargin: popup.effectiveShadowMargin
                + (popup.anchorPointerVisible
                    && popup.anchorPointerEdge === "bottom"
                    ? popup.anchorPointerInset : 0)
            radius: popup.surfaceRadius
            color: popup.surfaceColor
            border.width: popup.surfaceBorderWidth
            border.color: popup.surfaceBorderColor
        }
        Rectangle {
            visible: popup.anchorPointerVisible
            width: Math.max(
                0,
                popup.anchorPointerWidth
                    - 2 * popup.surfaceBorderWidth
            )
            height: popup.surfaceBorderWidth + 1
            x: popup.anchorPointerCenter - width / 2
            y: popup.anchorPointerEdge === "top"
                ? popup.effectiveShadowMargin
                    + popup.anchorPointerInset
                    - popup.surfaceBorderWidth / 2
                : popup.height - popup.effectiveShadowMargin
                    - popup.anchorPointerInset
                    - popup.surfaceBorderWidth / 2
            color: popup.surfaceColor
        }
    }
    Loader {
        anchors.fill: parent
        active: popup.visible
        sourceComponent: DropShadow {
            anchors.fill: parent
            source: surfaceSource
            horizontalOffset: 0
            verticalOffset: 4
            radius: 10
            samples: 21
            color: popup.theme.popupShadow
            transparentBorder: true
        }
    }
}
