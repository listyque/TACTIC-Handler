import QtQuick

// Publish one complete viewport per event turn; data and actions stay synchronous.
QtObject {
    id: root
    required property Item target
    property size size: Qt.size(0, 0)

    function synchronize() {
        root.size = Qt.size(root.target.width, root.target.height);
    }
    Component.onCompleted: root.synchronize()

    readonly property Timer updateTimer: Timer {
        interval: 0
        onTriggered: root.synchronize()
    }
    readonly property Connections changes: Connections {
        target: root.target
        function onWidthChanged() {
            root.updateTimer.restart();
        }
        function onHeightChanged() {
            root.updateTimer.restart();
        }
    }
}
