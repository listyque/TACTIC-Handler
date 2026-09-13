import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Rectangle {
    id: root

    required property var theme
    required property var treeModel
    required property var treeController
    property bool validContext: true
    property bool showVersionChooser: false
    property bool togglersExpanded: false
    property string emptyText: qsTr("Select a Search Type first")
    property string treeObjectName: "processSelectionTree"
    property string rowObjectName: "processSelectionTreeRow"

    radius: root.theme.itemRadius
    color: root.theme.surfaceContainerLow
    border.width: 1
    border.color: root.theme.outlineVariant
    clip: true

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 4
        spacing: 4

        Controls.SmoothListView {
            theme: root.theme
            id: treeView
            objectName: root.treeObjectName
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.treeModel

            delegate: Item {
                id: treeRow

                required property int index
                required property string title
                required property string kind
                required property int depth
                required property bool checkable
                required property bool checked
                required property bool expanded
                required property bool rowVisible
                required property bool selected
                required property string accent
                required property bool hasChildren

                objectName: root.rowObjectName
                width: treeView.width
                height: rowVisible ? 30 : 0
                visible: height > 0
                clip: true

                readonly property string displayTitle:
                    treeRow.kind === "child"
                        ? treeRow.title + qsTr(" (child)")
                        : treeRow.kind === "builtin"
                            ? treeRow.title + qsTr(" (builtin)")
                            : treeRow.title
                readonly property bool showKindIcon:
                    treeRow.kind === "child" || treeRow.kind === "process"

                Rectangle {
                    anchors.fill: parent
                    color: treeRow.selected
                        ? root.theme.contentSelection
                        : rowMouse.containsMouse
                            ? root.theme.rowHover
                            : treeRow.index % 2
                                ? root.theme.surfaceContainerHigh
                                : root.theme.surfaceContainerLow
                    border.width: treeRow.selected ? 1 : 0
                    border.color: root.theme.contentAccent

                    MouseArea {
                        id: rowMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: mouse => root.treeController.select_row(
                            treeRow.index,
                            Boolean(mouse.modifiers & Qt.ControlModifier)
                        )
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 5 + treeRow.depth * 18
                        anchors.rightMargin: 6
                        spacing: 3

                        Controls.CompactIconButton {
                            Layout.preferredWidth: 20
                            Layout.preferredHeight: 20
                            theme: root.theme
                            visible: treeRow.hasChildren
                            iconName: treeRow.expanded
                                ? "keyboard-arrow-down"
                                : "keyboard-arrow-right"
                            iconSize: 13
                            toolTip: treeRow.expanded
                                ? qsTr("Collapse") : qsTr("Expand")
                            onClickedWithModifiers: modifiers =>
                                root.treeController.toggle_expanded(
                                    treeRow.index,
                                    Boolean(modifiers & Qt.ShiftModifier)
                                )
                        }
                        Item {
                            Layout.preferredWidth: 20
                            Layout.preferredHeight: 20
                            visible: !treeRow.hasChildren
                        }
                        Controls.CheckBox {
                            Layout.preferredWidth: 28
                            Layout.preferredHeight: 24
                            theme: root.theme
                            compact: true
                            visible: treeRow.checkable
                            checked: treeRow.checked
                            onToggled: root.treeController.set_checked(
                                treeRow.index, checked
                            )
                        }
                        Item {
                            Layout.preferredWidth: 28
                            Layout.preferredHeight: 24
                            visible: !treeRow.checkable
                        }
                        Controls.MaterialIcon {
                            objectName: "processSelectionIcon_" + treeRow.kind
                            visible: treeRow.showKindIcon
                            Layout.preferredWidth: visible ? 16 : 0
                            Layout.preferredHeight: 16
                            Layout.leftMargin: visible ? 4 : 0
                            name: treeRow.kind === "child"
                                ? "view-sequential"
                                : "process-marker"
                            forceSolid: treeRow.kind === "process"
                            size: treeRow.kind === "process" ? 12 : 16
                            color: treeRow.accent.length
                                ? treeRow.accent : root.theme.secondaryText
                        }
                        Label {
                            objectName: "processSelectionTitle_" + treeRow.kind
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            Layout.leftMargin: 4
                            text: treeRow.displayTitle
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.body
                            elide: Text.ElideRight
                        }
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: treeView
            }
        }

        GridLayout {
            id: toggleGrid
            Layout.fillWidth: true
            visible: root.togglersExpanded
            columns: root.width < 720 ? 1 : 2
            columnSpacing: 4
            rowSpacing: 4

            Controls.Button {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Toggle All")
                icon.name: "checkbox-multiple-marked-outline"
                flat: true
                onClicked: root.treeController.toggle_kind("all")
            }
            Controls.Button {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Toggle Process")
                icon.name: "checkbox-blank-circle"
                flat: true
                onClicked: root.treeController.toggle_kind("process")
            }
            Controls.Button {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Toggle Builtin Processes")
                icon.name: "checkbox-blank-circle"
                flat: true
                onClicked: root.treeController.toggle_kind("builtin")
            }
            Controls.Button {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Toggle Children")
                icon.name: "view-sequential"
                flat: true
                onClicked: root.treeController.toggle_kind("child")
            }

            Controls.SegmentedButton {
                Layout.columnSpan: toggleGrid.columns
                Layout.fillWidth: true
                visible: root.showVersionChooser
                theme: root.theme
                segmentWidth: 145
                minimumSegmentWidth: 105
                currentValue: root.showVersionChooser
                    && root.treeController.fullSync
                    ? "full" : "versionless"
                model: [
                    { label: "Versionless Sync", value: "versionless" },
                    { label: "Full Sync", value: "full" }
                ]
                onActivated: value =>
                    root.treeController.set_full_sync(value === "full")
            }
        }

        Controls.Button {
            Layout.fillWidth: true
            theme: root.theme
            text: root.togglersExpanded
                ? qsTr("Hide Togglers") : qsTr("Show Togglers")
            icon.name: root.togglersExpanded
                ? "expand-more" : "expand-less"
            flat: true
            onClicked: root.togglersExpanded = !root.togglersExpanded
        }
    }

    Column {
        anchors.centerIn: parent
        visible: !root.validContext
        spacing: 6

        Controls.MaterialIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            name: "account-tree"
            size: 26
            color: root.theme.disabledText
        }
        Label {
            text: root.emptyText
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Typography.body
        }
    }
}
