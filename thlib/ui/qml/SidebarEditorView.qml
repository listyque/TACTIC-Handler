import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property var controller: sidebarEditorController
    readonly property int scrollContentGap: 16
    readonly property string presetContextKey:
        String(controller.selectedRow) + "|"
        + String(controller.selectedEntry.searchType || "")

    function switchEditorMode(value) {
        // Commit the currently focused Simple editor before its Loader is
        // replaced. Text fields write their value on editingFinished.
        root.forceActiveFocus(Qt.MouseFocusReason)
        Qt.callLater(function() {
            root.controller.set_mode(value)
        })
    }

    onPresetContextKeyChanged: Qt.callLater(
        controller.refresh_search_presets
    )

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainer
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 10

                Controls.MaterialIcon {
                    name: "edit"
                    size: 20
                    color: root.theme.action
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Sidebar Editor")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Project") + ": " + root.controller.projectTitle
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        elide: Text.ElideRight
                    }
                }
                Controls.SegmentedButton {
                    theme: root.theme
                    currentValue: root.controller.mode
                    segmentWidth: 94
                    model: [
                        {"value": "simple", "label": "Simple", "icon": "view_list"},
                        {"value": "xml", "label": "XML", "icon": "code"}
                    ]
                    onActivated: value => root.switchEditorMode(value)
                }
                Controls.CompactIconButton {
                    objectName: "sidebarEditorHelpButton"
                    theme: root.theme
                    iconName: "help"
                    round: true
                    toolTip: qsTr("Help")
                    Accessible.name: toolTip
                    onClicked: windowModel.open_help("sidebar_editor")
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "refresh"
                    round: true
                    toolTip: qsTr("Reload sidebar")
                    enabled: !root.controller.busy
                    onClicked: root.controller.reload()
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: root.controller.error.length > 0
            text: root.controller.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }

        SplitView {
            id: editorSplit
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal
            handle: Rectangle {
                implicitWidth: 10
                color: "transparent"

                Rectangle {
                    anchors.centerIn: parent
                    width: 1
                    height: Math.max(0, parent.height - 18)
                    color: root.theme.outlineVariant
                }
            }

            Rectangle {
                SplitView.preferredWidth: Math.max(280, root.width * 0.30)
                SplitView.minimumWidth: 260
                SplitView.maximumWidth: Math.max(360, root.width * 0.54)
                color: root.theme.surfaceContainerLow
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 52
                        Layout.leftMargin: 14
                        Layout.rightMargin: 8
                        spacing: 6

                        Controls.MaterialIcon {
                            name: "view_list"
                            size: 17
                            color: root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            text: qsTr("Sidebar items")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "filter-alt"
                            iconColor: root.controller.handlerOnly
                                ? root.theme.action : root.theme.secondaryText
                            backgroundColor: root.controller.handlerOnly
                                ? root.theme.secondaryContainer : "transparent"
                            toolTip: root.controller.handlerOnly
                                ? qsTr("Show all project views")
                                : qsTr("Show only TACTIC Handler")
                            onClicked: root.controller.set_handler_only(
                                !root.controller.handlerOnly
                            )
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 14
                        Layout.rightMargin: 8
                        Layout.bottomMargin: 8
                        spacing: 6

                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Add")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "add"
                            toolTip: qsTr("Add link")
                            onClicked: root.controller.add_entry("link")
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "create-new-folder"
                            toolTip: qsTr("Add section")
                            onClicked: root.controller.add_entry("section")
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            objectName: "sidebarAddSeparatorButton"
                            iconName: "sidebar-separator"
                            toolTip: qsTr("Add separator")
                            onClicked: root.controller.add_entry("separator")
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: root.theme.separator
                    }

                    ListView {
                        id: previewList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.topMargin: 8
                        Layout.bottomMargin: 8
                        clip: true
                        spacing: 0
                        rightMargin: root.scrollContentGap
                        model: sidebarEntryModel
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: Item {
                            id: previewEntry
                            required property int index
                            required property string title
                            required property string entryType
                            required property string glyph
                            required property string accent
                            required property string searchType
                            required property int depth
                            required property int displayDepth
                            required property bool selected
                            required property bool included
                            required property bool expanded
                            required property bool entryVisible
                            required property bool hasChildren

                            width: Math.max(
                                0,
                                previewList.width - previewList.rightMargin
                            )
                            height: !entryVisible ? 0
                                : editorSidebarRow.implicitHeight
                            visible: entryVisible

                            SidebarTreeRow {
                                id: editorSidebarRow
                                anchors.fill: parent
                                theme: root.theme
                                rowType: previewEntry.entryType
                                title: previewEntry.title
                                glyph: previewEntry.glyph
                                depth: previewEntry.displayDepth
                                accent: previewEntry.accent
                                expanded: previewEntry.expanded
                                selected: previewEntry.selected
                                dimmed: !previewEntry.included
                                interactive: true
                                onActivated: root.controller.activate_entry(
                                    previewEntry.index
                                )
                            }
                        }

                        ScrollBar.vertical: Controls.ScrollBar {
                            theme: root.theme
                            flickableTarget: previewList
                        }

                        Label {
                            anchors.centerIn: parent
                            visible: previewList.count === 0 && !root.controller.busy
                            text: root.controller.handlerOnly
                                ? qsTr("TACTIC Handler branch was not found")
                                : qsTr("This sidebar has no items")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                        }
                    }
                }
            }

            Rectangle {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 390
                color: root.theme.surfaceContainerLow
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                Loader {
                    anchors.fill: parent
                    anchors.margins: 14
                    sourceComponent: root.controller.mode === "xml"
                        ? xmlEditor : simpleEditor
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainer

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    text: root.controller.dirty
                        ? qsTr("Sidebar has unsaved changes")
                        : qsTr("Sidebar is up to date")
                    color: root.controller.dirty
                        ? root.theme.action : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("DISCARD")
                    icon.name: "undo"
                    enabled: root.controller.dirty && !root.controller.busy
                    onClicked: root.controller.discard()
                }
                Controls.Button {
                    theme: root.theme
                    text: root.controller.busy ? qsTr("Saving...") : qsTr("SAVE")
                    objectName: "sidebarSaveButton"
                    icon.name: "save"
                    highlighted: true
                    enabled: root.controller.dirty && !root.controller.busy
                    onClicked: {
                        root.forceActiveFocus()
                        root.controller.save()
                    }
                }
            }
        }
    }

    Component {
        id: simpleEditor

        SidebarEntrySettings {
            theme: root.theme
            controller: root.controller
            securityModel: sidebarSecurityGroupModel
        }
    }

    Component {
        id: xmlEditor

        ColumnLayout {
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Label {
                        text: qsTr("Advanced XML")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: root.controller.selectedRow >= 0
                            ? qsTr("Selected element") + ": "
                                + String(root.controller.selectedEntry.name || "")
                            : qsTr("Select a sidebar element first")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("APPLY XML")
                    icon.name: "code"
                    enabled: root.controller.selectedRow >= 0
                    onClicked: root.controller.apply_xml()
                }
            }

            Controls.TextArea {
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                text: root.controller.xmlText
                enabled: root.controller.selectedRow >= 0
                wrapMode: TextEdit.NoWrap
                font.family: "Consolas"
                font.pointSize: Controls.Typography.body
                onTextChanged: root.controller.set_xml_text(text)
            }
        }
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        visible: root.controller.busy
        theme: root.theme
        message: qsTr("Loading sidebar configuration...")
        cancellable: false
    }
}
