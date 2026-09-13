pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import "." as Controls

FocusScope {
    id: root

    required property var theme
    property var nodes: []
    property var edges: []
    property string selectedNode: ""
    property var selectedNodes: selectedNode ? [selectedNode] : []
    property int selectedEdge: -1
    property bool readOnly: false
    property bool selectionEnabled: true
    property string pendingConnection: ""
    property bool pendingInput: false
    property point connectionCursor: Qt.point(0, 0)
    readonly property point connectionPoint: Qt.point(
        worldRect.x + (canvasView.contentX + connectionCursor.x) / zoom,
        worldRect.y + (canvasView.contentY + connectionCursor.y) / zoom)
    property real zoom: 1
    property int delegateGeneration: 0
    property rect worldRect: Qt.rect(-canvasInset, -canvasInset, 800 + canvasInset * 2, 800 + canvasInset * 2)
    property var draggedNode: null
    property var draggedNodes: []
    property point dragStartWorld: Qt.point(0, 0)
    property point dragPointer: Qt.point(0, 0)
    property int activeSelectionModifiers: Qt.NoModifier
    property bool firstView: true
    readonly property real canvasInset: theme.controlHeight / 2
    readonly property real nodeWidth: 200
    readonly property real nodeHeight: theme.controlHeight * 2

    signal nodeSelected(string identity)
    signal nodesSelected(var identities, string primary)
    signal edgeSelected(int index)
    signal nodeMoved(string identity, real nodeX, real nodeY)
    signal nodesMoved(var positions)
    signal connectionRequested(string source, string target)
    signal removeRequested()
    signal saveRequested()
    signal clearSelectionRequested()

    function nodeSize(identity) {
        const node = nodes.find(row => row.identity === identity)
        return Qt.size(node && node.kind === "progress" ? nodeHeight : nodeWidth, nodeHeight)
    }

    function nodePosition(identity) {
        // Follow the delegate while dragging; publish XML only on release.
        // Re-evaluate when delegates are created/replaced after a model update.
        const generation = delegateGeneration
        for (let index = 0; index < nodeRepeater.count; ++index) {
            const item = nodeRepeater.itemAt(index)
            if (item && item.objectName === "graphNode_" + identity)
                return Qt.point(item.x, item.y)
        }
        for (const node of nodes) {
            if (node.identity === identity)
                return Qt.point(node.nodeX, node.nodeY)
        }
        return Qt.point(0, 0)
    }

    function nodeColor(identity) {
        for (const node of nodes) {
            if (node.identity === identity)
                return node.color || theme.action
        }
        return theme.action
    }

    function nodeBounds() {
        let left = 0, top = 0, right = 800, bottom = 800
        for (const node of nodes) {
            left = Math.min(left, node.nodeX)
            top = Math.min(top, node.nodeY)
            right = Math.max(right, node.nodeX + nodeWidth + 100)
            bottom = Math.max(bottom, node.nodeY + nodeHeight + 100)
        }
        return Qt.rect(left - canvasInset, top - canvasInset,
                       right - left + canvasInset * 2, bottom - top + canvasInset * 2)
    }

    function viewOrigin() {
        return Qt.point(worldRect.x + canvasView.contentX / zoom,
                        worldRect.y + canvasView.contentY / zoom)
    }

    function insertionPoint() {
        const origin = viewOrigin()
        return Qt.point(origin.x + canvasView.width / zoom / 2 - nodeWidth / 2,
                        origin.y + canvasView.height / zoom / 2 - nodeHeight / 2)
    }

    function revealNode(identity) {
        const position = nodePosition(identity)
        panTo(position.x + nodeSize(identity).width / 2 - canvasView.width / zoom / 2,
              position.y + nodeHeight / 2 - canvasView.height / zoom / 2)
    }

    function revealSelection() {
        const selected = Array.from(selectedNodes || [])
        if (!selected.length) return
        let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity
        for (const identity of selected) {
            const position = nodePosition(identity), size = nodeSize(identity)
            left = Math.min(left, position.x)
            top = Math.min(top, position.y)
            right = Math.max(right, position.x + size.width)
            bottom = Math.max(bottom, position.y + size.height)
        }
        panTo((left + right) / 2 - canvasView.width / zoom / 2,
              (top + bottom) / 2 - canvasView.height / zoom / 2)
    }

    function expandWorld(left, top, right, bottom) {
        const origin = viewOrigin()
        left = Math.min(left, worldRect.x)
        top = Math.min(top, worldRect.y)
        right = Math.max(right, worldRect.x + worldRect.width)
        bottom = Math.max(bottom, worldRect.y + worldRect.height)
        worldRect = Qt.rect(left, top, right - left, bottom - top)
        // Expanding left/up changes only the coordinate offset, never the
        // scene under the pointer or native node positions.
        canvasView.contentX = (origin.x - left) * zoom
        canvasView.contentY = (origin.y - top) * zoom
    }

    function panTo(x, y) {
        expandWorld(x - 100, y - 100,
                    x + canvasView.width / zoom + 100, y + canvasView.height / zoom + 100)
        canvasView.contentX = (x - worldRect.x) * zoom
        canvasView.contentY = (y - worldRect.y) * zoom
    }

    function zoomAt(value, x, y) {
        if (draggedNode || panDrag.active) return
        const origin = viewOrigin()
        const anchor = Qt.point(origin.x + x / zoom, origin.y + y / zoom)
        zoom = Math.max(0.4, Math.min(2, value))
        panTo(anchor.x - x / zoom, anchor.y - y / zoom)
    }

    function zoomCentered(value) {
        zoomAt(value, canvasView.width / 2, canvasView.height / 2)
    }

    function includeNodes() {
        if (!canvasView) return
        const bounds = nodeBounds()
        expandWorld(bounds.x, bounds.y, bounds.x + bounds.width, bounds.y + bounds.height)
        if (firstView && nodes.length) {
            canvasView.contentX = 0
            canvasView.contentY = 0
            firstView = false
        }
    }

    function sceneToWorld(point) {
        const local = canvasView.mapFromItem(null, point.x, point.y)
        const origin = viewOrigin()
        return Qt.point(origin.x + local.x / zoom, origin.y + local.y / zoom)
    }

    function selectionForNode(identity, modifiers, dragging) {
        let selected = Array.from(selectedNodes || [])
        const control = Boolean(modifiers & Qt.ControlModifier)
        const shift = Boolean(modifiers & Qt.ShiftModifier)
        const index = selected.indexOf(identity)
        if (dragging && index >= 0) return selected
        if (control) {
            if (index >= 0) selected.splice(index, 1)
            else selected.push(identity)
        } else if (shift) {
            if (index < 0) selected.push(identity)
        } else {
            selected = [identity]
        }
        return selected
    }

    function selectNodeWithModifiers(identity, modifiers) {
        const selected = selectionForNode(identity, modifiers, false)
        const primary = selected.indexOf(identity) >= 0
            ? identity : selected.length ? selected[selected.length - 1] : ""
        nodesSelected(selected, primary)
    }

    function startNodeDrag(node, press, pointer, modifiers) {
        let selected = selectionForNode(node.modelData.identity, modifiers, true)
        if (selected.indexOf(node.modelData.identity) < 0)
            selected.push(node.modelData.identity)
        nodesSelected(selected, node.modelData.identity)
        dragStartWorld = sceneToWorld(press)
        draggedNode = node
        draggedNodes = []
        for (let index = 0; index < nodeRepeater.count; ++index) {
            const item = nodeRepeater.itemAt(index)
            const data = item ? nodes.find(row => "graphNode_" + row.identity === item.objectName) : null
            if (item && data && selected.indexOf(data.identity) >= 0 && !data.referenceOnly)
                draggedNodes.push({item: item, identity: data.identity, x: item.x, y: item.y})
        }
        node.forceActiveFocus()
        moveDraggedNode(pointer)
    }

    function moveDraggedNode(pointer) {
        if (!draggedNode) return
        dragPointer = pointer
        const point = sceneToWorld(pointer)
        const dx = point.x - dragStartWorld.x, dy = point.y - dragStartWorld.y
        for (const entry of draggedNodes) {
            entry.item.x = entry.x + dx
            entry.item.y = entry.y + dy
            expandWorld(entry.item.x - canvasInset, entry.item.y - canvasInset,
                        entry.item.x + entry.item.width + canvasInset,
                        entry.item.y + entry.item.height + canvasInset)
        }
    }

    function finishNodeDrag(node) {
        if (draggedNode !== node) return
        const positions = draggedNodes.map(entry => ({
            identity: entry.identity,
            nodeX: entry.item.x,
            nodeY: entry.item.y
        }))
        draggedNode = null
        draggedNodes = []
        nodesMoved(positions)
    }

    function cancelNodeDrag() {
        draggedNode = null
        for (const entry of draggedNodes) {
            entry.item.x = entry.x
            entry.item.y = entry.y
        }
        draggedNodes = []
    }

    function moveSelectionBy(dx, dy) {
        const selected = Array.from(selectedNodes || [])
        const positions = []
        for (const identity of selected) {
            const node = nodes.find(row => row.identity === identity)
            if (node && !node.referenceOnly)
                positions.push({identity: identity, nodeX: node.nodeX + dx, nodeY: node.nodeY + dy})
        }
        if (positions.length) nodesMoved(positions)
    }

    function autoPan(seconds) {
        const point = canvasView.mapFromItem(null, dragPointer.x, dragPointer.y)
        const margin = theme.controlHeight
        const dx = point.x < margin ? point.x - margin : Math.max(0, point.x - canvasView.width + margin)
        const dy = point.y < margin ? point.y - margin : Math.max(0, point.y - canvasView.height + margin)
        if (!dx && !dy) return
        const origin = viewOrigin(), distance = Math.min(seconds, 0.05) * 10 / zoom
        panTo(origin.x + Math.max(-margin, Math.min(margin, dx)) * distance,
              origin.y + Math.max(-margin, Math.min(margin, dy)) * distance)
        moveDraggedNode(dragPointer)
    }

    function choosePort(identity, input) {
        if (!pendingConnection || pendingInput === input) {
            pendingConnection = pendingConnection === identity ? "" : identity
            pendingInput = input
            const position = nodePosition(identity)
            connectionCursor = Qt.point(
                (position.x + (input ? 0 : nodeSize(identity).width) - worldRect.x) * zoom - canvasView.contentX,
                (position.y + nodeHeight / 2 - worldRect.y) * zoom - canvasView.contentY)
        } else if (pendingConnection !== identity) {
            const source = input ? pendingConnection : identity
            const target = input ? identity : pendingConnection
            pendingConnection = ""
            connectionRequested(source, target)
        }
    }

    function resetView() {
        zoom = 1
        worldRect = nodeBounds()
        canvasView.contentX = 0
        canvasView.contentY = 0
    }

    activeFocusOnTab: true
    Accessible.name: qsTr("Node canvas")
    onNodesChanged: {
        pendingConnection = ""
        draggedNode = null
        draggedNodes = []
        includeNodes()
    }
    onVisibleChanged: if (!visible) {
        pendingConnection = ""
        cancelNodeDrag()
    }
    onReadOnlyChanged: if (readOnly) pendingConnection = ""
    Component.onCompleted: includeNodes()
    // Keys bubble only from the canvas, never from the sibling inspector/XML
    // inputs. Keep focus here before a mutation replaces the node delegates.
    Keys.onEscapePressed: {
        if (pendingConnection || draggedNode) {
            pendingConnection = ""
            cancelNodeDrag()
        } else {
            clearSelectionRequested()
        }
    }
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Shift) {
            root.activeSelectionModifiers |= Qt.ShiftModifier
            return
        }
        if (event.key === Qt.Key_Control) {
            root.activeSelectionModifiers |= Qt.ControlModifier
            return
        }
        if (!root.activeFocus || root.draggedNode || panDrag.active || root.pendingConnection) return
        const modifiers = event.modifiers & ~Qt.KeypadModifier
        if (event.key === Qt.Key_S && modifiers === Qt.ControlModifier) {
            if (!root.readOnly && !event.isAutoRepeat) root.saveRequested()
        } else if (modifiers === Qt.NoModifier || modifiers === Qt.ShiftModifier) {
            if (event.key === Qt.Key_Plus || event.key === Qt.Key_Equal)
                root.zoomCentered(root.zoom + 0.1)
            else if (event.key === Qt.Key_Minus)
                root.zoomCentered(root.zoom - 0.1)
            else if (modifiers !== Qt.NoModifier) return
            else if (event.key === Qt.Key_Home) root.resetView()
            else if (event.key === Qt.Key_F && root.selectedNodes.length) root.revealSelection()
            else if (event.key === Qt.Key_Delete) {
                if (!root.readOnly && !event.isAutoRepeat) root.removeRequested()
            } else {
                if (root.readOnly || !root.selectedNodes.length) return
                let dx = 0, dy = 0
                if (event.key === Qt.Key_Left) dx = -10
                else if (event.key === Qt.Key_Right) dx = 10
                else if (event.key === Qt.Key_Up) dy = -10
                else if (event.key === Qt.Key_Down) dy = 10
                else return
                root.forceActiveFocus()
                root.moveSelectionBy(dx, dy)
            }
        } else return
        event.accepted = true
    }
    Keys.onReleased: event => {
        if (event.key === Qt.Key_Shift)
            root.activeSelectionModifiers &= ~Qt.ShiftModifier
        else if (event.key === Qt.Key_Control)
            root.activeSelectionModifiers &= ~Qt.ControlModifier
        else return
        event.accepted = false
    }

    FrameAnimation {
        objectName: "graphDragAutoPan"
        running: root.visible && root.draggedNode !== null
        onTriggered: root.autoPan(frameTime)
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
        radius: root.theme.surfaceRadius
        border.color: root.activeFocus ? root.theme.action : root.theme.outlineVariant
        ActivationHandler {
            onActivated: root.forceActiveFocus()
        }
    }
    Item {
        id: verticalGutter
        width: verticalBar.reservedExtent
        anchors.top: canvasView.top
        anchors.bottom: canvasView.bottom
        anchors.right: parent.right
        anchors.rightMargin: 4
    }
    Item {
        id: horizontalGutter
        height: horizontalBar.reservedExtent
        anchors.left: canvasView.left
        anchors.right: canvasView.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 4
    }
    Flickable {
        id: canvasView
        objectName: "adminGraphCanvas"
        anchors.fill: parent
        anchors.margins: 8
        anchors.rightMargin: 8 + verticalBar.reservedExtent
        anchors.bottomMargin: 8 + horizontalBar.reservedExtent
        clip: true
        contentWidth: graphSpace.width * root.zoom
        contentHeight: graphSpace.height * root.zoom
        boundsBehavior: Flickable.StopAtBounds
        acceptedButtons: Qt.NoButton

        HoverHandler {
            parent: canvasView
            enabled: root.visible && root.pendingConnection.length > 0
            blocking: false
            onPointChanged: root.connectionCursor = canvasView.mapFromItem(
                null, point.scenePosition.x, point.scenePosition.y)
        }
        WheelHandler {
            id: zoomWheel
            parent: canvasView
            target: null
            blocking: true
            onWheel: event => {
                const steps = event.angleDelta.y ? event.angleDelta.y / 120 : event.pixelDelta.y / 40
                const pointer = canvasView.mapFromItem(null, zoomWheel.point.scenePosition.x,
                                                       zoomWheel.point.scenePosition.y)
                root.zoomAt(root.zoom * Math.pow(1.15, steps), pointer.x, pointer.y)
                event.accepted = true
            }
        }
        DragHandler {
            id: panDrag
            parent: canvasView
            target: null
            acceptedButtons: Qt.MiddleButton
            dragThreshold: 0
            cursorShape: active ? Qt.ClosedHandCursor : Qt.OpenHandCursor
            property point startOrigin: Qt.point(0, 0)
            function pan() {
                const delta = Qt.point(centroid.scenePosition.x - centroid.scenePressPosition.x,
                                       centroid.scenePosition.y - centroid.scenePressPosition.y)
                root.panTo(startOrigin.x - delta.x / root.zoom, startOrigin.y - delta.y / root.zoom)
            }
            onActiveChanged: if (active) {
                startOrigin = root.viewOrigin()
                pan()
            }
            onCentroidChanged: if (active) pan()
        }

        Item {
            id: graphSpace
            width: Math.max(root.worldRect.width, canvasView.width / root.zoom)
            height: Math.max(root.worldRect.height, canvasView.height / root.zoom)
            scale: root.zoom
            transformOrigin: Item.TopLeft

            // World coordinates remain native; only the viewport offset grows.
            Item {
                id: worldContent
                x: -root.worldRect.x
                y: -root.worldRect.y
                width: parent.width
                height: parent.height
                Controls.NodeGraphSelectionArea {
                    id: selectionArea
                    objectName: "graphSelectionArea"
                    x: root.worldRect.x
                    y: root.worldRect.y
                    width: root.worldRect.width
                    height: root.worldRect.height
                    theme: root.theme
                    nodes: root.nodes
                    selectedNodes: root.selectedNodes
                    nodeWidth: root.nodeWidth
                    nodeHeight: root.nodeHeight
                    interactionEnabled: root.selectionEnabled && !root.pendingConnection
                        && !root.draggedNode && !panDrag.active
                    activeModifiers: root.activeSelectionModifiers
                    onSelectionRequested: (identities, primary) => {
                        root.forceActiveFocus()
                        root.nodesSelected(identities, primary)
                    }
                    onClearRequested: {
                        root.forceActiveFocus()
                        root.clearSelectionRequested()
                    }
                }
                Repeater {
                    // Pointer movement changes only the transient connector's
                    // geometry, never the graph model or the other delegates.
                    model: root.edges.concat(root.pendingConnection ? [{
                        pending: true, edgeIndex: -1,
                        from: root.pendingInput ? "" : root.pendingConnection,
                        to: root.pendingInput ? root.pendingConnection : ""
                    }] : [])
                    delegate: Item {
                        id: connector

                        required property var modelData
                        readonly property bool pending: modelData.pending === true
                        readonly property bool cursorAtSource: pending && root.pendingInput
                        readonly property bool cursorAtTarget: pending && !root.pendingInput
                        readonly property point source: cursorAtSource
                            ? root.connectionPoint : root.nodePosition(modelData.from)
                        readonly property point target: cursorAtTarget
                            ? root.connectionPoint : root.nodePosition(modelData.to)
                        readonly property real startX: source.x + (cursorAtSource ? 0 : root.nodeSize(modelData.from).width)
                        readonly property real startY: source.y + (cursorAtSource ? 0 : root.nodeHeight / 2)
                        readonly property real endX: target.x
                        readonly property real endY: target.y + (cursorAtTarget ? 0 : root.nodeHeight / 2)
                        readonly property real bend: Math.max(pending ? 0 : 50, Math.abs(endX - startX) / 2)
                        readonly property bool selected: !pending && root.selectedEdge === modelData.edgeIndex
                        readonly property color accent: root.nodeColor(pending ? root.pendingConnection : modelData.from)
                        readonly property point arrowPoint: curvePoint(0.6)
                        readonly property real arrowAngle: {
                            const before = curvePoint(0.59), after = curvePoint(0.61)
                            return Math.atan2(after.y - before.y, after.x - before.x) * 180 / Math.PI
                        }

                        function curvePoint(t) {
                            const u = 1 - t
                            return Qt.point(
                                u * u * u * startX + 3 * u * u * t * (startX + bend)
                                + 3 * u * t * t * (endX - bend) + t * t * t * endX,
                                u * u * u * startY + 3 * u * u * t * startY
                                + 3 * u * t * t * endY + t * t * t * endY)
                        }

                        objectName: pending ? "graphPendingConnection" : "graphConnection_" + modelData.edgeIndex
                        x: Math.min(startX, endX) - bend
                        y: Math.min(startY, endY) - 20
                        width: Math.abs(endX - startX) + bend * 2
                        height: Math.abs(endY - startY) + 40

                        Shape {
                            anchors.fill: parent
                            // Analytic edge coverage at any canvas zoom, without
                            // an offscreen/MSAA layer for every connection.
                            preferredRendererType: Shape.CurveRenderer
                            antialiasing: true
                            ShapePath {
                                strokeColor: connector.selected ? root.theme.primaryText : connector.accent
                                strokeWidth: connector.selected ? 3.5 : 2.5
                                fillColor: "transparent"
                                startX: connector.startX - connector.x
                                startY: connector.startY - connector.y
                                PathCubic {
                                    x: connector.endX - connector.x
                                    y: connector.endY - connector.y
                                    control1X: connector.startX + connector.bend - connector.x
                                    control1Y: connector.startY - connector.y
                                    control2X: connector.endX - connector.bend - connector.x
                                    control2Y: connector.endY - connector.y
                                }
                            }
                        }
                        Controls.PopupAction {
                            id: edgeAction
                            objectName: "graphEdge_" + connector.modelData.edgeIndex
                            x: connector.arrowPoint.x - connector.x - width / 2
                            y: connector.arrowPoint.y - connector.y - height / 2
                            width: root.theme.controlHeight
                            height: root.theme.controlHeight
                            enabled: root.selectionEnabled && !connector.pending
                            visible: !connector.pending
                                || Math.abs(connector.endX - connector.startX)
                                    + Math.abs(connector.endY - connector.startY) > root.theme.controlHeight
                            Accessible.ignored: connector.pending || !root.selectionEnabled
                            padding: 0
                            Accessible.name: (connector.modelData.label
                                ? connector.modelData.label + " · " : "")
                                + connector.modelData.from + " → " + connector.modelData.to
                            onClicked: root.edgeSelected(connector.modelData.edgeIndex)
                            background: Rectangle {
                                radius: width / 2
                                antialiasing: true
                                color: edgeAction.hovered || edgeAction.visualFocus
                                    ? root.theme.overlay(root.theme.workspace, connector.accent, 0.2) : "transparent"
                                border.width: edgeAction.visualFocus ? 1 : 0
                                border.pixelAligned: false
                                border.color: connector.accent
                            }
                            contentItem: Item {
                                Shape {
                                    objectName: "graphDirectionArrow"
                                    anchors.centerIn: parent
                                    width: 12
                                    height: 10
                                    rotation: connector.arrowAngle
                                    preferredRendererType: Shape.CurveRenderer
                                    antialiasing: true
                                    ShapePath {
                                        strokeWidth: -1
                                        fillColor: connector.selected ? root.theme.primaryText : connector.accent
                                        startX: 0
                                        startY: 0
                                        PathLine { x: 12; y: 5 }
                                        PathLine { x: 0; y: 10 }
                                        PathLine { x: 0; y: 0 }
                                    }
                                }
                            }
                            Controls.ToolTip {
                                theme: root.theme
                                text: edgeAction.Accessible.name
                                visible: edgeAction.hovered
                            }
                        }
                    }
                }
                Repeater {
                    id: nodeRepeater
                    model: root.nodes
                    onItemAdded: root.delegateGeneration += 1
                    onItemRemoved: root.delegateGeneration += 1
                    delegate: Item {
                        id: nodeCard

                        required property var modelData
                        readonly property color accent: modelData.kind === "missing" ? root.theme.error : modelData.color || root.theme.action
                        readonly property bool selected: root.selectedNodes.indexOf(modelData.identity) >= 0
                        readonly property bool circular: modelData.kind === "progress"

                        objectName: "graphNode_" + modelData.identity
                        width: circular ? root.nodeHeight : root.nodeWidth
                        height: root.nodeHeight
                        x: modelData.nodeX
                        y: modelData.nodeY
                        z: nodeDrag.active ? 2 : 1
                        activeFocusOnTab: root.selectionEnabled
                        Accessible.role: Accessible.ListItem
                        Accessible.name: modelData.label
                        Accessible.selected: selected

                        Rectangle {
                            anchors.fill: parent
                            radius: nodeCard.circular ? width / 2 : root.theme.itemRadius
                            antialiasing: true
                            color: root.theme.blend(root.theme.surfaceContainer, nodeCard.accent,
                                                    nodeCard.selected ? 0.26 : 0.12)
                            border.width: nodeCard.selected || nodeCard.activeFocus ? 2 : 1
                            border.pixelAligned: false
                            border.color: nodeCard.selected || nodeCard.activeFocus
                                ? nodeCard.accent : root.theme.blend(root.theme.outlineVariant, nodeCard.accent, 0.5)
                        }
                        Column {
                            x: nodeCard.circular ? 12 : 22
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - x * 2
                            spacing: 6
                            Text {
                                width: parent.width
                                text: nodeCard.modelData.label
                                // The application uses native desktop glyphs;
                                // only zoomable canvas labels need scalable text.
                                renderType: Text.QtRendering
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                                horizontalAlignment: nodeCard.circular ? Text.AlignHCenter : Text.AlignLeft
                            }
                            Text {
                                width: parent.width
                                renderType: Text.QtRendering
                                text: nodeCard.modelData.pendingCreation ? qsTr("New · many-to-many")
                                    : nodeCard.modelData.kind === "instance" ? "many-to-many"
                                    : nodeCard.modelData.kind === "missing" ? qsTr("Missing process") : nodeCard.modelData.kind
                                visible: !nodeCard.circular
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                                elide: Text.ElideRight
                            }
                        }
                        Item {
                            // Port hit areas belong to the ports, not this drag target.
                            x: root.canvasInset
                            width: parent.width - root.canvasInset * 2
                            height: parent.height
                            ActivationHandler {
                                enabled: root.selectionEnabled
                                cursorShape: !root.selectionEnabled ? Qt.ArrowCursor
                                    : root.readOnly || nodeCard.modelData.referenceOnly
                                        ? Qt.PointingHandCursor
                                        : nodeDrag.active ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                                onActivated: modifiers => {
                                    root.selectNodeWithModifiers(
                                        nodeCard.modelData.identity,
                                        modifiers | root.activeSelectionModifiers)
                                    nodeCard.forceActiveFocus()
                                }
                            }
                            DragHandler {
                                id: nodeDrag
                                enabled: !root.readOnly && !nodeCard.modelData.referenceOnly
                                acceptedButtons: Qt.LeftButton
                                target: null
                                onActiveChanged: {
                                    if (active) root.startNodeDrag(
                                        nodeCard, centroid.scenePressPosition,
                                        centroid.scenePosition,
                                        centroid.modifiers | root.activeSelectionModifiers)
                                    else root.finishNodeDrag(nodeCard)
                                }
                                onCentroidChanged: if (active) root.moveDraggedNode(centroid.scenePosition)
                            }
                        }
                        Controls.GraphPort {
                            objectName: "graphInput_" + nodeCard.modelData.identity
                            x: -width / 2
                            anchors.verticalCenter: parent.verticalCenter
                            theme: root.theme
                            accent: nodeCard.accent
                            text: qsTr("Input — connect here")
                            activePort: enabled && root.pendingConnection.length > 0
                                && (root.pendingInput ? root.pendingConnection === nodeCard.modelData.identity
                                                      : root.pendingConnection !== nodeCard.modelData.identity)
                            enabled: !root.readOnly && !nodeCard.modelData.referenceOnly
                            onClicked: root.choosePort(nodeCard.modelData.identity, true)
                        }
                        Controls.GraphPort {
                            objectName: "graphOutput_" + nodeCard.modelData.identity
                            x: parent.width - width / 2
                            anchors.verticalCenter: parent.verticalCenter
                            theme: root.theme
                            accent: nodeCard.accent
                            text: qsTr("Output — connect here")
                            filled: true
                            activePort: root.pendingConnection.length > 0
                                && (root.pendingInput ? root.pendingConnection !== nodeCard.modelData.identity
                                                      : root.pendingConnection === nodeCard.modelData.identity)
                            enabled: !root.readOnly && !nodeCard.modelData.referenceOnly
                            onClicked: root.choosePort(nodeCard.modelData.identity, false)
                        }
                        Keys.onPressed: event => {
                            if (nodeCard.activeFocus && root.selectedNode !== nodeCard.modelData.identity
                                    && event.modifiers === Qt.NoModifier
                                    && [Qt.Key_Delete, Qt.Key_F, Qt.Key_Left, Qt.Key_Right,
                                        Qt.Key_Up, Qt.Key_Down].includes(event.key))
                                root.nodeSelected(nodeCard.modelData.identity)
                        }
                    }
                }
                Rectangle {
                    objectName: "graphSelectionRectangle"
                    visible: selectionArea.selecting
                    z: 4
                    x: selectionArea.selectionRect.x
                    y: selectionArea.selectionRect.y
                    width: selectionArea.selectionRect.width
                    height: selectionArea.selectionRect.height
                    color: root.theme.overlay(root.theme.workspace, root.theme.action, 0.14)
                    border.width: 1
                    border.pixelAligned: false
                    border.color: root.theme.action
                    radius: root.theme.itemRadius
                    antialiasing: true
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: verticalBar
            objectName: "adminGraphVerticalBar"
            parent: verticalGutter
            theme: root.theme
            flickableTarget: canvasView
        }
        ScrollBar.horizontal: Controls.ScrollBar {
            id: horizontalBar
            objectName: "adminGraphHorizontalBar"
            parent: horizontalGutter
            theme: root.theme
            flickableTarget: canvasView
        }
    }
}
