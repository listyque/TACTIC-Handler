import QtQuick

Item {
    id: root

    property int duplicateWindow: 180
    property double lastActivationAt: -1000
    property bool lastActivationWasTouch: false
    property int cursorShape: Qt.PointingHandCursor
    readonly property bool pressed: pointerTap.pressed || touchTap.pressed
    readonly property var point: touchTap.pressed ? touchTap.point : pointerTap.point
    signal activated(int modifiers, real x, real y)

    anchors.fill: parent

    function activate(handler, eventPoint) {
        const now = Date.now()
        if (now - root.lastActivationAt < root.duplicateWindow)
            return
        root.lastActivationAt = now
        root.lastActivationWasTouch = handler === touchTap
        root.activated(
            handler.point.modifiers,
            eventPoint.position.x,
            eventPoint.position.y
        )
    }

    TapHandler {
        id: pointerTap
        acceptedDevices: PointerDevice.Mouse
            | PointerDevice.TouchPad
            | PointerDevice.Stylus
        acceptedButtons: Qt.LeftButton
        gesturePolicy: TapHandler.DragThreshold
        cursorShape: root.cursorShape
        onTapped: eventPoint => root.activate(pointerTap, eventPoint)
    }

    TapHandler {
        id: touchTap
        acceptedDevices: PointerDevice.TouchScreen
        // A touchscreen tap is represented as a left-button activation by
        // Qt. Device filtering keeps the authentic touch path separate from
        // the mouse handler; NoButton rejects taps on some Windows devices.
        acceptedButtons: Qt.LeftButton
        gesturePolicy: TapHandler.DragThreshold
        onTapped: eventPoint => root.activate(touchTap, eventPoint)
    }
}
