pragma ComponentBehavior: Bound
import QtQuick
import "../../../controls" as Controls
import "../../../tactic_frame/features/administration/layouts/canvas.mjs" as Canvas

FocusScope {
    id: root
    required property var theme
    property var boxes: []
    property string selected: ""
    property var gesture: null
    property var ghost: null
    property real viewportScale: 1
    readonly property var chosen: ghost || boxes.find(b => b.key === selected) || null
    signal selectedKey(string key)
    signal committed(var change)
    function begin(area, mouse, box, handle, hit = false) {
        const point = area.mapToItem(root, mouse.x, mouse.y);
        if (hit && (mouse.modifiers & Qt.AltModifier))
            box = Canvas.pick(boxes, point.x, point.y, selected, true) || box;
        forceActiveFocus();
        selectedKey(box.key);
        if (box.canTransform === false)
            return;
        gesture = {
            box: Object.assign({}, box),
            handle,
            x: point.x,
            y: point.y
        };
        ghost = Object.assign({}, box);
    }
    function update(area, mouse) {
        if (!gesture)
            return;
        const point = area.mapToItem(root, mouse.x, mouse.y);
        ghost = Canvas.transform(gesture.box, gesture.handle, point.x - gesture.x, point.y - gesture.y);
    }
    function finish(area, mouse) {
        if (!gesture)
            return;
        update(area, mouse);
        const action = {
            key: gesture.box.key,
            handle: gesture.handle,
            before: gesture.box,
            after: ghost
        };
        gesture = null;
        ghost = null;
        if (JSON.stringify(action.before) !== JSON.stringify(action.after))
            committed(action);
    }
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape) {
            gesture = null;
            ghost = null;
            event.accepted = true;
            return;
        }
        if (!chosen || chosen.canTransform === false)
            return;
        const delta = {};
        delta[Qt.Key_Left] = [-1, 0];
        delta[Qt.Key_Right] = [1, 0];
        delta[Qt.Key_Up] = [0, -1];
        delta[Qt.Key_Down] = [0, 1];
        const d = delta[event.key];
        if (!d)
            return;
        const step = event.modifiers & Qt.ShiftModifier ? 10 : 1;
        const handle = event.modifiers & Qt.AltModifier ? "se" : "move";
        committed({
            key: chosen.key,
            handle,
            keyboard: true,
            before: chosen,
            after: Canvas.transform(chosen, handle, d[0] * step, d[1] * step)
        });
        event.accepted = true;
    }
    Repeater {
        model: root.boxes
        delegate: MouseArea {
            id: hit
            required property var modelData
            required property int index
            objectName: "canvasTarget_" + modelData.key
            x: (modelData.hit || modelData).x
            y: (modelData.hit || modelData).y
            width: (modelData.hit || modelData).width
            height: (modelData.hit || modelData).height
            z: index
            acceptedButtons: Qt.LeftButton
            hoverEnabled: true
            cursorShape: modelData.canTransform === false ? Qt.PointingHandCursor : Qt.SizeAllCursor
            preventStealing: pressed
            onPressed: mouse => root.begin(hit, mouse, modelData, "move", true)
            onPositionChanged: mouse => {
                if (pressed)
                    root.update(hit, mouse);
            }
            onReleased: mouse => root.finish(hit, mouse)
            onCanceled: {
                root.gesture = null;
                root.ghost = null;
            }
            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.width: 1
                border.color: root.theme.contentAccent
                visible: hit.containsMouse && !hit.pressed
            }
        }
    }
    Rectangle {
        id: outline
        z: 200
        visible: !!root.chosen
        x: root.chosen?.x || 0
        y: root.chosen?.y || 0
        width: root.chosen?.width || 0
        height: root.chosen?.height || 0
        color: "transparent"
        border.color: root.theme.contentAccent
        border.width: 1 / root.viewportScale
        MouseArea {
            id: moveEdge
            visible: root.chosen?.canTransform !== false
            x: 0
            y: -4 / root.viewportScale
            width: parent.width
            height: 8 / root.viewportScale
            cursorShape: Qt.SizeAllCursor
            acceptedButtons: Qt.LeftButton
            preventStealing: pressed
            onPressed: mouse => root.begin(moveEdge, mouse, root.chosen, "move")
            onPositionChanged: mouse => {
                if (pressed)
                    root.update(moveEdge, mouse);
            }
            onReleased: mouse => root.finish(moveEdge, mouse)
            onCanceled: {
                root.gesture = null;
                root.ghost = null;
            }
        }
        Controls.SelectableText {
            theme: root.theme
            activeFocusOnTab: false
            selectByMouse: false
            y: -20 / root.viewportScale
            text: Math.round(outline.width) + " × " + Math.round(outline.height)
            color: root.theme.contentAccent
            font.pixelSize: Math.round(11 / root.viewportScale)
        }
        Repeater {
            model: root.chosen?.canTransform === false ? [] : Canvas.handles
            delegate: MouseArea {
                id: handle
                required property string modelData
                objectName: "canvasHandle_" + modelData
                width: 14 / root.viewportScale
                height: 14 / root.viewportScale
                x: modelData.indexOf("e") >= 0 ? outline.width - width / 2 : outline.width / 2 - width / 2
                y: modelData.indexOf("s") >= 0 ? outline.height - height / 2 : outline.height / 2 - height / 2
                cursorShape: modelData === "se" ? Qt.SizeFDiagCursor : modelData === "e" ? Qt.SizeHorCursor : Qt.SizeVerCursor
                acceptedButtons: Qt.LeftButton
                preventStealing: pressed
                onPressed: mouse => root.begin(handle, mouse, root.chosen, modelData)
                onPositionChanged: mouse => {
                    if (pressed)
                        root.update(handle, mouse);
                }
                onReleased: mouse => root.finish(handle, mouse)
                onCanceled: {
                    root.gesture = null;
                    root.ghost = null;
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: 6 / root.viewportScale
                    height: 6 / root.viewportScale
                    color: root.theme.panel
                    border.color: root.theme.contentAccent
                    border.width: 1 / root.viewportScale
                }
            }
        }
    }
}
