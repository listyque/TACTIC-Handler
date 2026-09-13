import QtQuick

QtObject {
    id: root
    required property var view
    required property var controller
    required property var model
    required property bool presented
    readonly property string contextKey:
        String(controller.selectedObject.searchKey || "") + "\u001f" + controller.process
    property string previousContext: ""
    property var positions: ({})
    property var recent: []
    property bool pending: true

    function capture() {
        if (previousContext && view && !pending)
            positions[previousContext] = view.contentY
    }

    function restore() {
        if (!presented || controller.loading || !view || !controller.hasTarget || !pending)
            return
        view.forceLayout()
        if (positions[contextKey] !== undefined) {
            const minimum = view.originY
            const maximum = Math.max(minimum, minimum + view.contentHeight - view.height)
            view.contentY = Math.max(minimum, Math.min(maximum, positions[contextKey]))
        } else {
            view.positionViewAtEnd()
        }
        pending = false
    }

    onContextKeyChanged: {
        capture()
        previousContext = contextKey
        recent = recent.filter(key => key !== contextKey).concat([contextKey])
        while (recent.length > 24)
            delete positions[recent.shift()]
        pending = true
        restore()
    }
    onPresentedChanged: {
        if (presented)
            restore()
        else
            capture()
    }
    property Connections historyChanges: Connections {
        target: root.model
        function onContentReplaced() { root.restore() }
    }
    property Connections controllerChanges: Connections {
        target: root.controller
        function onStateChanged() {
            if (root.pending)
                root.restore()
        }
    }
    property Connections viewChanges: Connections {
        target: root.view
        function onContentHeightChanged() {
            if (root.pending)
                root.restore()
        }
    }
}
