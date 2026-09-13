pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    required property var controller
    required property var columnsController
    required property var columns
    required property var selectedIds
    required property bool columnsBusy
    required property string columnsError
    required property int rowCount
    required property real rowHeight
    required property real viewportContentX
    required property real viewportWidth
    required property real selectionColumnWidth
    required property real actionColumnWidth
    required property var columnWidthProvider
    property var columnContext: ({})
    property int draggedColumn: -1
    property int dropColumn: -1

    signal widthPreviewRequested(string name, real width)
    signal widthClearRequested(string name)
    signal widthCommitRequested(var column, real width)
    signal columnsEditorRequested(int row, string target)
    signal selectAllRequested(bool selected)
    signal rowHeightRequested(real height)

    function columnWidth(column) {
        return Number(columnWidthProvider(column))
    }

    function columnIndexAtSceneX(sceneX) {
        const contentX = mapFromItem(null, sceneX, 0).x
            - selectionColumnWidth
        let left = 0
        for (let index = 0; index < columns.length; ++index) {
            const width = columnWidth(columns[index])
            if (contentX < left + width / 2)
                return index
            left += width
        }
        return Math.max(0, columns.length - 1)
    }

    function updateColumnDrag(sourceIndex, sceneX) {
        draggedColumn = sourceIndex
        dropColumn = columnIndexAtSceneX(sceneX)
    }

    function finishColumnDrag() {
        const sourceIndex = draggedColumn
        const targetIndex = dropColumn
        draggedColumn = -1
        dropColumn = -1
        if (
            columnsBusy || sourceIndex < 0 || targetIndex < 0
            || sourceIndex === targetIndex
        )
            return
        const source = columns[sourceIndex]
        const target = columns[targetIndex]
        columnsController.move(
            Number(source.row), Number(target.row) - Number(source.row)
        )
        columnsController.apply()
    }

    function moveColumn(sourceIndex, offset) {
        if (!columns.length)
            return
        draggedColumn = sourceIndex
        dropColumn = Math.max(
            0, Math.min(columns.length - 1, sourceIndex + offset)
        )
        finishColumnDrag()
    }

    function contextActions() {
        const column = columnContext || ({})
        if (column.row === undefined)
            return []
        const label = String(column.label || column.name || "")
        const dataType = String(column.dataType || "").toLowerCase()
        const dateSort = ["date", "datetime", "time"].indexOf(dataType) >= 0
        const sortMode = String(controller.result_sort_mode || "")
        const modePrefix = "column:" + String(column.name || "") + ":"
        const actions = [{
            "title": label + " · Column",
            "header": true,
            "translate": false
        }]
        if (Boolean(column.sortable)) {
            actions.push({
                "title": dateSort ? "Order by oldest" : "Order by ascending",
                "icon": "sort-ascending",
                "command": "sort:ascending",
                "checked": sortMode === modePrefix + "asc"
            })
            actions.push({
                "title": dateSort ? "Order by newest" : "Order by descending",
                "icon": "sort-descending",
                "command": "sort:descending",
                "checked": sortMode === modePrefix + "desc"
            })
            actions.push({"separator": true})
        }
        actions.push({
            "title": "Edit Column Definition",
            "icon": "edit",
            "command": "edit_definition"
        })
        actions.push({
            "title": "Column Manager",
            "icon": "view-column",
            "command": "columns"
        })
        actions.push({"separator": true})
        actions.push({
            "title": "Remove Column",
            "icon": "visibility-off",
            "command": "remove",
            "enabled": columns.length > 1 && !columnsBusy,
            "status": columns.length > 1
                ? "" : qsTr("At least one column must remain visible")
        })
        actions.push({"separator": true})
        actions.push({"title": "Row height", "header": true})
        actions.push({
            "title": "Compact rows", "command": "row_height:52",
            "checked": rowHeight === 52
        })
        actions.push({
            "title": "Comfortable rows", "command": "row_height:68",
            "checked": rowHeight === 68
        })
        actions.push({
            "title": "Large rows", "command": "row_height:84",
            "checked": rowHeight === 84
        })
        return actions
    }

    objectName: "searchResultTableHeader"
    radius: theme.itemRadius
    color: theme.surfaceContainer

    Row {
        anchors.left: parent.left
        anchors.leftMargin: root.selectionColumnWidth
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        Repeater {
            id: headerRepeater
            model: root.columns

            delegate: Item {
                id: headerCell
                required property int index
                required property var modelData
                width: root.columnWidth(modelData)
                height: root.height

                Rectangle {
                    anchors.fill: parent
                    radius: root.theme.itemRadius
                    color: root.theme.secondaryContainer
                    visible: root.draggedColumn === headerCell.index
                }
                Label {
                    anchors.fill: parent
                    leftPadding: headerCell.index === 0 ? 14 : 10
                    rightPadding: 12
                    verticalAlignment: Text.AlignVCenter
                    text: String(
                        headerCell.modelData.label
                        || headerCell.modelData.name || ""
                    )
                    elide: Text.ElideRight
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                }
                Rectangle {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    width: 1
                    height: parent.height - 12
                    color: root.theme.separator
                }
                MouseArea {
                    objectName: "tableColumnContextArea_"
                        + String(headerCell.modelData.name || "")
                    anchors.fill: parent
                    anchors.rightMargin: 10
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    cursorShape: root.draggedColumn === headerCell.index
                        ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                    preventStealing: true
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Button
                    Accessible.name: qsTr("Move column") + " "
                        + String(headerCell.modelData.label || "")
                    property real pressSceneX: 0
                    property bool leftPressed: false

                    onPressed: function(mouse) {
                        leftPressed = mouse.button === Qt.LeftButton
                        if (leftPressed)
                            pressSceneX = mapToItem(null, mouse.x, mouse.y).x
                    }
                    onPositionChanged: function(mouse) {
                        if (!leftPressed)
                            return
                        const sceneX = mapToItem(null, mouse.x, mouse.y).x
                        if (
                            root.draggedColumn < 0
                            && Math.abs(sceneX - pressSceneX) < 6
                        )
                            return
                        root.updateColumnDrag(headerCell.index, sceneX)
                    }
                    onReleased: {
                        leftPressed = false
                        if (root.draggedColumn >= 0)
                            root.finishColumnDrag()
                    }
                    onCanceled: {
                        leftPressed = false
                        if (root.draggedColumn === headerCell.index)
                            root.finishColumnDrag()
                    }
                    onClicked: function(mouse) {
                        if (mouse.button === Qt.RightButton) {
                            root.columnContext = headerCell.modelData
                            columnContextMenu.openBelow(headerCell)
                        }
                    }
                    Keys.onPressed: function(event) {
                        if (
                            event.key !== Qt.Key_Left
                            && event.key !== Qt.Key_Right
                        )
                            return
                        root.moveColumn(
                            headerCell.index,
                            event.key === Qt.Key_Right ? 1 : -1
                        )
                        event.accepted = true
                    }
                }
                MouseArea {
                    id: resizeHandle
                    objectName: "tableColumnResize_"
                        + String(headerCell.modelData.name || "")
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 12
                    enabled: !root.columnsBusy
                    acceptedButtons: Qt.LeftButton
                    cursorShape: Qt.SplitHCursor
                    preventStealing: true
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Slider
                    Accessible.name: qsTr("Resize column") + " "
                        + String(headerCell.modelData.label || "")
                    property real pressSceneX: 0
                    property real startWidth: 0
                    property bool changed: false

                    onPressed: function(mouse) {
                        pressSceneX = mapToItem(null, mouse.x, mouse.y).x
                        startWidth = root.columnWidth(headerCell.modelData)
                        changed = false
                    }
                    onPositionChanged: function(mouse) {
                        if (!pressed)
                            return
                        const sceneX = mapToItem(null, mouse.x, mouse.y).x
                        const nextWidth = startWidth + sceneX - pressSceneX
                        root.widthPreviewRequested(
                            String(headerCell.modelData.name || ""), nextWidth
                        )
                        changed = true
                    }
                    onReleased: {
                        if (changed) {
                            root.widthCommitRequested(
                                headerCell.modelData,
                                root.columnWidth(headerCell.modelData)
                            )
                        }
                    }
                    onCanceled: {
                        if (changed) {
                            root.widthClearRequested(
                                String(headerCell.modelData.name || "")
                            )
                        }
                    }
                    Keys.onPressed: function(event) {
                        if (
                            event.key !== Qt.Key_Left
                            && event.key !== Qt.Key_Right
                        )
                            return
                        const direction = event.key === Qt.Key_Right ? 1 : -1
                        const step = event.modifiers & Qt.ShiftModifier ? 16 : 8
                        const nextWidth = root.columnWidth(
                            headerCell.modelData
                        ) + direction * step
                        root.widthPreviewRequested(
                            String(headerCell.modelData.name || ""), nextWidth
                        )
                        root.widthCommitRequested(
                            headerCell.modelData, nextWidth
                        )
                        event.accepted = true
                    }
                }
            }
        }
    }

    Rectangle {
        visible: root.draggedColumn >= 0 && root.dropColumn >= 0
        x: {
            const target = headerRepeater.itemAt(root.dropColumn)
            if (!target)
                return root.selectionColumnWidth
            return root.selectionColumnWidth + target.x
                + (root.draggedColumn < root.dropColumn ? target.width : 0)
        }
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 3
        z: 4
        radius: width / 2
        color: root.theme.action
    }

    Rectangle {
        x: root.viewportContentX
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.selectionColumnWidth
        z: 5
        color: root.theme.surfaceContainer
        border.width: 1
        border.color: root.theme.separator

        Controls.CheckBox {
            objectName: "tableSelectionAll"
            anchors.centerIn: parent
            width: 28
            height: 28
            compact: true
            theme: root.theme
            checked: root.rowCount > 0
                && root.selectedIds.length >= root.rowCount
            Accessible.name: qsTr("Select all rows")
            onClicked: root.selectAllRequested(checked)
        }
    }

    Item {
        x: Math.max(
            0, root.viewportContentX + root.viewportWidth - width
        )
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.actionColumnWidth

        Rectangle {
            anchors.fill: parent
            color: root.theme.surfaceContainer
            border.width: 1
            border.color: root.theme.separator
        }
        Controls.BusyIndicator {
            anchors.centerIn: parent
            width: 24
            height: 24
            visible: root.columnsBusy
            running: visible
            uiTheme: root.theme
        }
        Controls.CompactIconButton {
            objectName: "configureTableColumnsButton"
            anchors.centerIn: parent
            visible: !root.columnsBusy
            theme: root.theme
            iconName: root.columnsError.length > 0
                ? "error" : "view_column"
            iconColor: root.columnsError.length > 0
                ? root.theme.error : root.theme.secondaryText
            toolTip: root.columnsError.length > 0
                ? root.columnsError : qsTr("Configure columns")
            Accessible.name: qsTr("Configure columns")
            onClicked: root.columnsEditorRequested(-1, "definition")
        }
    }

    ActionMenu {
        id: columnContextMenu
        objectName: "tableColumnContextMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 280
        actions: root.contextActions()
        onTriggered: command => {
            const row = Number(root.columnContext.row)
            if (command === "sort:ascending")
                root.columnsController.sort_column(row, false)
            else if (command === "sort:descending")
                root.columnsController.sort_column(row, true)
            else if (command === "edit_definition")
                root.columnsEditorRequested(row, "edit_definition")
            else if (command === "columns")
                root.columnsEditorRequested(-1, "definition")
            else if (command === "remove")
                root.columnsController.remove_column(row)
            else if (command.indexOf("row_height:") === 0)
                root.rowHeightRequested(Number(command.split(":")[1]))
        }
    }
}
