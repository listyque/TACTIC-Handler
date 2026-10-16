import QtQuick
import QtQuick.Controls
import "__QML_ROOT__" as TH

ApplicationWindow {
    id: window
    visible: true
    width: 1100
    height: 800
    color: uiTheme.workspace
    TH.Theme {
        id: uiTheme
        dark: true
        clickAnimationsEnabled: false
        hoverAnimationsEnabled: false
        fadeAnimationsEnabled: false
        popupAnimationsEnabled: false
    }
    Item {
        id: workspace
        function focusDockTab(identity) {
            for (let index = 0; index < panels.count; index++) {
                const item = panels.itemAt(index);
                const panel = item ? item : null;
                if (!panel)
                    continue;
                const center = panel.stackPanels.some(record => record.panelId === "results");
                if (panel.focusTab(identity || (center ? panel.panelId : "")))
                    return;
            }
        }
        anchors.fill: parent
        function beginDockDrag(id) {
        }
        function updateDockDrag(id, x, y) {
        }
        function finishDockDrag(id, x, y, w, h, floating) {
        }
        function cancelDockDrag(id) {
        }
        function beginDockResize(id, orientation, boundary, start, end, shared) {
        }
        function updateDockResizeBoundary(boundary, start, end) {
        }
        function endDockResize() {
        }
        Repeater {
            id: panels
            model: dockModel
            delegate: TH.DockPanel {
                required property var model
                host: workspace
                theme: uiTheme
                panelId: model.panelId
                title: model.title
                kind: model.kind
                panelX: model.panelX
                panelY: model.panelY
                panelWidth: model.panelWidth
                panelHeight: model.panelHeight
                modelVisible: model.panelVisible && model.stackActive && !model.detached
                panelOpen: model.panelVisible && model.stackActive && !model.detached
                stackActive: model.stackActive
                closable: model.closable
                stackOrder: model.stackOrder
                dockArea: model.dockArea
                canResizeLeft: model.canResizeLeft
                canResizeRight: model.canResizeRight
                canResizeTop: model.canResizeTop
                canResizeBottom: model.canResizeBottom
                stackPanels: model.stackPanels
                stackSize: model.stackSize
                contentComponent: Component {
                    Item {}
                }
            }
        }
    }
}
