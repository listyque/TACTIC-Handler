pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Window
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
    readonly property var previewSizing: Cells.taskPreviewLayout(recordCount, Window.window ? Window.window.width : width, Window.window ? Window.window.height : height, theme.style)
    readonly property real previewCardsWidth: previewSizing.contentWidth
    readonly property var preview: popupLoader.item
    readonly property bool previewVisible: Boolean(preview && preview.visible)
    readonly property bool inlineHovered: cellHover.hovered && Cells.taskCardsHovered(cellHover.point.position.x, cellHover.point.position.y, visibleCardsWidth, height)
    readonly property bool pointerHovered: inlineHovered || Boolean(preview && preview.contentHovered)
    readonly property bool hoverActive: pointerHovered

    function openTaskPreview(pinned) {
        if (recordCount <= 0)
            return;
        previewOpenTimer.stop();
        previewCloseTimer.stop();
        popupLoader.active = true;
        preview.pinned = Boolean(pinned);
        preview.reopenAtItem(root, -preview.leftPadding, -preview.topPadding, false);
    }

    function openTaskManager() {
        previewOpenTimer.stop();
        previewCloseTimer.stop();
        if (preview)
            preview.close();
        controller.open_process_details(nodeId, "tasks", "");
    }

    function schedulePreviewClose() {
        if (!hoverActive && preview && !preview.contentHovered && !preview.pinned)
            previewCloseTimer.restart();
    }

    onHoverActiveChanged: {
        if (hoverActive && hoverPreviewEnabled && showMenuButton && recordCount > 0 && !scrolling && !previewVisible) {
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
            if (preview)
                preview.close();
        }
    }

    clip: true

    HoverHandler {
        id: cellHover
    }

    TacticTaskCards {
        objectName: "tableInlineTaskCards"
        opacity: previewVisible ? 0 : 1
        enabled: !root.previewVisible
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
        opacity: previewVisible ? 0 : 1
        enabled: !root.previewVisible
        width: 28
        height: 28
        theme: root.theme
        iconName: "tasks"
        count: root.effectiveCount
        toolTipsAllowed: !previewVisible
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
            if (!root.hoverActive && preview && !preview.contentHovered && !preview.pinned)
                preview.close();
        }
    }

    Loader {
        id: popupLoader
        active: false
        sourceComponent: Controls.Popup {
            id: taskPreview
            objectName: "tableTaskCardsPreview"
            parent: Overlay.overlay
            theme: root.theme
            usePopupWindow: false
            coordinateGlobally: false
            modal: false
            focus: false
            margins: 8
            padding: root.previewSizing.padding
            width: root.previewSizing.width
            height: root.previewSizing.height
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
                        parent: taskPreview.contentItem ? taskPreview.contentItem.parent : null
                        onHoveredChanged: taskPreview.contentHovered = hovered
                    }
                    TapHandler {
                        onTapped: taskPreview.pinned = true
                    }

                    Item {
                        id: previewScrollSurface
                        anchors.fill: parent
                        anchors.bottomMargin: root.previewSizing.footerHeight
                        Flickable {
                            id: previewFlick
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 0
                            anchors.rightMargin: previewVerticalBar.hasOverflow ? previewVerticalBar.reservedExtent + 4 : 0
                            clip: true
                            contentWidth: root.previewCardsWidth
                            contentHeight: root.previewSizing.contentHeight
                            boundsBehavior: Flickable.StopAtBounds
                            flickableDirection: Flickable.VerticalFlick

                            TacticTaskCards {
                                width: root.previewCardsWidth
                                height: root.previewSizing.contentHeight
                                theme: root.theme
                                controller: root.controller
                                columnsController: root.columnsController
                                userModel: root.userModel
                                nodeId: root.nodeId
                                records: root.records || []
                                cardWidth: root.previewSizing.cardWidth
                                cardSpacing: root.previewSizing.gap
                                columns: root.previewSizing.columns
                                scrolling: previewFlick.moving
                                expanded: true
                            }
                            ScrollBar.vertical: Controls.ScrollBar {
                                id: previewVerticalBar
                                objectName: "tableTaskCardsPreviewVerticalScrollBar"
                                parent: previewScrollSurface
                                orientation: Qt.Vertical
                                theme: root.theme
                                flickableTarget: previewFlick
                            }
                        }
                    }
                    Item {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: root.previewSizing.footerHeight
                        Rectangle {
                            width: parent.width
                            height: 1
                            color: root.theme.outlineVariant
                        }
                        Controls.Button {
                            objectName: "tableTaskPreviewManager"
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            width: Math.min(implicitWidth, parent.width)
                            height: 28
                            theme: root.theme
                            text: qsTr("Task Manager") + (root.effectiveCount ? " · " + root.effectiveCount : "")
                            icon.name: "tasks"
                            font.pointSize: Controls.Typography.caption
                            onClicked: root.openTaskManager()
                        }
                    }
                }
            }
        }
    }
}
