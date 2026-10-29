import QtQuick
import "../.."
import QtQuick.Controls
import QtQuick.Window
import "../../../controls" as Controls
import "graph.state.mjs" as State
import "graph.ui.mjs" as UI

FocusScope {
    id: root
    required property var theme
    required property var node
    readonly property var nodes: node.nodes || []
    readonly property var edges: node.edges || []
    readonly property bool readOnly: !!node.readOnly
    readonly property bool selectionEnabled: node.selectionEnabled !== false
    readonly property string modelKey: node.resetKey || node.center || node.id
    property var ui: State.initial()
    readonly property var viewport: UI.viewport(node)
    readonly property var edgePaintBounds: UI.paintBounds(node, ui, viewport, State.selectionRect(ui))
    property bool synchronizing: false
    readonly property var paintPalette: [theme.workspace, theme.action, theme.primaryText, theme.surfaceContainerHigh, theme.outlineVariant]
    signal event(var action)
    clip: true
    objectName: node.id
    Accessible.role: Accessible.Grouping
    Accessible.name: node.label || "Graph"
    function dispatch(action) {
        const result = State.reduce(ui, action, node, viewport);
        ui = result.ui;
        for (const command of result.commands)
            root.event(Object.assign({}, node.action || {
                type: "graph"
            }, {
                value: command
            }));
    }
    function color(role): color {
        if (role && role.mix)
            return theme.blend(color(role.mix[0]), color(role.mix[1]), role.mix[2]);
        return !role ? "transparent" : String(role).charAt(0) === "#" || role === "transparent" ? Qt.darker(role, 1.0) : theme[role];
    }
    function synchronize() {
        if (!worldView || !node)
            return;
        synchronizing = true;
        worldView.contentX = (ui.x - ui.world.x) * ui.zoom;
        worldView.contentY = (ui.y - ui.world.y) * ui.zoom;
        synchronizing = false;
        edges.requestPaint();
    }
    function scrolled() {
        if (!synchronizing)
            Qt.callLater(function () {
                if (Math.abs(worldView.contentX - (root.ui.x - root.ui.world.x) * root.ui.zoom) > .6 || Math.abs(worldView.contentY - (root.ui.y - root.ui.world.y) * root.ui.zoom) > .6)
                    root.dispatch({
                        type: "scroll",
                        x: worldView.contentX,
                        y: worldView.contentY
                    });
            });
    }
    function includeNodes() {
        ui = State.include(ui, node, viewport);
    }
    function modifiers(value) {
        return {
            control: Boolean(value & (Qt.ControlModifier | Qt.MetaModifier)),
            shift: Boolean(value & Qt.ShiftModifier),
            alt: Boolean(value & Qt.AltModifier)
        };
    }
    function pointer(type, mouse) {
        if (type === "down")
            root.forceActiveFocus();
        dispatch(Object.assign({
            type,
            x: mouse.x,
            y: mouse.y,
            button: mouse.button === Qt.MiddleButton ? 1 : 0
        }, modifiers(mouse.modifiers)));
    }
    function insertionPoint() {
        return Qt.point(ui.x + viewport.width / ui.zoom / 2 - 100, ui.y + viewport.height / ui.zoom / 2 - 36);
    }
    function revealNode(identity) {
        dispatch({
            type: "reveal",
            identities: [identity]
        });
    }
    function resetView() {
        dispatch({
            type: "reset"
        });
    }
    onUiChanged: synchronize()
    onPaintPaletteChanged: if (edges)
        edges.requestPaint()
    onNodeChanged: Qt.callLater(includeNodes)
    onModelKeyChanged: {
        ui = State.initial();
        Qt.callLater(includeNodes);
    }
    onViewportChanged: Qt.callLater(includeNodes)
    onVisibleChanged: if (!visible)
        dispatch({
            type: "cancel"
        })
    Component.onCompleted: {
        includeNodes();
        synchronize();
    }
    Connections {
        target: root.theme
        ignoreUnknownSignals: true
        function onThemeChanged() {
            edges.requestPaint();
        }
    }
    Connections {
        target: root.Window.window
        function onActiveChanged() {
            if (!root.Window.window || !root.Window.window.active)
                root.dispatch({
                    type: "cancel"
                });
        }
    }
    Keys.priority: Keys.AfterItem
    Keys.onPressed: key => {
        const names = {};
        names[Qt.Key_Escape] = "Escape";
        names[Qt.Key_Delete] = "Delete";
        names[Qt.Key_Home] = "Home";
        names[Qt.Key_Left] = "ArrowLeft";
        names[Qt.Key_Right] = "ArrowRight";
        names[Qt.Key_Up] = "ArrowUp";
        names[Qt.Key_Down] = "ArrowDown";
        const text = names[key.key] || (key.key === Qt.Key_S ? "s" : key.text);
        if (["Escape", "Delete", "Home", "+", "=", "-", "f", "F", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].indexOf(text) < 0 && !(key.modifiers & (Qt.ControlModifier | Qt.MetaModifier) && text.toLowerCase() === "s")) {
            key.accepted = false;
            return;
        }
        root.dispatch(Object.assign({
            type: "key",
            key: text,
            repeat: key.isAutoRepeat
        }, root.modifiers(key.modifiers)));
        key.accepted = true;
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
        radius: root.theme.surfaceRadius
    }
    FrameBranch {
        x: 0
        y: 0
        width: root.width
        height: Math.max(0, root.viewport.y - 4)
        theme: root.theme
        scene: UI.toolbar(root.node, root.ui, root.node.language || "en")
        onEvent: action => root.dispatch(action)
    }
    Item {
        x: root.viewport.x
        y: root.viewport.y
        width: root.viewport.width + 16
        height: root.viewport.height + 16
        Flickable {
            id: worldView
            objectName: root.node.id + "Viewport"
            width: root.viewport.width
            height: root.viewport.height
            interactive: false
            clip: true
            contentWidth: (root.ui.world.right - root.ui.world.x) * root.ui.zoom
            contentHeight: (root.ui.world.bottom - root.ui.world.y) * root.ui.zoom
            onContentXChanged: root.scrolled()
            onContentYChanged: root.scrolled()
            ScrollBar.vertical: Controls.ScrollBar {
                objectName: root.node.id + "VerticalBar"
                parent: verticalGutter
                theme: root.theme
                flickableTarget: worldView
            }
            ScrollBar.horizontal: Controls.ScrollBar {
                objectName: root.node.id + "HorizontalBar"
                parent: horizontalGutter
                theme: root.theme
                flickableTarget: worldView
            }
        }
        Item {
            id: verticalGutter
            x: root.viewport.width + 4
            y: 0
            width: 12
            height: root.viewport.height
        }
        Item {
            id: horizontalGutter
            x: 0
            y: root.viewport.height + 4
            width: root.viewport.width
            height: 12
        }
        Item {
            id: camera
            width: root.viewport.width
            height: root.viewport.height
            clip: true
            Canvas {
                id: edges
                x: root.edgePaintBounds.x
                y: root.edgePaintBounds.y
                width: Math.max(1, root.edgePaintBounds.width)
                height: Math.max(1, root.edgePaintBounds.height)
                visible: root.edgePaintBounds.width > 0 && root.edgePaintBounds.height > 0
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    const paintState = Object.assign({}, root.ui, {
                        x: root.ui.x + x / root.ui.zoom,
                        y: root.ui.y + y / root.ui.zoom
                    });
                    UI.paint(ctx, root.node, paintState, {
                        width: width,
                        height: height
                    }, role => String(root.color(role)), State.selectionRect(root.ui));
                }
            }
            FrameBranch {
                x: -(root.ui.x - root.ui.world.x) * root.ui.zoom
                y: -(root.ui.y - root.ui.world.y) * root.ui.zoom
                width: root.ui.world.right - root.ui.world.x
                height: root.ui.world.bottom - root.ui.world.y
                scale: root.ui.zoom
                transformOrigin: Item.TopLeft
                theme: root.theme
                scene: UI.describe(root.node, root.ui, root.node.language || "en")
                onEvent: action => root.dispatch(action)
            }
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                hoverEnabled: true
                cursorShape: root.ui.pointer && root.ui.pointer.active && (root.ui.pointer.kind === "pan" || root.ui.pointer.kind === "node") ? Qt.ClosedHandCursor : Qt.ArrowCursor
                onPressed: mouse => root.pointer("down", mouse)
                onPositionChanged: mouse => {
                    if (root.ui.pointer || root.ui.pending)
                        root.pointer("move", mouse);
                }
                onReleased: mouse => root.pointer("up", mouse)
                onCanceled: root.dispatch({
                    type: "cancel"
                })
                onWheel: wheel => {
                    root.dispatch({
                        type: "zoom",
                        value: root.ui.zoom * (wheel.angleDelta.y > 0 ? 1.1 : 1 / 1.1),
                        x: wheel.x,
                        y: wheel.y
                    });
                    wheel.accepted = true;
                }
            }
            MultiPointTouchArea {
                anchors.fill: parent
                mouseEnabled: false
                minimumTouchPoints: 1
                maximumTouchPoints: 2
                touchPoints: [
                    TouchPoint {
                        id: touchA
                    },
                    TouchPoint {
                        id: touchB
                    }
                ]
                function updateTouches() {
                    root.forceActiveFocus();
                    root.dispatch({
                        type: "touch",
                        points: [touchA, touchB].filter(p => p.pressed).map(p => ({
                                    x: p.x,
                                    y: p.y
                                }))
                    });
                }
                onPressed: updateTouches()
                onUpdated: updateTouches()
                onReleased: updateTouches()
                onCanceled: root.dispatch({
                    type: "cancel"
                })
            }
        }
    }
    FrameAnimation {
        running: root.visible && !!root.ui.pointer && root.ui.pointer.active && root.ui.pointer.kind === "node"
        onTriggered: root.dispatch({
            type: "tick",
            seconds: frameTime
        })
    }
}
