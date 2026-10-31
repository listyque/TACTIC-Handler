pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "tactic_frame" as Frame
import "features/table" as Table
import "tactic_frame/features/table/nested.ui.mjs" as Nested
import "tactic_frame/features/table/columns.mjs" as TableColumnLayout
import "tactic_frame/features/table/host.ui.mjs" as TableHost
import "tactic_frame/features/table/parent.ui.mjs" as ParentUI
import "tactic_frame/features/table/cells.ui.mjs" as Cells

Item {
    id: root
    required property var theme
    required property var controller
    required property var resultModel
    required property var columnsController
    property var selectionOwner: controller
    property bool selectable: true
    readonly property var checkedIds: selectionOwner ? selectionOwner.selected_result_node_ids : []
    property var userModel: null
    property var tableServices: typeof tableServicesController === "undefined" ? null : tableServicesController
    Component {
        id: nestedTableComponent
        Table.NestedTableView {
            theme: root.theme
            controller: root.controller
            columnsController: root.columnsController
            userModel: root.userModel
            services: root.tableServices
            administration: typeof administrationController === "undefined" ? null : administrationController
            onClosed: root.tableServices.close_nested(scope)
        }
    }
    property var focusedNestedView: null
    readonly property var nestedFocusBounds: {
        const view = focusedNestedView;
        if (!view || !view.parent)
            return null;
        return {
            x: rows.x,
            y: rows.y + view.parent.y + view.y - rows.contentY,
            width: view.width,
            height: view.height
        };
    }
    Frame.FrameBranch {
        objectName: "nestedFocusLayer"
        anchors.fill: parent
        z: 10
        theme: root.theme
        scene: Nested.focusScene(root.nestedFocusBounds, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        onEvent: action => {
            if (action.type === "close" && root.focusedNestedView)
                root.focusedNestedView.closed();
        }
    }
    property bool presentationActive: false
    property var widthOverrides: ({})
    property bool autoFitColumns: false
    property bool scrollColumns: false
    property real rowHeight: 58
    property bool automaticRowHeight: false
    readonly property var columns: columnsController ? columnsController.visibleColumns : []
    readonly property real availableColumnWidth: Math.max(0, rows.width - selectionColumnWidth - actionColumnWidth)
    readonly property var tableLayout: TableHost.describe({
        columns: columns,
        overrides: widthOverrides,
        autoFit: autoFitColumns,
        scrollColumns: scrollColumns,
        rowHeight: rowHeight,
        automaticRowHeight: automaticRowHeight
    }, rows.width)
    readonly property var effectiveColumns: tableLayout.columns
    readonly property var fitWidthOverrides: tableLayout.fitted
    readonly property bool columnsBusy: Boolean(columnsController && columnsController.busy)
    readonly property bool columnsDirty: Boolean(columnsController && columnsController.dirty)
    readonly property string columnsError: columnsController ? String(columnsController.error || "") : ""
    readonly property bool hasThumbnailColumn: TableColumnLayout.hasKind(effectiveColumns, "thumbnail")
    readonly property real thumbnailColumnWidth: TableColumnLayout.widthForKind(effectiveColumns, "thumbnail", widthOverrides, fitWidthOverrides)
    readonly property real effectiveRowHeight: tableLayout.rowHeight
    readonly property real headerHeight: TableHost.metrics.header
    readonly property real selectionColumnWidth: TableHost.metrics.selection
    readonly property real actionColumnWidth: TableHost.metrics.actions
    readonly property real columnsWidth: TableColumnLayout.totalWidth(effectiveColumns, widthOverrides, fitWidthOverrides)
    readonly property real tableWidth: tableLayout.width
    readonly property var summaryRow: {
        const empty = TableHost.summarize(effectiveColumns, []);
        if (!empty.hasSummary || !columnsController || !columnsController.all_cells)
            return empty;
        const cells = columnsController.all_cells(columnsController.cellRevision);
        return TableHost.summarize(effectiveColumns, Object.keys(cells).map(key => ({
                    __search_key__: key
                })), cells, "bottom");
    }
    readonly property real contentY: initialTablePresentation.retainedContentY
    readonly property int count: rows.count
    signal actionMenuRequested(string nodeId, var actions, var anchorItem, real localX, real localY, bool below)
    signal processCountMenuRequested(string nodeId, string panel, var anchorItem)
    function displayText(value) {
        return value === undefined || value === null ? "" : String(value);
    }

    function initials(value) {
        const parts = String(value || "").trim().split(/\s+/);
        if (!parts.length || !parts[0])
            return "?";
        return String(parts[0][0] + (parts.length > 1 ? parts[1][0] : "")).toUpperCase();
    }

    function columnWidth(column) {
        return TableColumnLayout.resolvedWidth(column, widthOverrides, fitWidthOverrides);
    }

    function setWidthOverride(name, width) {
        autoFitColumns = false;
        const next = Object.assign({}, widthOverrides);
        next[String(name || "")] = TableHost.boundedWidth(width);
        widthOverrides = next;
    }

    function clearWidthOverride(name) {
        const next = Object.assign({}, widthOverrides);
        delete next[String(name || "")];
        widthOverrides = next;
    }

    function commitColumnWidth(column, width) {
        if (!columnsController || columnsBusy)
            return;
        columnsController.set_width(Number(column.row), Math.round(TableHost.boundedWidth(width)));
        columnsController.apply();
    }

    function openColumnsEditor(row, target) {
        columnsController.request_column_focus(row === undefined ? -1 : Number(row), String(target || "definition"));
        controller.open_columns_editor();
    }

    function requestActionMenu(nodeId, anchorItem, x, y, below) {
        actionMenuRequested(nodeId, controller.item_menu_actions(nodeId), anchorItem, x, y, below);
    }

    function restoreContentY(value, valid) {
        initialTablePresentation.restoreContentY(value, valid);
    }

    function positionViewAtIndex(row) {
        rows.positionViewAtIndex(row, ListView.Contain);
    }

    onVisibleChanged: {
        if (visible && columnsController) {
            widthOverrides = ({});
            columnsController.begin_session();
        }
    }
    Component.onCompleted: {
        if (visible && columnsController)
            columnsController.begin_session();
    }

    Connections {
        target: root.columnsController

        function onStateChanged() {
            if (!root.columnsBusy && !root.columnsDirty)
                root.widthOverrides = TableColumnLayout.acknowledgedWidths(root.columns, root.widthOverrides);
        }
    }

    Loader {
        id: selectionActions
        objectName: "tableSelectionActions"
        anchors.top: parent.top
        width: parent.width
        height: active ? 36 : 0
        active: root.checkedIds.length > 0
        sourceComponent: Rectangle {
            color: root.theme.contentSelection

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 8

                Controls.Button {
                    objectName: "clearTableSelection"
                    theme: root.theme
                    implicitHeight: 28
                    text: (root.checkedIds.length === 1 ? qsTr("Deselect %1 item") : qsTr("Deselect %1 items")).arg(root.checkedIds.length)
                    onClicked: root.selectionOwner.clear_result_selection()
                }
                Item {
                    Layout.fillWidth: true
                }
            }
        }
    }

    Item {
        id: scrollBarFrame
        anchors.fill: parent
        anchors.margins: 0
        anchors.topMargin: selectionActions.height + (taskDraftActions.visible ? taskDraftActions.height + 12 : 0)
    }

    Loader {
        id: taskDraftActions
        objectName: "tableTaskDraftActions"
        anchors.top: selectionActions.bottom
        anchors.right: parent.right
        anchors.margins: 8
        active: Number(root.columnsController ? root.columnsController.dirtyTaskCount || 0 : 0) > 0
        visible: active
        sourceComponent: RowLayout {
            spacing: 8

            Label {
                text: Number(root.columnsController ? root.columnsController.dirtyTaskCount || 0 : 0) + qsTr(" unsaved")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
            }
            Controls.CompactIconButton {
                objectName: "discardTableTaskChanges"
                theme: root.theme
                iconName: "undo"
                toolTip: qsTr("Reset task changes")
                enabled: !root.columnsBusy
                onClicked: root.columnsController.discard_task_changes()
            }
            Controls.CompactIconButton {
                objectName: "saveTableTaskChanges"
                theme: root.theme
                iconName: "save"
                iconColor: root.theme.action
                toolTip: qsTr("Save task changes")
                enabled: !root.columnsBusy
                onClicked: root.columnsController.save_task_changes()
            }
        }
    }

    ListView {
        id: rows
        objectName: "searchResultsTableView"
        anchors.fill: parent
        anchors.margins: 0
        anchors.topMargin: scrollBarFrame.y
        opacity: initialTablePresentation.ready ? 1 : 0
        model: initialTablePresentation.activated ? root.resultModel : null
        clip: true
        spacing: 0
        reuseItems: true
        cacheBuffer: Math.max(80, root.effectiveRowHeight * 1.5)
        currentIndex: -1
        keyNavigationEnabled: false
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: Flickable.AutoFlickDirection
        contentWidth: root.tableWidth
        headerPositioning: ListView.OverlayHeader
        activeFocusOnTab: root.visible
        focus: root.visible

        function requestMoreFromScroll() {
            if (!atYEnd || !root.controller.has_more || root.controller.loading_mode !== "infinite" || !verticalBar.takePaginationPermit(false))
                return;
            root.controller.load_more();
        }

        function selectRow(index, modifiers) {
            if (count <= 0)
                return;
            currentIndex = Math.max(0, Math.min(count - 1, index));
            positionViewAtIndex(currentIndex, ListView.Contain);
            Qt.callLater(function () {
                const item = rows.itemAtIndex(rows.currentIndex);
                if (item)
                    item.selectWithModifiers(modifiers);
            });
        }

        function openCurrent() {
            const item = itemAtIndex(currentIndex);
            if (item)
                item.activate(0);
        }

        onContentYChanged: requestMoreFromScroll()

        Keys.onPressed: function (event) {
            if (event.key === Qt.Key_A && (event.modifiers & Qt.ControlModifier)) {
                root.selectionOwner.select_all_result_siblings();
                event.accepted = true;
            } else if (event.key === Qt.Key_Up) {
                selectRow(currentIndex < 0 ? 0 : currentIndex - 1, event.modifiers);
                event.accepted = true;
            } else if (event.key === Qt.Key_Down) {
                selectRow(currentIndex < 0 ? 0 : currentIndex + 1, event.modifiers);
                event.accepted = true;
            } else if (event.key === Qt.Key_Home) {
                selectRow(0, event.modifiers);
                event.accepted = true;
            } else if (event.key === Qt.Key_End) {
                selectRow(count - 1, event.modifiers);
                event.accepted = true;
            } else if (event.key === Qt.Key_Space) {
                if (currentIndex < 0)
                    selectRow(0, event.modifiers);
                else {
                    const item = itemAtIndex(currentIndex);
                    if (item && item.isGroup)
                        item.activate(event.modifiers);
                    else
                        selectRow(currentIndex, event.modifiers);
                }
                event.accepted = true;
            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                openCurrent();
                event.accepted = true;
            }
        }

        header: SearchResultTableHeader {
            z: 3
            width: root.tableWidth
            height: root.headerHeight
            theme: root.theme
            controller: root.controller
            selectionOwner: root.selectionOwner
            tableScope: root.selectionOwner !== root.controller ? root.selectionOwner : null
            selectable: root.selectable
            tableServices: root.tableServices
            columnsController: root.columnsController
            columns: root.effectiveColumns
            selectedIds: root.checkedIds
            columnsBusy: root.columnsBusy
            columnsError: root.columnsError
            rowCount: root.resultModel ? root.resultModel.selectableCount : 0
            rowHeight: root.rowHeight
            automaticRowHeight: root.automaticRowHeight
            viewportContentX: rows.contentX
            viewportWidth: rows.width
            selectionColumnWidth: root.selectionColumnWidth
            actionColumnWidth: root.actionColumnWidth
            columnWidthProvider: root.columnWidth
            widthOverrides: root.widthOverrides
            autoFitColumns: root.autoFitColumns
            scrollColumns: root.scrollColumns
            onScrollColumnsRequested: {
                root.scrollColumns = !root.scrollColumns;
                root.autoFitColumns = false;
            }
            onAutoFitRequested: {
                root.autoFitColumns = !root.autoFitColumns;
                root.scrollColumns = false;
            }
            onWidthPreviewRequested: (name, width) => root.setWidthOverride(name, width)
            onWidthClearRequested: name => root.clearWidthOverride(name)
            onWidthCommitRequested: (column, width) => root.commitColumnWidth(column, width)
            onColumnsEditorRequested: (row, target) => root.openColumnsEditor(row, target)
            onRowHeightRequested: function (height) {
                root.automaticRowHeight = height <= 0;
                if (height > 0)
                    root.rowHeight = height;
            }
            onSelectAllRequested: selected => {
                if (!selected) {
                    root.selectionOwner.clear_result_selection();
                } else if (rows.currentIndex < 0) {
                    rows.selectRow(0, 0);
                    Qt.callLater(function () {
                        root.selectionOwner.select_all_result_siblings();
                    });
                } else {
                    root.selectionOwner.select_all_result_siblings();
                }
            }
        }

        delegate: Item {
            id: resultRow
            objectName: "searchResultTableRow"
            required property int index
            required property string nodeId
            required property string nodeType
            required property string searchKey
            required property string itemCode
            required property string title
            required property int comments
            required property int tasks
            required property var values
            required property string accent
            required property string previewUrl
            required property bool previewRequested
            required property bool previewRevealed
            required property bool expanded
            required property int childCount
            property bool viewPooled: false
            readonly property var nestedScope: root.tableServices ? root.tableServices.nested_row(nodeId, root.tableServices.nestedRevision) : null
            readonly property real nestedHeight: nestedScope ? Nested.extent(nestedScope.model, rows.width, Math.max(0, rows.height - root.headerHeight - root.effectiveRowHeight)) : 0
            property var nestedView: null
            function updateNestedView() {
                if (nestedScope && inVerticalViewport && !viewPooled) {
                    if (!nestedView) {
                        nestedView = nestedTableComponent.createObject(resultRow, {
                            scope: nestedScope,
                            height: Qt.binding(() => resultRow.nestedHeight),
                            y: Qt.binding(() => root.effectiveRowHeight),
                            x: Qt.binding(() => rows.contentX),
                            width: Qt.binding(() => Math.max(0, rows.width))
                        });
                        root.focusedNestedView = nestedView;
                    } else
                        nestedView.scope = nestedScope;
                } else if (nestedView) {
                    if (root.focusedNestedView === nestedView)
                        root.focusedNestedView = null;
                    nestedView.destroy();
                    nestedView = null;
                }
            }
            Component.onDestruction: {
                if (root.focusedNestedView === nestedView)
                    root.focusedNestedView = null;
            }
            onNestedScopeChanged: updateNestedView()
            onInVerticalViewportChanged: updateNestedView()
            onViewPooledChanged: updateNestedView()
            readonly property bool isGroup: nodeType === "group"
            readonly property var parentGroup: isGroup ? values.parentGroup || null : null
            readonly property bool active: !isGroup && root.selectionOwner && root.selectionOwner.selected_node_id === nodeId
            readonly property bool selected: !isGroup && root.checkedIds.indexOf(nodeId) >= 0
            readonly property bool inVerticalViewport: y + height >= rows.contentY && y <= rows.contentY + rows.height
            readonly property bool previewActive: root.presentationActive && root.hasThumbnailColumn && !isGroup && inVerticalViewport && !viewPooled
            readonly property var nativeCells: !isGroup && root.columnsController ? root.columnsController.row_cells(searchKey, root.columnsController.cellRevision) : ({})
            readonly property real actionX: Math.max(0, rows.contentX + rows.width - root.actionColumnWidth)
            width: root.tableWidth
            height: isGroup ? (parentGroup ? ParentUI.groupHeight : TableHost.metrics.group) : root.effectiveRowHeight + nestedHeight
            focus: ListView.isCurrentItem && rows.activeFocus
            Accessible.role: isGroup ? Accessible.Button : Accessible.ListItem
            Accessible.name: isGroup ? title + " · " + childCount : title
            Accessible.selected: selected || active

            function cellRecord(columnName) {
                const nativeCell = nativeCells ? nativeCells[columnName] : undefined;
                if (nativeCell)
                    return nativeCell;
                const value = values ? values[columnName] : undefined;
                if (value !== undefined && value !== null)
                    return {
                        "text": String(value)
                    };
                if (columnName === "code")
                    return {
                        "text": itemCode
                    };
                if (columnName === "name" || columnName === "title")
                    return {
                        "text": title
                    };
                return {
                    "text": ""
                };
            }

            function selectWithModifiers(modifiers) {
                if (isGroup)
                    return;
                root.selectionOwner.select_result_node(nodeId, searchKey, nodeType, modifiers, false);
            }

            function activate(modifiers) {
                if (isGroup)
                    root.selectionOwner.toggle_result_node(nodeId);
                else
                    root.controller.handle_item_double_click(nodeId, modifiers);
            }

            function requestPreviewIfNeeded() {
                if (previewActive && !previewRequested && !previewUrl)
                    root.controller.request_item_preview(nodeId);
            }

            Component.onCompleted: requestPreviewIfNeeded()
            onPreviewActiveChanged: requestPreviewIfNeeded()
            onPreviewUrlChanged: requestPreviewIfNeeded()
            onPreviewRequestedChanged: requestPreviewIfNeeded()
            ListView.onPooled: viewPooled = true
            ListView.onReused: {
                viewPooled = false;
                requestPreviewIfNeeded();
            }

            Controls.ItemSurface {
                id: rowSurface
                objectName: "searchResultTableRowSurface"
                anchors.fill: parent
                anchors.bottomMargin: resultRow.nestedHeight
                theme: root.theme
                selected: resultRow.selected || resultRow.active || resultRow.activeFocus
                normalColor: rowHover.hovered ? root.theme.rowHover : resultRow.isGroup ? root.theme.surfaceContainerHigh : root.theme[resultRow.index % 2 ? TableHost.paint.alternateRow : TableHost.paint.row]
                separatorVisible: false
                railVisible: false
                animateStateChanges: !rows.moving
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                y: root.effectiveRowHeight - 1
                height: 1
                color: root.theme[TableHost.paint.divider]
            }

            MouseArea {
                anchors.fill: parent
                anchors.bottomMargin: resultRow.nestedHeight
                acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                cursorShape: Qt.PointingHandCursor

                onClicked: function (mouse) {
                    rows.currentIndex = resultRow.index;
                    rows.forceActiveFocus();
                    if (resultRow.isGroup) {
                        if (mouse.button === Qt.LeftButton)
                            resultRow.activate(mouse.modifiers);
                        return;
                    }
                    root.selectionOwner.select_result_node(resultRow.nodeId, resultRow.searchKey, resultRow.nodeType, mouse.modifiers, !(mouse.modifiers & Qt.ShiftModifier));
                    if (mouse.button === Qt.RightButton) {
                        root.requestActionMenu(resultRow.nodeId, resultRow, mouse.x, mouse.y, false);
                    } else if (mouse.button === Qt.MiddleButton) {
                        root.controller.invoke_item_action("new_tab", resultRow.nodeId);
                    }
                }
                onDoubleClicked: function (mouse) {
                    if (mouse.button === Qt.LeftButton && !resultRow.isGroup)
                        resultRow.activate(mouse.modifiers);
                }
            }

            Row {
                anchors.left: parent.left
                anchors.leftMargin: root.selectionColumnWidth
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: resultRow.nestedHeight
                visible: !resultRow.isGroup

                Repeater {
                    model: resultRow.isGroup ? [] : root.effectiveColumns
                    delegate: Item {
                        id: cellDelegate
                        required property int index
                        required property var modelData
                        property bool editing: false
                        // Detach the QVariant once instead of traversing it in every value binding.
                        readonly property var cell: Object.assign({}, resultRow.cellRecord(String(modelData.name || "")))
                        readonly property string kind: String(cell.kind || modelData.kind || "text")
                        readonly property string textValue: root.displayText(cell.text)
                        readonly property bool inHorizontalViewport: {
                            const left = x + root.selectionColumnWidth;
                            return left + width >= rows.contentX && left <= rows.contentX + rows.width - root.actionColumnWidth;
                        }
                        width: root.columnWidth(modelData)
                        height: root.effectiveRowHeight
                        z: editing ? 10 : 0

                        Loader {
                            id: cellDisplay
                            anchors.fill: parent
                            active: cellDelegate.inHorizontalViewport && !cellDelegate.editing

                            sourceComponent: TacticTableCellDisplay {
                                id: taskCellDisplay
                                theme: root.theme
                                controller: root.controller
                                selectionOwner: root.selectionOwner
                                tableServices: root.tableServices
                                columnsController: root.columnsController
                                userModel: root.userModel
                                nodeId: resultRow.nodeId
                                kind: cellDelegate.kind
                                cell: cellDelegate.cell
                                textValue: cellDelegate.textValue
                                columnIndex: cellDelegate.index
                                fieldName: cellDelegate.modelData.name || ""
                                previewActive: resultRow.previewActive
                                previewUrl: resultRow.previewUrl
                                previewRevealed: resultRow.previewRevealed
                                title: root.initials(resultRow.title)
                                accent: resultRow.accent
                                comments: resultRow.comments
                                tasks: resultRow.tasks
                                displayOptions: Cells.presentationOptions(cellDelegate.modelData.displayOptions || ({}), cellDelegate.modelData.attributes || ({}))
                                widgetClass: cellDelegate.modelData.widgetClass || cellDelegate.modelData.resolvedClass || ""
                                effectsEnabled: !rows.moving
                                scrolling: rows.moving
                                onProcessCountMenuRequested: function (panel, anchorItem) {
                                    root.processCountMenuRequested(resultRow.nodeId, panel, anchorItem);
                                }
                            }
                        }
                        Loader {
                            id: inlineEditorLoader
                            anchors.fill: parent
                            z: 4
                            active: Boolean(cellDelegate.modelData.editable) && (cellDelegate.inHorizontalViewport || cellDelegate.editing)

                            sourceComponent: TacticTableInlineEditor {
                                theme: root.theme
                                controller: root.controller
                                columnsController: root.columnsController
                                nodeId: resultRow.nodeId
                                columnName: String(cellDelegate.modelData.name || "")
                                editable: true
                                pooled: resultRow.viewPooled
                                onEditingChanged: cellDelegate.editing = editing
                                onSelectRequested: {
                                    rows.currentIndex = resultRow.index;
                                    root.selectionOwner.select_result_node(resultRow.nodeId, resultRow.searchKey, resultRow.nodeType, 0, true);
                                }
                                onFocusTableRequested: rows.forceActiveFocus()
                            }
                        }
                    }
                }
            }

            Loader {
                id: groupRowLoader
                x: rows.contentX + 12
                anchors.verticalCenter: parent.verticalCenter
                width: Math.max(0, rows.width - 24)
                height: parent.height
                active: resultRow.isGroup

                sourceComponent: resultRow.parentGroup ? parentGroupComponent : ordinaryGroupComponent
            }
            Component {
                id: parentGroupComponent
                Table.ParentGroupHeader {
                    width: groupRowLoader.width
                    height: groupRowLoader.height
                    theme: root.theme
                    model: ({
                            cell: resultRow.parentGroup,
                            count: resultRow.childCount,
                            closed: !resultRow.expanded
                        })
                    editable: root.controller.can_manage_tools
                    server: root.controller.server_url || ""
                    onToggleRequested: {
                        rows.currentIndex = resultRow.index;
                        rows.forceActiveFocus();
                        resultRow.activate(0);
                    }
                    onCreateRequested: root.tableServices.parentGroups.create_child(resultRow.parentGroup)
                }
            }
            Component {
                id: ordinaryGroupComponent
                Row {
                    objectName: "searchResultTableGroupRow"
                    width: groupRowLoader.width
                    spacing: 8

                    Controls.MaterialIcon {
                        anchors.verticalCenter: parent.verticalCenter
                        name: resultRow.expanded ? "expand_more" : "chevron_right"
                        size: 20
                        color: root.theme.secondaryText
                    }
                    Label {
                        objectName: "searchResultTableGroupTitle"
                        anchors.verticalCenter: parent.verticalCenter
                        width: Math.max(0, parent.width - 72)
                        text: resultRow.title
                        elide: Text.ElideRight
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                    }
                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        text: resultRow.childCount
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                }
            }

            HoverHandler {
                id: rowHover
                cursorShape: Qt.PointingHandCursor
            }
            Rectangle {
                objectName: "tableSelectionSurface"
                border.width: 0
                x: rows.contentX
                width: root.selectionColumnWidth
                height: root.effectiveRowHeight - 1
                z: 4
                color: rowSurface.interactionColor
                visible: !resultRow.isGroup

                Rectangle {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: 3
                    height: root.effectiveRowHeight - 14
                    radius: width / 2
                    color: resultRow.accent || root.theme.action
                    opacity: resultRow.selected ? 1 : 0.82
                }

                Controls.CheckBox {
                    objectName: "tableSelection_" + resultRow.nodeId
                    anchors.centerIn: parent
                    width: 28
                    height: 28
                    leftPadding: 4
                    theme: root.theme
                    visible: root.selectable
                    checked: resultRow.selected
                    Accessible.name: qsTr("Select row") + " " + resultRow.title
                    onClicked: root.selectionOwner.select_result_node(resultRow.nodeId, resultRow.searchKey, resultRow.nodeType, Qt.ControlModifier, false)
                }
            }
            Rectangle {
                objectName: "tableActionSurface"
                border.width: 0
                x: resultRow.actionX
                width: root.actionColumnWidth
                height: root.effectiveRowHeight - 1
                z: 3
                color: rowSurface.interactionColor
                visible: !resultRow.isGroup
            }
            Controls.CompactIconButton {
                id: rowActions
                anchors.verticalCenterOffset: -resultRow.nestedHeight / 2
                objectName: "searchResultTableActions"
                x: resultRow.actionX + root.actionColumnWidth - width - 4
                anchors.verticalCenter: parent.verticalCenter
                z: 4
                theme: root.theme
                iconName: "more_vert"
                opacity: rowHover.hovered || resultRow.selected || resultRow.active ? 1 : 0.35
                toolTip: qsTr("Item actions")
                visible: !resultRow.isGroup
                Accessible.name: qsTr("Item actions")
                onClicked: {
                    rows.currentIndex = resultRow.index;
                    root.selectionOwner.select_result_node(resultRow.nodeId, resultRow.searchKey, resultRow.nodeType, 0, true);
                    root.requestActionMenu(resultRow.nodeId, rowActions, 0, rowActions.height, true);
                }
            }
        }

        footer: Rectangle {
            width: root.tableWidth
            height: root.summaryRow && root.summaryRow.hasSummary ? TableHost.metrics.group : 0
            visible: Boolean(root.summaryRow && root.summaryRow.hasSummary)
            color: root.theme ? root.theme.surfaceContainerHigh : "transparent"
            Repeater {
                model: root.summaryRow && root.summaryRow.hasSummary ? root.tableLayout.cells : []
                delegate: Text {
                    required property var modelData
                    x: modelData.x + modelData.padding
                    width: Math.max(0, modelData.width - modelData.padding * 2)
                    height: parent.height
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                    font.family: root.theme ? root.theme.fontFamily : ""
                    font.pointSize: Controls.Typography.body
                    font.bold: true
                    color: root.theme ? root.theme.primaryText : "#fff"
                    text: root.displayText(root.summaryRow.values[modelData.name])
                }
            }
        }

        ScrollBar.vertical: Controls.ScrollBar {
            id: verticalBar
            objectName: "tableVerticalScrollBar"
            parent: scrollBarFrame
            theme: root.theme
            flickableTarget: rows
        }
        ScrollBar.horizontal: Controls.ScrollBar {
            id: horizontalBar
            objectName: "tableHorizontalScrollBar"
            parent: scrollBarFrame
            theme: root.theme
            flickableTarget: rows
        }
    }

    // Defer viewport-dependent insets until column layout has settled.
    Binding {
        target: rows
        property: "anchors.rightMargin"
        value: verticalBar.hasOverflow ? verticalBar.reservedExtent + 4 : 0
        delayed: true
    }
    Binding {
        target: rows
        property: "anchors.bottomMargin"
        value: horizontalBar.hasOverflow ? horizontalBar.reservedExtent + 4 : 0
        delayed: true
    }

    Controls.InitialBatchPresentation {
        id: initialTablePresentation
        objectName: "initialTablePresentation"
        view: rows
        enabled: root.presentationActive && rows.visible
    }

    Loader {
        objectName: "tableColumnsEmptyState"
        anchors.centerIn: parent
        width: Math.min(420, Math.max(180, parent.width - 48))
        active: root.columns.length === 0 && !root.columnsBusy
        visible: active
        sourceComponent: Column {
            spacing: 10
            Controls.EmptyState {
                width: parent.width
                height: 112
                theme: root.theme
                iconName: root.columnsError.length > 0 ? "error" : "table_view"
                title: root.columnsError.length > 0 ? qsTr("Table unavailable") : qsTr("No table columns")
                message: root.columnsError.length > 0 ? root.columnsError : qsTr("This TACTIC table view has no visible columns.")
            }
            Controls.Button {
                anchors.horizontalCenter: parent.horizontalCenter
                theme: root.theme
                text: root.columnsError.length > 0 ? qsTr("Retry") : qsTr("Configure columns")
                onClicked: {
                    if (root.columnsError.length > 0)
                        root.columnsController.reload();
                    else
                        root.openColumnsEditor();
                }
            }
        }
    }

    ContentLoadingOverlay {
        objectName: "tableColumnsLoading"
        anchors.fill: parent
        z: 5
        visible: root.columnsBusy && root.columns.length === 0
        theme: root.theme
        message: qsTr("Loading…")
    }
}
