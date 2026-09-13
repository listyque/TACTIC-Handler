import QtQuick
import Qt5Compat.GraphicalEffects

Item {
    id: root
    required property var theme
    required property color color
    property real originX: width / 2
    property real originY: height / 2
    property real diameter: Math.max(width, height) * 2.2
    property real shapeRadius: 0
    property bool rendering: false
    property int animationGeneration: 0
    anchors.fill: parent
    clip: true
    z: 90

    function burst(x, y) {
        if (!visible || !theme.clickAnimationsEnabled) {
            cancel()
            return
        }
        animationGeneration += 1
        originX = x
        originY = y
        if (visualLoader.item) {
            visualLoader.item.burst(animationGeneration)
            return
        }
        rendering = true
    }

    function cancel() {
        animationGeneration += 1
        if (visualLoader.item) {
            visualLoader.item.cancel(animationGeneration)
            return
        }
        rendering = false
    }

    function releaseAfterAnimation(generation) {
        // Loader destruction from an animation callback tears down the active
        // animation graph while QUnifiedTimer is still stopping its driver.
        // Release it on the next event-loop turn, after the stop completed.
        Qt.callLater(function() {
            if (root.animationGeneration !== generation)
                return
            root.rendering = false
        })
    }

    Connections {
        target: root.theme

        function onClickAnimationsEnabledChanged() {
            if (root.theme.clickAnimationsEnabled)
                return
            root.cancel()
        }
    }

    Loader {
        id: visualLoader
        objectName: "materialRippleVisualLoader"
        anchors.fill: parent
        active: root.rendering
        sourceComponent: rippleVisualComponent
        onLoaded: item.burst(root.animationGeneration)
    }

    Component {
        id: rippleVisualComponent

        Item {
            id: visual
            property int generation: 0
            anchors.fill: parent
            visible: ripple.opacity > 0
            layer.enabled: visible && root.shapeRadius > 0
            layer.effect: OpacityMask {
                maskSource: Rectangle {
                    width: visual.width
                    height: visual.height
                    radius: root.shapeRadius
                }
            }

            function burst(nextGeneration) {
                rippleAnimation.stop()
                generation = nextGeneration
                ripple.scale = 0.05
                ripple.opacity = 0.42
                rippleAnimation.start()
            }

            function cancel(nextGeneration) {
                rippleAnimation.stop()
                generation = nextGeneration
                ripple.opacity = 0
                root.releaseAfterAnimation(generation)
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
                onStopped: root.releaseAfterAnimation(visual.generation)

                NumberAnimation {
                    target: ripple
                    property: "scale"
                    from: 0.05
                    to: 1
                    duration: root.theme.clickMotionExtended
                        + root.theme.clickMotionFast
                    easing.type: Easing.OutCubic
                }
                SequentialAnimation {
                    PauseAnimation {
                        duration: root.theme.clickMotionInstant
                    }
                    NumberAnimation {
                        target: ripple
                        property: "opacity"
                        to: 0
                        duration: root.theme.clickMotionExtended
                        easing.type: Easing.OutQuad
                    }
                }
            }
        }
    }
}
