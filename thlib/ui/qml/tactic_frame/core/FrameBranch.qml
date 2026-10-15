import QtQuick

// A URL loader breaks QML's static recursive-type restriction for child scenes.
Loader {
    id: root
    required property var theme
    property var scene: ({
            nodes: []
        })
    property var views: ({})
    property var models: ({})
    property var describeRow: null
    property var describeCell: null
    property bool interactive: true
    signal event(var action)
    function loadedView(): var {
        return root.item;
    }

    function focusControl(name) {
        return loadedView() ? loadedView().focusControl(name) : false;
    }
    function focusGrid(id, row, column, name) {
        return loadedView() ? loadedView().focusGrid(id, row, column, name) : false;
    }
    function graphCommand(id, command) {
        return loadedView() ? loadedView().graphCommand(id, command) : null;
    }
    Component.onCompleted: setSource(Qt.resolvedUrl("FrameView.qml"), {
        theme: Qt.binding(() => root.theme),
        scene: Qt.binding(() => root.scene),
        views: Qt.binding(() => root.views),
        models: Qt.binding(() => root.models),
        describeRow: Qt.binding(() => root.describeRow),
        describeCell: Qt.binding(() => root.describeCell),
        interactive: Qt.binding(() => root.interactive)
    })
    Connections {
        target: root.item
        function onEvent(action) {
            root.event(action);
        }
    }
}
