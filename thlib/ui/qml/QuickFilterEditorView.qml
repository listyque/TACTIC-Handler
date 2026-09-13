import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

// The controller supplies only entries this user may configure. Show hidden
// never exposes anything removed by the server visibility policy.
Item {
    id: root

    required property var theme
    required property string windowId
    property var controller: quickFilterEditorController
    property var windows: windowModel
    objectName: "quickFilterEditorView"

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        Label {
            Layout.fillWidth: true
            text: root.controller.contextTitle
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
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

        Flickable {
            id: editorFlickable
            objectName: "quickFilterEditorScroll"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: editorContent.implicitHeight
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: editorContent
                objectName: "quickFilterEditorContent"
                width: Math.max(0, editorFlickable.width - editorScrollBar.reservedExtent - 8)
                spacing: 12

                Label {
                    objectName: "quickFilterEditorLoading"
                    Layout.fillWidth: true
                    visible: root.controller.busy
                    text: qsTr("Loading filters…")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.Wrap
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Selected filters")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }
                Label {
                    Layout.fillWidth: true
                    visible: root.controller.standardSelectionCount === 0
                    text: qsTr("No filters selected")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.Wrap
                }
                Repeater {
                    model: root.controller.standardSelections

                    delegate: Flow {
                        id: selectionGroup
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 7

                        Repeater {
                            model: selectionGroup.modelData.options

                            delegate: QuickFilterChip {
                                required property var modelData
                                objectName: "removeStandardFilter:" + selectionGroup.modelData.key + ":" + modelData.key
                                theme: root.theme
                                text: String(selectionGroup.modelData.title) + ": " + modelData.title
                                maximumChipWidth: selectionGroup.width
                                iconName: "close"
                                checked: true
                                subtle: true
                                enabled: root.controller.canEdit && !root.controller.busy
                                Accessible.name: qsTr("Remove filter") + ": " + text
                                onClicked: root.controller.remove_standard_selection(
                                    selectionGroup.modelData.key, modelData.key
                                )
                            }
                        }
                    }
                }
                Flow {
                    Layout.fillWidth: true
                    spacing: 8

                    Controls.Button {
                        objectName: "useCurrentQuickFiltersAsStandardButton"
                        theme: root.theme
                        visible: root.controller.canSaveDefaults
                        text: qsTr("Copy selection from current tab")
                        icon.name: "bookmark"
                        tonal: true
                        enabled: root.controller.canEdit && !root.controller.busy
                        onClicked: root.controller.use_current_as_standard()
                    }
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Clear selected filters")
                        icon.name: "filter_alt_off"
                        enabled: root.controller.canEdit
                            && root.controller.standardSelectionCount > 0
                            && !root.controller.busy
                        onClicked: root.controller.clear_standard()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: root.theme.outlineVariant
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Available filters")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }
                Controls.CheckBox {
                    id: showHidden
                    objectName: "showHiddenQuickFilters"
                    theme: root.theme
                    text: qsTr("Show hidden filters")
                    Layout.fillWidth: true
                }

                Label {
                    objectName: "quickFilterEditorEmpty"
                    Layout.fillWidth: true
                    visible: !root.controller.busy && root.controller.groups.length === 0
                        && root.controller.error.length === 0
                    text: qsTr("No filters available")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.Wrap
                }

                Repeater {
                    model: root.controller.groups

                    delegate: ColumnLayout {
                        id: groupSection
                        required property int index
                        required property var modelData
                        objectName: "quickFilterGroup:" + modelData.key
                        Layout.fillWidth: true
                        spacing: 6
                        visible: Boolean(modelData.enabled) || showHidden.checked

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Controls.CheckBox {
                                objectName: "quickFilterGroupToggle:" + groupSection.modelData.key
                                theme: root.theme
                                Layout.fillWidth: true
                                text: String(groupSection.modelData.title)
                                checked: Boolean(groupSection.modelData.enabled)
                                enabled: root.controller.canEdit && !root.controller.busy
                                onToggled: root.controller.set_group_enabled(groupSection.index, checked)
                            }
                            Controls.CompactIconButton {
                                theme: root.theme
                                iconName: "arrow_upward"
                                toolTip: qsTr("Move up")
                                enabled: root.controller.canEdit && groupSection.index > 0
                                    && !root.controller.busy
                                onClicked: root.controller.move_group(groupSection.index, -1)
                            }
                            Controls.CompactIconButton {
                                theme: root.theme
                                iconName: "arrow_downward"
                                toolTip: qsTr("Move down")
                                enabled: root.controller.canEdit && groupSection.index
                                    < root.controller.groups.length - 1 && !root.controller.busy
                                onClicked: root.controller.move_group(groupSection.index, 1)
                            }
                        }

                        Flow {
                            id: optionFlow
                            Layout.fillWidth: true
                            spacing: 7
                            visible: Boolean(groupSection.modelData.enabled)

                            Repeater {
                                model: groupSection.modelData.options

                                delegate: QuickFilterChip {
                                    required property var modelData
                                    objectName: "quickFilterOption:" + groupSection.modelData.key + ":" + modelData.key
                                    theme: root.theme
                                    text: String(modelData.title || "")
                                    maximumChipWidth: optionFlow.width
                                    accent: modelData.accent || root.theme.action
                                    showAccentMarker: Boolean(modelData.showAccentMarker)
                                    subtle: true
                                    checked: Boolean(modelData.selected)
                                    enabled: root.controller.canEdit && !root.controller.busy
                                    onClicked: root.controller.set_option_selected(
                                        groupSection.modelData.key, modelData.key, !checked
                                    )
                                }
                            }
                        }
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                id: editorScrollBar
                objectName: "quickFilterEditorScrollBar"
                theme: root.theme
                flickableTarget: editorFlickable
            }
        }

        Flow {
            Layout.fillWidth: true
            layoutDirection: Qt.RightToLeft
            spacing: 8

            Controls.Button {
                objectName: "saveQuickFilterEditorButton"
                theme: root.theme
                text: qsTr("SAVE")
                icon.name: "save"
                highlighted: true
                enabled: root.controller.canEdit && !root.controller.busy
                onClicked: root.controller.save()
            }
            Controls.Button {
                objectName: "saveQuickFilterDefaultsButton"
                theme: root.theme
                visible: root.controller.canSaveDefaults
                text: qsTr("Save as defaults on server")
                icon.name: "cloud_upload"
                enabled: root.controller.canEdit && !root.controller.busy
                onClicked: root.controller.save_defaults()
            }
            Controls.Button {
                objectName: "cancelQuickFilterEditorButton"
                theme: root.theme
                text: qsTr("CANCEL")
                enabled: !root.controller.busy
                onClicked: {
                    root.windows.close_window(root.windowId)
                }
            }
        }
    }
}
