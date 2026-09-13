pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.EditorPanel {
    id: root

    required property var controller
    required property string scope
    property int selectedRow: -1
    property int selectedColumn: -1
    readonly property real labelWidth: Math.min(260, width * 0.36)
    readonly property real cellWidth: 136
    readonly property real rowHeight: theme.controlHeight + 8
    readonly property var selectedCell: {
        controller.groupDocument
        return controller.matrix.cell_at(selectedRow, selectedColumn)
    }

    function filterMatrix() {
        if (!controller || !targetSearch || !groupSearch)
            return
        controller.matrix.filter(scope, targetSearch.text, groupSearch.text)
        selectedRow = -1
        selectedColumn = -1
    }
    function focusCell(row, column) {
        if (row < 0 || row >= grid.rows || column < 0 || column >= grid.columns)
            return
        const loaded = grid.itemAtCell(Qt.point(column, row))
        if (loaded && loaded.x >= grid.contentX && loaded.x + loaded.width <= grid.contentX + grid.width
                && loaded.y >= grid.contentY && loaded.y + loaded.height <= grid.contentY + grid.height) {
            loaded.forceActiveFocus()
            return
        }
        grid.positionViewAtCell(Qt.point(column, row), TableView.Contain)
        grid.forceLayout()
        const item = grid.itemAtCell(Qt.point(column, row))
        if (item)
            item.forceActiveFocus()
    }
    onScopeChanged: filterMatrix()
    Component.onCompleted: filterMatrix()

    RowLayout {
        Layout.fillWidth: true
        spacing: 12
        Controls.TextField {
            id: targetSearch
            objectName: "adminSecurityTargetSearch"
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            theme: root.theme
            placeholderText: qsTr("Find a permission")
            onTextEdited: root.filterMatrix()
        }
        Controls.TextField {
            id: groupSearch
            objectName: "adminSecurityGroupSearch"
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            theme: root.theme
            placeholderText: qsTr("Find a group")
            onTextEdited: root.filterMatrix()
        }
    }

    Item {
        id: gridFrame
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: 100

        Label {
            width: root.labelWidth
            height: columnHeaders.height
            leftPadding: 12
            text: qsTr("Permission / Group")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.WordWrap
        }
        HorizontalHeaderView {
            id: columnHeaders
            objectName: "adminSecurityColumnHeaders"
            anchors.left: grid.left
            anchors.right: grid.right
            anchors.top: parent.top
            height: root.rowHeight
            syncView: grid
            clip: true
            interactive: false
            delegate: Item {
                id: columnHeader
                required property var display
                implicitWidth: root.cellWidth
                implicitHeight: root.rowHeight
                Label {
                    anchors.fill: parent
                    leftPadding: 8
                    rightPadding: 8
                    text: columnHeader.display.label || ""
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    wrapMode: Text.Wrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                Controls.ToolTip {
                    visible: hovered.hovered
                    text: columnHeader.display.label || ""
                    theme: root.theme
                }
                HoverHandler { id: hovered }
            }
        }
        VerticalHeaderView {
            objectName: "adminSecurityRowHeaders"
            anchors.left: parent.left
            anchors.top: grid.top
            anchors.bottom: grid.bottom
            width: root.labelWidth
            syncView: grid
            clip: true
            interactive: false
            delegate: Item {
                id: rowHeader
                required property var display
                implicitWidth: root.labelWidth
                implicitHeight: root.rowHeight
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: rowHeader.display.all ? qsTr("All") : rowHeader.display.label
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: rowHeader.display.all ? Font.DemiBold : Font.Normal
                        color: root.theme.primaryText
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: rowHeader.display.detail || Object.values(rowHeader.display.attributes || {}).filter(value =>
                            value !== root.controller.identity).join(" · ")
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        color: root.theme.secondaryText
                        elide: Text.ElideRight
                    }
                }
            }
        }
        TableView {
            id: grid
            objectName: "adminSecurityMatrix"
            anchors.left: parent.left
            anchors.leftMargin: root.labelWidth
            anchors.right: parent.right
            anchors.rightMargin: verticalBar.reservedExtent + 4
            anchors.top: columnHeaders.bottom
            anchors.bottom: parent.bottom
            anchors.bottomMargin: horizontalBar.reservedExtent + 4
            clip: true
            reuseItems: true
            keyNavigationEnabled: false
            boundsBehavior: Flickable.StopAtBounds
            model: root.controller.matrix
            columnWidthProvider: column => root.cellWidth
            rowHeightProvider: row => root.rowHeight
            delegate: FocusScope {
                id: cellItem
                required property int row
                required property int column
                required property var cell
                implicitWidth: root.cellWidth
                implicitHeight: root.rowHeight

                Controls.ItemSurface {
                    anchors.fill: parent
                    theme: root.theme
                    railVisible: false
                    selected: cellItem.cell.checked
                    hovered: check.hovered
                    pressed: check.down
                    normalColor: root.theme.surfaceContainerLow
                }
                Controls.CheckBox {
                    id: check
                    focus: true
                    objectName: "adminSecurityCell_" + cellItem.row + "_" + cellItem.column
                    anchors.centerIn: parent
                    theme: root.theme
                    width: 38
                    height: root.rowHeight
                    leftPadding: (width - indicator.width) / 2
                    checked: cellItem.cell.checked
                    checkable: false
                    enabled: root.controller.canWrite && !cellItem.cell.locked
                    Accessible.name: root.controller.matrix.cell_label(cellItem.row, cellItem.column)
                    onActiveFocusChanged: {
                        if (activeFocus) {
                            root.selectedRow = cellItem.row
                            root.selectedColumn = cellItem.column
                        }
                    }
                    onClicked: {
                        root.selectedRow = cellItem.row
                        root.selectedColumn = cellItem.column
                        root.controller.matrix.set_allowed(cellItem.row, cellItem.column, !cellItem.cell.checked)
                    }
                    Keys.onLeftPressed: root.focusCell(cellItem.row, cellItem.column - 1)
                    Keys.onRightPressed: root.focusCell(cellItem.row, cellItem.column + 1)
                    Keys.onUpPressed: root.focusCell(cellItem.row - 1, cellItem.column)
                    Keys.onDownPressed: root.focusCell(cellItem.row + 1, cellItem.column)
                }
                Controls.MaterialIcon {
                    anchors.left: check.right
                    anchors.verticalCenter: check.verticalCenter
                    name: cellItem.cell.custom ? "code" : cellItem.cell.locked ? "lock" : "account-tree"
                    size: 14
                    color: root.theme.secondaryText
                    visible: cellItem.cell.custom || cellItem.cell.locked || (cellItem.cell.inherited && cellItem.cell.checked)
                }
                Controls.ToolTip {
                    visible: cellHover.hovered
                    theme: root.theme
                    text: root.controller.matrix.cell_label(cellItem.row, cellItem.column) + "\n" +
                    (cellItem.cell.custom ? qsTr("Custom access level: %1. Edit it in Advanced rules.").arg(cellItem.cell.access)
                     : cellItem.cell.locked ? qsTr("Granted by defaults, subgroups or an All rule. Change the granting rule first.")
                     : cellItem.cell.inherited ? qsTr("Inherited. Click to set an explicit permission.")
                     : qsTr("Explicit permission for this group."))
                }
                HoverHandler { id: cellHover }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                id: verticalBar
                objectName: "adminSecurityMatrixVerticalBar"
                parent: gridFrame
                theme: root.theme
                flickableTarget: grid
            }
            ScrollBar.horizontal: Controls.ScrollBar {
                id: horizontalBar
                objectName: "adminSecurityMatrixHorizontalBar"
                parent: gridFrame
                theme: root.theme
                flickableTarget: grid
            }
        }
        Label {
            anchors.centerIn: grid
            width: Math.max(0, grid.width - 24)
            visible: grid.rows === 0 || grid.columns === 0
            text: qsTr("No matching permissions or groups")
            color: root.theme.secondaryText
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Label {
            Layout.fillWidth: true
            text: qsTr("Checked = allowed. The lock marks a grant controlled by another rule. Other group memberships can also grant access.")
            color: root.theme.secondaryText
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
        Controls.Button {
            objectName: "adminSecurityInherit"
            theme: root.theme
            text: qsTr("Use inherited rule")
            icon.name: "undo"
            enabled: root.controller.canWrite && root.selectedCell.explicit === true && !root.selectedCell.custom
            onClicked: root.controller.matrix.inherit(root.selectedRow, root.selectedColumn)
        }
    }
}
