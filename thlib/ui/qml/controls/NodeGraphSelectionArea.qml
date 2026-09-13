import QtQuick

Item {
    id: root

    required property var theme
    property var nodes: []
    property var selectedNodes: []
    property real nodeWidth: 200
    property real nodeHeight: 80
    property bool interactionEnabled: true
    property int activeModifiers: Qt.NoModifier
    property bool selecting: false
    property point startPoint: Qt.point(0, 0)
    property point currentPoint: Qt.point(0, 0)
    property int selectionModifiers: Qt.NoModifier
    readonly property rect selectionRect: Qt.rect(
        Math.min(startPoint.x, currentPoint.x),
        Math.min(startPoint.y, currentPoint.y),
        Math.abs(currentPoint.x - startPoint.x),
        Math.abs(currentPoint.y - startPoint.y)
    )

    signal selectionRequested(var identities, string primary)
    signal clearRequested()

    function worldPoint(mouse) {
        return Qt.point(mouse.x + root.x, mouse.y + root.y)
    }

    function candidates() {
        const rectangle = root.selectionRect
        const result = []
        for (const node of root.nodes || []) {
            const width = node.kind === "progress" ? root.nodeHeight : root.nodeWidth
            if (rectangle.x < node.nodeX + width
                    && rectangle.x + rectangle.width > node.nodeX
                    && rectangle.y < node.nodeY + root.nodeHeight
                    && rectangle.y + rectangle.height > node.nodeY)
                result.push(node.identity)
        }
        return result
    }

    function nodeAt(point) {
        const portMargin = root.theme.controlHeight / 2
        for (const node of root.nodes || []) {
            const width = node.kind === "progress" ? root.nodeHeight : root.nodeWidth
            if (point.x >= node.nodeX - portMargin
                    && point.x <= node.nodeX + width + portMargin
                    && point.y >= node.nodeY
                    && point.y <= node.nodeY + root.nodeHeight)
                return true
        }
        return false
    }

    function finishSelection() {
        const found = root.candidates()
        let result = Array.from(root.selectedNodes || [])
        const control = Boolean(root.selectionModifiers & Qt.ControlModifier)
        const shift = Boolean(root.selectionModifiers & Qt.ShiftModifier)
        if (control) {
            for (const identity of found) {
                const index = result.indexOf(identity)
                if (index >= 0) result.splice(index, 1)
                else result.push(identity)
            }
        } else if (shift) {
            for (const identity of found)
                if (result.indexOf(identity) < 0) result.push(identity)
        } else {
            result = found
        }
        const primary = found.length && result.indexOf(found[found.length - 1]) >= 0
            ? found[found.length - 1] : result.length ? result[result.length - 1] : ""
        root.selectionRequested(result, primary)
        root.selecting = false
    }

    MouseArea {
        objectName: "graphSelectionMouseArea"
        anchors.fill: parent
        enabled: root.interactionEnabled
        acceptedButtons: Qt.LeftButton
        preventStealing: true
        cursorShape: root.selecting ? Qt.CrossCursor : Qt.ArrowCursor
        onPressed: mouse => {
            const point = root.worldPoint(mouse)
            if (root.nodeAt(point)) {
                mouse.accepted = false
                return
            }
            root.startPoint = point
            root.currentPoint = root.startPoint
            root.selectionModifiers = mouse.modifiers | root.activeModifiers
            root.selecting = false
        }
        onPositionChanged: mouse => {
            if (!pressed) return
            const point = root.worldPoint(mouse)
            if (!root.selecting && Math.abs(point.x - root.startPoint.x)
                    + Math.abs(point.y - root.startPoint.y) >= root.theme.controlHeight / 6)
                root.selecting = true
            if (root.selecting) root.currentPoint = point
        }
        onReleased: mouse => {
            if (root.selecting) {
                root.currentPoint = root.worldPoint(mouse)
                root.finishSelection()
            } else if (!(root.selectionModifiers & (Qt.ControlModifier | Qt.ShiftModifier))) {
                root.clearRequested()
            }
        }
        onCanceled: root.selecting = false
    }
}
