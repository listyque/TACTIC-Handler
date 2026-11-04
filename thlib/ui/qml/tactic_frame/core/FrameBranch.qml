import QtQuick

// A URL loader breaks QML's static recursive-type restriction for child scenes.
Loader {
    id: root
    objectName: "frameBranch"
    required property var theme
    property var scene: ({
            nodes: []
        })
    active: !!scene.nodes && scene.nodes.length > 0
    property var views: ({})
    property var models: ({})
    property var describeRow: null
    property var describeCell: null
    property bool interactive: true
    property bool rowInteraction: false
    signal event(var action, var source)
    function loadedView(): var {
        return root.item;
    }

    function focusControl(name) {
        return loadedView() ? loadedView().focusControl(name) : false;
    }
    function focusListRow(id, row, controlId) {
        return loadedView() ? loadedView().focusListRow(id, row, controlId) : false;
    }
    function focusGrid(id, row, column, name) {
        return loadedView() ? loadedView().focusGrid(id, row, column, name) : false;
    }
    function graphCommand(id, command) {
        return loadedView() ? loadedView().graphCommand(id, command) : null;
    }
    property bool completed: false
    function loadBranch() {
        if (!completed || !active || item)
            return;
        setSource(Qt.resolvedUrl("FrameView.qml"), {
            theme: Qt.binding(() => root.theme),
            scene: Qt.binding(() => root.scene),
            views: Qt.binding(() => root.views),
            models: Qt.binding(() => root.models),
            describeRow: Qt.binding(() => root.describeRow),
            describeCell: Qt.binding(() => root.describeCell),
            interactive: Qt.binding(() => root.interactive),
            rowInteraction: Qt.binding(() => root.rowInteraction)
        });
    }
    onActiveChanged: loadBranch()
    Component.onCompleted: {
        completed = true;
        loadBranch();
    }
    Connections {
        target: root.item
        function onEvent(action, source) {
            root.event(action, source);
        }
    }
}
