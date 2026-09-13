pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property var resultModel
    required property var columnsController
    property var userModel: null
    property bool presentationActive: false
    property var widthOverrides: ({})
    property real rowHeight: 68
    readonly property var columns: columnsController
        ? columnsController.visibleColumns : []
    readonly property bool columnsBusy: columnsController
        ? Boolean(columnsController.busy) : false
    readonly property bool columnsDirty: columnsController
        ? Boolean(columnsController.dirty) : false
    readonly property string columnsError: columnsController
        ? String(columnsController.error || "") : ""
    readonly property bool hasThumbnailColumn: {
        for (let index = 0; index < columns.length; ++index) {
            if (String(columns[index].kind || "") === "thumbnail")
                return true
        }
        return false
    }
    readonly property real headerHeight: 34
    readonly property real selectionColumnWidth: 40
    readonly property real actionColumnWidth: 40
    readonly property real columnsWidth: {
        let width = 0
        for (let index = 0; index < columns.length; ++index)
            width += columnWidth(columns[index])
        return width
    }
    readonly property real tableWidth: Math.max(
        rows.width,
        selectionColumnWidth + columnsWidth + actionColumnWidth
    )
    readonly property real contentY: rows.contentY
    readonly property int count: rows.count

    signal actionMenuRequested(
        string nodeId,
        var actions,
        var anchorItem,
        real localX,
        real localY,
        bool below
    )
    signal processCountMenuRequested(
        string nodeId,
        string panel,
        var anchorItem
    )

    function displayText(value) {
        return value === undefined || value === null ? "" : String(value)
    }

    function initials(value) {
        const parts = String(value || "").trim().split(/\s+/)
        if (!parts.length || !parts[0])
            return "?"
        return String(
            parts[0][0] + (parts.length > 1 ? parts[1][0] : "")
        ).toUpperCase()
    }

    function columnWidth(column) {
        const name = String(column.name || "")
        const override = widthOverrides[name]
        return Math.max(48, Math.min(
            640,
            Number(override !== undefined ? override : column.width || 160)
        ))
    }

    function setWidthOverride(name, width) {
        const next = Object.assign({}, widthOverrides)
        next[String(name || "")] = Math.max(48, Math.min(640, width))
        widthOverrides = next
    }

    function clearWidthOverride(name) {
        const next = Object.assign({}, widthOverrides)
        delete next[String(name || "")]
        widthOverrides = next
    }

    function commitColumnWidth(column, width) {
        if (!columnsController || columnsBusy)
            return
        columnsController.set_width(
            Number(column.row), Math.round(Math.max(48, Math.min(640, width)))
        )
        columnsController.apply()
    }

    function openColumnsEditor(row, target) {
        if (row !== undefined && row >= 0)
            columnsController.request_column_focus(
                Number(row), String(target || "definition")
            )
        controller.open_window("columns_editor")
    }

    function requestActionMenu(nodeId, anchorItem, x, y, below) {
        actionMenuRequested(
            nodeId,
            controller.item_menu_actions(nodeId),
            anchorItem,
            x,
            y,
            below
        )
    }

    function restoreContentY(value, valid) {
        if (valid)
            rows.contentY = Math.max(rows.originY, Number(value || 0))
    }

    function positionViewAtIndex(row) {
        rows.positionViewAtIndex(row, ListView.Contain)
    }

    onVisibleChanged: {
        if (visible && columnsController) {
            widthOverrides = ({})
            columnsController.begin_session()
        }
    }
    Component.onCompleted: {
        if (visible && columnsController)
            columnsController.begin_session()
    }

    Connections {
        target: root.columnsController

        function onStateChanged() {
            if (!root.columnsBusy && !root.columnsDirty)
                root.widthOverrides = ({})
        }
    }

    ListView {
        id: rows
        objectName: "searchResultsTableView"
        anchors.fill: parent
        anchors.margins: 8
        anchors.rightMargin: 18
        anchors.bottomMargin: 18
        opacity: initialTablePresentation.ready ? 1 : 0
        model: root.resultModel
        clip: true
        spacing: 0
        reuseItems: true
        cacheBuffer: Math.max(80, root.rowHeight * 1.5)
        currentIndex: -1
        keyNavigationEnabled: false
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: Flickable.AutoFlickDirection
        contentWidth: root.tableWidth
        headerPositioning: ListView.OverlayHeader
        activeFocusOnTab: root.visible
        focus: root.visible

        function requestMoreFromScroll() {
            if (
                !atYEnd || !root.controller.has_more
                || root.controller.loading_mode !== "infinite"
                || !verticalBar.takePaginationPermit(false)
            )
                return
            root.controller.load_more()
        }

        function selectRow(index, modifiers) {
            if (count <= 0)
                return
            currentIndex = Math.max(0, Math.min(count - 1, index))
            positionViewAtIndex(currentIndex, ListView.Contain)
            Qt.callLater(function() {
                const item = rows.itemAtIndex(rows.currentIndex)
                if (item)
                    item.selectWithModifiers(modifiers)
            })
        }

        function openCurrent() {
            const item = itemAtIndex(currentIndex)
            if (item)
                root.controller.handle_item_double_click(item.nodeId, 0)
        }

        onContentYChanged: requestMoreFromScroll()

        Keys.onPressed: function(event) {
            if (
                event.key === Qt.Key_A
                && (event.modifiers & Qt.ControlModifier)
            ) {
                root.controller.select_all_result_siblings()
                event.accepted = true
            } else if (event.key === Qt.Key_Up) {
                selectRow(currentIndex < 0 ? 0 : currentIndex - 1,
                          event.modifiers)
                event.accepted = true
            } else if (event.key === Qt.Key_Down) {
                selectRow(currentIndex < 0 ? 0 : currentIndex + 1,
                          event.modifiers)
                event.accepted = true
            } else if (event.key === Qt.Key_Home) {
                selectRow(0, event.modifiers)
                event.accepted = true
            } else if (event.key === Qt.Key_End) {
                selectRow(count - 1, event.modifiers)
                event.accepted = true
            } else if (event.key === Qt.Key_Space) {
                selectRow(currentIndex < 0 ? 0 : currentIndex, event.modifiers)
                event.accepted = true
            } else if (
                event.key === Qt.Key_Return || event.key === Qt.Key_Enter
            ) {
                openCurrent()
                event.accepted = true
            }
        }

        header: SearchResultTableHeader {
            z: 3
            width: root.tableWidth
            height: root.headerHeight
            theme: root.theme
            controller: root.controller
            columnsController: root.columnsController
            columns: root.columns
            selectedIds: root.controller.selected_result_node_ids
            columnsBusy: root.columnsBusy
            columnsError: root.columnsError
            rowCount: rows.count
            rowHeight: root.rowHeight
            viewportContentX: rows.contentX
            viewportWidth: rows.width
            selectionColumnWidth: root.selectionColumnWidth
            actionColumnWidth: root.actionColumnWidth
            columnWidthProvider: root.columnWidth
            onWidthPreviewRequested: (name, width) =>
                root.setWidthOverride(name, width)
            onWidthClearRequested: name => root.clearWidthOverride(name)
            onWidthCommitRequested: (column, width) =>
                root.commitColumnWidth(column, width)
            onColumnsEditorRequested: (row, target) =>
                root.openColumnsEditor(row, target)
            onRowHeightRequested: height => root.rowHeight = height
            onSelectAllRequested: selected => {
                if (!selected) {
                    root.controller.clear_result_selection()
                } else if (rows.currentIndex < 0) {
                    rows.selectRow(0, 0)
                    Qt.callLater(function() {
                        root.controller.select_all_result_siblings()
                    })
                } else {
                    root.controller.select_all_result_siblings()
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
            property bool viewPooled: false
            readonly property bool selected:
                root.controller.selected_result_node_ids.indexOf(nodeId) >= 0
            readonly property bool inVerticalViewport:
                y + height >= rows.contentY
                && y <= rows.contentY + rows.height
            readonly property bool previewActive:
                root.presentationActive && root.hasThumbnailColumn
                && inVerticalViewport && !viewPooled
            readonly property var nativeCells:
                root.columnsController
                    ? root.columnsController.row_cells(
                        searchKey, root.columnsController.cellRevision
                    ) : ({})
            readonly property real actionX: Math.max(
                0, rows.contentX + rows.width - root.actionColumnWidth
            )
            width: root.tableWidth
            height: root.rowHeight
            focus: ListView.isCurrentItem && rows.activeFocus
            Accessible.role: Accessible.ListItem
            Accessible.name: title
            Accessible.selected: selected

            function cellRecord(columnName) {
                const nativeCell = nativeCells
                    ? nativeCells[columnName] : undefined
                if (nativeCell && nativeCell.text !== undefined)
                    return nativeCell
                const value = values ? values[columnName] : undefined
                if (value !== undefined && value !== null)
                    return {"text": String(value)}
                if (columnName === "code")
                    return {"text": itemCode}
                if (columnName === "name" || columnName === "title")
                    return {"text": title}
                return {"text": ""}
            }

            function selectWithModifiers(modifiers) {
                root.controller.select_result_node(
                    nodeId, searchKey, nodeType, modifiers, false
                )
            }

            function requestPreviewIfNeeded() {
                if (previewActive && !previewRequested && !previewUrl)
                    root.controller.request_item_preview(nodeId)
            }

            Component.onCompleted: requestPreviewIfNeeded()
            onPreviewActiveChanged: requestPreviewIfNeeded()
            onPreviewUrlChanged: requestPreviewIfNeeded()
            onPreviewRequestedChanged: requestPreviewIfNeeded()
            ListView.onPooled: viewPooled = true
            ListView.onReused: {
                viewPooled = false
                requestPreviewIfNeeded()
            }

            Rectangle {
                anchors.fill: parent
                color: resultRow.selected
                    ? root.theme.contentSelection
                    : rowHover.hovered
                        ? root.theme.rowHover
                        : root.theme.surfaceContainerLow
                Behavior on color {
                    enabled: !rows.moving
                    ColorAnimation {
                        duration: resultRow.selected
                            ? root.theme.clickMotionFast
                            : root.theme.hoverMotionFast
                        easing.type: Easing.OutCubic
                    }
                }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                width: 3
                height: parent.height - 14
                radius: width / 2
                color: root.theme.action
                opacity: resultRow.selected ? 1 : 0.78
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: root.theme.separator
            }
            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.width: resultRow.activeFocus ? 1 : 0
                border.color: root.theme.action
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                    | Qt.MiddleButton
                cursorShape: Qt.PointingHandCursor

                onClicked: function(mouse) {
                    rows.currentIndex = resultRow.index
                    rows.forceActiveFocus()
                    root.controller.select_result_node(
                        resultRow.nodeId,
                        resultRow.searchKey,
                        resultRow.nodeType,
                        mouse.modifiers,
                        mouse.button === Qt.RightButton && resultRow.selected
                    )
                    if (mouse.button === Qt.RightButton) {
                        root.requestActionMenu(
                            resultRow.nodeId,
                            resultRow,
                            mouse.x,
                            mouse.y,
                            false
                        )
                    } else if (mouse.button === Qt.MiddleButton) {
                        root.controller.invoke_item_action(
                            "new_tab", resultRow.nodeId
                        )
                    }
                }
                onDoubleClicked: function(mouse) {
                    if (mouse.button === Qt.LeftButton) {
                        root.controller.handle_item_double_click(
                            resultRow.nodeId, mouse.modifiers
                        )
                    }
                }
            }

            Row {
                anchors.left: parent.left
                anchors.leftMargin: root.selectionColumnWidth
                anchors.top: parent.top
                anchors.bottom: parent.bottom

                Repeater {
                    model: root.columns
                    delegate: Item {
                        id: cellDelegate
                        required property int index
                        required property var modelData
                        property bool editing: false
                        readonly property var cell: resultRow.cellRecord(
                            String(modelData.name || "")
                        )
                        readonly property string kind: String(
                            cell.kind || modelData.kind || "text"
                        )
                        readonly property string textValue:
                            root.displayText(cell.text)
                        readonly property bool inHorizontalViewport: {
                            const left = x + root.selectionColumnWidth
                            return left + width >= rows.contentX
                                && left <= rows.contentX + rows.width
                                    - root.actionColumnWidth
                        }
                        width: root.columnWidth(modelData)
                        height: resultRow.height
                        z: editing ? 10 : 0

                        Loader {
                            id: cellDisplay
                            anchors.fill: parent
                            active: cellDelegate.inHorizontalViewport
                                && !cellDelegate.editing

                            sourceComponent: TacticTableCellDisplay {
                                theme: root.theme
                                controller: root.controller
                                columnsController: root.columnsController
                                userModel: root.userModel
                                nodeId: resultRow.nodeId
                                kind: cellDelegate.kind
                                cell: cellDelegate.cell
                                textValue: cellDelegate.textValue
                                columnIndex: cellDelegate.index
                                previewActive: resultRow.previewActive
                                previewUrl: resultRow.previewUrl
                                previewRevealed: resultRow.previewRevealed
                                title: root.initials(resultRow.title)
                                accent: resultRow.accent
                                comments: resultRow.comments
                                tasks: resultRow.tasks
                                displayOptions:
                                    cellDelegate.modelData.displayOptions || ({})
                                effectsEnabled: !rows.moving
                                scrolling: rows.moving
                                onProcessCountMenuRequested:
                                    function(panel, anchorItem) {
                                    root.processCountMenuRequested(
                                        resultRow.nodeId, panel, anchorItem
                                    )
                                }
                            }
                        }
                        Rectangle {
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            width: 1
                            height: parent.height - 16
                            color: root.theme.separator
                            opacity: 0.45
                        }
                        Loader {
                            id: inlineEditorLoader
                            anchors.fill: parent
                            z: 4
                            active: Boolean(cellDelegate.modelData.editable)
                                && (cellDelegate.inHorizontalViewport
                                    || cellDelegate.editing)

                            sourceComponent: TacticTableInlineEditor {
                                theme: root.theme
                                controller: root.controller
                                columnsController: root.columnsController
                                nodeId: resultRow.nodeId
                                columnName: String(
                                    cellDelegate.modelData.name || ""
                                )
                                editable: true
                                pooled: resultRow.viewPooled
                                onEditingChanged:
                                    cellDelegate.editing = editing
                                onSelectRequested: {
                                    rows.currentIndex = resultRow.index
                                    resultRow.selectWithModifiers(0)
                                }
                                onFocusTableRequested: rows.forceActiveFocus()
                            }
                        }
                    }
                }
            }

            HoverHandler {
                id: rowHover
                cursorShape: Qt.PointingHandCursor
            }
            Rectangle {
                x: rows.contentX
                width: root.selectionColumnWidth
                height: parent.height
                z: 4
                color: resultRow.selected
                    ? root.theme.contentSelection
                    : rowHover.hovered
                        ? root.theme.rowHover
                        : root.theme.surfaceContainerLow
                border.width: 1
                border.color: root.theme.separator

                Controls.CheckBox {
                    objectName: "tableSelection_" + resultRow.nodeId
                    anchors.centerIn: parent
                    width: 28
                    height: 28
                    compact: true
                    theme: root.theme
                    checked: resultRow.selected
                    Accessible.name: qsTr("Select row") + " "
                        + resultRow.title
                    onClicked: root.controller.select_result_node(
                        resultRow.nodeId,
                        resultRow.searchKey,
                        resultRow.nodeType,
                        Qt.ControlModifier,
                        false
                    )
                }
            }
            Rectangle {
                x: resultRow.actionX
                width: root.actionColumnWidth
                height: parent.height
                z: 3
                color: resultRow.selected
                    ? root.theme.contentSelection
                    : rowHover.hovered
                        ? root.theme.rowHover
                        : root.theme.surfaceContainerLow
                border.width: 1
                border.color: root.theme.separator
            }
            Controls.CompactIconButton {
                id: rowActions
                objectName: "searchResultTableActions"
                x: resultRow.actionX + root.actionColumnWidth - width - 4
                anchors.verticalCenter: parent.verticalCenter
                z: 4
                theme: root.theme
                iconName: "more_vert"
                opacity: rowHover.hovered || resultRow.selected ? 1 : 0.35
                toolTip: qsTr("Item actions")
                Accessible.name: qsTr("Item actions")
                onClicked: {
                    rows.currentIndex = resultRow.index
                    root.controller.select_result_node(
                        resultRow.nodeId,
                        resultRow.searchKey,
                        resultRow.nodeType,
                        0,
                        resultRow.selected
                    )
                    root.requestActionMenu(
                        resultRow.nodeId, rowActions,
                        0, rowActions.height, true
                    )
                }
            }
        }

        ScrollBar.vertical: Controls.ScrollBar {
            id: verticalBar
            objectName: "tableVerticalScrollBar"
            theme: root.theme
            flickableTarget: rows
        }
        ScrollBar.horizontal: Controls.ScrollBar {
            objectName: "tableHorizontalScrollBar"
            theme: root.theme
            flickableTarget: rows
        }
    }

    Controls.InitialBatchPresentation {
        id: initialTablePresentation
        objectName: "initialTablePresentation"
        view: rows
        enabled: root.presentationActive && rows.visible
    }

    Column {
        objectName: "tableColumnsEmptyState"
        anchors.centerIn: parent
        width: Math.min(420, Math.max(180, parent.width - 48))
        spacing: 10
        visible: root.columns.length === 0 && !root.columnsBusy

        Controls.EmptyState {
            width: parent.width
            height: 112
            theme: root.theme
            iconName: root.columnsError.length > 0 ? "error" : "table_view"
            title: root.columnsError.length > 0
                ? qsTr("Table unavailable") : qsTr("No table columns")
            message: root.columnsError.length > 0
                ? root.columnsError
                : qsTr("This TACTIC table view has no visible columns.")
        }
        Controls.Button {
            anchors.horizontalCenter: parent.horizontalCenter
            theme: root.theme
            text: root.columnsError.length > 0
                ? qsTr("Retry") : qsTr("Configure columns")
            onClicked: {
                if (root.columnsError.length > 0)
                    root.columnsController.reload()
                else
                    root.openColumnsEditor()
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
