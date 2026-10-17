pragma ComponentBehavior: Bound

import QtQuick
import "tactic_frame/features/table/cells.ui.mjs" as Cells
import QtQuick.Controls
import "controls" as Controls

Item {
    id: root
    objectName: "tableTaskCell"

    required property var theme
    required property var controller
    required property var columnsController
    required property var userModel
    required property string nodeId
    property var records: []
    property var options: ({})
    property int taskCount: 0
    property bool scrolling: false
    property bool selectedPreviewActive: false
    property bool hoverPreviewEnabled: true
    readonly property var cellLayout: Cells.taskLayout(recordCount, width, height)
    readonly property int cardSpacing: Cells.metrics.taskGap
    readonly property int cardWidth: Cells.metrics.taskWidth
    readonly property int menuWidth: Cells.metrics.taskMenu
    readonly property int recordCount: records ? records.length : 0
    readonly property int fullCardCount: Math.max(0, Math.floor((width + cardSpacing) / (cardWidth + cardSpacing)))
    readonly property bool showMenuButton: cellLayout.overflow
    readonly property int visibleCardCount: cellLayout.visible
    readonly property real visibleCardsWidth: cellLayout.visibleWidth
    readonly property int effectiveCount: Math.max(taskCount, records ? records.filter(record => Boolean(record.hasTask)).length : 0)
    readonly property real previewCardsWidth: cellLayout.previewWidth
    readonly property bool pointerHovered: cellHover.hovered || taskPreview.contentHovered
    readonly property bool hoverActive: selectedPreviewActive || pointerHovered
    signal previewHoverChanged(bool hovered)
    onPointerHoveredChanged: previewHoverChanged(pointerHovered)
    Component.onDestruction: previewHoverChanged(false)

    function openTaskPreview(pinned) {
        if (recordCount <= 0)
            return;
        previewOpenTimer.stop();
        previewCloseTimer.stop();
        taskPreview.pinned = Boolean(pinned);
        taskPreview.reopenAtItem(root, -taskPreview.leftPadding, -taskPreview.topPadding, false);
    }

    function openTaskManager() {
        previewOpenTimer.stop();
        previewCloseTimer.stop();
        taskPreview.close();
        controller.open_process_details(nodeId, "tasks", "");
    }

    function schedulePreviewClose() {
        if (!hoverActive && !taskPreview.contentHovered && !taskPreview.pinned)
            previewCloseTimer.restart();
    }

    onHoverActiveChanged: {
        if (hoverActive && hoverPreviewEnabled && showMenuButton && recordCount > 0 && !scrolling && !taskPreview.visible) {
            previewCloseTimer.stop();
            previewOpenTimer.restart();
        } else {
            previewOpenTimer.stop();
            schedulePreviewClose();
        }
    }
    onScrollingChanged: {
        if (scrolling) {
            previewOpenTimer.stop();
            taskPreview.close();
        }
    }

    clip: true

    HoverHandler {
        id: cellHover
    }

    TacticTaskCards {
        objectName: "tableInlineTaskCards"
        opacity: taskPreview.visible ? 0 : 1
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.visibleCardsWidth
        theme: root.theme
        controller: root.controller
        columnsController: root.columnsController
        userModel: root.userModel
        nodeId: root.nodeId
        records: (root.records || []).slice(0, root.visibleCardCount)
        cardWidth: root.cardWidth
        cardSpacing: root.cardSpacing
        scrolling: root.scrolling
    }

    Controls.ItemCountActionButton {
        id: taskButton
        objectName: "tableCellTasks"
        x: Math.round(root.visibleCardsWidth + (root.width - root.visibleCardsWidth - width) / 2)
        anchors.verticalCenter: parent.verticalCenter
        visible: root.showMenuButton
        opacity: taskPreview.visible ? 0 : 1
        width: 28
        height: 28
        theme: root.theme
        iconName: "tasks"
        count: root.effectiveCount
        toolTipsAllowed: !taskPreview.visible
        toolTip: qsTr("Task Manager")
        onClicked: root.openTaskManager()
    }

    Timer {
        id: previewOpenTimer
        interval: 260
        onTriggered: {
            if (root.hoverActive && root.hoverPreviewEnabled && root.showMenuButton && root.recordCount > 0 && !root.scrolling)
                root.openTaskPreview(false);
        }
    }

    Timer {
        id: previewCloseTimer
        interval: 180
        onTriggered: {
            if (!root.hoverActive && !taskPreview.contentHovered && !taskPreview.pinned)
                taskPreview.close();
        }
    }

    Controls.Popup {
        id: taskPreview
        objectName: "tableTaskCardsPreview"
        parent: Overlay.overlay
        theme: root.theme
        usePopupWindow: false
        coordinateGlobally: false
        modal: false
        focus: false
        padding: 8
        width: Math.min(root.previewCardsWidth + leftPadding + rightPadding, parent && parent.width > 0 ? Math.max(180, parent.width - 8) : root.previewCardsWidth + leftPadding + rightPadding)
        height: root.height + topPadding + bottomPadding + (root.previewCardsWidth > availableWidth ? 16 : 0)
        settledClosePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        property bool pinned: false
        property bool contentHovered: false

        onContentHoveredChanged: {
            if (contentHovered)
                previewCloseTimer.stop();
            else
                root.schedulePreviewClose();
        }
        onClosed: {
            pinned = false;
            contentHovered = false;
        }

        contentItem: Loader {
            id: previewLoader
            active: taskPreview.visible

            sourceComponent: Item {
                id: previewSurface

                HoverHandler {
                    onHoveredChanged: taskPreview.contentHovered = hovered
                }
                TapHandler {
                    onTapped: taskPreview.pinned = true
                }

                Flickable {
                    id: previewFlick
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: previewBar.hasOverflow ? previewBar.reservedExtent + 4 : 0
                    clip: true
                    contentWidth: root.previewCardsWidth
                    contentHeight: height
                    boundsBehavior: Flickable.StopAtBounds
                    flickableDirection: Flickable.HorizontalFlick

                    TacticTaskCards {
                        width: root.previewCardsWidth
                        height: previewFlick.height
                        theme: root.theme
                        controller: root.controller
                        columnsController: root.columnsController
                        userModel: root.userModel
                        nodeId: root.nodeId
                        records: root.records || []
                        cardWidth: root.cardWidth
                        cardSpacing: root.cardSpacing
                    }
                }

                Controls.ScrollBar {
                    id: previewBar
                    objectName: "tableTaskCardsPreviewScrollBar"
                    parent: previewSurface
                    orientation: Qt.Horizontal
                    theme: root.theme
                    flickableTarget: previewFlick
                }
            }
        }
    }
}
