import QtQuick

ListView {
    id: root

    property real wheelStep: 148
    property int wheelAnimationDuration: 115
    property real wheelTargetY: contentY
    readonly property bool interactionMoving:
        moving || flicking || wheelScroll.running

    boundsBehavior: Flickable.StopAtBounds
    flickDeceleration: 3600
    maximumFlickVelocity: 4800
    pixelAligned: false
    reuseItems: true

    function cancelWheelScroll() {
        wheelScroll.stop()
        wheelTargetY = contentY
    }

    function scrollWithWheel(pixelDelta, angleDelta) {
        const delta = pixelDelta !== 0
            ? pixelDelta * 1.65
            : (angleDelta / 120) * wheelStep
        if (delta === 0)
            return
        const minimumY = originY
        const maximumY = Math.max(
            minimumY,
            minimumY + contentHeight - height
        )
        const baseY = wheelScroll.running ? wheelTargetY : contentY
        wheelTargetY = Math.max(
            minimumY,
            Math.min(maximumY, baseY - delta)
        )
        wheelScroll.stop()
        wheelScroll.to = wheelTargetY
        wheelScroll.start()
    }

    NumberAnimation {
        id: wheelScroll
        target: root
        property: "contentY"
        duration: root.wheelAnimationDuration
        easing.type: Easing.OutCubic
    }

    WheelHandler {
        target: null
        blocking: true
        onWheel: function(event) {
            root.scrollWithWheel(
                event.pixelDelta.y,
                event.angleDelta.y
            )
            event.accepted = true
        }
    }

    onFlickStarted: cancelWheelScroll()
}
