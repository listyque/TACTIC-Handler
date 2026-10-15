import QtQuick

// The URL loader owns its bindings, independent of the delegate creation context.
Loader {
    id: root
    required property var theme
    required property var node
    property var sourceModel
    property var describeCell
    signal event(var action)
    function loadedView(): var {return root.item}
    function focusGrid(id, row, column, name) {return loadedView() ? loadedView().focusGrid(id, row, column, name) : false}
    Component.onCompleted: setSource(Qt.resolvedUrl("FrameGrid.qml"), {
        theme: Qt.binding(() => root.theme), node: Qt.binding(() => root.node),
        sourceModel: Qt.binding(() => root.sourceModel), describeCell: Qt.binding(() => root.describeCell)
    })
    Connections {target: root.item; function onEvent(action) {root.event(action)}}
}
