import QtQuick

Loader {
    id: root
    required property var theme
    required property var node
    signal event(var action)
    function loadedView(): var {
        return root.item;
    }
    function graphCommand(command) {
        if (!loadedView())
            return null;
        if (command.type === "point")
            return loadedView().insertionPoint();
        loadedView().dispatch(command);
        return true;
    }
    Component.onCompleted: setSource(Qt.resolvedUrl("FrameGraph.qml"), {
        theme: Qt.binding(() => root.theme),
        node: Qt.binding(() => root.node)
    })
    Connections {
        target: root.item
        function onEvent(action) {
            root.event(action);
        }
    }
}
