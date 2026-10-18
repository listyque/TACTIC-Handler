import QtQuick
import QtQuick.Window
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/screenshot.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property bool sessionStarted: false
    property bool ready: false
    property var region: ({
            x: 0,
            y: 0,
            width: 0,
            height: 0
        })
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language

    function startCapture() {
        if (sessionStarted)
            return;
        sessionStarted = true;
        const hostWindow = root.Window.window;
        const returnWindow = hostWindow ? hostWindow.transientParent : null;
        const controller = screenshotController;
        const windows = windowModel;
        if (hostWindow && hostWindow.screen)
            captureWindow.screen = hostWindow.screen;
        if (hostWindow)
            hostWindow.hide();
        Qt.callLater(function () {
            controller.begin_capture(returnWindow);
            if (!controller.selecting)
                windows.close_window("screenshot_maker");
        });
    }
    function resetSelection() {
        ready = false;
        region = {
            x: 0,
            y: 0,
            width: 0,
            height: 0
        };
    }
    function dispatch(action) {
        if (action.type === "redraw")
            resetSelection();
        else if (action.type === "cancel")
            screenshotController.cancel_capture();
        else if (action.type === "capture" && ready && !screenshotController.busy)
            screenshotController.capture(Math.round(captureWindow.x + region.x), Math.round(captureWindow.y + region.y), Math.round(region.width), Math.round(region.height));
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
        onVisibleChanged: {
            if (visible) {
                root.resetSelection();
                requestActivate();
                keyboardScope.forceActiveFocus();
            } else if (root.sessionStarted) {
                if (screenshotController.busy)
                    screenshotController.finish_capture();
                if (!screenshotController.selecting && !screenshotController.busy) {
                    root.sessionStarted = false;
                    windowModel.close_window("screenshot_maker");
                }
            }
        }
        onClosing: close => {
            close.accepted = false;
            screenshotController.cancel_capture();
        }
        FocusScope {
            id: keyboardScope
            anchors.fill: parent
            focus: true
            Keys.onEscapePressed: screenshotController.cancel_capture()
            MouseArea {
                id: drawArea
                objectName: "screenshotDrawArea"
                anchors.fill: parent
                enabled: !root.ready
                cursorShape: Qt.CrossCursor
                property point origin: Qt.point(0, 0)
                onPressed: mouse => {
                    origin = Qt.point(mouse.x, mouse.y);
                    root.region = {
                        x: mouse.x,
                        y: mouse.y,
                        width: 1,
                        height: 1
                    };
                }
                onPositionChanged: mouse => {
                    if (pressed)
                        root.region = UI.draw(origin, {
                            x: mouse.x,
                            y: mouse.y
                        }, width, height);
                }
                onReleased: {
                    root.region = UI.finish(root.region, origin, width, height);
                    root.ready = true;
                }
            }
            Item {
                id: selection
                objectName: "screenshotSelection"
                readonly property bool ready: root.ready
                x: root.region.x
                y: root.region.y
                width: root.region.width
                height: root.region.height
                visible: root.ready
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.SizeAllCursor
                    property point origin: Qt.point(0, 0)
                    property var initial: ({})
                    onPressed: mouse => {
                        origin = mapToItem(captureWindow.contentItem, mouse.x, mouse.y);
                        initial = root.region;
                    }
                    onPositionChanged: mouse => {
                        if (!pressed)
                            return;
                        const point = mapToItem(captureWindow.contentItem, mouse.x, mouse.y);
                        root.region = UI.move(initial, {
                            x: point.x - origin.x,
                            y: point.y - origin.y
                        }, captureWindow.width, captureWindow.height);
                    }
                }
            }
            FontMetrics {
                id: instructionMetrics
                font: Qt.font({
                    family: root.theme.fontFamily,
                    pixelSize: 14,
                    weight: Font.DemiBold
                })
            }
            FontMetrics {
                id: buttonMetrics
                font: Qt.font({
                    family: root.theme.fontFamily,
                    pixelSize: 13,
                    weight: Font.DemiBold
                })
            }
            Frame.FrameView {
                anchors.fill: parent
                theme: root.theme
                scene: UI.describe({
                    region: root.region,
                    ready: root.ready,
                    busy: screenshotController.busy,
                    instructionWidth: instructionMetrics.advanceWidth(root.ready ? qsTr("Move or resize the area, then capture") : qsTr("Drag over the area to capture")),
                    redrawWidth: buttonMetrics.advanceWidth(qsTr("Draw again")),
                    captureWidth: buttonMetrics.advanceWidth(screenshotController.busy ? qsTr("Capturing…") : qsTr("Capture"))
                }, width, height, root.language)
                views: ({
                        resize: resizePort
                    })
                onEvent: action => root.dispatch(action)
            }
            Component {
                id: resizePort
                Item {
                    HoverHandler {
                        cursorShape: Qt.SizeFDiagCursor
                    }
                    DragHandler {
                        target: null
                        property var initial: ({})
                        onActiveChanged: if (active)
                            initial = root.region
                        onTranslationChanged: {
                            if (active)
                                root.region = UI.resize(initial, {
                                    x: translation.x,
                                    y: translation.y
                                }, captureWindow.width, captureWindow.height);
                        }
                    }
                }
            }
            Shortcut {
                sequences: [StandardKey.Cancel]
                onActivated: screenshotController.cancel_capture()
            }
        }
    }
}
