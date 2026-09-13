import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    readonly property var summary: tasksController.workspaceSummary
    readonly property bool management: tasksController.managementScope

    implicitHeight: management ? 108 : 52
    radius: theme.surfaceRadius
    color: theme.surfaceContainerLow

    function presetSelected(value) {
        const filters = tasksController.activeQuickFilters
        for (let index = 0; index < filters.length; ++index) {
            if (filters[index].group === "preset"
                    && filters[index].key === value)
                return true
        }
        return false
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 8
        anchors.topMargin: 6
        anchors.bottomMargin: 6
        spacing: 5

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            spacing: 6

            ColumnLayout {
                Layout.preferredWidth: 132
                spacing: 0
                Label {
                    text: qsTr("SCOPE SUMMARY")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: root.summary.complete
                        ? root.summary.loaded + qsTr(" tasks loaded")
                        : root.summary.total >= 0
                            ? root.summary.loaded + qsTr(" of ") + root.summary.total
                                + qsTr(" tasks loaded")
                            : root.summary.loaded
                                + qsTr(" tasks loaded | partial scope")
                    color: root.summary.complete
                        ? root.theme.primaryText : root.theme.yellow
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    elide: Text.ElideRight
                }
            }

            Flickable {
                id: presetFlick
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: presetRow.width
                contentHeight: height
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.horizontal: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: presetFlick
                }

                Row {
                    id: presetRow
                    height: parent.height
                    spacing: 6

                    QuickFilterChip {
                        anchors.verticalCenter: parent.verticalCenter
                        theme: root.theme
                        height: 28
                        text: qsTr("ALL")
                        checked: tasksController.activeQuickFilterCount === 0
                        onClicked: tasksController.apply_workspace_preset("")
                    }
                    QuickFilterChip {
                        anchors.verticalCenter: parent.verticalCenter
                        theme: root.theme
                        height: 28
                        text: qsTr("TODAY  ") + root.summary.today
                        checked: root.presetSelected("today")
                        onClicked: tasksController.apply_workspace_preset("today")
                    }
                    QuickFilterChip {
                        anchors.verticalCenter: parent.verticalCenter
                        theme: root.theme
                        height: 28
                        text: qsTr("OVERDUE  ") + root.summary.overdue
                        accent: root.theme.error
                        checked: root.presetSelected("overdue")
                        onClicked: tasksController.apply_workspace_preset("overdue")
                    }
                    QuickFilterChip {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: root.management
                        theme: root.theme
                        height: 28
                        text: qsTr("UNASSIGNED  ") + root.summary.unassigned
                        checked: root.presetSelected("unassigned")
                        onClicked: tasksController.apply_workspace_preset("unassigned")
                    }
                    QuickFilterChip {
                        anchors.verticalCenter: parent.verticalCenter
                        theme: root.theme
                        height: 28
                        text: qsTr("REVIEW  ") + root.summary.review
                        checked: root.presetSelected("review")
                        onClicked: tasksController.apply_workspace_preset("review")
                    }
                    QuickFilterChip {
                        anchors.verticalCenter: parent.verticalCenter
                        theme: root.theme
                        height: 28
                        text: qsTr("RECENT  ") + root.summary.recent
                        checked: root.presetSelected("recent")
                        onClicked: tasksController.apply_workspace_preset("recent")
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.management
            spacing: 7

            Label {
                text: qsTr("WORKLOAD")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                font.weight: Font.DemiBold
            }
            ListView {
                id: workloadList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                orientation: ListView.Horizontal
                spacing: 5
                reuseItems: true
                boundsBehavior: Flickable.StopAtBounds
                model: tasksController.workloadSummary
                ScrollBar.horizontal: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: workloadList
                }
                delegate: Rectangle {
                    id: workloadItem
                    required property var modelData
                    width: 148
                    height: workloadList.height
                    radius: root.theme.itemRadius
                    color: workloadHover.hovered
                        ? root.theme.surfaceContainerHighest
                        : root.theme.surfaceContainerHigh

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 7
                        anchors.rightMargin: 7
                        spacing: 6
                        Controls.ItemPreview {
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 26
                            theme: root.theme
                            source: String(modelData.avatarUrl || "")
                            fallbackIcon: "person"
                            fallbackText: String(
                                modelData.label || "?"
                            ).slice(0, 2).toUpperCase()
                            previewSize: 26
                            round: true
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Label {
                                Layout.fillWidth: true
                                text: modelData.label
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: modelData.count + qsTr(" tasks")
                                    + (modelData.overdue
                                        ? " | " + modelData.overdue
                                            + qsTr(" overdue") : "")
                                color: modelData.overdue
                                    ? root.theme.error
                                    : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.micro
                                elide: Text.ElideRight
                            }
                        }
                    }
                    HoverHandler {
                        id: workloadHover
                        cursorShape: Qt.PointingHandCursor
                    }
                    Controls.ActivationHandler {
                        onActivated: {
                            if (modelData.login)
                                tasksController.toggle_quick_filter(
                                    "assigned", modelData.login)
                            else
                                tasksController.apply_workspace_preset(
                                    "unassigned")
                                }
                            }
                }
            }

            Label {
                text: qsTr("STATUSES")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                font.weight: Font.DemiBold
            }
            Flickable {
                id: statusFlick
                Layout.preferredWidth: Math.min(360, root.width * 0.32)
                Layout.fillHeight: true
                contentWidth: statusRow.width
                contentHeight: height
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.horizontal: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: statusFlick
                }
                Row {
                    id: statusRow
                    height: parent.height
                    spacing: 5
                    Repeater {
                        model: tasksController.statusDistribution
                        delegate: QuickFilterChip {
                            required property var modelData
                            anchors.verticalCenter: parent.verticalCenter
                            theme: root.theme
                            height: 28
                            maximumChipWidth: 132
                            text: modelData.label + "  " + modelData.count
                            accent: modelData.color
                                ? modelData.color : root.theme.action
                            enabled: String(modelData.status || "").length > 0
                            onClicked: tasksController.toggle_quick_filter(
                                "status", modelData.status)
                        }
                    }
                }
            }
        }
    }
}
