import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls
Item {
    id: root
    required property var theme
    property bool sessionStarted: false

    function startCapture() {
        if (sessionStarted)
            return
        sessionStarted = true
        const hostWindow = root.Window.window
        const returnWindow = hostWindow ? hostWindow.transientParent : null
        const controller = screenshotController
        const windows = windowModel
        if (hostWindow && hostWindow.screen)
            captureWindow.screen = hostWindow.screen
        if (hostWindow)
            hostWindow.hide()
        Qt.callLater(function() {
            controller.begin_capture(returnWindow)
            if (!controller.selecting)
                windows.close_window("screenshot_maker")
        })
    }

    Component.onCompleted: Qt.callLater(root.startCapture)
    onVisibleChanged: if (visible)
        Qt.callLater(root.startCapture)

    Window {
        id: captureWindow
        transientParent: null
        visible: screenshotController.selecting
        x: Screen.virtualX
        y: Screen.virtualY
        width: Screen.width
        height: Screen.height
        color: "transparent"
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        title: qsTr("Screenshot Maker")

        function resetSelection() {
            selection.ready = false
            selection.x = 0
            selection.y = 0
            selection.width = 0
            selection.height = 0
        }

        onVisibleChanged: {
            if (visible) {
                resetSelection()
                requestActivate()
            } else if (root.sessionStarted) {
                if (screenshotController.busy)
                    screenshotController.finish_capture()
                if (!screenshotController.selecting
                        && !screenshotController.busy) {
                    root.sessionStarted = false
                    windowModel.close_window("screenshot_maker")
                }
            }
        }
        onClosing: function(close) {
            close.accepted = false
            screenshotController.cancel_capture()
        }

        Rectangle {
            anchors.fill: parent
            color: root.theme.blackMix
            opacity: 0.08
        }

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 18
            width: instruction.implicitWidth + 28
            height: 38
            radius: 19
            color: root.theme.surfaceContainerHigh
            border.width: 1
            border.color: root.theme.outlineVariant
            z: 4

            Label {
                id: instruction
                anchors.centerIn: parent
                text: selection.ready
                    ? qsTr("Move or resize the area, then capture")
                    : qsTr("Drag over the area to capture")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
            }
        }

        MouseArea {
            id: drawArea
            objectName: "screenshotDrawArea"
            anchors.fill: parent
            enabled: !selection.ready
            cursorShape: Qt.CrossCursor
            property point origin: Qt.point(0, 0)

            onPressed: mouse => {
                origin = Qt.point(mouse.x, mouse.y)
                selection.x = mouse.x
                selection.y = mouse.y
                selection.width = 1
                selection.height = 1
            }
            onPositionChanged: mouse => {
                if (!pressed)
                    return
                selection.x = Math.min(origin.x, mouse.x)
                selection.y = Math.min(origin.y, mouse.y)
                selection.width = Math.abs(mouse.x - origin.x)
                selection.height = Math.abs(mouse.y - origin.y)
            }
            onReleased: {
                if (selection.width < 32 || selection.height < 32) {
                    selection.width = Math.min(128, captureWindow.width)
                    selection.height = Math.min(128, captureWindow.height)
                    selection.x = Math.max(0, Math.min(
                        origin.x - selection.width / 2,
                        captureWindow.width - selection.width
                    ))
                    selection.y = Math.max(0, Math.min(
                        origin.y - selection.height / 2,
                        captureWindow.height - selection.height
                    ))
                }
                selection.ready = true
            }
        }

        Rectangle {
            id: selection
            objectName: "screenshotSelection"
            property bool ready: false
            visible: width > 1 && height > 1
            color: Qt.rgba(
                root.theme.action.r,
                root.theme.action.g,
                root.theme.action.b,
                0.08
            )
            border.width: 2
            border.color: root.theme.action
            radius: root.theme.itemRadius
            z: 2

            MouseArea {
                anchors.fill: parent
                enabled: selection.ready
                cursorShape: Qt.SizeAllCursor
                drag.target: selection
                drag.minimumX: 0
                drag.minimumY: 0
                drag.maximumX: captureWindow.width - selection.width
                drag.maximumY: captureWindow.height - selection.height
            }

            Rectangle {
                id: resizeHandle
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                width: 24
                height: 24
                radius: 8
                color: root.theme.action
                visible: selection.ready
                property real startWidth: 0
                property real startHeight: 0

                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    name: "open_in_full"
                    size: 13
                    color: root.theme.selectedText
                }
                DragHandler {
                    target: null
                    onActiveChanged: {
                        if (active) {
                            resizeHandle.startWidth = selection.width
                            resizeHandle.startHeight = selection.height
                        }
                    }
                    onTranslationChanged: {
                        selection.width = Math.max(32, Math.min(
                            captureWindow.width - selection.x,
                            resizeHandle.startWidth + translation.x
                        ))
                        selection.height = Math.max(32, Math.min(
                            captureWindow.height - selection.y,
                            resizeHandle.startHeight + translation.y
                        ))
                    }
                }
            }

            RowLayout {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.rightMargin: 32
                anchors.bottomMargin: 8
                spacing: 6
                visible: selection.ready

                Controls.Button {
                    objectName: "screenshotCaptureButton"
                    theme: root.theme
                    text: qsTr("Draw again")
                    icon.name: "refresh"
                    flat: true
                    onClicked: captureWindow.resetSelection()
                }
                Controls.Button {
                    theme: root.theme
                    text: screenshotController.busy
                        ? qsTr("Capturing…") : qsTr("Capture")
                    icon.name: "photo_camera"
                    highlighted: true
                    enabled: !screenshotController.busy
                    onClicked: screenshotController.capture(
                        Math.round(captureWindow.x + selection.x),
                        Math.round(captureWindow.y + selection.y),
                        Math.round(selection.width),
                        Math.round(selection.height)
                    )
                }
            }
        }

        Controls.CompactIconButton {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: 18
            theme: root.theme
            iconName: "close"
            toolTip: qsTr("Cancel screenshot")
            onClicked: screenshotController.cancel_capture()
            z: 5
        }

        Shortcut {
            sequences: [StandardKey.Cancel]
            onActivated: screenshotController.cancel_capture()
        }
    }
}
