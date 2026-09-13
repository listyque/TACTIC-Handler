import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme

    readonly property bool compactFilters: width < 760
    readonly property var historyFilters: [
        {"value": "all", "label": "All", "icon": "select-all"},
        {"value": "server", "label": "Server", "icon": "dns"},
        {
            "value": "repository",
            "label": "Repository sync",
            "icon": "repository-sync"
        },
        {"value": "checkin", "label": "Check-in", "icon": "commit-queue"},
        {"value": "client", "label": "Client", "icon": "desktop"}
    ]

    function kindAccent(kind) {
        if (kind === "error")
            return theme.red
        if (kind === "warning")
            return theme.yellow
        if (kind === "complete")
            return theme.green
        return theme.action
    }

    function kindIcon(kind) {
        if (kind === "error")
            return "priority-high"
        if (kind === "warning")
            return "warning"
        if (kind === "complete")
            return "check-circle"
        if (kind === "progress")
            return "sync"
        return "info"
    }

    function groupTitle(group) {
        if (group === "repository")
            return qsTr("Repository sync")
        if (group === "checkin")
            return qsTr("Check-in operations")
        if (group === "server")
            return qsTr("Server transactions")
        return qsTr("Client")
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    Rectangle {
        id: notificationsPanel
        objectName: "notificationsPanel"
        anchors.fill: parent
        anchors.margins: 12
        radius: root.theme.surfaceRadius
        color: root.theme.panel
        border.width: 1
        border.color: root.theme.outlineVariant
        clip: true

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            Rectangle {
                id: notificationsToolbar
                objectName: "notificationsToolbar"
                Layout.fillWidth: true
                Layout.preferredHeight: toolbarContent.implicitHeight + 20
                radius: root.theme.itemRadius
                color: root.theme.surfaceContainerHigh

                ColumnLayout {
                    id: toolbarContent
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Controls.SectionLabel {
                            Layout.fillWidth: true
                            theme: root.theme
                            text: qsTr("ACTIVITY & NOTIFICATIONS")
                        }
                        Controls.Button {
                            theme: root.theme
                            text: qsTr("Clear history")
                            icon.name: "delete-sweep"
                            enabled: notificationHistoryModel.count() > 0
                            onClicked: notificationController.clear_history()
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: qsTr(
                            "Client events and background operations from this session."
                        )
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        wrapMode: Text.WordWrap
                    }

                    Controls.SegmentedButton {
                        objectName: "notificationHistoryFilters"
                        Layout.fillWidth: true
                        theme: root.theme
                        model: root.historyFilters
                        currentValue: notificationController.historyGroup
                        iconOnly: root.compactFilters
                        segmentWidth: root.compactFilters ? 46 : 104
                        minimumSegmentWidth: root.compactFilters ? 38 : 72
                        onActivated: value =>
                            notificationController.set_history_group(value)
                    }
                }
            }

            Controls.SmoothListView {
                theme: root.theme
                id: history
                objectName: "notificationHistoryList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.rightMargin: 8
                clip: true
                spacing: 6
                model: notificationGroupedHistoryModel

                ScrollBar.vertical: Controls.ScrollBar {
                    objectName: "notificationHistoryScrollBar"
                    theme: root.theme
                    flickableTarget: history
                }

                delegate: Item {
                    id: row

                    required property string kind
                    required property string group
                    required property string message
                    required property string detail
                    required property string timestamp
                    required property string timestampPretty
                    required property string timestampFull

                    width: Math.max(0, history.width - 12)
                    height: rowContent.implicitHeight + 22

                    HoverHandler { id: rowHover }

                    Controls.ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        hovered: rowHover.hovered
                        accent: root.kindAccent(row.kind)
                        normalColor: root.theme.surfaceContainerHigh
                        cornerRadius: root.theme.itemRadius
                        inset: 1
                        borderWidth: 1
                        borderColor: root.theme.outlineVariant
                        railVisible: true
                        separatorVisible: false
                    }

                    RowLayout {
                        id: rowContent
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 10
                        anchors.topMargin: 10
                        anchors.bottomMargin: 10
                        spacing: 10

                        Controls.MaterialIcon {
                            Layout.alignment: Qt.AlignTop
                            name: root.kindIcon(row.kind)
                            size: 19
                            color: root.kindAccent(row.kind)
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            GridLayout {
                                Layout.fillWidth: true
                                columns: row.width >= 620 ? 2 : 1
                                columnSpacing: 8
                                rowSpacing: 2

                                Controls.SelectableText {
                                    objectName: "notificationMessageText"
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: contentHeight
                                    theme: root.theme
                                    richText: true
                                    text: (typeof appController !== "undefined"
                                            && appController.rich_text_html)
                                        ? appController.rich_text_html(row.message)
                                        : row.message
                                    font.pointSize:
                                        Controls.Typography.bodyLarge
                                    font.weight: Font.DemiBold
                                    onLinkActivated: link => {
                                        if (typeof appController !== "undefined"
                                                && appController.open_rich_link)
                                            appController.open_rich_link(link)
                                    }
                                }

                                Controls.SelectableText {
                                    objectName: "notificationTimestampText"
                                    Layout.fillWidth: row.width < 620
                                    Layout.preferredHeight: contentHeight
                                    Layout.alignment: row.width >= 620
                                        ? Qt.AlignRight : Qt.AlignLeft
                                    theme: root.theme
                                    text: row.timestampPretty
                                    visible: text.length > 0
                                    color: root.theme.secondaryText
                                    font.pointSize: Controls.Typography.caption
                                    horizontalAlignment: row.width >= 620
                                        ? Text.AlignRight : Text.AlignLeft

                                    HoverHandler { id: timestampHover }
                                    Controls.ToolTip {
                                        theme: root.theme
                                        visible: timestampHover.hovered
                                            && row.timestampFull.length > 0
                                        text: row.timestampFull
                                    }
                                }
                            }

                            Label {
                                Layout.fillWidth: true
                                text: root.groupTitle(row.group)
                                color: root.kindAccent(row.kind)
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.DemiBold
                            }

                            Controls.SelectableText {
                                objectName: "notificationDetailText"
                                Layout.fillWidth: true
                                Layout.preferredHeight: contentHeight
                                visible: row.detail.length > 0
                                theme: root.theme
                                richText: true
                                text: (typeof appController !== "undefined"
                                        && appController.rich_text_html)
                                    ? appController.rich_text_html(row.detail)
                                    : row.detail
                                color: root.theme.secondaryText
                                font.pointSize: Controls.Typography.label
                                onLinkActivated: link => {
                                    if (typeof appController !== "undefined"
                                            && appController.open_rich_link)
                                        appController.open_rich_link(link)
                                }
                            }
                        }
                    }
                }

                Controls.EmptyState {
                    objectName: "notificationsEmptyState"
                    anchors.centerIn: parent
                    width: Math.min(maximumContentWidth, availableViewportWidth)
                    visible: history.count === 0
                    theme: root.theme
                    iconName: "notifications"
                    title: qsTr("No events in this group")
                }
            }
        }
    }
}
