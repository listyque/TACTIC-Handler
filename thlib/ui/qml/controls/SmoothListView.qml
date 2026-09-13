import QtQuick

ListView {
    id: root

    required property var theme
    property real wheelStep: 148
    property int wheelAnimationDuration: theme.scrollMotion
    property real wheelTargetY: contentY
    property bool bottomAnchored: false
    property bool _bottomAnchorUpdateQueued: false
    property real _bottomAnchorAppliedMargin: 0
    readonly property bool interactionMoving:
        moving || flicking || wheelScroll.running
    readonly property real minimumContentY: originY - topMargin
    readonly property real maximumContentY: Math.max(
        minimumContentY,
        originY + contentHeight + bottomMargin - height
    )

    signal wheelScrollRequested(real delta)

    boundsBehavior: Flickable.StopAtBounds
    flickDeceleration: 3600
    maximumFlickVelocity: 4800
    pixelAligned: false
    reuseItems: true

    function scheduleBottomAnchorUpdate() {
        if (!bottomAnchored || _bottomAnchorUpdateQueued)
            return
        _bottomAnchorUpdateQueued = true
        Qt.callLater(function() {
            root._bottomAnchorUpdateQueued = false
            if (!root.bottomAnchored)
                return
            const keepAtEnd = root.atYEnd
                || root.count <= 1
                || root.contentHeight <= root.height
            const margin = Math.max(0, root.height - root.contentHeight)
            if (Math.abs(root.topMargin - margin) > 0.5) {
                root.topMargin = margin
                root._bottomAnchorAppliedMargin = margin
                root.forceLayout()
            }
            if (keepAtEnd && root.count > 0)
                root.positionViewAtEnd()
            root.wheelTargetY = root.contentY
        })
    }

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
        // Intent must precede even a zero-duration move or a wheel at the end.
        wheelScrollRequested(delta)
        const minimumY = minimumContentY
        const maximumY = maximumContentY
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
    onHeightChanged: scheduleBottomAnchorUpdate()
    onContentHeightChanged: scheduleBottomAnchorUpdate()
    onBottomAnchoredChanged: {
        if (bottomAnchored) {
            scheduleBottomAnchorUpdate()
        } else if (_bottomAnchorAppliedMargin > 0) {
            topMargin = 0
            _bottomAnchorAppliedMargin = 0
            wheelTargetY = contentY
        }
    }
    Component.onCompleted: scheduleBottomAnchorUpdate()
}
