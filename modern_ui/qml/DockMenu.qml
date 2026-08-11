import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A QML counterpart to Ui_checkInOutWidget.fill_gear_menu().  The model is
// Python-owned, so closing/reopening a dock never leaves stale QML state.
Md3Popup {
    id: root
    property var panelModel
    property var lastSourceItem: null
    property double lastClosedAt: 0
    width: Math.min(244, Math.max(0, (parent ? parent.width : 244) - 8))
    height: Math.min(
        implicitHeight,
        Math.max(0, (parent ? parent.height : implicitHeight) - 8)
    )
    implicitHeight: menuColumn.implicitHeight + topPadding + bottomPadding
    padding: 8
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnReleaseOutside
    onAboutToShow: ActionMenuCoordinator.activate(root)
    onClosed: {
        lastClosedAt = Date.now()
        ActionMenuCoordinator.release(root)
    }

    function openAt(sourceItem, localX, localY) {
        if (!sourceItem || !root.parent) {
            root.open()
            return
        }
        const point = sourceItem.mapToItem(root.parent, localX, localY)
        root.x = Math.max(6, Math.min(root.parent.width - root.width - 6, point.x))
        root.y = Math.max(6, Math.min(root.parent.height - root.implicitHeight - 6, point.y))
        root.open()
    }

    function openBelow(sourceItem) {
        const sameSource = root.lastSourceItem === sourceItem
        if (sameSource && (
                root.opened || Date.now() - root.lastClosedAt < 140)) {
            if (root.opened)
                root.close()
            return
        }
        ActionMenuCoordinator.activate(root)
        root.lastSourceItem = sourceItem
        openAt(sourceItem, sourceItem ? sourceItem.width - root.width : 0,
               sourceItem ? sourceItem.height + 5 : 0)
    }

    function toggleBelow(sourceItem) {
        openBelow(sourceItem)
    }

    contentItem: Flickable {
        id: menuFlickable
        clip: true
        contentWidth: width
        contentHeight: menuColumn.implicitHeight
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: menuColumn
            width: menuFlickable.width
            spacing: 1

            Label {
                width: parent.width
                height: 28
                leftPadding: 12
                verticalAlignment: Text.AlignVCenter
                text: qsTr("Workspace panels")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }

            Repeater {
                model: root.panelModel
                delegate: Item {
                    id: panelRow
                    required property string panelId
                    required property string title
                    required property string kind
                    required property bool panelVisible
                    required property bool closable
                    width: parent.width
                    height: 40
                    property string iconName: kind === "snapshot" ? "movie"
                        : kind === "tasks" ? "task_alt"
                        : kind === "task_calendar" ? "calendar_month"
                        : kind === "drop_plate" ? "publish"
                        : kind === "notes" ? "comment"
                        : kind === "description" ? "description"
                        : kind === "advanced_search" ? "search"
                        : kind === "fast_controls" ? "tune"
                        : kind === "repo_sync_queue" ? "sync"
                        : kind === "commit_queue" ? "publish"
                        : kind === "watch_folders" ? "folder"
                        : kind === "db_table" ? "table"
                        : "view_kanban"

                    Rectangle {
                        anchors.fill: parent
                        radius: root.theme.itemRadius
                        color: root.theme.primaryText
                        opacity: panelMouse.pressed ? 0.12
                            : panelMouse.containsMouse ? 0.08 : 0
                        Behavior on opacity {
                            NumberAnimation {
                                duration: panelMouse.containsMouse
                                    ? root.theme.motionFast
                                    : root.theme.motionMedium
                                easing.type: Easing.OutCubic
                            }
                        }
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 10
                        spacing: 12
                        MaterialIcon {
                            name: panelRow.iconName
                            size: 18
                            color: root.theme.secondaryText
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr(panelRow.title)
                            color: panelRow.closable || !panelRow.panelVisible
                                ? root.theme.primaryText
                                : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                        MaterialIcon {
                            visible: panelRow.panelVisible
                            name: "check_circle"
                            size: 18
                            color: root.theme.action
                        }
                    }
                    MouseArea {
                        id: panelMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: panelRow.closable
                            || !panelRow.panelVisible
                            ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onPressed: mouse =>
                            panelRipple.burst(mouse.x, mouse.y)
                        onClicked: {
                            if (panelRow.closable || !panelRow.panelVisible) {
                                root.panelModel.toggle_panel(panelRow.panelId)
                                root.close()
                            }
                        }
                    }
                    MaterialRipple {
                        id: panelRipple
                        color: root.theme.ripple
                        shapeRadius: 10
                    }
                }
            }

            Item {
                width: parent.width
                height: 9
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width
                    height: 1
                    color: root.theme.separator
                }
            }

            Item {
                width: parent.width
                height: 40
                Rectangle {
                    anchors.fill: parent
                        radius: root.theme.itemRadius
                    color: root.theme.primaryText
                    opacity: resetMouse.pressed ? 0.12
                        : resetMouse.containsMouse ? 0.08 : 0
                    Behavior on opacity {
                        NumberAnimation {
                            duration: resetMouse.containsMouse
                                ? root.theme.motionFast
                                : root.theme.motionMedium
                            easing.type: Easing.OutCubic
                        }
                    }
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 10
                    spacing: 12
                    MaterialIcon {
                        name: "sync"
                        size: 18
                        color: root.theme.secondaryText
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Reset layout")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                    }
                }
                MouseArea {
                    id: resetMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: mouse =>
                        resetRipple.burst(mouse.x, mouse.y)
                    onClicked: {
                        root.panelModel.reset_layout()
                        root.close()
                    }
                }
                MaterialRipple {
                    id: resetRipple
                    color: root.theme.ripple
                    shapeRadius: 10
                }
            }
        }

        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            flickableTarget: menuFlickable
            policy: menuFlickable.contentHeight > menuFlickable.height
                ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
        }
    }
}
