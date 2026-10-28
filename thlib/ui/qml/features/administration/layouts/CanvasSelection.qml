pragma ComponentBehavior: Bound
import QtQuick
import "../../../controls" as Controls
import "../../../tactic_frame/features/administration/layouts/canvas.mjs" as Canvas
import "../../../tactic_frame/features/administration/layouts/page.selection.mjs" as Selection

FocusScope {
    id: root
    required property var theme
    property var boxes: []
    property string selected: ""
    property var gesture: null
    property var ghost: null
    property real viewportScale: 1
    property var selection: []
    property bool multiple: false
    property bool multiSelect: false
    property bool snap: false
    property var preview: null
    property var rubber: null
    readonly property var group: Selection.selected(boxes, selection)
    readonly property var outlines: preview ? preview.changes.map(change => change.after) : group
    readonly property var chosen: multiple && group.length > 1 ? Object.assign({}, Selection.bounds(outlines), {
        group: true
    }) : ghost || (preview ? preview.changes[0].after : null) || boxes.find(b => b.key === selected) || null
    signal selectionEdited(var keys)
    signal selectedKey(string key)
    signal committed(var change)
    function cancel() {
        gesture = null;
        ghost = null;
        preview = null;
        rubber = null;
    }
    function begin(area, mouse, box, handle, hit = false) {
        const point = area.mapToItem(root, mouse.x, mouse.y);
        forceActiveFocus();
        if (multiple && (!box || (mouse.modifiers & Qt.ShiftModifier))) {
            gesture = {
                marquee: true,
                start: {
                    x: point.x,
                    y: point.y
                },
                base: selection,
                box
            };
            rubber = {
                x: point.x,
                y: point.y,
                width: 0,
                height: 0
            };
            return;
        }
        if (hit && (mouse.modifiers & Qt.AltModifier))
            box = Canvas.pick(boxes, point.x, point.y, selected, true) || box;
        if (multiple) {
            let keys = selection;
            if (!box.group && ((mouse.modifiers & (Qt.ControlModifier | Qt.MetaModifier)) || multiSelect)) {
                selectionEdited(Selection.toggle(keys, box.key));
                return;
            }
            if (!box.group && !keys.includes(box.key))
                keys = [box.key];
            selectionEdited(keys);
            const chosenBoxes = Selection.selected(boxes, keys);
            if (!chosenBoxes.length)
                return;
            gesture = {
                boxes: chosenBoxes,
                handle,
                x: point.x,
                y: point.y
            };
            return;
        }
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
        if (gesture.marquee) {
            rubber = Selection.bounds([Object.assign({}, gesture.start, {
                    width: 0,
                    height: 0
                }),
                {
                    x: point.x,
                    y: point.y,
                    width: 0,
                    height: 0
                }
            ]);
            return;
        }
        const dx = point.x - gesture.x, dy = point.y - gesture.y;
        if (gesture.boxes) {
            if (Math.hypot(dx, dy) * viewportScale < 3 && !gesture.moved)
                return;
            gesture.moved = true;
            preview = Selection.drag(gesture.boxes, gesture.handle, dx, dy, boxes, viewportScale, snap && !(mouse.modifiers & Qt.AltModifier));
        } else
            ghost = Canvas.transform(gesture.box, gesture.handle, dx, dy);
    }
    function finish(area, mouse) {
        if (!gesture)
            return;
        update(area, mouse);
        const g = gesture;
        if (g.marquee) {
            const point = area.mapToItem(root, mouse.x, mouse.y);
            const small = Math.hypot(point.x - g.start.x, point.y - g.start.y) * viewportScale < 3;
            selectionEdited(small ? (g.box ? Selection.toggle(g.base, g.box.key) : []) : Selection.roots(g.base.concat(Selection.marquee(boxes, g.start, point))));
        } else if (g.boxes) {
            const changes = preview ? preview.changes : [];
            if (changes.some(c => JSON.stringify(c.before) !== JSON.stringify(c.after)))
                committed({
                    changes
                });
        } else if (JSON.stringify(g.box) !== JSON.stringify(ghost))
            committed({
                key: g.box.key,
                handle: g.handle,
                before: g.box,
                after: ghost
            });
        cancel();
    }
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape) {
            cancel();
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
        const step = event.modifiers & Qt.ShiftModifier ? 10 : 1, handle = event.modifiers & Qt.AltModifier ? 'se' : 'move';
        if (multiple) {
            if (group.length > 1 && handle !== 'move')
                return;
            committed({
                changes: Selection.drag(group, handle, d[0] * step, d[1] * step, [], viewportScale, false).changes
            });
        } else
            committed({
                key: chosen.key,
                handle,
                keyboard: true,
                before: chosen,
                after: Canvas.transform(chosen, handle, d[0] * step, d[1] * step)
            });
        event.accepted = true;
    }
    MouseArea {
        id: background
        objectName: "canvasMarqueeArea"
        anchors.fill: parent
        visible: root.multiple
        z: -1
        preventStealing: pressed
        onPressed: mouse => root.begin(background, mouse, null, "move")
        onPositionChanged: mouse => {
            if (pressed)
                root.update(background, mouse);
        }
        onReleased: mouse => root.finish(background, mouse)
        onCanceled: root.cancel()
    }
    Repeater {
        model: root.multiple ? root.outlines : []
        delegate: Rectangle {
            required property var modelData
            objectName: "canvasSelected_" + modelData.key
            x: modelData.x
            y: modelData.y
            width: modelData.width
            height: modelData.height
            z: 200
            color: "transparent"
            border.color: root.theme.contentAccent
            border.width: 1 / root.viewportScale
        }
    }
    Repeater {
        model: root.preview ? root.preview.guides : []
        delegate: Rectangle {
            required property var modelData
            objectName: "canvasGuide_" + modelData.axis
            x: modelData.axis === 'x' ? modelData.value : modelData.start
            y: modelData.axis === 'y' ? modelData.value : modelData.start
            width: modelData.axis === 'x' ? 1 / root.viewportScale : modelData.end - modelData.start
            height: modelData.axis === 'y' ? 1 / root.viewportScale : modelData.end - modelData.start
            z: 250
            color: root.theme.contentAccent
        }
    }
    Rectangle {
        visible: !!root.rubber
        x: root.rubber?.x || 0
        y: root.rubber?.y || 0
        width: root.rubber?.width || 0
        height: root.rubber?.height || 0
        z: 260
        color: root.theme.overlay("transparent", root.theme.contentAccent, .12)
        border.color: root.theme.contentAccent
        border.width: 1 / root.viewportScale
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
                root.cancel();
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
                root.cancel();
            }
        }
        Controls.SelectableText {
            theme: root.theme
            activeFocusOnTab: false
            selectByMouse: false
            y: -20 / root.viewportScale
            text: Math.round(outline.width) + " Г— " + Math.round(outline.height)
            color: root.theme.contentAccent
            font.pixelSize: Math.round(11 / root.viewportScale)
        }
        Repeater {
            model: root.chosen?.canTransform === false || root.chosen?.group ? [] : Canvas.handles
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
                    root.cancel();
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
