import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    objectName: "navigationDrawer"
    required property var model
    required property var theme
    property string selectedKey: "overview"
    property bool opened: false
    readonly property real drawerWidth: Math.min(360, Math.max(280, width - 56))
    readonly property real autoCloseDistance: 120
    signal selected(string key, string title, string command)

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
        color: "#000000"
        opacity: root.opened ? 0.32 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: root.opened ? 220 : 180
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
                duration: root.opened ? 260 : 200
                easing.type: root.opened ? Easing.OutCubic : Easing.InCubic
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 76

                Column {
                    anchors.left: parent.left
                    anchors.leftMargin: 20
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: closeButton.left
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
                        font.pixelSize: 11
                        elide: Text.ElideRight
                    }
                }
                CompactIconButton {
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

            ListView {
                id: list
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: 8
                Layout.bottomMargin: 8
                clip: true
                spacing: 0
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

                    readonly property bool isSection: entryType === "section"
                    readonly property bool isSeparator: entryType === "separator"
                    readonly property bool isSelected:
                        entryType === "link" && entryKey === root.selectedKey
                    readonly property color itemAccent:
                        accent.length > 0 ? accent : root.theme.action

                    width: list.width
                    height: !entryVisible ? 0
                        : isSeparator ? 16 : isSection ? 48 : 56
                    visible: entryVisible
                    enabled: available
                    opacity: available ? 1 : 0.38

                    Rectangle {
                        visible: entry.isSeparator
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 20
                        anchors.rightMargin: 20
                        height: 1
                        color: root.theme.separator
                    }

                    Item {
                        id: indicator
                        visible: !entry.isSeparator
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        anchors.topMargin: 4
                        anchors.bottomMargin: 4

                        Rectangle {
                            anchors.fill: parent
                            radius: height / 2
                            color: entry.isSelected ? root.theme.selected : "transparent"
                        }
                        Rectangle {
                            anchors.fill: parent
                            radius: height / 2
                            color: entry.isSelected
                                ? root.theme.action : root.theme.primaryText
                            opacity: navMouse.pressed ? 0.12
                                : navMouse.containsMouse ? 0.08 : 0
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: navMouse.containsMouse ? 100 : 140
                                    easing.type: Easing.OutCubic
                                }
                            }
                        }
                        MaterialRipple {
                            id: navRipple
                            shapeRadius: indicator.height / 2
                            color: entry.isSelected
                                ? Qt.rgba(
                                    root.theme.action.r,
                                    root.theme.action.g,
                                    root.theme.action.b,
                                    0.28
                                )
                                : root.theme.dark ? "#52ffffff" : "#38000000"
                        }
                    }

                    RowLayout {
                        visible: !entry.isSeparator
                        anchors.fill: indicator
                        anchors.leftMargin: 16 + entry.entryDepth * 16
                        anchors.rightMargin: 16
                        spacing: 12

                        Item {
                            Layout.preferredWidth: 32
                            Layout.preferredHeight: 32

                            MaterialIcon {
                                anchors.centerIn: parent
                                visible: entry.isSection
                                name: entry.expanded
                                    ? "keyboard_arrow_down" : "chevron_right"
                                size: 17
                                color: root.theme.secondaryText
                            }
                            ItemPreview {
                                anchors.centerIn: parent
                                visible: !entry.isSection
                                theme: root.theme
                                previewSize: 32
                                round: true
                                accent: entry.itemAccent
                                fallbackIcon: entry.glyph
                                selected: entry.isSelected
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            // Every drawer entry and section is defined by
                            // the project's SideBarWdg configuration.
                            text: entry.title
                            color: entry.isSelected
                                ? root.theme.action : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: entry.isSection ? 12 : 14
                            font.weight: entry.isSection
                                ? Font.DemiBold : entry.isSelected
                                    ? Font.Medium : Font.Normal
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }

                        Rectangle {
                            visible: entry.badge > 0
                            Layout.preferredWidth: Math.max(24, badgeLabel.implicitWidth + 12)
                            Layout.preferredHeight: 24
                            radius: 12
                            color: entry.isSelected
                                ? root.theme.action : root.theme.rowHover
                            Label {
                                id: badgeLabel
                                anchors.centerIn: parent
                                text: entry.badge > 99 ? "99+" : entry.badge
                                color: entry.isSelected
                                    ? root.theme.selectedText : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                            }
                        }
                    }

                    MouseArea {
                        id: navMouse
                        anchors.fill: indicator
                        hoverEnabled: true
                        enabled: !entry.isSeparator
                        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onPressed: mouse => navRipple.burst(mouse.x, mouse.y)
                        onClicked: {
                            if (entry.isSection) {
                                root.model.toggle_section(entry.index)
                            } else {
                                root.selected(entry.entryKey, entry.title, entry.command)
                                root.close()
                            }
                        }
                    }
                }

                ScrollBar.vertical: Md3ScrollBar {
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
            GradientStop { position: 0; color: "#26000000" }
            GradientStop { position: 1; color: "#00000000" }
        }
        Behavior on opacity {
            NumberAnimation { duration: 160 }
        }
    }
}
