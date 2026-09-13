import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    required property var controller
    required property var columnsController
    property var userModel: null
    required property var surfacesModel
    required property var versionResultsModel
    property bool presentationActive: visible
    readonly property bool autoCompact: width < 445
    readonly property bool compactRows:
        (autoCompact && controller.results_view_mode !== "table")
        || controller.results_view_mode === "compact"
    readonly property bool splitRight:
        !compactRows
        && controller.results_view_mode === "splitted_vertical"
    readonly property bool splitBottom:
        !compactRows
        && controller.results_view_mode === "splitted_horizontal"
    readonly property bool splitView: splitRight || splitBottom
    property string processCountMenuNodeId: ""
    property string processCountMenuPanel: ""
    property var processCountMenuAnchorItem: null
    property var processCountRootRecords: []
    property var activeResultSurface: null
    readonly property int activeResultCount: activeResultSurface
        ? activeResultSurface.resultCount : 0
    readonly property real activeResultWidth: activeResultSurface
        ? activeResultSurface.resultWidth : 0
    readonly property real activeResultHeight: activeResultSurface
        ? activeResultSurface.resultHeight : 0
    function openProcessCountMenu(nodeId, panel, anchorItem) {
        const records = root.controller.process_count_actions(nodeId, panel)
        if (records.length <= 1) {
            if (records.length > 0 && records[0].taskCode) {
                root.controller.open_process_task_details(
                    nodeId, panel, String(records[0].process || "publish"),
                    String(records[0].taskCode)
                )
            } else {
                const process = records.length > 0
                    ? String(records[0].process
                        || records[0].command || "publish") : "publish"
                root.controller.open_process_details(nodeId, panel, process)
            }
            return
        }

        processCountMenuNodeId = nodeId
        processCountMenuPanel = panel
        processCountMenuAnchorItem = anchorItem
        processCountRootRecords = records
        showProcessCountRecords(
            records, panel === "tasks" ? qsTr("Tasks") : qsTr("Notes"),
            false
        )
    }

    function showProcessCountRecords(records, title, includeBack) {
        const actions = [{
            "title": title,
            "header": true
        }]
        if (includeBack) {
            actions.push({
                "title": qsTr("All processes"),
                "translate": false,
                "icon": "arrow-left",
                "command": "back-processes",
                "keepOpen": true
            })
        }
        for (let index = 0; index < records.length; ++index)
            actions.push(records[index])
        processCountMenu.replaceActions(actions)
        if (processCountMenu.opened)
            return
        Qt.callLater(function() {
            if (root.processCountMenuAnchorItem)
                processCountMenu.openBelow(root.processCountMenuAnchorItem)
        })
    }

    function processCountAction(command) {
        const records = processCountMenu.actions || []
        for (let index = 0; index < records.length; ++index) {
            if (String(records[index].command || "") === command)
                return records[index]
        }
        return ({})
    }

    Connections {
        target: root.controller

        function onRepository_sync_changed() {
            if (itemActionMenu.opened && root.itemActionMenuNodeId)
                itemActionMenu.replaceActions(
                    root.controller.repo_sync_menu_actions(
                        root.itemActionMenuNodeId
                    )
                )
        }
    }

    color: root.theme.workspace
    clip: true

    Repeater {
        id: resultSurfaceRepeater
        model: root.surfacesModel

        delegate: SearchResultSurface {
            anchors.fill: root
            z: current ? 1 : 0
            theme: root.theme
            controller: root.controller
            columnsController: root.columnsController
            userModel: root.userModel
            presentationActive: root.presentationActive && current
            compactRows: (root.autoCompact && effectiveViewMode !== "table")
                || effectiveViewMode === "compact"
            splitRight: current && root.splitRight
            splitBottom: current && root.splitBottom
            splitView: current && root.splitView
            dividerThickness: splitDivider.thickness
            cardNavigationHeight: cardNavigation.height
            itemActionMenuVisible: itemActionMenu.visible
            itemActionMenuNodeId: root.itemActionMenuNodeId
            resultActionMenuVisible: resultsActionMenu.visible
            resultActionMenuNodeId: root.resultsActionMenuNodeId
            processCountMenuVisible: processCountMenu.visible
            processCountMenuNodeId: root.processCountMenuNodeId

            onCurrentChanged: {
                if (current)
                    root.activeResultSurface = this
                else if (root.activeResultSurface === this)
                    root.activeResultSurface = null
            }
            Component.onCompleted: {
                if (current)
                    root.activeResultSurface = this
            }
            Component.onDestruction: {
                if (root.activeResultSurface === this)
                    root.activeResultSurface = null
            }
            onInteractionStarted: {
                if (resultsActionMenu.visible)
                    resultsActionMenu.close()
                if (processCountMenu.visible)
                    processCountMenu.close()
            }
            onActionMenuRequested: function(
                selectedNodeId, menuActions, anchorItem,
                localX, localY, below
            ) {
                if (below) {
                    root.itemActionMenuNodeId = selectedNodeId
                    itemActionMenu.actions = menuActions
                    itemActionMenu.openBelow(anchorItem)
                } else {
                    root.resultsActionMenuNodeId = selectedNodeId
                    resultsActionMenu.actions = menuActions
                    resultsActionMenu.openAt(
                        anchorItem, localX, localY
                    )
                }
            }
            onProcessCountMenuRequested: function(
                selectedNodeId, panel, anchorItem
            ) {
                root.openProcessCountMenu(
                    selectedNodeId, panel, anchorItem
                )
            }
        }
    }
    property string resultsActionMenuNodeId: ""
    ActionMenu {
        id: resultsActionMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: []
        onTriggered: function(command) {
            root.controller.invoke_item_action(
                command, root.resultsActionMenuNodeId
            )
        }
        onSecondaryTriggered: function(command) {
            root.controller.invoke_item_action(
                command, root.resultsActionMenuNodeId
            )
        }
    }
    property string itemActionMenuNodeId: ""
    ActionMenu {
        id: itemActionMenu
        parent: Overlay.overlay
        theme: root.theme
        usePopupWindow: false
        preferredWidth: 212
        processPickerStyle: true
        alignBelowRight: true
        belowRightOverhang: 12
        anchorPointerVisible: true
        actions: []
        onTriggered: function(command) {
            root.controller.invoke_item_action(
                command, root.itemActionMenuNodeId
            )
        }
        onSecondaryTriggered: function(command) {
            root.controller.invoke_item_action(
                command, root.itemActionMenuNodeId
            )
        }
    }
    ActionMenu {
        id: processCountMenu
        objectName: "workspaceProcessCountMenu"
        parent: Overlay.overlay
        theme: root.theme
        usePopupWindow: false
        preferredWidth: 212
        processPickerStyle: true
        alignBelowRight: true
        belowRightOverhang: 12
        anchorPointerVisible: true
        actions: []
        onTriggered: function(command) {
            if (command === "back-processes") {
                root.showProcessCountRecords(
                    root.processCountRootRecords,
                    root.processCountMenuPanel === "tasks"
                        ? qsTr("Tasks") : qsTr("Notes"),
                    false
                )
                return
            }
            const action = root.processCountAction(command)
            if (action.taskCode) {
                root.controller.open_process_task_details(
                    root.processCountMenuNodeId,
                    root.processCountMenuPanel,
                    String(action.process || "publish"),
                    String(action.taskCode)
                )
                return
            }
            root.controller.open_process_details(
                root.processCountMenuNodeId,
                root.processCountMenuPanel,
                String(action.process || command || "publish")
            )
        }
        onSecondaryTriggered: function(command) {
            if (command.indexOf("tasks:") !== 0)
                return
            const process = command.slice(6)
            const records = root.controller.process_task_actions(
                root.processCountMenuNodeId,
                root.processCountMenuPanel,
                process
            )
            root.showProcessCountRecords(records, process, true)
        }
    }
    Rectangle {
        id: cardNavigation
        parent: root
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: visible ? 38 : 0
        visible: !root.compactRows
            && root.controller.results_view_mode === "tiles"
        color: root.theme.panel
        border.color: root.theme.separator
        Row {
            anchors.fill: parent
            anchors.leftMargin: 8
            spacing: 6
            Controls.CompactIconButton {
                anchors.verticalCenter: parent.verticalCenter
                visible: root.controller.card_can_go_back
                width: 30
                height: 30
                theme: root.theme
                iconName: "arrow-left"
                round: true
                backgroundColor: root.theme.panelRaised
                toolTip: qsTr("Back one level")
                onClicked: root.controller.leave_card_level()
            }
            Repeater {
                model: root.controller.card_breadcrumb
                delegate: Row {
                    required property var modelData
                    height: cardNavigation.height
                    spacing: 6
                    Controls.MaterialIcon {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: modelData.depth > 0
                        name: "chevron-right"
                        size: 11
                        color: root.theme.secondaryText
                    }
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: crumbRow.implicitWidth + 12
                        height: 26
                        radius: 13
                        color: crumbMouse.containsMouse
                            && modelData.depth
                                < root.controller.card_breadcrumb.length - 1
                            ? root.theme.panelRaised : "transparent"
                        Row {
                            id: crumbRow
                            anchors.centerIn: parent
                            spacing: 5
                            Controls.MaterialIcon {
                                name: modelData.icon
                                size: 13
                                color: root.theme.action
                            }
                            Label {
                                text: modelData.depth === 0
                                    ? qsTr("Search results") : modelData.title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                            }
                        }
                        MouseArea {
                            id: crumbMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            enabled: modelData.depth
                                < root.controller.card_breadcrumb.length - 1
                            cursorShape: enabled
                                ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: root.controller.open_card_breadcrumb(
                                modelData.depth)
                        }
                    }
                }
            }
        }
    }
    ContentLoadingOverlay {
        parent: root
        anchors.fill: parent
        z: 100
        visible: root.activeResultCount === 0
            && root.controller.search_state === "loading"
        theme: root.theme
        message: "Loading results…"
        cancellable: true
        onCancelRequested: root.controller.cancel_search()
    }
    Rectangle {
        parent: root
        x: Math.max(0, (root.activeResultWidth - width) / 2)
        y: Math.max(0, root.activeResultHeight - height - 12)
        width: loadingMoreRow.implicitWidth + 28
        height: 36
        radius: 18
        z: 20
        visible: root.controller.loading_more
        color: root.theme.panelRaised
        border.width: 1
        border.color: root.theme.border
        opacity: visible ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: theme.motionMedium
                easing.type: Easing.OutCubic
            }
        }
        Row {
            id: loadingMoreRow
            anchors.centerIn: parent
            spacing: 8
            Controls.BusyIndicator {
                uiTheme: root.theme
                width: 18
                height: 18
                running: parent.parent.visible
            }
            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Loading more results\u2026")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            Controls.CompactIconButton {
                anchors.verticalCenter: parent.verticalCenter
                width: 24
                height: 24
                theme: root.theme
                iconName: "close"
                round: true
                toolTip: qsTr("Cancel search")
                onClicked: root.controller.cancel_search()
            }
        }
    }
    Rectangle {
        id: versionsPane
        parent: root
        visible: root.splitView
        x: root.splitRight
            ? root.activeResultWidth + splitDivider.thickness : 0
        y: root.splitBottom
            ? root.activeResultHeight + splitDivider.thickness : 0
        width: root.splitRight
            ? Math.max(0, root.width - x) : root.width
        height: root.splitBottom
            ? Math.max(0, root.height - y) : root.height
        color: root.theme.panelDeep

        Rectangle {
            id: versionsHeader
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 36
            color: root.theme.panelRaised
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 8
                spacing: 8
                Controls.MaterialIcon {
                    name: "history"
                    size: 16
                    color: root.theme.secondaryText
                }
                Label {
                    text: qsTr("Versions")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                }
                Rectangle {
                    Layout.preferredWidth: Math.max(
                        24, versionsCount.implicitWidth + 12
                    )
                    Layout.preferredHeight: 22
                    radius: 11
                    color: root.theme.rowHover
                    Label {
                        id: versionsCount
                        anchors.centerIn: parent
                        text: versionsList.count
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                    }
                }
                Item { Layout.fillWidth: true }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: root.theme.separator
            }
        }

        ListView {
            id: versionsList
            readonly property bool interactionMoving: moving || flicking
            anchors.top: versionsHeader.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            clip: true
            spacing: 0
            model: root.versionResultsModel
            boundsBehavior: Flickable.StopAtBounds
            reuseItems: true
            onInteractionMovingChanged: {
                if (interactionMoving && versionsActionMenu.visible)
                    versionsActionMenu.close()
            }
            delegate: WorkspaceResultItem {
                theme: root.theme
                externalMenuVisible: versionsActionMenu.visible
                    && versionsPane.menuNodeId === nodeId
                selected: versionsPane.selectedVersionId === nodeId
                onActionMenuRequested: function(
                    id, actions, anchorItem, localX, localY, below
                ) {
                    versionsPane.menuNodeId = id
                    versionsActionMenu.actions = actions
                    if (below)
                        versionsActionMenu.openBelow(anchorItem)
                    else
                        versionsActionMenu.openAt(
                            anchorItem, localX, localY
                        )
                }
                onSelectedRequested: function(
                    selectedId, selectedKey, selectedType,
                    modifiers, preserveSelection
                ) {
                    versionsPane.selectedVersionId = selectedId
                    root.controller.select_version_node(selectedId)
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                id: versionsScrollBar
                theme: root.theme
            }
        }
        property string selectedVersionId: ""
        property string menuNodeId: ""
        ActionMenu {
            id: versionsActionMenu
            parent: Overlay.overlay
            theme: root.theme
            actions: []
            onTriggered: function(command) {
                root.controller.invoke_item_action(
                    command, versionsPane.menuNodeId
                )
            }
            onSecondaryTriggered: function(command) {
                root.controller.invoke_item_action(
                    command, versionsPane.menuNodeId
                )
            }
        }
    }
    Rectangle {
        id: splitDivider
        parent: root
        property real dragRatio: root.controller.results_splitter_ratio
        property int thickness: root.splitView ? 7 : 0
        readonly property real currentRatio: dividerMouse.pressed
            ? dragRatio : root.controller.results_splitter_ratio
        visible: root.splitView
        z: 20
        x: root.splitRight ? root.activeResultWidth : 0
        y: root.splitBottom ? root.activeResultHeight : 0
        width: root.splitRight ? thickness : root.width
        height: root.splitBottom ? thickness : root.height
        color: dividerMouse.containsMouse || dividerMouse.pressed
            ? root.theme.action : root.theme.separator
        opacity: dividerMouse.containsMouse || dividerMouse.pressed
            ? 0.72 : 0.55
        Behavior on color { ColorAnimation { duration: theme.hoverMotionFast } }
        Behavior on opacity { NumberAnimation { duration: theme.hoverMotionFast } }

        MouseArea {
            id: dividerMouse
            anchors.fill: parent
            anchors.margins: -3
            hoverEnabled: true
            preventStealing: true
            cursorShape: root.splitRight
                ? Qt.SizeHorCursor : Qt.SizeVerCursor
            onPressed: splitDivider.dragRatio =
                root.controller.results_splitter_ratio
            onPositionChanged: function(mouse) {
                if (!pressed)
                    return
                const point = splitDivider.mapToItem(
                    root, mouse.x, mouse.y
                )
                const extent = root.splitRight
                    ? root.width : root.height
                const position = root.splitRight
                    ? point.x : point.y
                splitDivider.dragRatio = Math.max(
                    0.25, Math.min(0.75, position / Math.max(1, extent))
                )
            }
            onReleased: root.controller.set_results_splitter_ratio(
                splitDivider.dragRatio
            )
        }
    }
    Rectangle {
        parent: root
        anchors.fill: parent
        z: 100
        visible: root.activeResultCount === 0
            && root.controller.search_state !== "idle"
            && root.controller.search_state !== "ready"
            && root.controller.search_state !== "loading"
        color: root.theme.workspace
        opacity: visible ? 0.88 : 0
        Behavior on opacity { NumberAnimation { duration: theme.motionMedium } }
        Column {
            anchors.centerIn: parent
            spacing: 10
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.controller.search_state === "error"
                    ? root.controller.search_error
                    : root.controller.search_state === "cancelled"
                        ? qsTr("Search cancelled")
                        : root.controller.search_state === "empty"
                            ? qsTr("No results found")
                            : qsTr("No results found")
                color: root.controller.search_state === "error"
                    ? root.theme.red : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                width: Math.min(420, root.width - 40)
            }
            Controls.Button {
                theme: root.theme
                anchors.horizontalCenter: parent.horizontalCenter
                text: qsTr("Retry")
                visible: root.controller.search_state !== "empty"
                onClicked: {
                    root.controller.retry_search()
                }
            }
        }
    }
}
