pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls

Item {
    id: root
    required property var theme
    required property var node
    required property var sourceModel
    required property var describeCell
    readonly property int rows: node.rowHeaders.length
    readonly property int columns: node.columnHeaders.length
    readonly property real cellWidth: node.cellWidth
    readonly property real cellHeight: node.rowHeight
    property bool completed: false
    Component.onCompleted: completed = true
    onCellWidthChanged: if (completed)
        Qt.callLater(grid.forceLayout)
    onCellHeightChanged: if (completed)
        Qt.callLater(grid.forceLayout)
    property alias contentX: grid.contentX
    property alias contentY: grid.contentY
    readonly property real originY: 0
    readonly property real contentWidth: grid.contentWidth + node.labelWidth + 16
    readonly property real contentHeight: grid.contentHeight + node.headerHeight + 16
    signal event(var action)

    objectName: node.id
    function cellAt(row, column): var {
        return grid.itemAtCell(Qt.point(column, row));
    }
    function focusCell(row, column, name) {
        if (column * node.cellWidth < grid.contentX)
            grid.contentX = column * node.cellWidth;
        else if ((column + 1) * node.cellWidth > grid.contentX + grid.width)
            grid.contentX = (column + 1) * node.cellWidth - grid.width;
        if (row * node.rowHeight < grid.contentY)
            grid.contentY = row * node.rowHeight;
        else if ((row + 1) * node.rowHeight > grid.contentY + grid.height)
            grid.contentY = (row + 1) * node.rowHeight - grid.height;
        grid.forceLayout();
        const item = root.cellAt(row, column);
        if (item)
            item.focusControl(name);
    }
    function focusGrid(id, row, column, name) {
        if (id !== node.id)
            return false;
        focusCell(row, column, name);
        return true;
    }

    Rectangle {
        width: root.node.labelWidth
        height: root.node.headerHeight
        color: root.theme.surfaceContainerHigh
        Label {
            anchors.fill: parent
            anchors.margins: 6
            text: root.node.caption || ""
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.WordWrap
        }
    }
    Flickable {
        objectName: root.node.columnHeadersId || ""
        x: grid.x
        width: grid.width
        height: root.node.headerHeight
        contentWidth: grid.contentWidth
        contentX: grid.contentX
        interactive: false
        clip: true
        Rectangle {
            width: parent.width
            height: parent.height
            color: root.theme.surfaceContainerHigh
        }
        Repeater {
            model: root.node.columnHeaders
            delegate: Item {
                required property var modelData
                required property int index
                objectName: root.node.id + "_column_" + index
                x: index * root.node.cellWidth
                width: root.node.cellWidth
                height: root.node.headerHeight
                Label {
                    anchors.fill: parent
                    leftPadding: 6
                    rightPadding: 6
                    visible: typeof parent.modelData === "string"
                    text: visible ? parent.modelData : ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                Label {
                    objectName: parent.objectName + "_title"
                    x: 6
                    y: 1
                    width: parent.width - 12
                    height: 19
                    visible: typeof parent.modelData !== "string"
                    text: visible ? parent.modelData.label || "" : ""
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 13
                    font.weight: 600
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                Label {
                    objectName: parent.objectName + "_detail"
                    x: 6
                    y: 20
                    width: parent.width - 12
                    height: 19
                    visible: typeof parent.modelData !== "string"
                    text: visible ? parent.modelData.detail || "" : ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 12
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
            }
        }
    }
    ListView {
        objectName: root.node.rowHeadersId || ""
        y: grid.y
        width: root.node.labelWidth
        height: grid.height
        interactive: false
        clip: true
        contentY: grid.contentY
        model: root.node.rowHeaders
        delegate: Item {
            id: rowHeader
            required property var modelData
            required property int index
            objectName: root.node.id + "_row_" + index
            width: root.node.labelWidth
            height: root.node.rowHeight
            Label {
                visible: !parent.modelData.children
                x: 6
                y: (parent.height - 38) / 2
                width: parent.width - 12
                height: 19
                text: parent.modelData.label || ""
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                font.weight: parent.modelData.all ? 600 : 400
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
            Label {
                visible: !parent.modelData.children
                x: 6
                y: parent.height / 2
                width: parent.width - 12
                height: 19
                text: parent.modelData.detail || ""
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
            Loader {
                id: headerLoader
                anchors.fill: parent
                active: !!rowHeader.modelData.children
                Component.onCompleted: if (active)
                    setSource(Qt.resolvedUrl("../../core/FrameView.qml"), {
                        theme: Qt.binding(() => root.theme),
                        scene: Qt.binding(() => ({
                                    nodes: rowHeader.modelData.children || []
                                }))
                    })
                Connections {
                    target: headerLoader.item
                    function onEvent(action) {
                        root.event(action);
                    }
                }
            }
        }
    }
    TableView {
        id: grid
        objectName: root.node.id + "Viewport"
        x: root.node.labelWidth
        y: root.node.headerHeight
        width: Math.max(1, root.width - x - 16)
        height: Math.max(1, root.height - y - 16)
        clip: true
        reuseItems: true
        keyNavigationEnabled: false
        boundsBehavior: Flickable.StopAtBounds
        model: root.sourceModel
        columnWidthProvider: () => root.node.cellWidth
        rowHeightProvider: () => root.node.rowHeight
        delegate: Item {
            id: cell
            required property int row
            required property int column
            required property var model
            implicitWidth: root.node.cellWidth
            implicitHeight: root.node.rowHeight
            property var cellScene: root.describeCell(root.node, model[root.node.cellRole || "cell"] || {}, row, column)
            function loadedCell(): var {
                return cellLoader.item;
            }
            function focusControl(name) {
                return loadedCell() ? loadedCell().focusControl(name) : false;
            }
            Loader {
                id: cellLoader
                anchors.fill: parent
                Component.onCompleted: setSource(Qt.resolvedUrl("../../core/FrameView.qml"), {
                    theme: Qt.binding(() => root.theme),
                    scene: Qt.binding(() => cell.cellScene)
                })
                Connections {
                    target: cellLoader.item
                    function onEvent(action) {
                        root.event(action);
                    }
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            objectName: root.node.verticalBarId || root.node.id + "VerticalBar"
            parent: root
            x: root.width - width
            y: grid.y
            height: grid.height
            theme: root.theme
            flickableTarget: grid
        }
        ScrollBar.horizontal: Controls.ScrollBar {
            objectName: root.node.horizontalBarId || root.node.id + "HorizontalBar"
            parent: root
            x: grid.x
            y: root.height - height
            width: grid.width
            theme: root.theme
            flickableTarget: grid
        }
    }
}
