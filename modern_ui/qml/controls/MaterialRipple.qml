import QtQuick
import Qt5Compat.GraphicalEffects

Item {
    id: root
    property color color: "#30ffffff"
    property real originX: width / 2
    property real originY: height / 2
    property real diameter: Math.max(width, height) * 2.2
    property real shapeRadius: 0
    anchors.fill: parent
    clip: true
    visible: ripple.opacity > 0
    z: 90
    layer.enabled: shapeRadius > 0
    layer.effect: OpacityMask {
        maskSource: Rectangle {
            width: root.width
            height: root.height
            radius: root.shapeRadius
        }
    }

    function burst(x, y) {
        originX = x
        originY = y
        rippleAnimation.stop()
        ripple.scale = 0.05
        ripple.opacity = 0.42
        rippleAnimation.start()
    }

    Rectangle {
        id: ripple
        x: root.originX - width / 2
        y: root.originY - height / 2
        width: root.diameter
        height: width
        radius: width / 2
        color: root.color
        opacity: 0
        scale: 0.05
    }

    ParallelAnimation {
        id: rippleAnimation
        NumberAnimation {
            target: ripple
            property: "scale"
            from: 0.05
            to: 1
            duration: 420
            easing.type: Easing.OutCubic
        }
        SequentialAnimation {
            PauseAnimation { duration: 90 }
            NumberAnimation {
                target: ripple
                property: "opacity"
                to: 0
                duration: 330
                easing.type: Easing.OutQuad
            }
        }
    }
}
