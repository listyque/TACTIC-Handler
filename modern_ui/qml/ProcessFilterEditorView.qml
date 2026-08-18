import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property string windowId
    readonly property bool compact: width < 720

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 11

                Rectangle {
                    Layout.preferredWidth: 44
                    Layout.preferredHeight: 44
                    radius: root.theme.itemRadius
                    color: root.theme.secondaryContainer
                    MaterialIcon {
                        anchors.centerIn: parent
                        name: "filter-alt"
                        size: 21
                        color: root.theme.action
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 2
                    Label {
                        text: qsTr("Process tree visibility")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: processFilterEditorController.context_title
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.body
                        elide: Text.ElideRight
                    }
                }
                Label {
                    visible: !root.compact
                    text: qsTr("Ctrl-click selects several rows")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.compact ? 2 : 4
            columnSpacing: 8
            rowSpacing: 8

            Md3Button {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("None / All")
                icon.name: "select_all"
                onClicked: processFilterEditorController.toggle_kind("all")
            }
            Md3Button {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Toggle Processes")
                icon.name: "process"
                onClicked: processFilterEditorController.toggle_kind("process")
            }
            Md3Button {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Toggle Built-ins")
                icon.name: "settings-suggest"
                onClicked: processFilterEditorController.toggle_kind("builtin")
            }
            Md3Button {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Toggle Children")
                icon.name: "schema"
                onClicked: processFilterEditorController.toggle_kind("child")
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true

            SmoothListView {
                id: processTree
                anchors.fill: parent
                anchors.margins: 6
                anchors.rightMargin: 12
                clip: true
                model: processFilterModel

                delegate: Item {
                    id: processRow
                    required property int index
                    required property string title
                    required property string subtitle
                    required property string kind
                    required property string group
                    required property int depth
                    required property bool checkable
                    required property bool checked
                    required property bool expanded
                    required property bool rowVisible
                    required property bool selected
                    required property string accent

                    width: processTree.width
                    height: rowVisible ? 48 : 0
                    visible: height > 0
                    clip: true

                    Rectangle {
                        anchors.fill: parent
                        anchors.topMargin: 2
                        anchors.bottomMargin: 2
                        radius: root.theme.itemRadius
                        color: processRow.selected
                            ? root.theme.selected : rowMouse.containsMouse
                                ? root.theme.rowHover
                                : root.theme.surfaceContainerHigh
                        border.width: processRow.selected ? 1 : 0
                        border.color: root.theme.action

                        MouseArea {
                            id: rowMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: mouse =>
                                processFilterEditorController.select_row(
                                    processRow.index,
                                    Boolean(mouse.modifiers & Qt.ControlModifier)
                                )
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8 + processRow.depth * 20
                            anchors.rightMargin: 10
                            spacing: 7

                            CompactIconButton {
                                Layout.preferredWidth: 26
                                Layout.preferredHeight: 26
                                theme: root.theme
                                visible: processRow.kind === "child"
                                    || processRow.kind === "pipeline"
                                iconName: processRow.expanded
                                    ? "keyboard_arrow_down"
                                    : "keyboard_arrow_right"
                                toolTip: processRow.expanded
                                    ? qsTr("Collapse") : qsTr("Expand")
                                onClicked:
                                    processFilterEditorController
                                        .toggle_expanded(processRow.index)
                            }
                            Item {
                                Layout.preferredWidth: 26
                                Layout.preferredHeight: 26
                                visible: processRow.kind !== "child"
                                    && processRow.kind !== "pipeline"
                            }
                            Md3CheckBox {
                                theme: root.theme
                                visible: processRow.checkable
                                checked: processRow.checked
                                onToggled:
                                    processFilterEditorController.set_checked(
                                        processRow.index, checked
                                    )
                            }
                            Item {
                                Layout.preferredWidth: 22
                                Layout.preferredHeight: 22
                                visible: !processRow.checkable
                            }
                            MaterialIcon {
                                name: processRow.kind === "child" ? "schema"
                                    : processRow.kind === "builtin"
                                        ? "settings-suggest" : "process"
                                size: 17
                                color: processRow.accent.length
                                    ? processRow.accent : root.theme.action
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.minimumWidth: 0
                                spacing: 0
                                Label {
                                    Layout.fillWidth: true
                                    text: processRow.title
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.bodyLarge
                                    font.weight: processRow.kind === "pipeline"
                                        || processRow.kind === "child"
                                        ? Font.DemiBold : Font.Normal
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: processRow.kind === "child"
                                        ? qsTr("Child Search Type")
                                        : processRow.kind === "pipeline"
                                            ? qsTr("Pipeline")
                                        : processRow.kind === "builtin"
                                            ? qsTr("Built-in process")
                                            : processRow.subtitle
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                            Label {
                                visible: !root.compact
                                    && processRow.kind === "process"
                                    && processRow.group.length > 0
                                text: processRow.group
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.caption
                            }
                        }
                    }
                }

                ScrollBar.vertical: Md3ScrollBar {
                    theme: root.theme
                    flickableTarget: processTree
                }
            }

            Column {
                anchors.centerIn: parent
                visible: !processFilterEditorController.valid_context
                spacing: 8
                MaterialIcon {
                    anchors.horizontalCenter: parent.horizontalCenter
                    name: "filter-alt"
                    size: 28
                    color: root.theme.disabledText
                }
                Label {
                    text: qsTr("Select a Search Tab first")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 62
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    text: processFilterEditorController.dirty
                        ? qsTr("Visibility has unsaved changes") : ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    flat: true
                    onClicked: {
                        processFilterEditorController.cancel()
                        windowModel.close_window(root.windowId)
                    }
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Save")
                    icon.name: "save"
                    enabled: processFilterEditorController.valid_context
                    onClicked: processFilterEditorController.save()
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Save and close")
                    icon.name: "done"
                    highlighted: true
                    enabled: processFilterEditorController.valid_context
                    onClicked: {
                        if (processFilterEditorController.save())
                            windowModel.close_window(root.windowId)
                    }
                }
            }
        }
    }
}
