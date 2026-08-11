import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Md3Popup {
    id: root
    property var actions: []
    property real preferredWidth: 244
    property double lastClosedAt: 0
    property bool sourceWasOpen: false
    property var lastSourceItem: null
    signal triggered(string command)
    signal secondaryTriggered(string command)
    width: Math.min(
        preferredWidth,
        Math.max(0, (parent ? parent.width : preferredWidth) - 8)
    )
    height: Math.min(
        implicitHeight,
        Math.max(0, (parent ? parent.height : implicitHeight) - 8)
    )
    padding: 8
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnReleaseOutside
    implicitHeight: menuColumn.implicitHeight + topPadding + bottomPadding
    onAboutToShow: ActionMenuCoordinator.activate(root)
    onOpened: clampToViewport()
    onWidthChanged: {
        if (opened)
            Qt.callLater(clampToViewport)
    }
    onHeightChanged: {
        if (opened)
            Qt.callLater(clampToViewport)
    }
    onClosed: {
        lastClosedAt = Date.now()
        ActionMenuCoordinator.release(root)
    }

    function clampToViewport() {
        if (!root.parent)
            return
        root.x = Math.max(
            4,
            Math.min(Math.max(4, root.parent.width - root.width - 4), root.x)
        )
        root.y = Math.max(
            4,
            Math.min(Math.max(4, root.parent.height - root.height - 4), root.y)
        )
    }

    function prepareOpen() {
        ActionMenuCoordinator.activate(root)
    }

    function openAt(sourceItem, localX, localY) {
        root.prepareOpen()
        if (!sourceItem || !root.parent) {
            root.open()
            return
        }
        const point = sourceItem.mapToItem(root.parent, localX, localY)
        root.x = Math.max(4, Math.min(root.parent.width - root.width - 4, point.x))
        root.y = Math.max(4, Math.min(root.parent.height - root.height - 4, point.y))
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
        root.prepareOpen()
        if (!sourceItem || !root.parent) {
            root.lastSourceItem = sourceItem
            root.open()
            return
        }

        const gap = 6
        const topLeft = sourceItem.mapToItem(root.parent, 0, 0)
        const below = sourceItem.mapToItem(root.parent, 0, sourceItem.height)
        root.x = Math.max(
            4,
            Math.min(root.parent.width - root.width - 4, topLeft.x)
        )

        if (below.y + gap + root.height <= root.parent.height - 4)
            root.y = below.y + gap
        else
            root.y = Math.max(4, topLeft.y - root.height - gap)

        root.lastSourceItem = sourceItem
        root.open()
    }

    function toggleBelow(sourceItem) {
        if (root.sourceWasOpen || root.opened) {
            root.close()
        } else {
            root.openBelow(sourceItem)
        }
        root.sourceWasOpen = false
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
            Repeater {
                model: root.actions
                delegate: Item {
                id: actionRow
                required property var modelData
                readonly property bool actionEnabled: modelData.enabled !== false
                readonly property bool hasAccent: !!modelData.accent
                readonly property color actionAccent: hasAccent
                    ? modelData.accent : root.theme.action
                visible: modelData.visible !== false
                width: parent.width
                height: !visible ? 0 : modelData.separator ? 9
                    : modelData.header ? 28 : modelData.status ? 48 : 40
                Rectangle {
                    visible: !!modelData.separator
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width
                    height: 1
                    color: root.theme.separator
                }
                Rectangle {
                    radius: root.theme.itemRadius
                    visible: !modelData.separator && !modelData.header
                    anchors.fill: parent
                    color: actionRow.hasAccent && !!modelData.checked
                        ? actionRow.actionAccent : root.theme.primaryText
                    opacity: actionRow.hasAccent && !!modelData.checked ? 0.14
                        : actionMouse.pressed ? 0.12
                        : actionMouse.containsMouse ? 0.08 : 0
                    Behavior on opacity {
                        NumberAnimation {
                            duration: actionMouse.containsMouse
                                ? root.theme.motionFast
                                : root.theme.motionMedium
                            easing.type: Easing.OutCubic
                        }
                    }
                }
                RowLayout {
                    visible: !modelData.separator
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 10
                    spacing: 12
                    Rectangle {
                        visible: !modelData.header && actionRow.hasAccent
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        radius: 12
                        color: Qt.rgba(
                            actionRow.actionAccent.r,
                            actionRow.actionAccent.g,
                            actionRow.actionAccent.b,
                            0.16
                        )
                        Rectangle {
                            anchors.centerIn: parent
                            width: 10
                            height: 10
                            radius: 5
                            color: actionRow.actionAccent
                        }
                    }
                    MaterialIcon {
                        visible: !modelData.header && !!modelData.icon
                        name: modelData.icon || "info"
                        size: 18
                        color: root.theme.secondaryText
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            Layout.fillWidth: true
                            text: modelData.translate === false
                                ? String(modelData.title || "")
                                : qsTr(modelData.title || "")
                            color: modelData.header || !actionRow.actionEnabled
                                ? root.theme.secondaryText
                                : actionRow.hasAccent && !!modelData.checked
                                    ? actionRow.actionAccent
                                    : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: modelData.header ? 10 : 12
                            font.weight: modelData.header ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                        }
                        Label {
                            visible: !!modelData.status && !modelData.header
                            Layout.fillWidth: true
                            text: modelData.statusTranslate === false
                                ? String(modelData.status || "")
                                : qsTr(modelData.status || "")
                            color: modelData.status === "Experimental"
                                ? root.theme.action : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 9
                            elide: Text.ElideRight
                        }
                    }
                    Rectangle {
                        visible: Number(modelData.badgeCount || 0) > 0
                        Layout.preferredWidth: Math.max(
                            18, menuBadgeLabel.implicitWidth + 8
                        )
                        Layout.preferredHeight: 18
                        radius: 9
                        color: root.theme.error
                        Label {
                            id: menuBadgeLabel
                            anchors.centerIn: parent
                            text: Number(modelData.badgeCount || 0) > 99
                                ? "99+" : String(modelData.badgeCount || 0)
                            color: root.theme.selectedText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 8
                            font.weight: Font.Bold
                        }
                    }
                    MaterialIcon {
                        visible: !!modelData.checked
                        name: "check_circle"
                        size: 18
                        color: actionRow.hasAccent
                            ? actionRow.actionAccent : root.theme.action
                    }
                    MaterialIcon {
                        visible: !!modelData.secondaryCommand
                        name: "update"
                        size: 15
                        color: secondaryMouse.containsMouse ? root.theme.action : root.theme.secondaryText
                    }
                }
                MouseArea {
                    id: actionMouse
                    visible: !modelData.separator && !modelData.header
                        && parent.actionEnabled
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.rightMargin: modelData.secondaryCommand ? 30 : 0
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: mouse => actionRipple.burst(mouse.x, mouse.y)
                    onClicked: {
                        root.close()
                        root.triggered(modelData.command)
                    }
                }
                MaterialRipple {
                    id: actionRipple
                    visible: !modelData.separator && !modelData.header
                    color: root.theme.ripple
                    shapeRadius: 10
                }
                MouseArea {
                    id: secondaryMouse
                    visible: !modelData.separator && !modelData.header && !!modelData.secondaryCommand
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    width: 30
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        root.close()
                        root.secondaryTriggered(modelData.secondaryCommand)
                    }
                    Md3ToolTip {
                        theme: root.theme
                        visible: secondaryMouse.containsMouse
                            && !root.theme.suppressToolTips
                        text: qsTr("Sync updates only")
                        delay: 400
                    }
                }
                }
            }
        }
        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            policy: menuFlickable.contentHeight > menuFlickable.height
                ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
        }
    }
}
