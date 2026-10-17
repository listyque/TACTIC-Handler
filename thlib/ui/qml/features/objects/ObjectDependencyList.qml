import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/objects/delete.ui.mjs" as UI

ListView {
    id: root
    required property var theme
    required property var rows
    property var frameNode
    property real pendingOffset: -1
    function replaceRows() {
        if (pendingOffset < 0)
            pendingOffset = contentY;
        model = rows;
        Qt.callLater(restoreOffset);
    }
    function restoreOffset() {
        if (pendingOffset < 0)
            return;
        contentY = Math.max(0, Math.min(pendingOffset, contentHeight - height));
        pendingOffset = -1;
    }
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    onRowsChanged: replaceRows()
    Component.onCompleted: replaceRows()
    delegate: Frame.FrameView {
        required property var modelData
        width: ListView.view.width
        height: UI.dependencyHeight(modelData)
        theme: root.theme
        scene: UI.dependency(modelData, width)
    }
    ScrollBar.vertical: Controls.ScrollBar {
        theme: root.theme
        flickableTarget: root
    }
}
