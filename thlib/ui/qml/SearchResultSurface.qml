pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import "tactic_frame/features/search/card.ui.mjs" as Card
import "tactic_frame/features/administration/layouts/layout.preview.mjs" as Composition
import QtQuick.Controls
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property var resultModel
    property var userModel: null
    property var columnsController: null
    required property bool current
    required property string viewMode
    required property real splitterRatio
    property bool presentationActive: false
    property bool compactRows: false
    property bool splitRight: false
    property bool splitBottom: false
    property bool splitView: false
    property real dividerThickness: 0
    property real cardNavigationHeight: 0
    property bool itemActionMenuVisible: false
    property string itemActionMenuNodeId: ""
    property bool resultActionMenuVisible: false
    property string resultActionMenuNodeId: ""
    property bool processCountMenuVisible: false
    property string processCountMenuNodeId: ""
    property var configuredLayout: null
    property var expansionOwner: controller
    property bool layoutEditing: false
    property string selectedLayoutElement: ""
    signal layoutElementSelected(string name)
    readonly property var itemLayout: configuredLayout || resultModel.itemLayout || null
    readonly property real screenWidth: root.Window.window ? root.Window.window.width : root.width
    readonly property real configuredTileHeight: {
        if (!itemLayout?.elements?.length || itemLayout.flow === "contents")
            return 0;
        const samples = resultModel.itemLayoutSamples || [];
        let height = Composition.maximumHeight(itemLayout, samples, itemLayout.card_width - 24, typeof localizationController === "undefined" ? "en" : localizationController.current_language, root.screenWidth) + 38;
        for (const sample of samples)
            if (!Composition.supports(itemLayout, sample, root.screenWidth))
                height = Math.max(height, Card.tileHeight({
                    kind: sample.kind,
                    compact: controller.card_compact_level
                }) + 14);
        return height;
    }

    readonly property string effectiveViewMode: layoutEditing ? (itemLayout?.collection === "grid" ? "tiles" : "continious") : current ? controller.results_view_mode : viewMode
    readonly property real effectiveSplitterRatio: current ? controller.results_splitter_ratio : splitterRatio
    readonly property real listContentY: tableViewport.visible ? tableViewport.contentY : initialResultPresentation.retainedContentY
    readonly property real tileContentY: initialTilePresentation.retainedContentY
    readonly property int resultCount: tableViewport.visible ? tableViewport.count : results.count
    readonly property real resultWidth: tableViewport.visible ? tableViewport.width : results.width
    readonly property real resultHeight: tableViewport.visible ? tableViewport.height : results.height

    signal actionMenuRequested(string nodeId, var actions, var anchorItem, real localX, real localY, bool below)
    signal processCountMenuRequested(string nodeId, string panel, var anchorItem)
    signal interactionStarted

    visible: current

    function restoreContentY(listContentY, tileContentY, listValid, tileValid) {
        initialResultPresentation.restoreContentY(listContentY, listValid);
        tableViewport.restoreContentY(listContentY, listValid);
        initialTilePresentation.restoreContentY(tileContentY, tileValid);
    }

    function revealNode(nodeId) {
        if (!root.current || !nodeId)
            return;
        const row = root.resultModel.row_for_node(nodeId);
        if (row < 0)
            return;
        Qt.callLater(function () {
            if (!root.current)
                return;
            if (tileViewport.visible)
                resultTiles.positionViewAtIndex(row, GridView.Contain);
            else if (tableViewport.visible)
                tableViewport.positionViewAtIndex(row);
            else
                results.positionViewAtIndex(row, ListView.Contain);
        });
    }

    function handleOutsidePress(sourceItem, x, y) {
        const card = resultTiles.expandedCard;
        if (!card)
            return;
        const cardPoint = card.mapFromItem(sourceItem, x, y);
        if (cardPoint.x < 0 || cardPoint.y < 0 || cardPoint.x > card.width || cardPoint.y > card.height)
            controller.clear_result_selection();
    }

    ListView {
        id: results
        objectName: "searchResultsListView"

        readonly property bool interactionMoving: moving || flicking || wheelScroll.running
        property real wheelTargetY: contentY
        property alias treeRevealGeneration: treeExpansionMotion.generation
        property alias treeRevealFirstRow: treeExpansionMotion.firstRow
        property alias treeRevealLastRow: treeExpansionMotion.lastRow
        property alias treeRevealActive: treeExpansionMotion.active
        property alias treeCollapseGeneration: treeExpansionMotion.collapseGeneration
        property alias treeCollapseFirstRow: treeExpansionMotion.collapseFirstRow
        property alias treeCollapseLastRow: treeExpansionMotion.collapseLastRow
        property alias treeCollapseActive: treeExpansionMotion.collapseActive
        property alias treeCollapseOwnerId: treeExpansionMotion.collapseOwnerId

        x: 8
        y: 8
        width: root.splitRight ? Math.max(220, Math.round((root.width - root.dividerThickness) * root.effectiveSplitterRatio)) - 12 : Math.max(0, root.width - 16)
        height: root.splitBottom ? Math.max(150, Math.round((root.height - root.dividerThickness) * root.effectiveSplitterRatio)) - 12 : Math.max(0, root.height - 16)
        opacity: initialResultPresentation.ready ? 1 : 0
        visible: root.current && (root.compactRows || (root.effectiveViewMode !== "tiles" && root.effectiveViewMode !== "table"))
        clip: true
        spacing: 3
        model: root.resultModel
        focus: root.current
        activeFocusOnTab: root.current
        boundsBehavior: Flickable.StopAtBounds
        flickDeceleration: 3600
        maximumFlickVelocity: 4800
        pixelAligned: false
        cacheBuffer: 280
        reuseItems: true

        function toggleResultNodePreservingScroll(nodeId, recursive, expanding) {
            treeExpansionMotion.toggle(nodeId, recursive, expanding);
        }

        function treeStaggerDelay(row, firstRow) {
            return treeExpansionMotion.staggerDelay(row, firstRow);
        }

        function cancelWheelScroll() {
            wheelScroll.stop();
            wheelTargetY = contentY;
        }

        function requestMoreFromScroll() {
            if (root.layoutEditing)
                return;
            if (!root.current || !atYEnd || controller.card_can_go_back || !controller.has_more || controller.loading_mode !== "infinite")
                return;
            if (!resultsScrollBar.takePaginationPermit(false))
                return;
            controller.load_more();
        }

        function scrollWithWheel(pixelDelta, angleDelta) {
            const rawDelta = pixelDelta !== 0 ? pixelDelta * 1.65 : (angleDelta / 120) * 148;
            if (rawDelta === 0)
                return;
            resultsScrollBar.armPagination();
            const minimumY = originY;
            const maximumY = Math.max(minimumY, minimumY + contentHeight - height);
            const baseY = wheelScroll.running ? wheelTargetY : contentY;
            wheelTargetY = Math.max(minimumY, Math.min(maximumY, baseY - rawDelta));
            wheelScroll.stop();
            wheelScroll.to = wheelTargetY;
            wheelScroll.start();
        }

        onInteractionMovingChanged: {
            if (interactionMoving)
                root.interactionStarted();
        }
        onFlickStarted: cancelWheelScroll()
        onContentYChanged: requestMoreFromScroll()

        Keys.onPressed: function (event) {
            if (root.layoutEditing)
                return;
            if (event.key === Qt.Key_A && (event.modifiers & Qt.ControlModifier)) {
                controller.select_all_result_siblings();
                event.accepted = true;
            }
        }

        NumberAnimation {
            id: wheelScroll
            target: results
            property: "contentY"
            duration: root.theme.scrollMotion
            easing.type: Easing.OutCubic
        }

        WheelHandler {
            target: null
            blocking: true
            onWheel: function (event) {
                results.scrollWithWheel(event.pixelDelta.y, event.angleDelta.y);
                results.requestMoreFromScroll();
                event.accepted = true;
            }
        }

        Controls.TreeExpansionMotion {
            id: treeExpansionMotion
            theme: root.theme
            enabled: root.presentationActive && results.visible
            view: results
            model: root.resultModel
            ownerRowForId: function (nodeId) {
                return root.resultModel.row_for_node(nodeId);
            }
            descendantEndRowForId: function (nodeId) {
                return root.resultModel.descendant_end_row(nodeId);
            }
            toggleNode: function (nodeId, recursive) {
                root.expansionOwner.toggle_result_node_recursive(nodeId, recursive);
            }
        }

        delegate: WorkspaceResultItem {
            required property var values
            theme: root.theme
            configuredRecord: values
            configuredLayout: root.configuredLayout || root.resultModel.itemLayout || null
            layoutEditing: root.layoutEditing
            presentationReadOnly: root.layoutEditing
            selectedLayoutElement: root.selectedLayoutElement
            onLayoutElementSelected: name => root.layoutElementSelected(name)
            controller: root.controller
            presentationActive: root.presentationActive && results.visible
            compactMode: root.compactRows
            hideVersionSnapshots: root.splitView
            externalMenuVisible: root.current && (root.itemActionMenuVisible && root.itemActionMenuNodeId === nodeId) || root.current && (root.processCountMenuVisible && root.processCountMenuNodeId === nodeId)
            selected: !root.layoutEditing && root.current && controller.selected_result_node_ids.indexOf(nodeId) >= 0
            onActionMenuRequested: function (selectedNodeId, menuActions, anchorItem, localX, localY, below) {
                root.actionMenuRequested(selectedNodeId, menuActions, anchorItem, localX, localY, below);
            }
            onSelectedRequested: function (selectedId, selectedKey, selectedType, modifiers, preserveSelection) {
                controller.select_result_node(selectedId, selectedKey, selectedType, modifiers, preserveSelection);
            }
            onProcessCountMenuRequested: function (selectedNodeId, panel, anchorItem) {
                root.processCountMenuRequested(selectedNodeId, panel, anchorItem);
            }
        }

        ScrollBar.vertical: Controls.ScrollBar {
            id: resultsScrollBar
            theme: root.theme
            flickableTarget: results
        }
    }

    Controls.InitialBatchPresentation {
        id: initialResultPresentation
        objectName: "initialResultPresentation"
        view: results
        enabled: root.presentationActive && results.visible
    }

    SearchResultTable {
        id: tableViewport
        anchors.fill: parent
        visible: root.current && !root.compactRows && root.effectiveViewMode === "table"
        theme: root.theme
        controller: root.controller
        columnsController: root.columnsController
        userModel: root.userModel
        resultModel: root.resultModel
        presentationActive: root.presentationActive && visible
        onActionMenuRequested: function (selectedNodeId, menuActions, anchorItem, localX, localY, below) {
            root.actionMenuRequested(selectedNodeId, menuActions, anchorItem, localX, localY, below);
        }
        onProcessCountMenuRequested: function (selectedNodeId, panel, anchorItem) {
            root.processCountMenuRequested(selectedNodeId, panel, anchorItem);
        }
        onVisibleChanged: {
            if (visible)
                root.interactionStarted();
        }
    }

    Item {
        id: tileViewport

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: root.cardNavigationHeight
        visible: root.current && !root.compactRows && root.effectiveViewMode === "tiles"
        clip: true
    }

    GridView {
        id: resultTiles
        objectName: "searchResultsGridView"

        property real wheelTargetY: contentY
        property var expandedCard: null
        readonly property bool interactionMoving: moving || flicking || tileWheelScroll.running

        parent: tileViewport
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 14
        anchors.topMargin: 12
        anchors.bottomMargin: 8
        opacity: initialTilePresentation.ready ? 1 : 0
        visible: tileViewport.visible
        clip: true
        model: root.resultModel
        cellWidth: root.configuredTileHeight ? root.itemLayout.card_width + 18 : 230
        cellHeight: root.configuredTileHeight || (controller.card_compact_level ? 178 : 258)
        cacheBuffer: 280
        reuseItems: true
        boundsBehavior: Flickable.StopAtBounds
        flickDeceleration: 3600
        maximumFlickVelocity: 4800

        function cancelWheelScroll() {
            tileWheelScroll.stop();
            wheelTargetY = contentY;
        }

        function requestMoreFromScroll() {
            if (root.layoutEditing)
                return;
            if (!root.current || !atYEnd || controller.card_can_go_back || !controller.has_more || controller.loading_mode !== "infinite")
                return;
            if (!resultTilesScrollBar.takePaginationPermit(false))
                return;
            controller.load_more();
        }

        function scrollWithWheel(pixelDelta, angleDelta) {
            const delta = pixelDelta !== 0 ? pixelDelta * 1.65 : (angleDelta / 120) * 148;
            if (delta === 0)
                return;
            resultTilesScrollBar.armPagination();
            const minimumY = originY;
            const maximumY = Math.max(minimumY, minimumY + contentHeight - height);
            const baseY = tileWheelScroll.running ? wheelTargetY : contentY;
            wheelTargetY = Math.max(minimumY, Math.min(maximumY, baseY - delta));
            tileWheelScroll.stop();
            tileWheelScroll.to = wheelTargetY;
            tileWheelScroll.start();
        }

        onFlickStarted: cancelWheelScroll()
        onInteractionMovingChanged: {
            if (interactionMoving)
                root.interactionStarted();
        }
        onContentYChanged: requestMoreFromScroll()

        NumberAnimation {
            id: tileWheelScroll
            target: resultTiles
            property: "contentY"
            duration: root.theme.scrollMotion
            easing.type: Easing.OutCubic
        }

        WheelHandler {
            target: null
            blocking: true
            onWheel: function (event) {
                resultTiles.scrollWithWheel(event.pixelDelta.y, event.angleDelta.y);
                resultTiles.requestMoreFromScroll();
                event.accepted = true;
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton
            // Reject card presses before grabbing, so their own controls receive them.
            onPressed: function (mouse) {
                const viewPoint = Qt.point(mouse.x, mouse.y);
                const contentPoint = Qt.point(viewPoint.x + resultTiles.contentX, viewPoint.y + resultTiles.contentY);
                const itemIndex = resultTiles.indexAt(contentPoint.x, contentPoint.y);
                const item = itemIndex >= 0 ? resultTiles.itemAtIndex(itemIndex) : null;
                if (!item)
                    return;
                const localPoint = item.mapFromItem(resultTiles, viewPoint.x, viewPoint.y);
                mouse.accepted = (localPoint.x < 0 || localPoint.y < 0 || localPoint.x > item.width || localPoint.y > item.height);
            }
            enabled: !root.layoutEditing
            onClicked: controller.clear_result_selection()
        }

        delegate: WorkspaceCard {
            required property var model
            configuredLayout: root.itemLayout
            configuredRecord: model.values
            compositionDepth: model.depth
            compositionPreviewUrl: model.previewUrl
            layoutEditing: root.layoutEditing
            selectedLayoutElement: root.selectedLayoutElement
            onLayoutElementSelected: name => root.layoutElementSelected(name)
            controller: root.controller
            presentationActive: root.presentationActive && resultTiles.visible
            width: resultTiles.cellWidth - 18
            height: configured ? configuredHeight : Card.tileHeight({
                kind: nodeType === "sobject" ? "object" : nodeType,
                compact: controller.card_compact_level
            })
            z: 1
            theme: root.theme
            externalMenuVisible: root.current && (root.itemActionMenuVisible && root.itemActionMenuNodeId === nodeId) || root.current && (root.processCountMenuVisible && root.processCountMenuNodeId === nodeId)
            selected: !root.layoutEditing && root.current && controller.selected_result_node_ids.indexOf(nodeId) >= 0
            onActionMenuRequested: function (selectedNodeId, menuActions, anchorItem, localX, localY, below) {
                root.actionMenuRequested(selectedNodeId, menuActions, anchorItem, localX, localY, below);
            }
            onProcessCountMenuRequested: function (selectedNodeId, panel, anchorItem) {
                root.processCountMenuRequested(selectedNodeId, panel, anchorItem);
            }
            onExpandedChanged: {
                if (expanded)
                    resultTiles.expandedCard = this;
                else if (resultTiles.expandedCard === this)
                    resultTiles.expandedCard = null;
            }
            Component.onDestruction: {
                if (resultTiles.expandedCard === this)
                    resultTiles.expandedCard = null;
            }
        }

        ScrollBar.vertical: Controls.ScrollBar {
            id: resultTilesScrollBar
            theme: root.theme
            flickableTarget: resultTiles
        }
    }

    Controls.InitialBatchPresentation {
        id: initialTilePresentation
        objectName: "initialTilePresentation"
        view: resultTiles
        enabled: root.presentationActive && resultTiles.visible
    }
}
