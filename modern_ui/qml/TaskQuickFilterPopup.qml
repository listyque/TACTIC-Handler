import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Md3Popup {
    id: root

    parent: Overlay.overlay
    property bool sourceWasOpen: false
    width: parent ? Math.min(520, Math.max(0, parent.width - 16)) : 520
    height: Math.min(
        implicitHeight,
        410,
        parent ? Math.max(0, parent.height - 16) : 410
    )
    implicitHeight: filterColumn.implicitHeight + 24
    padding: 12
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnReleaseOutside

    function openBelow(sourceItem) {
        if (!sourceItem || !parent) {
            open()
            return
        }
        const point = sourceItem.mapToItem(
            parent, sourceItem.width - width, sourceItem.height + 6
        )
        x = Math.max(8, Math.min(parent.width - width - 8, point.x))
        y = Math.max(8, Math.min(parent.height - height - 8, point.y))
        open()
    }

    function toggleBelow(sourceItem) {
        if (sourceWasOpen || opened)
            close()
        else
            openBelow(sourceItem)
        sourceWasOpen = false
    }

    contentItem: Flickable {
        id: filterFlickable
        clip: true
        contentWidth: width
        contentHeight: filterColumn.implicitHeight
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: filterColumn
            width: filterFlickable.width
            spacing: 16

            RowLayout {
                width: parent.width
                Label {
                    Layout.fillWidth: true
                    text: qsTr("QUICK FILTERS")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }
                QuickFilterChip {
                    theme: root.theme
                    height: 28
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
                            font.pixelSize: 8
                            font.weight: Font.DemiBold
                        }
                        CompactIconButton {
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

        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            flickableTarget: filterFlickable
        }
    }
}
