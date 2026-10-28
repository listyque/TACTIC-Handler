pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame/features/table/menus.ui.mjs" as TableMenus
import "tactic_frame/features/table/host.ui.mjs" as TableHost

Rectangle {
    id: root

    required property var theme
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    required property var controller
    required property var columnsController
    required property var columns
    required property var selectedIds
    required property bool columnsBusy
    required property string columnsError
    required property int rowCount
    required property real rowHeight
    required property bool automaticRowHeight
    required property real viewportContentX
    required property real viewportWidth
    required property real selectionColumnWidth
    required property real actionColumnWidth
    required property var columnWidthProvider
    required property bool autoFitColumns
    property var columnContext: ({})
    property var tableViewPresetMenu: null
    property int draggedColumn: -1
    property int dropColumn: -1

    signal widthPreviewRequested(string name, real width)
    signal widthClearRequested(string name)
    signal widthCommitRequested(var column, real width)
    signal columnsEditorRequested(int row, string target)
    signal selectAllRequested(bool selected)
    signal rowHeightRequested(real height)
    signal autoFitRequested

    function columnWidth(column) {
        return Number(columnWidthProvider(column));
    }

    function columnIndexAtSceneX(sceneX) {
        const contentX = mapFromItem(null, sceneX, 0).x - selectionColumnWidth;
        let left = 0;
        for (let index = 0; index < columns.length; ++index) {
            const width = columnWidth(columns[index]);
            if (contentX < left + width / 2)
                return index;
            left += width;
        }
        return Math.max(0, columns.length - 1);
    }

    function updateColumnDrag(sourceIndex, sceneX) {
        draggedColumn = sourceIndex;
        dropColumn = columnIndexAtSceneX(sceneX);
    }

    function finishColumnDrag() {
        const sourceIndex = draggedColumn;
        const targetIndex = dropColumn;
        draggedColumn = -1;
        dropColumn = -1;
        if (columnsBusy || sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex)
            return;
        const source = columns[sourceIndex];
        const target = columns[targetIndex];
        columnsController.move(Number(source.row), Number(target.row) - Number(source.row));
        columnsController.apply();
    }

    function moveColumn(sourceIndex, offset) {
        if (!columns.length)
            return;
        draggedColumn = sourceIndex;
        dropColumn = Math.max(0, Math.min(columns.length - 1, sourceIndex + offset));
        finishColumnDrag();
    }

    function contextActions() {
        const column = columnContext || ({});
        return TableMenus.columnActions({
            column: column,
            count: columns.length,
            index: columns.findIndex(item => item.name === column.name),
            busy: columnsBusy,
            editable: true,
            sorted: String(controller.result_sort_mode || "").indexOf("column:" + column.name + ":") === 0,
            direction: String(controller.result_sort_mode || "").endsWith(":desc") ? "desc" : "asc",
            group: String(controller.result_group_mode || "none"),
            rowHeight: rowHeight,
            automaticRowHeight: automaticRowHeight
        }, root.language);
    }

    function currentTableViewTitle() {
        const views = columnsController ? columnsController.tableViews || [] : [];
        for (let index = 0; index < views.length; ++index) {
            if (Boolean(views[index].current) && String(views[index].view || "") === "table")
                return qsTr("Default table");
            if (Boolean(views[index].current))
                return String(views[index].title || views[index].view || "");
        }
        return qsTr("Default table");
    }

    function openTableViewPresetMenu(anchor) {
        if (!tableViewPresetMenu) {
            const component = Qt.createComponent(Qt.resolvedUrl("TableViewPresetMenu.qml"));
            if (component.status !== Component.Ready)
                return;
            tableViewPresetMenu = component.createObject(root, {
                "theme": root.theme,
                "columnsController": root.columnsController
            });
            tableViewPresetMenu.configureRequested.connect(function () {
                root.columnsEditorRequested(-1, "definition");
            });
            tableViewPresetMenu.closeRequested.connect(function () {
                const menu = root.tableViewPresetMenu;
                root.tableViewPresetMenu = null;
                Qt.callLater(function () {
                    menu.destroy();
                });
            });
        }
        tableViewPresetMenu.openBelow(anchor);
    }

    objectName: "searchResultTableHeader"
    radius: 0
    color: theme.background

    Rectangle {
        objectName: "tableHeaderSurface"
        x: root.viewportContentX
        width: root.viewportWidth
        height: root.height
        radius: root.radius
        color: root.theme[TableHost.paint.header]
    }

    Component {
        id: insertButtonComponent
        Controls.CompactIconButton {
            required property var header
            objectName: "tableColumnInsert_" + String(header.modelData.name || "")
            anchors.left: parent.left
            anchors.leftMargin: header.index === 0 ? TableHost.metrics.firstPadding : TableHost.metrics.padding
            anchors.verticalCenter: parent.verticalCenter
            z: 1
            theme: root.theme
            enabled: !root.columnsBusy && typeof tableServicesController !== "undefined" && !!tableServicesController && !tableServicesController.busy
            iconName: header.insertAction.icon || "add"
            toolTip: header.insertAction.type === "publish" ? qsTr("Multi Publish") : qsTr("Create")
            Accessible.name: toolTip
            onClicked: {
                if (header.insertAction.type === "publish")
                    tableServicesController.insert_record(header.insertAction.view, "publish");
                else
                    tableServicesController.insert_record(header.insertAction.view);
            }
        }
    }

    Row {
        anchors.left: parent.left
        anchors.leftMargin: root.selectionColumnWidth
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 3

        Repeater {
            id: headerRepeater
            model: root.columns

            delegate: Item {
                id: headerCell
                required property int index
                required property var modelData
                property var insertControl: null
                property bool insertReady: false
                readonly property var insertAction: TableHost.headerAction(modelData)

                function updateInsertControl() {
                    if (!insertReady)
                        return;
                    if (insertAction && !insertControl)
                        insertControl = insertButtonComponent.createObject(headerCell, {
                            header: headerCell
                        });
                    else if (!insertAction && insertControl) {
                        insertControl.destroy();
                        insertControl = null;
                    }
                }
                onInsertActionChanged: updateInsertControl()
                Component.onCompleted: {
                    insertReady = true;
                    updateInsertControl();
                }
                readonly property bool grouped: String(root.controller.result_group_mode || "") === "column:" + String(modelData.name || "")
                width: root.columnWidth(modelData)
                height: parent.height

                Rectangle {
                    anchors.fill: parent
                    radius: root.theme.itemRadius
                    color: root.theme.secondaryContainer
                    visible: root.draggedColumn === headerCell.index
                }
                Label {
                    objectName: "tableColumnHeaderLabel_" + String(headerCell.modelData.name || "")
                    anchors.fill: parent
                    leftPadding: headerCell.index === 0 ? 14 : 10
                    verticalAlignment: Text.AlignVCenter
                    text: TableHost.headerAction(headerCell.modelData) ? "" : String(headerCell.modelData.label || headerCell.modelData.name || "").toUpperCase()
                    elide: Text.ElideRight
                    color: headerCell.grouped ? root.theme.action : root.theme[TableHost.paint.headerText]
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                    rightPadding: headerCell.grouped ? 30 : 12
                }
                Controls.MaterialIcon {
                    objectName: "tableColumnGroupIndicator_" + String(headerCell.modelData.name || "")
                    anchors.right: parent.right
                    anchors.rightMargin: 14
                    anchors.verticalCenter: parent.verticalCenter
                    visible: headerCell.grouped
                    name: "group-items"
                    size: 14
                    color: root.theme.action
                    Accessible.ignored: true
                }
                MouseArea {
                    objectName: "tableColumnContextArea_" + String(headerCell.modelData.name || "")
                    anchors.fill: parent
                    anchors.rightMargin: 10
                    enabled: !root.columnsBusy
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    cursorShape: root.draggedColumn === headerCell.index ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                    preventStealing: true
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Button
                    Accessible.name: qsTr("Move column") + " " + String(headerCell.modelData.label || "")
                    Accessible.description: headerCell.grouped ? qsTr("Group by this column") : ""
                    property real pressSceneX: 0
                    property bool leftPressed: false

                    onPressed: function (mouse) {
                        leftPressed = mouse.button === Qt.LeftButton;
                        if (leftPressed)
                            pressSceneX = mapToItem(null, mouse.x, mouse.y).x;
                    }
                    onPositionChanged: function (mouse) {
                        if (!leftPressed)
                            return;
                        const sceneX = mapToItem(null, mouse.x, mouse.y).x;
                        if (root.draggedColumn < 0 && Math.abs(sceneX - pressSceneX) < 6)
                            return;
                        root.updateColumnDrag(headerCell.index, sceneX);
                    }
                    onReleased: {
                        leftPressed = false;
                        if (root.draggedColumn >= 0)
                            root.finishColumnDrag();
                    }
                    onCanceled: {
                        leftPressed = false;
                        root.draggedColumn = -1;
                        root.dropColumn = -1;
                    }
                    onClicked: function (mouse) {
                        if (mouse.button === Qt.RightButton) {
                            root.columnContext = headerCell.modelData;
                            columnContextMenu.openBelow(headerCell);
                        }
                    }
                    Keys.onPressed: function (event) {
                        if (event.key !== Qt.Key_Left && event.key !== Qt.Key_Right)
                            return;
                        root.moveColumn(headerCell.index, event.key === Qt.Key_Right ? 1 : -1);
                        event.accepted = true;
                    }
                }
                MouseArea {
                    id: resizeHandle
                    objectName: "tableColumnResize_" + String(headerCell.modelData.name || "")
                    z: 2
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 12
                    hoverEnabled: true
                    enabled: !root.columnsBusy
                    acceptedButtons: Qt.LeftButton
                    cursorShape: Qt.SplitHCursor
                    preventStealing: true
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Slider
                    Accessible.name: qsTr("Resize column") + " " + String(headerCell.modelData.label || "")
                    Controls.ColumnHeaderGrip {
                        theme: root.theme
                        highlighted: resizeHandle.containsMouse || resizeHandle.activeFocus || resizeHandle.pressed
                    }
                    property real pressSceneX: 0
                    property real startWidth: 0
                    property bool changed: false

                    onPressed: function (mouse) {
                        pressSceneX = mapToItem(null, mouse.x, mouse.y).x;
                        startWidth = root.columnWidth(headerCell.modelData);
                        changed = false;
                    }
                    onPositionChanged: function (mouse) {
                        if (!pressed)
                            return;
                        const sceneX = mapToItem(null, mouse.x, mouse.y).x;
                        const nextWidth = startWidth + sceneX - pressSceneX;
                        root.widthPreviewRequested(String(headerCell.modelData.name || ""), nextWidth);
                        changed = true;
                    }
                    onReleased: {
                        if (changed) {
                            root.widthCommitRequested(headerCell.modelData, root.columnWidth(headerCell.modelData));
                        }
                    }
                    onCanceled: {
                        if (changed) {
                            root.widthClearRequested(String(headerCell.modelData.name || ""));
                        }
                    }
                    Keys.onPressed: function (event) {
                        if (event.key !== Qt.Key_Left && event.key !== Qt.Key_Right)
                            return;
                        const direction = event.key === Qt.Key_Right ? 1 : -1;
                        const step = event.modifiers & Qt.ShiftModifier ? 16 : 8;
                        const nextWidth = root.columnWidth(headerCell.modelData) + direction * step;
                        root.widthPreviewRequested(String(headerCell.modelData.name || ""), nextWidth);
                        root.widthCommitRequested(headerCell.modelData, nextWidth);
                        event.accepted = true;
                    }
                }
            }
        }
    }

    Rectangle {
        visible: root.draggedColumn >= 0 && root.dropColumn >= 0
        x: {
            const target = headerRepeater.itemAt(root.dropColumn);
            if (!target)
                return root.selectionColumnWidth;
            return root.selectionColumnWidth + target.x + (root.draggedColumn < root.dropColumn ? target.width : 0);
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
        anchors.bottomMargin: 3
        width: root.selectionColumnWidth
        z: 5
        color: root.theme[TableHost.paint.header]
        radius: root.radius

        Controls.CheckBox {
            objectName: "tableSelectionAll"
            anchors.centerIn: parent
            width: 28
            height: 28
            leftPadding: 4
            theme: root.theme
            checkState: root.selectedIds.length === 0 ? Qt.Unchecked : root.rowCount > 0 && root.selectedIds.length >= root.rowCount ? Qt.Checked : Qt.PartiallyChecked
            Accessible.name: qsTr("Select all rows")
            onClicked: root.selectAllRequested(checked)
        }
    }

    Item {
        x: Math.max(0, root.viewportContentX + root.viewportWidth - width)
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 3
        width: root.actionColumnWidth

        Rectangle {
            anchors.fill: parent
            color: root.theme[TableHost.paint.header]
            radius: root.radius
        }
        Controls.BusyIndicator {
            anchors.centerIn: parent
            width: 24
            height: 24
            visible: root.columnsBusy
            running: visible
            uiTheme: root.theme
        }
        Row {
            anchors.centerIn: parent
            spacing: 4
            visible: !root.columnsBusy

            Controls.CompactIconButton {
                objectName: "autoFitTableColumnsButton"
                theme: root.theme
                backgroundColor: root.autoFitColumns ? root.theme.secondaryContainer : root.theme.surfaceContainerHigh
                iconName: "fit-width"
                iconColor: root.autoFitColumns ? root.theme.action : root.theme[TableHost.paint.headerText]
                toolTip: qsTr("Auto Fit columns")
                Accessible.name: qsTr("Auto Fit columns")
                onClicked: root.autoFitRequested()
            }
            Controls.CompactIconButton {
                objectName: "configureTableColumnsButton"
                theme: root.theme
                backgroundColor: root.theme.surfaceContainerHigh
                iconName: root.columnsError.length > 0 ? "error" : "view_column"
                iconColor: root.columnsError.length > 0 ? root.theme.error : root.theme[TableHost.paint.headerText]
                toolTip: root.columnsError.length > 0 ? root.columnsError : qsTr("Table view: %1").arg(root.currentTableViewTitle())
                Accessible.name: qsTr("Table views and columns")
                onClicked: root.openTableViewPresetMenu(this)
            }
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
            const row = Number(root.columnContext.row);
            if (command === "sort:ascending")
                root.columnsController.sort_column(row, false);
            else if (command === "sort:descending")
                root.columnsController.sort_column(row, true);
            else if (command === "group")
                root.columnsController.group_column(row);
            else if (command === "ungroup")
                root.controller.set_result_group_mode("none");
            else if (command === "edit_definition")
                root.columnsEditorRequested(row, "definition");
            else if (command === "columns")
                root.columnsEditorRequested(-1, "definition");
            else if (command === "left" || command === "right")
                root.moveColumn(root.columns.findIndex(item => item.name === root.columnContext.name), command === "left" ? -1 : 1);
            else if (command === "remove")
                root.columnsController.remove_column(row);
            else if (command.indexOf("row_height:") === 0)
                root.rowHeightRequested(Number(command.split(":")[1]));
        }
    }
}
