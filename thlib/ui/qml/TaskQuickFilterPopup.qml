import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.ScrollablePopup {
    id: root

    parent: Overlay.overlay
    preferredSurfaceWidth: 440
    minimumSurfaceWidth: 280
    maximumSurfaceHeight: 400
    contentSpacing: 0

    function openBelow(sourceItem) {
        root.openBelowItem(sourceItem, true, 6)
    }

    function toggleBelow(sourceItem) {
        root.toggleBelowItem(sourceItem, true, 6)
    }

    Column {
        id: filterColumn
        width: parent.width
        spacing: 16

            RowLayout {
                width: parent.width
                Label {
                    Layout.fillWidth: true
                    text: qsTr("QUICK FILTERS")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                }
                QuickFilterChip {
                    theme: root.theme
                Layout.preferredHeight: 28
                    text: qsTr("ALL")
                    checked: tasksController.activeQuickFilterCount === 0
                    onClicked: {
                        tasksController.clear_quick_filters()
                        root.close()
                    }
                }
            }

            Repeater {
                model: tasksController.quickFilterGroups
                delegate: Column {
                    id: filterGroup
                    required property var modelData
                    width: filterColumn.width
                    spacing: 7

                    RowLayout {
                        width: parent.width
                        Label {
                            Layout.fillWidth: true
                            text: filterGroup.modelData.title
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            font.weight: Font.DemiBold
                        }
                        Controls.CompactIconButton {
                            visible: !filterGroup.modelData.allSelected
                            theme: root.theme
                            iconName: "close"
                            iconSize: 13
                            toolTip: qsTr("Clear this filter group")
                            onClicked: tasksController.clear_quick_filter_group(
                                filterGroup.modelData.key
                            )
                        }
                    }

                    Flow {
                        width: parent.width
                        spacing: 7

                        Repeater {
                            model: filterGroup.modelData.options
                            delegate: QuickFilterChip {
                                required property var modelData
                                theme: root.theme
                                height: 29
                                maximumChipWidth: filterGroup.width
                                text: modelData.title + "  " + modelData.count
                                accent: modelData.accent
                                    ? modelData.accent : root.theme.action
                                showAccentMarker:
                                    filterGroup.modelData.key === "process"
                                    || filterGroup.modelData.key === "status"
                                subtle: showAccentMarker
                                checked: modelData.selected
                                onClicked: tasksController.toggle_quick_filter(
                                    filterGroup.modelData.key, modelData.key
                                )
                            }
                        }
                    }
                }
            }
    }
}
