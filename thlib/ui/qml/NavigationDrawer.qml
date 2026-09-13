import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    objectName: "navigationDrawer"
    required property var model
    required property var theme
    property string selectedKey: "overview"
    property bool opened: false
    property bool sidebarEditingAvailable: false
    readonly property real drawerWidth: Math.min(360, Math.max(280, width - 56))
    readonly property real autoCloseDistance: 120
    signal selected(string key, string title, string command)
    signal editSidebarRequested()

    anchors.fill: parent
    z: 100
    visible: opened || panel.x > -panel.width
    focus: visible

    function open() {
        opened = true
        forceActiveFocus()
    }
    function close() {
        opened = false
    }

    Keys.onEscapePressed: close()

    Rectangle {
        id: scrim
        anchors.fill: parent
        color: root.theme.blackMix
        opacity: root.opened ? 0.32 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: root.opened ? theme.motionExtended : theme.motionSlow
                easing.type: root.opened ? Easing.OutCubic : Easing.InCubic
            }
        }
        MouseArea {
            id: scrimMouse
            anchors.fill: parent
            enabled: root.opened
            hoverEnabled: true
            cursorShape: enabled
                ? Qt.PointingHandCursor : Qt.ArrowCursor
            preventStealing: true
            onPositionChanged: mouse => {
                if (mouse.x > root.drawerWidth + root.autoCloseDistance)
                    root.close()
            }
            onWheel: wheel => wheel.accepted = true
            onClicked: root.close()
        }
    }

    Rectangle {
        id: panel
        width: root.drawerWidth
        height: root.height
        x: root.opened ? 0 : -width
        radius: 0
        color: root.theme.panelRaised
        clip: true
        Behavior on x {
            NumberAnimation {
                duration: root.opened ? theme.motionExtended : theme.motionSlow
                easing.type: root.opened ? Easing.OutCubic : Easing.InCubic
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
            onWheel: wheel => wheel.accepted = true
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 76

                WheelHandler {
                    target: null
                    blocking: true
                    onWheel: event => event.accepted = true
                }

                Column {
                    anchors.left: parent.left
                    anchors.leftMargin: 20
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: editSidebarButton.visible
                        ? editSidebarButton.left : closeButton.left
                    anchors.rightMargin: 12
                    spacing: 1
                    Label {
                        width: parent.width
                        text: qsTr("Navigation")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        width: parent.width
                        text: qsTr("Project workspace")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        elide: Text.ElideRight
                    }
                }
                Controls.CompactIconButton {
                    id: editSidebarButton
                    objectName: "editSidebarButton"
                    visible: root.sidebarEditingAvailable
                    anchors.top: parent.top
                    anchors.right: closeButton.left
                    anchors.topMargin: 8
                    anchors.rightMargin: 2
                    width: 40
                    height: 40
                    theme: root.theme
                    iconName: "edit"
                    round: true
                    toolTip: qsTr("Edit project sidebar")
                    onClicked: {
                        root.close()
                        root.editSidebarRequested()
                    }
                }
                Controls.CompactIconButton {
                    id: closeButton
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.topMargin: 8
                    anchors.rightMargin: 8
                    width: 40
                    height: 40
                    theme: root.theme
                    iconName: "close"
                    round: true
                    toolTip: qsTr("Close navigation")
                    onClicked: root.close()
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 1
                color: root.theme.separator
            }

            Controls.SmoothListView {
                theme: root.theme
                id: list
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: 8
                Layout.bottomMargin: 8
                clip: true
                spacing: 0
                rightMargin: navigationScrollBar.reservedExtent
                boundsBehavior: Flickable.StopAtBounds
                model: root.model

                delegate: Item {
                    id: entry
                    required property int index
                    required property string entryKey
                    required property string title
                    required property string glyph
                    required property string command
                    required property int badge
                    required property bool available
                    required property string entryType
                    required property int entryDepth
                    required property string accent
                    required property bool expanded
                    required property bool entryVisible

                    width: Math.max(0, list.width - list.rightMargin)
                    height: !entryVisible ? 0
                        : sidebarRow.implicitHeight
                    visible: entryVisible
                    SidebarTreeRow {
                        id: sidebarRow
                        anchors.fill: parent
                        theme: root.theme
                        rowType: entry.entryType
                        title: entry.title
                        glyph: entry.glyph
                        depth: entry.entryDepth
                        accent: entry.accent
                        expanded: entry.expanded
                        selected: entry.entryType === "link"
                            && entry.entryKey === root.selectedKey
                        badge: entry.badge
                        dimmed: !entry.available
                        interactive: entry.available && entry.entryType !== "separator"
                        Accessible.description: entry.available ? "" : unavailableHint.text
                        onActivated: {
                            if (entry.entryType === "section") {
                                root.model.toggle_section(entry.index)
                            } else {
                                root.selected(entry.entryKey, entry.title, entry.command)
                                root.close()
                            }
                        }
                    }
                    HoverHandler {
                        id: unavailableHover
                        enabled: !entry.available && entry.entryType === "link"
                    }
                    Controls.ToolTip {
                        id: unavailableHint
                        objectName: "sidebarUnavailableHint"
                        theme: root.theme
                        visible: unavailableHover.hovered
                        text: qsTr("This sidebar item has no Search Type. Configure it in Sidebar Editor.")
                    }
                }

                ScrollBar.vertical: Controls.ScrollBar {
                    id: navigationScrollBar
                    theme: root.theme
                    flickableTarget: list
                }
            }
        }
    }

    Rectangle {
        x: panel.x + panel.width
        width: 14
        height: root.height
        visible: panel.x + panel.width > 0
        opacity: root.opened ? 1 : 0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: root.theme.popupShadow }
            GradientStop { position: 1; color: "transparent" }
        }
        Behavior on opacity {
            NumberAnimation { duration: theme.motionMedium }
        }
    }
}
