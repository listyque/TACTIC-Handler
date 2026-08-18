import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    readonly property var summary: sobjectInfoController.summary
    readonly property var metrics: sobjectInfoController.metrics
    readonly property real pageWidth: Math.max(280, reportScroll.availableWidth - 10)

    component SectionTitle: RowLayout {
        required property var theme
        property string iconName: "info"
        property string title: ""
        property string detail: ""
        spacing: 8

        MaterialIcon { name: parent.iconName; size: 15; color: parent.theme.action }
        Label {
            text: parent.title
            color: parent.theme.primaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Typography.body
            font.weight: Font.DemiBold
            font.letterSpacing: 0.45
        }
        Item { Layout.fillWidth: true }
        Label {
            visible: text.length > 0
            text: parent.detail
            color: parent.theme.secondaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Typography.caption
        }
    }

    component DashboardPanel: Rectangle {
        required property var theme
        property bool outlined: true
        radius: theme.surfaceRadius
        color: theme.panel
        border.width: outlined ? 1 : 0
        border.color: theme.outlineVariant
    }

    component SummaryMetric: ColumnLayout {
        required property var theme
        property string label: ""
        property string value: ""
        property color accent: theme.primaryText
        Layout.fillWidth: true
        spacing: 1
        Label {
            text: parent.value
            color: parent.accent
            font.family: parent.theme.fontFamily
            font.pixelSize: 21
            font.weight: Font.DemiBold
        }
        Label {
            text: parent.label
            color: parent.theme.secondaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Typography.caption
            font.weight: Font.DemiBold
            font.letterSpacing: 0.25
        }
    }

    component EmptyState: ColumnLayout {
        required property var theme
        property string iconName: "info"
        property string message: ""
        Layout.fillWidth: true
        Layout.preferredHeight: 140
        spacing: 8
        MaterialIcon {
            Layout.alignment: Qt.AlignHCenter
            name: parent.iconName
            size: 30
            color: parent.theme.secondaryText
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: parent.message
            color: parent.theme.secondaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Typography.body
        }
    }

    component ProfileRow: RowLayout {
        required property var theme
        property string iconName: "info"
        property string label: ""
        property string value: ""
        spacing: 8
        visible: value.length > 0

        MaterialIcon { name: parent.iconName; size: 14; color: parent.theme.secondaryText }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Label {
                text: parent.parent.label
                color: parent.parent.theme.secondaryText
                font.family: parent.parent.theme.fontFamily
                font.pointSize: Typography.caption
            }
            Label {
                Layout.fillWidth: true
                text: parent.parent.value
                color: parent.parent.theme.primaryText
                font.family: parent.parent.theme.fontFamily
                font.pointSize: Typography.body
                elide: Text.ElideMiddle
            }
        }
    }

    Rectangle { anchors.fill: parent; color: root.theme.workspace }

    DashboardPanel {
        id: presentationHeader
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 12
        anchors.leftMargin: 12
        anchors.rightMargin: 18
        height: 194
        theme: root.theme
        color: root.theme.surfaceContainerHigh

        RowLayout {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 16

            ItemPreview {
                Layout.preferredWidth: 166
                Layout.preferredHeight: 166
                theme: root.theme
                source: String(root.summary.previewUrl || "")
                fallbackIcon: "sobject"
                fallbackText: String(root.summary.title || "?").slice(0, 2).toUpperCase()
                previewSize: 166
                cornerRadius: 18
                outlined: true
                accent: root.summary.accent || root.theme.action
                fillMode: Image.PreserveAspectCrop
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: 10
                Layout.bottomMargin: 10
                Layout.minimumWidth: 190
                spacing: 7

                Label {
                    Layout.fillWidth: true
                    text: root.summary.title || qsTr("No sObject selected")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 19
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    StatusChip {
                        theme: root.theme
                        text: root.summary.typeTitle || ""
                        iconName: "sobject"
                        accentColor: root.summary.accent || root.theme.action
                    }
                    StatusChip {
                        visible: String(root.summary.pipeline || "").length > 0
                        theme: root.theme
                        text: root.summary.pipeline || ""
                        iconName: "workflow"
                        accentColor: root.theme.primaryText
                    }
                    StatusChip {
                        visible: String(root.summary.project || "").length > 0
                        theme: root.theme
                        text: root.summary.project || ""
                        iconName: "project-diagram"
                        accentColor: root.theme.secondaryText
                    }
                }
                Label {
                    Layout.fillWidth: true
                    Layout.maximumHeight: 64
                    text: root.summary.description || qsTr("No description provided")
                    color: root.summary.description ? root.theme.primaryText : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                    wrapMode: Text.WordWrap
                    maximumLineCount: 3
                    elide: Text.ElideRight
                }
                Item { Layout.fillHeight: true }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        Layout.fillWidth: true
                        text: [root.summary.code, root.summary.updated]
                            .filter(value => String(value || "").length > 0).join("  ·  ")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.caption
                        elide: Text.ElideRight
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "open-in-new"
                        toolTip: qsTr("Open sObject")
                        enabled: String(root.summary.searchKey || "").length > 0
                        onClicked: sobjectInfoController.open_search_key(root.summary.searchKey)
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "refresh"
                        toolTip: qsTr("Refresh report")
                        enabled: sobjectInfoController.hasObject && !sobjectInfoController.busy
                        onClicked: sobjectInfoController.refresh()
                    }
                }
            }

            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                Layout.topMargin: 8
                Layout.bottomMargin: 8
                color: root.theme.separator
            }

            ColumnLayout {
                Layout.preferredWidth: 280
                Layout.minimumWidth: 190
                Layout.maximumWidth: 340
                Layout.alignment: Qt.AlignVCenter
                spacing: 7

                SectionTitle {
                    Layout.fillWidth: true
                    theme: root.theme
                    iconName: "info"
                    title: qsTr("OBJECT DETAILS")
                }
                GridLayout {
                    Layout.fillWidth: true
                    columns: width >= 270 ? 2 : 1
                    columnSpacing: 12
                    rowSpacing: 7
                    ProfileRow {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "code"
                        label: qsTr("Code")
                        value: root.summary.code || ""
                    }
                    ProfileRow {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "sobject"
                        label: qsTr("Search Type")
                        value: root.summary.searchType || ""
                    }
                    ProfileRow {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "project-diagram"
                        label: qsTr("Project")
                        value: root.summary.project || ""
                    }
                    ProfileRow {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "workflow"
                        label: qsTr("Pipeline")
                        value: root.summary.pipeline || ""
                    }
                    ProfileRow {
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        theme: root.theme
                        iconName: "history"
                        label: qsTr("Updated")
                        value: root.summary.updated || ""
                    }
                }
            }
        }
    }

    TabBar {
        id: reportTabs
        anchors.top: presentationHeader.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 10
        anchors.leftMargin: 12
        anchors.rightMargin: 18
        height: 50
        spacing: 0
        background: Rectangle {
            color: root.theme.panel
        }

        WorkspaceTabButton { theme: root.theme; text: qsTr("OVERVIEW"); indicatorVisible: false }
        WorkspaceTabButton { theme: root.theme; text: qsTr("TASKS"); indicatorVisible: false }
        WorkspaceTabButton { theme: root.theme; text: qsTr("FILES & SNAPSHOTS"); indicatorVisible: false }
        WorkspaceTabButton { theme: root.theme; text: qsTr("ACTIVITY"); indicatorVisible: false }

        onCurrentIndexChanged: reportScroll.contentItem.contentY = 0
    }

    ScrollView {
        id: reportScroll
        anchors.top: reportTabs.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.topMargin: 8
        anchors.leftMargin: 12
        anchors.rightMargin: 8
        anchors.bottomMargin: 12
        rightPadding: 10
        clip: true
        contentWidth: availableWidth
        contentHeight: pageLoader.height
        ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

        Loader {
            id: pageLoader
            width: root.pageWidth
            height: item ? item.implicitHeight : 0
            sourceComponent: reportTabs.currentIndex === 0 ? overviewPage
                : reportTabs.currentIndex === 1 ? tasksPage
                : reportTabs.currentIndex === 2 ? filesPage : activityPage
        }
    }

    Component {
        id: overviewPage
        ColumnLayout {
            width: root.pageWidth
            spacing: 12

            GridLayout {
                Layout.fillWidth: true
                columns: root.pageWidth >= 940 ? 2 : 1
                columnSpacing: 12
                rowSpacing: 12

                DashboardPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(170,
                        66 + Math.ceil(sobjectPropertyModel.count() / 2) * 42)
                    theme: root.theme
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10
                        SectionTitle {
                            Layout.fillWidth: true
                            theme: root.theme
                            iconName: "info"
                            title: qsTr("OBJECT DETAILS")
                            detail: root.summary.searchType || ""
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            columns: root.pageWidth >= 1180 ? 2 : 1
                            columnSpacing: 8
                            rowSpacing: 7
                            Repeater {
                                model: sobjectPropertyModel
                                delegate: Rectangle {
                                    required property string label
                                    required property string value
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 38
                                    radius: root.theme.itemRadius
                                    color: root.theme.surfaceContainerHigh
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 10
                                        anchors.topMargin: 4
                                        anchors.bottomMargin: 4
                                        spacing: 0
                                        Label {
                                            Layout.fillWidth: true
                                            text: label
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.micro
                                            font.weight: Font.DemiBold
                                            elide: Text.ElideRight
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: value
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.label
                                            elide: Text.ElideMiddle
                                        }
                                    }
                                }
                            }
                            EmptyState {
                                visible: sobjectPropertyModel.count() === 0
                                theme: root.theme
                                iconName: "info"
                                message: qsTr("No additional properties")
                            }
                        }
                    }
                }

                DashboardPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 250
                    theme: root.theme
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10
                        SectionTitle {
                            Layout.fillWidth: true
                            theme: root.theme
                            iconName: "group"
                            title: qsTr("PEOPLE INVOLVED")
                            detail: qsTr("%1 people").arg(root.metrics.participants || 0)
                        }
                        Flow {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 7
                            Repeater {
                                model: sobjectParticipantModel
                                delegate: Item {
                                    id: participantRow
                                    required property string login
                                    required property string displayName
                                    required property string initials
                                    required property string avatarUrl
                                    required property int taskCount
                                    required property int noteCount
                                    required property int snapshotCount
                                    width: Math.min(250, Math.max(190, root.pageWidth / 3 - 24))
                                    height: 64
                                    ItemSurface {
                                        anchors.fill: parent
                                        theme: root.theme
                                        hovered: participantHover.hovered
                                        normalColor: root.theme.surfaceContainerHigh
                                        separatorVisible: false
                                        railVisible: false
                                    }
                                    HoverHandler { id: participantHover; cursorShape: Qt.PointingHandCursor }
                                    TapHandler { onTapped: sobjectInfoController.open_participant(participantRow.login) }
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 9
                                        spacing: 8
                                        ItemPreview {
                                            Layout.preferredWidth: 38
                                            Layout.preferredHeight: 38
                                            theme: root.theme
                                            source: participantRow.avatarUrl
                                            fallbackIcon: "person"
                                            fallbackText: participantRow.initials
                                            previewSize: 38
                                            round: true
                                            outlined: true
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 2
                                            Label {
                                                Layout.fillWidth: true
                                                text: participantRow.displayName
                                                color: root.theme.primaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Typography.body
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                            }
                                            Label {
                                                Layout.fillWidth: true
                                                text: qsTr("%1 tasks · %2 notes · %3 snapshots")
                                                    .arg(participantRow.taskCount)
                                                    .arg(participantRow.noteCount)
                                                    .arg(participantRow.snapshotCount)
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Typography.caption
                                                elide: Text.ElideRight
                                            }
                                        }
                                    }
                                }
                            }
                            EmptyState {
                                visible: sobjectParticipantModel.count() === 0
                                theme: root.theme
                                iconName: "group"
                                message: qsTr("No participants found")
                            }
                        }
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: root.pageWidth >= 780 ? 2 : 1
                columnSpacing: 20
                rowSpacing: 12
                DashboardPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 106
                    theme: root.theme
                    outlined: false
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 13
                        SummaryMetric { theme: root.theme; label: qsTr("TASKS"); value: String(root.metrics.tasks || 0) }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("NOTES"); value: String(root.metrics.notes || 0) }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("SNAPSHOTS"); value: String(root.metrics.snapshots || 0) }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("FILES"); value: String(root.metrics.files || 0) }
                    }
                }
                DashboardPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 106
                    theme: root.theme
                    outlined: false
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 13
                        SummaryMetric { theme: root.theme; label: qsTr("PEOPLE"); value: String(root.metrics.participants || 0) }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("PROCESSES"); value: String(root.metrics.processes || 0) }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("TOTAL SIZE"); value: String(root.metrics.totalSize || "0 B") }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("LATEST VERSION"); value: String(root.metrics.latestVersion || "—") }
                    }
                }
            }
        }
    }

    Component {
        id: tasksPage
        ColumnLayout {
            width: root.pageWidth
            spacing: 12

            GridLayout {
                Layout.fillWidth: true
                columns: root.pageWidth >= 780 ? 2 : 1
                columnSpacing: 20
                rowSpacing: 12
                DashboardPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 110
                    theme: root.theme
                    outlined: false
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 13
                        SummaryMetric { theme: root.theme; label: qsTr("TOTAL"); value: String(root.metrics.tasks || 0) }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("ACTIVE TASKS"); value: String(root.metrics.activeTasks || 0) }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("COMPLETED"); value: String(root.metrics.completedTasks || 0); accent: root.theme.green }
                    }
                }
                DashboardPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 110
                    theme: root.theme
                    outlined: false
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 13
                        SummaryMetric { theme: root.theme; label: qsTr("OVERDUE"); value: String(root.metrics.overdueTasks || 0); accent: Number(root.metrics.overdueTasks || 0) > 0 ? root.theme.red : root.theme.primaryText }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("UNASSIGNED"); value: String(root.metrics.unassignedTasks || 0) }
                        Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 42; color: root.theme.separator }
                        SummaryMetric { theme: root.theme; label: qsTr("AVERAGE PROGRESS"); value: qsTr("%1%").arg(root.metrics.averageProgress || 0) }
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: root.pageWidth >= 860 ? 2 : 1
                columnSpacing: 12
                rowSpacing: 12
                DashboardPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 150
                    theme: root.theme
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 9
                        SectionTitle { Layout.fillWidth: true; theme: root.theme; iconName: "system-activity"; title: qsTr("TASKS BY STATUS") }
                        Flow {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 7
                            Repeater {
                                model: sobjectTaskStatusModel
                                delegate: StatusChip {
                                    required property string label
                                    required property int count
                                    required property string accent
                                    theme: root.theme
                                    text: label + "  " + count
                                    iconName: "system-activity"
                                    accentColor: accent
                                }
                            }
                        }
                    }
                }
                DashboardPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 150
                    theme: root.theme
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 9
                        SectionTitle { Layout.fillWidth: true; theme: root.theme; iconName: "workflow"; title: qsTr("TASKS BY PROCESS") }
                        Flow {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 7
                            Repeater {
                                model: sobjectTaskProcessModel
                                delegate: StatusChip {
                                    required property string label
                                    required property int count
                                    required property string accent
                                    theme: root.theme
                                    text: label + "  " + count
                                    iconName: "workflow"
                                    accentColor: accent
                                }
                            }
                        }
                    }
                }
            }

            DashboardPanel {
                Layout.fillWidth: true
                Layout.preferredHeight: taskRows.implicitHeight + 58
                theme: root.theme
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 7
                    SectionTitle {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "task"
                        title: qsTr("TASKS")
                        detail: qsTr("%1 tasks").arg(root.metrics.tasks || 0)
                    }
                    ColumnLayout {
                        id: taskRows
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: sobjectTaskModel
                            delegate: Item {
                                id: taskRow
                                required property string searchKey
                                required property string processLabel
                                required property string processColor
                                required property string status
                                required property string statusColor
                                required property string assignedLabel
                                required property string assignedAvatar
                                required property string end
                                required property string dueState
                                required property int progress
                                required property string description
                                required property int notesCount
                                required property string hoursLabel
                                Layout.fillWidth: true
                                Layout.preferredHeight: 72
                                ItemSurface {
                                    anchors.fill: parent
                                    theme: root.theme
                                    hovered: taskHover.hovered
                                    normalColor: root.theme.surfaceContainerHigh
                                    separatorVisible: false
                                    railVisible: true
                                    accent: taskRow.processColor
                                }
                                HoverHandler { id: taskHover; cursorShape: Qt.PointingHandCursor }
                                TapHandler { onTapped: sobjectInfoController.open_search_key(taskRow.searchKey) }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 10
                                    spacing: 10
                                    Rectangle {
                                        Layout.preferredWidth: 38
                                        Layout.preferredHeight: 38
                                        radius: 12
                                        color: root.theme.panelRaised
                                        MaterialIcon { anchors.centerIn: parent; name: "workflow"; size: 16; color: taskRow.processColor }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Label {
                                                Layout.fillWidth: true
                                                text: taskRow.processLabel
                                                color: root.theme.primaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Typography.bodyLarge
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                            }
                                            StatusChip { theme: root.theme; text: taskRow.status; iconName: "system-activity"; accentColor: taskRow.statusColor }
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: taskRow.description || taskRow.assignedLabel
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.caption
                                            elide: Text.ElideRight
                                        }
                                    }
                                    Label { text: taskRow.assignedLabel; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.caption; Layout.maximumWidth: 140; elide: Text.ElideRight }
                                    Label { text: taskRow.end; visible: text.length > 0; color: taskRow.dueState === "overdue" ? root.theme.error : root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.caption }
                                    Label { text: taskRow.progress + "%"; color: root.theme.primaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.label; font.weight: Font.DemiBold }
                                    MaterialIcon { name: "notes"; size: 14; color: root.theme.secondaryText }
                                    Label { text: taskRow.notesCount; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.caption }
                                    MaterialIcon { name: "arrow-forward"; size: 15; color: root.theme.secondaryText }
                                }
                            }
                        }
                        EmptyState { visible: sobjectTaskModel.count() === 0; theme: root.theme; iconName: "task"; message: qsTr("No tasks for this sObject") }
                    }
                }
            }
        }
    }

    Component {
        id: filesPage
        ColumnLayout {
            width: root.pageWidth
            spacing: 12
            DashboardPanel {
                Layout.fillWidth: true
                Layout.preferredHeight: snapshotRows.implicitHeight + 58
                theme: root.theme
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 7
                    SectionTitle {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "snapshot"
                        title: qsTr("SNAPSHOTS AND VERSIONS")
                        detail: qsTr("Latest %1").arg(root.metrics.latestVersion || "—")
                    }
                    ColumnLayout {
                        id: snapshotRows
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: sobjectSnapshotModel
                            delegate: Item {
                                id: snapshotRow
                                required property string searchKey
                                required property string title
                                required property string process
                                required property string context
                                required property string version
                                required property string author
                                required property string timestamp
                                required property string previewUrl
                                required property int fileCount
                                required property string sizeText
                                required property string repository
                                required property bool isLatest
                                required property bool isVersionless
                                Layout.fillWidth: true
                                Layout.preferredHeight: 72
                                ItemSurface { anchors.fill: parent; theme: root.theme; hovered: snapshotHover.hovered; normalColor: root.theme.surfaceContainerHigh; separatorVisible: false; railVisible: true; accent: root.summary.accent || root.theme.action }
                                HoverHandler { id: snapshotHover; cursorShape: Qt.PointingHandCursor }
                                TapHandler { onTapped: sobjectInfoController.open_search_key(snapshotRow.searchKey) }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 10
                                    ItemPreview { Layout.preferredWidth: 54; Layout.preferredHeight: 54; theme: root.theme; source: snapshotRow.previewUrl; fallbackIcon: "snapshot"; fallbackText: snapshotRow.version; previewSize: 54; outlined: true; animateAppearance: false }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        Label { Layout.fillWidth: true; text: snapshotRow.title; color: root.theme.primaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.bodyLarge; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                        Label { Layout.fillWidth: true; text: [snapshotRow.process, snapshotRow.context, snapshotRow.author, snapshotRow.repository].filter(value => String(value).length > 0).join("  ·  "); color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.caption; elide: Text.ElideRight }
                                        Label { Layout.fillWidth: true; text: qsTr("%1 files · %2 · %3").arg(snapshotRow.fileCount).arg(snapshotRow.sizeText).arg(snapshotRow.timestamp); color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.caption; elide: Text.ElideRight }
                                    }
                                    StatusChip { theme: root.theme; text: snapshotRow.version; iconName: snapshotRow.isVersionless ? "sync" : "history"; accentColor: snapshotRow.isLatest ? root.theme.green : root.theme.action }
                                    MaterialIcon { name: "arrow-forward"; size: 15; color: root.theme.secondaryText }
                                }
                            }
                        }
                        EmptyState { visible: sobjectSnapshotModel.count() === 0; theme: root.theme; iconName: "snapshot"; message: qsTr("No snapshots found") }
                    }
                }
            }

            DashboardPanel {
                Layout.fillWidth: true
                Layout.preferredHeight: fileRows.implicitHeight + 58
                theme: root.theme
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 7
                    SectionTitle { Layout.fillWidth: true; theme: root.theme; iconName: "folder"; title: qsTr("FILES"); detail: qsTr("%1 files · %2").arg(root.metrics.files || 0).arg(root.metrics.totalSize || "0 B") }
                    ColumnLayout {
                        id: fileRows
                        Layout.fillWidth: true
                        spacing: 7
                        Repeater {
                            model: sobjectFileModel
                            delegate: AttachmentCard {
                                id: fileRow
                                required property string token
                                required property bool exists
                                Layout.fillWidth: true
                                theme: root.theme
                                local: fileRow.exists
                                animatePreview: false
                                onActivated: sobjectInfoController.activate_file(fileRow.token)
                                onContextRequested: (x, y) => { if (fileRow.exists) sobjectInfoController.show_file_folder(fileRow.token) }
                            }
                        }
                        EmptyState { visible: sobjectFileModel.count() === 0; theme: root.theme; iconName: "file"; message: qsTr("No files found") }
                    }
                }
            }
        }
    }

    Component {
        id: activityPage
        ColumnLayout {
            width: root.pageWidth
            spacing: 12
            DashboardPanel {
                Layout.fillWidth: true
                Layout.preferredHeight: activityRows.implicitHeight + 58
                theme: root.theme
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 7
                    SectionTitle {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "activity-feed"
                        title: qsTr("RECENT ACTIVITY")
                        detail: qsTr("Status changes, notes and publications")
                    }
                    ColumnLayout {
                        id: activityRows
                        Layout.fillWidth: true
                        spacing: 7
                        Repeater {
                            model: sobjectActivityModel
                            delegate: Item {
                                id: activityRow
                                required property int index
                                required property string searchKey
                                required property string targetSearchKey
                                required property string targetTitle
                                required property string targetType
                                required property string kind
                                required property string title
                                required property string detail
                                required property string actor
                                required property string timestamp
                                required property string project
                                required property string process
                                required property string context
                                required property string version
                                required property bool canOpen
                                Layout.fillWidth: true
                                Layout.preferredHeight: activityCard.implicitHeight

                                ActivityEventCard {
                                    id: activityCard
                                    anchors.fill: parent
                                    theme: root.theme
                                    kind: activityRow.kind
                                    eventTitle: activityRow.title
                                    detail: activityRow.detail
                                    actor: activityRow.actor
                                    timestamp: activityRow.timestamp
                                    targetSearchKey: activityRow.targetSearchKey
                                    targetTitle: activityRow.targetTitle
                                    targetType: activityRow.targetType
                                    process: activityRow.process
                                    context: activityRow.context
                                    version: activityRow.version
                                    canOpenActivity: activityRow.canOpen
                                    canOpenTarget: activityRow.targetSearchKey.length > 0
                                    onActivityRequested: sobjectInfoController.open_activity(
                                        activityRow.index
                                    )
                                    onTargetRequested: sobjectInfoController.open_search_key(
                                        activityRow.targetSearchKey
                                    )
                                }
                            }
                        }
                        EmptyState { visible: sobjectActivityModel.count() === 0; theme: root.theme; iconName: "activity-feed"; message: qsTr("No recent activity") }
                    }
                }
            }
        }
    }

    Label {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 14
        visible: sobjectInfoController.error.length > 0
        text: sobjectInfoController.error
        color: root.theme.error
        font.family: root.theme.fontFamily
        font.pointSize: Typography.label
        wrapMode: Text.WordWrap
    }

    ColumnLayout {
        anchors.centerIn: parent
        visible: !sobjectInfoController.hasObject && !sobjectInfoController.busy
        spacing: 12
        MaterialIcon { Layout.alignment: Qt.AlignHCenter; name: "sobject"; size: 42; color: root.theme.secondaryText }
        Label { text: qsTr("Select an sObject to view its report"); color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pixelSize: 12 }
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        visible: sobjectInfoController.busy
        theme: root.theme
        message: qsTr("Loading sObject report...")
    }
}
