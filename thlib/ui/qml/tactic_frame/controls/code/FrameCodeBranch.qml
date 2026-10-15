import QtQuick

Loader {
    id: root
    required property var theme
    required property var node
    required property var controller
    signal event(var action)
    Component.onCompleted: setSource(Qt.resolvedUrl("FrameCode.qml"), {
        theme: Qt.binding(() => root.theme),
        controller: Qt.binding(() => root.controller),
        node: Qt.binding(() => root.node)
    })
    Connections {
        target: root.item
        function onEvent(action) {
            root.event(action);
        }
    }
}
