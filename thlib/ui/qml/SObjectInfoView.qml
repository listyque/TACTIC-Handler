import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property var summary: sobjectInfoController.summary
    readonly property var metrics: sobjectInfoController.metrics
    readonly property string reportIdentity: String(
        (summary && (summary.searchKey || summary.code)) || ""
    )
    property int reportGeneration: 0
    readonly property color objectAccent: root.summary
        && root.summary.accent ? root.summary.accent : root.theme.action
    readonly property real pageWidth: Math.max(0, reportPages.width)
    readonly property real expandedHeaderHeight: Math.max(
        256,
        expandedHeaderContent.implicitHeight + 28
    )
    readonly property var reportSections: [
        {"value": "tasks", "label": "Tasks", "icon": "task"},
        {"value": "notes", "label": "Notes", "icon": "notes"},
        {"value": "children", "label": "Children", "icon": "account-tree"},
        {"value": "snapshots", "label": "Snapshots", "icon": "snapshot"},
        {"value": "activity", "label": "Activity", "icon": "activity-feed"}
    ]

    onReportIdentityChanged: reportGeneration += 1

    function requestMoreActivityIfNeeded() {
        if (reportTabs.currentIndex !== 4
                || sobjectInfoController.busy
                || sobjectInfoController.activityLoadingMore
                || !sobjectInfoController.activityHasMore)
            return
        const underfilled = reportScroll.contentHeight
            <= reportScroll.height + 1
        if ((!underfilled && !reportScroll.atYEnd)
                || !reportScrollBar.takePaginationPermit(underfilled))
            return
        sobjectInfoController.load_more_activity()
    }

    component SectionTitle: RowLayout {
        required property var theme
        property string iconName: "info"
        property string title: ""
        property string detail: ""
        spacing: 8

        Controls.MaterialIcon { name: parent.iconName; size: 15; color: parent.theme.action }
        Label {
            text: parent.title
            color: parent.theme.primaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
            font.letterSpacing: 0.45
        }
        Item { Layout.fillWidth: true }
        Label {
            visible: text.length > 0
            text: parent.detail
            color: parent.theme.secondaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Controls.Typography.caption
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
        Layout.minimumWidth: 0
        spacing: 1
        Label {
            Layout.fillWidth: true
            text: parent.value
            color: parent.accent
            font.family: parent.theme.fontFamily
            font.pixelSize: 21
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Label {
            Layout.fillWidth: true
            text: parent.label
            color: parent.theme.secondaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Controls.Typography.caption
            font.weight: Font.DemiBold
            font.letterSpacing: 0.25
            elide: Text.ElideRight
        }
    }

    component ReportPageHost: Item {
        id: pageHost

        required property Component pageComponent
        required property bool current
        required property int generation
        property bool requested: false
        property int observedGeneration: -1
        implicitHeight: pageLoader.item ? pageLoader.item.implicitHeight : 0

        function synchronizeRequest() {
            if (observedGeneration !== generation) {
                observedGeneration = generation
                requested = current
                return
            }
            if (current)
                requested = true
        }

        Component.onCompleted: synchronizeRequest()
        onCurrentChanged: synchronizeRequest()
        onGenerationChanged: synchronizeRequest()

        Loader {
            id: pageLoader
            width: pageHost.width
            height: item ? item.implicitHeight : 0
            active: pageHost.requested
            sourceComponent: pageHost.pageComponent
        }
    }
    Rectangle { anchors.fill: parent; color: root.theme.workspace }

    Flickable {
        id: reportScroll
        objectName: "sobjectInfoReportScroll"
        anchors.fill: parent
        clip: true
        contentWidth: width
        contentHeight: Math.max(
            height,
            reportContent.y + reportContent.height + 12
        )
        flickableDirection: Flickable.VerticalFlick
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: Controls.ScrollBar {
            id: reportScrollBar
            objectName: "sobjectInfoReportScrollBar"
            theme: root.theme
            flickableTarget: reportScroll
        }

        onMovementEnded: root.requestMoreActivityIfNeeded()
        onAtYEndChanged: {
            if (atYEnd)
                root.requestMoreActivityIfNeeded()
        }
        onContentHeightChanged:
            Qt.callLater(root.requestMoreActivityIfNeeded)

        ColumnLayout {
            id: reportContent
            objectName: "sobjectInfoReportContent"
            x: 12
            y: 12
            width: Math.max(0, reportScroll.width - 30)
            height: implicitHeight
            spacing: 10

            DashboardPanel {
                id: presentationHeader
                objectName: "sobjectInfoPresentationHeader"
                Layout.fillWidth: true
                Layout.preferredHeight: root.expandedHeaderHeight
                theme: root.theme
                color: root.theme.surfaceContainerHigh

                ColumnLayout {
                    id: expandedHeaderContent
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: presentationHeader.width >= 560 ? 18 : 10

                Controls.ItemPreview {
                    Layout.preferredWidth: presentationHeader.width >= 700
                        ? 142 : (presentationHeader.width >= 420 ? 116 : 82)
                    Layout.preferredHeight: Layout.preferredWidth
                    theme: root.theme
                    source: String(root.summary.previewUrl || "")
                    fallbackIcon: "sobject"
                    fallbackText: String(root.summary.title || "?").slice(0, 2).toUpperCase()
                    previewSize: Layout.preferredWidth
                    cornerRadius: root.theme.surfaceRadius
                    outlined: true
                    accent: root.objectAccent
                    fillMode: Image.PreserveAspectCrop
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 6

                    Label {
                        Layout.fillWidth: true
                        text: root.summary.title || qsTr("No sObject selected")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Controls.StatusChip {
                            theme: root.theme
                            text: root.summary.typeTitle || ""
                            iconName: "sobject"
                            accentColor: root.objectAccent
                        }
                        Item { Layout.fillWidth: true }
                    }
                    Controls.SelectableText {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(contentHeight, 42)
                        Layout.maximumHeight: 42
                        theme: root.theme
                        richText: true
                        text: root.summary.description
                            ? (typeof appController !== "undefined"
                                    && typeof appController.rich_text_html === "function"
                                ? appController.rich_text_html(root.summary.description)
                                : root.summary.description)
                            : qsTr("No description provided")
                        color: root.summary.description
                            ? root.theme.primaryText : root.theme.secondaryText
                        font.pointSize: Controls.Typography.body
                        clip: true
                        onLinkActivated: link => {
                            if (typeof appController !== "undefined"
                                    && typeof appController.open_rich_link === "function")
                                appController.open_rich_link(link)
                        }
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: presentationHeader.width >= 1040
                            ? 4 : (presentationHeader.width >= 560 ? 2 : 1)
                        columnSpacing: 14
                        rowSpacing: 5
                        Controls.ProfileInfoRow {
                            Layout.fillWidth: true
                            theme: root.theme
                            iconName: "code"
                            label: qsTr("Code")
                            value: root.summary.code || ""
                        }
                        Controls.ProfileInfoRow {
                            Layout.fillWidth: true
                            theme: root.theme
                            iconName: "sobject"
                            label: qsTr("Search Type")
                            value: root.summary.searchType || ""
                        }
                        Controls.ProfileInfoRow {
                            Layout.fillWidth: true
                            theme: root.theme
                            iconName: "project-diagram"
                            label: qsTr("Project")
                            value: root.summary.project || ""
                        }
                        Controls.ProfileInfoRow {
                            Layout.fillWidth: true
                            theme: root.theme
                            iconName: "workflow"
                            label: qsTr("Pipeline")
                            value: root.summary.pipeline || ""
                        }
                    }
                    Item { Layout.fillHeight: true }
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            id: updatedLabel
                            Layout.fillWidth: true
                            text: root.summary.updatedPretty
                                ? qsTr("Updated") + ": "
                                    + root.summary.updatedPretty : ""
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            elide: Text.ElideRight
                            ToolTip.visible: updatedHover.hovered
                                && String(root.summary.updatedFull || "").length > 0
                            ToolTip.text: root.summary.updatedFull || ""

                            HoverHandler { id: updatedHover }
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "open-in-new"
                            toolTip: qsTr("Open sObject")
                            enabled: String(root.summary.searchKey || "").length > 0
                            onClicked: sobjectInfoController.open_search_key(root.summary.searchKey)
                        }
                        RefreshIconButton {
                            theme: root.theme
                            toolTip: qsTr("Refresh report")
                            enabled: sobjectInfoController.hasObject
                                && !sobjectInfoController.busy
                            onClicked: sobjectInfoController.refresh()
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: root.theme.separator
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: presentationHeader.width >= 1040
                    ? 50 : (presentationHeader.width >= 560
                        ? 86 : (presentationHeader.width >= 340 ? 150 : 300))
                columns: presentationHeader.width >= 1040
                    ? 8 : (presentationHeader.width >= 560
                        ? 4 : (presentationHeader.width >= 340 ? 2 : 1))
                columnSpacing: 12
                rowSpacing: 5
                SummaryMetric { theme: root.theme; label: qsTr("TASKS"); value: String(root.metrics.tasks || 0) }
                SummaryMetric { theme: root.theme; label: qsTr("NOTES"); value: String(root.metrics.notes || 0) }
                SummaryMetric { theme: root.theme; label: qsTr("CHILDREN"); value: String(root.metrics.children || 0) }
                SummaryMetric { theme: root.theme; label: qsTr("PEOPLE"); value: String(root.metrics.participants || 0) }
                SummaryMetric { theme: root.theme; label: qsTr("WORK HOURS"); value: qsTr("%1 h").arg(Number(root.metrics.workHours || 0).toFixed(1)) }
                SummaryMetric { theme: root.theme; label: qsTr("FILES"); value: String(root.metrics.files || 0) }
                SummaryMetric { theme: root.theme; label: qsTr("SNAPSHOTS"); value: String(root.metrics.snapshots || 0) }
                SummaryMetric {
                    theme: root.theme
                    label: root.metrics.canViewCosts ? qsTr("TOTAL COST") : qsTr("TOTAL SIZE")
                    value: root.metrics.canViewCosts
                        ? Number(root.metrics.totalCost || 0).toFixed(2)
                        : String(root.metrics.totalSize || "0 B")
                }
            }
        }
    }
    Controls.SegmentedButton {
        id: reportTabs
        objectName: "sobjectInfoTabs"
        property int currentIndex: 0

        Layout.fillWidth: true
        Layout.minimumWidth: 0
        theme: root.theme
        model: root.reportSections
        currentValue: root.reportSections[currentIndex].value
        iconOnly: false
        segmentWidth: 128
        minimumSegmentWidth: 56
        onActivated: value => {
            for (let index = 0; index < root.reportSections.length; ++index) {
                if (root.reportSections[index].value === value) {
                    currentIndex = index
                    Qt.callLater(root.requestMoreActivityIfNeeded)
                    return
                }
            }
        }
    }

    StackLayout {
        id: reportPages
        objectName: "sobjectInfoReportPages"
        Layout.fillWidth: true
        Layout.preferredHeight: currentPageHeight
        currentIndex: reportTabs.currentIndex
        onCurrentIndexChanged: sobjectInfoController.set_page(currentIndex)
        Component.onCompleted: sobjectInfoController.set_page(currentIndex)
        readonly property real currentPageHeight: currentIndex === 0
            ? tasksPageHost.implicitHeight : currentIndex === 1
            ? notesPageHost.implicitHeight : currentIndex === 2
            ? childrenPageHost.implicitHeight : currentIndex === 3
            ? snapshotsPageHost.implicitHeight : activityPageHost.implicitHeight

        ReportPageHost {
            id: tasksPageHost
            objectName: "sobjectTasksPageHost"
            pageComponent: tasksPage
            current: reportPages.currentIndex === 0
            generation: root.reportGeneration
        }
        ReportPageHost {
            id: notesPageHost
            objectName: "sobjectNotesPageHost"
            pageComponent: notesPage
            current: reportPages.currentIndex === 1
            generation: root.reportGeneration
        }
        ReportPageHost {
            id: childrenPageHost
            objectName: "sobjectChildrenPageHost"
            pageComponent: childrenPage
            current: reportPages.currentIndex === 2
            generation: root.reportGeneration
        }
        ReportPageHost {
            id: snapshotsPageHost
            objectName: "sobjectSnapshotsPageHost"
            pageComponent: filesPage
            current: reportPages.currentIndex === 3
            generation: root.reportGeneration
        }
        ReportPageHost {
            id: activityPageHost
            objectName: "sobjectActivityPageHost"
            pageComponent: activityPage
            current: reportPages.currentIndex === 4
            generation: root.reportGeneration
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
                                delegate: Controls.StatusChip {
                                    required property string label
                                    required property string value
                                    required property int count
                                    required property string accent
                                    theme: root.theme
                                    text: label + "  " + count
                                    iconName: "system-activity"
                                    accentColor: accent
                                    interactive: true
                                    onClicked: sobjectInfoController.open_tasks_filter("status", value)
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
                                delegate: Controls.StatusChip {
                                    required property string value
                                    required property string label
                                    required property int count
                                    required property string accent
                                    theme: root.theme
                                    text: label + "  " + count
                                    iconName: "workflow"
                                    accentColor: accent
                                    interactive: true
                                    onClicked: sobjectInfoController.open_tasks_filter("process", value)
                                }
                            }
                        }
                    }
                }
            }

            DashboardPanel {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.max(150, participantFlow.implicitHeight + 70)
                theme: root.theme
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10
                    SectionTitle {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "group"
                        title: qsTr("PEOPLE AND WORK HOURS")
                        detail: qsTr("%1 people · %2 h")
                            .arg(root.metrics.participants || 0)
                            .arg(Number(root.metrics.workHours || 0).toFixed(1))
                    }
                    Flow {
                        id: participantFlow
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            id: participantRepeater
                            model: sobjectParticipantModel
                            delegate: Item {
                                id: participantRow
                                required property string login
                                required property string displayName
                                required property string initials
                                required property string avatarUrl
                                required property string avatarColor
                                required property int taskCount
                                required property int noteCount
                                required property int snapshotCount
                                required property real hours
                                required property real cost
                                width: root.pageWidth >= 940
                                    ? Math.max(260, (participantFlow.width - 16) / 3)
                                    : (root.pageWidth >= 600
                                        ? Math.max(250, (participantFlow.width - 8) / 2)
                                        : participantFlow.width)
                                height: 76
                                Controls.ItemSurface {
                                    anchors.fill: parent
                                    theme: root.theme
                                    hovered: participantHover.hovered
                                    normalColor: root.theme.surfaceContainerHigh
                                    separatorVisible: false
                                    railVisible: participantRow.hours > 0
                                    accent: root.objectAccent
                                }
                                HoverHandler { id: participantHover; cursorShape: Qt.PointingHandCursor }
                                Controls.ActivationHandler { onActivated: sobjectInfoController.open_participant(participantRow.login) }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 9
                                    Controls.ItemPreview {
                                        Layout.preferredWidth: 42
                                        Layout.preferredHeight: 42
                                        theme: root.theme
                                        source: participantRow.avatarUrl
                                        fallbackIcon: "person"
                                        fallbackText: participantRow.initials
                                        previewSize: 42
                                        round: true
                                        outlined: true
                                        accent: participantRow.avatarColor
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        Label {
                                            Layout.fillWidth: true
                                            text: participantRow.displayName
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
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
                                            font.pointSize: Controls.Typography.caption
                                            elide: Text.ElideRight
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.alignment: Qt.AlignVCenter
                                        spacing: 1
                                        Label {
                                            text: qsTr("%1 h").arg(participantRow.hours.toFixed(1))
                                            color: participantRow.hours > 0
                                                ? root.objectAccent : root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
                                            font.weight: Font.DemiBold
                                        }
                                        Label {
                                            visible: Boolean(root.metrics.canViewCosts) && participantRow.cost > 0
                                            text: qsTr("Cost %1").arg(participantRow.cost.toFixed(2))
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.caption
                                        }
                                    }
                                    Controls.MaterialIcon { name: "arrow-forward"; size: 15; color: root.theme.secondaryText }
                                }
                            }
                        }
                    }
                    Controls.EmptyState {
                        Layout.fillWidth: true
                        visible: participantRepeater.count === 0
                        theme: root.theme
                        iconName: "group"
                        message: qsTr("No participants found")
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
                            id: taskRepeater
                            model: sobjectTaskModel
                            delegate: Item {
                                id: taskRow
                                required property string searchKey
                                required property string processLabel
                                required property string process
                                required property string processColor
                                required property string status
                                required property string statusColor
                                required property string assignedLabel
                                required property string assignedAvatar
                                required property string assignedColor
                                required property string end
                                required property string endPretty
                                required property string endFull
                                required property string dueState
                                required property int progress
                                required property string description
                                required property int notesCount
                                required property real loggedHours
                                required property real plannedHours
                                required property string taskCode
                                Layout.fillWidth: true
                                Layout.preferredHeight: 72
                                Controls.ItemSurface {
                                    anchors.fill: parent
                                    theme: root.theme
                                    hovered: taskHover.hovered
                                    normalColor: root.theme.surfaceContainerHigh
                                    separatorVisible: false
                                    railVisible: true
                                    accent: taskRow.processColor
                                }
                                HoverHandler { id: taskHover; cursorShape: Qt.PointingHandCursor }
                                Controls.ActivationHandler { onActivated: sobjectInfoController.open_task(taskRow.taskCode, taskRow.process) }
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
                                        Controls.MaterialIcon { anchors.centerIn: parent; name: "workflow"; size: 16; color: taskRow.processColor }
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
                                                font.pointSize: Controls.Typography.bodyLarge
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                            }
                                            Controls.StatusChip { theme: root.theme; text: taskRow.status; iconName: "system-activity"; accentColor: taskRow.statusColor }
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: taskRow.description || taskRow.assignedLabel
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.caption
                                            elide: Text.ElideRight
                                        }
                                    }
                                    RowLayout {
                                        Layout.maximumWidth: 160
                                        spacing: 6
                                        Controls.ItemPreview {
                                            Layout.preferredWidth: 26
                                            Layout.preferredHeight: 26
                                            theme: root.theme
                                            source: taskRow.assignedAvatar
                                            fallbackIcon: "person"
                                            fallbackText: taskRow.assignedLabel.slice(0, 2).toUpperCase()
                                            previewSize: 26
                                            round: true
                                            accent: taskRow.assignedColor
                                        }
                                        Label { Layout.fillWidth: true; text: taskRow.assignedLabel; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.caption; elide: Text.ElideRight }
                                    }
                                    Label { text: qsTr("%1 / %2 h").arg(taskRow.loggedHours.toFixed(1)).arg(taskRow.plannedHours.toFixed(1)); color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.caption }
                                    Label {
                                        id: taskDeadlineLabel
                                        text: taskRow.endPretty
                                        visible: text.length > 0
                                        color: taskRow.dueState === "overdue"
                                            ? root.theme.error
                                            : root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        ToolTip.visible: taskDeadlineHover.hovered
                                            && taskRow.endFull.length > 0
                                        ToolTip.text: taskRow.endFull
                                        HoverHandler { id: taskDeadlineHover }
                                    }
                                    Label { text: taskRow.progress + "%"; color: root.theme.primaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.label; font.weight: Font.DemiBold }
                                    Controls.MaterialIcon { name: "notes"; size: 14; color: root.theme.secondaryText }
                                    Label { text: taskRow.notesCount; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.caption }
                                    Controls.MaterialIcon { name: "arrow-forward"; size: 15; color: root.theme.secondaryText }
                                }
                            }
                        }
                        Controls.EmptyState {
                            objectName: "sobjectTasksEmptyState"
                            Layout.fillWidth: true
                            visible: taskRepeater.count === 0
                            theme: root.theme
                            iconName: "task"
                            message: qsTr("No tasks for this sObject")
                        }
                    }
                }
            }
        }
    }
    Component {
        id: notesPage
        ColumnLayout {
            width: root.pageWidth
            spacing: 12
            DashboardPanel {
                Layout.fillWidth: true
                Layout.preferredHeight: noteRows.implicitHeight + 58
                theme: root.theme
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 7
                    SectionTitle {
                        Layout.fillWidth: true
                        theme: root.theme
                        iconName: "notes"
                        title: qsTr("OBJECT AND TASK NOTES")
                        detail: qsTr("%1 object · %2 task notes")
                            .arg(root.metrics.objectNotes || 0)
                            .arg(root.metrics.taskNotes || 0)
                    }
                    ColumnLayout {
                        id: noteRows
                        Layout.fillWidth: true
                        spacing: 7
                        Repeater {
                            id: noteRepeater
                            objectName: "sobjectNoteRepeater"
                            model: sobjectNoteModel
                            delegate: Item {
                                id: noteRow
                                required property int index
                                objectName: "sobjectNoteRow" + index
                                required property string searchKey
                                required property string body
                                required property string authorLabel
                                required property string avatarUrl
                                required property string initials
                                required property string authorColor
                                required property string timestamp
                                required property string timestampPretty
                                required property string timestampFull
                                required property string process
                                required property string taskCode
                                required property string taskTitle
                                required property bool isTaskNote
                                Layout.fillWidth: true
                                Layout.preferredHeight: Math.max(84, noteBody.implicitHeight + 54)
                                Controls.ItemSurface {
                                    anchors.fill: parent
                                    theme: root.theme
                                    hovered: noteHover.hovered
                                    normalColor: root.theme.surfaceContainerHigh
                                    separatorVisible: false
                                    railVisible: true
                                    accent: noteRow.isTaskNote ? root.theme.action : root.objectAccent
                                }
                                HoverHandler { id: noteHover; cursorShape: Qt.PointingHandCursor }
                                Controls.ActivationHandler { onActivated: sobjectInfoController.open_note(index) }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 11
                                    spacing: 10
                                    Controls.ItemPreview {
                                        Layout.preferredWidth: 34
                                        Layout.preferredHeight: 34
                                        Layout.alignment: Qt.AlignTop
                                        theme: root.theme
                                        source: noteRow.avatarUrl
                                        fallbackIcon: "person"
                                        fallbackText: noteRow.initials
                                        previewSize: 34
                                        round: true
                                        accent: noteRow.authorColor
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 4
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Label {
                                                Layout.fillWidth: true
                                                text: noteRow.authorLabel
                                                color: root.theme.primaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Controls.Typography.body
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                            }
                                            Controls.StatusChip {
                                                theme: root.theme
                                                text: noteRow.isTaskNote
                                                    ? (noteRow.taskTitle || qsTr("Task note"))
                                                    : qsTr("Object note")
                                                iconName: noteRow.isTaskNote ? "task" : "sobject"
                                                accentColor: noteRow.isTaskNote
                                                    ? root.theme.action : root.objectAccent
                                            }
                                            Label {
                                                id: noteTimestampLabel
                                                text: noteRow.timestampPretty
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Controls.Typography.caption
                                                ToolTip.visible: noteTimestampHover.hovered
                                                    && noteRow.timestampFull.length > 0
                                                ToolTip.text: noteRow.timestampFull
                                                HoverHandler { id: noteTimestampHover }
                                            }
                                        }
                                        Label {
                                            id: noteBody
                                            Layout.fillWidth: true
                                            text: noteRow.body
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
                                            wrapMode: Text.Wrap
                                        }
                                    }
                                    Controls.MaterialIcon { name: "arrow-forward"; size: 15; color: root.theme.secondaryText }
                                }
                            }
                        }
                        Controls.EmptyState {
                            objectName: "sobjectNotesEmptyState"
                            Layout.fillWidth: true
                            visible: noteRepeater.count === 0
                            theme: root.theme
                            iconName: "notes"
                            message: qsTr("No object or task notes")
                        }
                    }
                }
            }
        }
    }

    Component {
        id: childrenPage
        ColumnLayout {
            objectName: "sobjectChildrenPage"
            width: root.pageWidth
            spacing: 12
            DashboardPanel {
                objectName: "sobjectChildrenPanel"
                Layout.fillWidth: true
                Layout.preferredHeight: childTypeFlow.implicitHeight + 52
                theme: root.theme
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    SectionTitle { Layout.fillWidth: true; theme: root.theme; iconName: "account-tree"; title: qsTr("CHILD TYPES"); detail: qsTr("%1 relations").arg(root.metrics.childTypes || 0) }
                    Flow {
                        id: childTypeFlow
                        Layout.fillWidth: true
                        spacing: 7
                        Repeater {
                            model: sobjectChildTypeModel
                            delegate: Controls.StatusChip {
                                required property string label
                                required property int count
                                required property string accent
                                theme: root.theme
                                text: label + "  " + count
                                iconName: "account-tree"
                                accentColor: accent
                            }
                        }
                    }
                }
            }
            DashboardPanel {
                objectName: "sobjectChildrenListPanel"
                Layout.fillWidth: true
                Layout.preferredHeight: childRows.implicitHeight + 58
                theme: root.theme
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 7
                    SectionTitle { Layout.fillWidth: true; theme: root.theme; iconName: "account-tree"; title: qsTr("CHILDREN"); detail: qsTr("%1 children").arg(root.metrics.children || 0) }
                    ColumnLayout {
                        id: childRows
                        objectName: "sobjectChildrenRows"
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            id: childRepeater
                            objectName: "sobjectChildrenRepeater"
                            model: sobjectChildModel
                            delegate: Item {
                                id: childRow
                                required property string searchKey
                                required property string title
                                required property string subtitle
                                required property string typeTitle
                                required property string relationship
                                required property string status
                                required property string accent
                                required property string previewUrl
                                Layout.fillWidth: true
                                Layout.preferredHeight: 68
                                Controls.ItemSurface { anchors.fill: parent; theme: root.theme; hovered: childHover.hovered; normalColor: root.theme.surfaceContainerHigh; separatorVisible: false; railVisible: true; accent: childRow.accent }
                                HoverHandler { id: childHover; cursorShape: Qt.PointingHandCursor }
                                Controls.ActivationHandler { onActivated: sobjectInfoController.open_search_key(childRow.searchKey) }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 9
                                    spacing: 10
                                    Controls.ItemPreview { Layout.preferredWidth: 44; Layout.preferredHeight: 44; theme: root.theme; source: childRow.previewUrl; fallbackIcon: "sobject"; fallbackText: childRow.title.slice(0, 2).toUpperCase(); previewSize: 44; cornerRadius: 12; accent: childRow.accent }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        Label { Layout.fillWidth: true; text: childRow.title; color: root.theme.primaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.body; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                        Label { Layout.fillWidth: true; text: childRow.subtitle; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.caption; elide: Text.ElideRight }
                                    }
                                    Controls.StatusChip { theme: root.theme; text: childRow.typeTitle; iconName: "sobject"; accentColor: childRow.accent }
                                    Controls.StatusChip { visible: childRow.status.length > 0; theme: root.theme; text: childRow.status; iconName: "system-activity"; accentColor: root.theme.secondaryText }
                                    Label { visible: childRow.relationship.length > 0; text: childRow.relationship; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.caption }
                                    Controls.MaterialIcon { name: "arrow-forward"; size: 15; color: root.theme.secondaryText }
                                }
                            }
                        }
                        Controls.EmptyState {
                            objectName: "sobjectChildrenEmptyState"
                            Layout.fillWidth: true
                            visible: childRepeater.count === 0
                            theme: root.theme
                            iconName: "account-tree"
                            message: qsTr("No related children")
                        }
                    }
                }
            }
        }
    }


    Component {
        id: filesPage
        SObjectSnapshotTree {
            width: root.pageWidth
            theme: root.theme
            metrics: root.metrics
            snapshotProcessModel: sobjectSnapshotProcessModel
            controller: sobjectInfoController
        }
    }

    Component {
        id: activityPage
        ColumnLayout {
            width: root.pageWidth
            spacing: 10

            SectionTitle {
                Layout.fillWidth: true
                theme: root.theme
                iconName: "activity-feed"
                title: qsTr("RECENT ACTIVITY")
                detail: qsTr("Object, task, note, snapshot, work-hour and child history")
            }

            ColumnLayout {
                id: activityRows
                Layout.fillWidth: true
                spacing: 5

                Repeater {
                    id: activityRepeater
                    model: sobjectActivityModel
                    delegate: Item {
                        id: activityRow
                        required property int index
                        required property string searchKey
                        required property string targetSearchKey
                        required property string targetTitle
                        required property string targetType
                        required property string targetTypeTitle
                        required property string kind
                        required property string title
                        required property string detail
                        required property string actor
                        required property string actorLabel
                        required property string actorAvatar
                        required property string actorInitials
                        required property string actorColor
                        required property string timestamp
                        required property string timestampPretty
                        required property string timestampFull
                        required property string itemCode
                        required property string itemTitle
                        required property string itemType
                        required property string itemTypeTitle
                        required property string itemTypeColor
                        required property string relationAction
                        required property real hours
                        required property string workDay
                        required property string workDayPretty
                        required property string workHourAction
                        required property string workHourCategory
                        required property string workHourStatus
                        required property string workHourOwner
                        required property string typeColor
                        required property string processColor
                        required property string project
                        required property string process
                        required property string context
                        required property string version
                        required property string statusBefore
                        required property string statusAfter
                        required property string statusBeforeColor
                        required property string statusAfterColor
                        required property var changes
                        required property string taskCode
                        required property bool serverGenerated
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
                            actorLabel: activityRow.actorLabel
                            actorAvatar: activityRow.actorAvatar
                            actorInitials: activityRow.actorInitials
                            actorColor: activityRow.actorColor
                            timestamp: activityRow.timestamp
                            timestampPretty: activityRow.timestampPretty
                            timestampFull: activityRow.timestampFull
                            targetSearchKey: activityRow.targetSearchKey
                            targetTitle: activityRow.targetTitle
                            targetType: activityRow.targetType
                            targetTypeTitle: activityRow.targetTypeTitle
                            itemCode: activityRow.itemCode
                            itemTitle: activityRow.itemTitle
                            itemType: activityRow.itemType
                            itemTypeTitle: activityRow.itemTypeTitle
                            itemTypeColor: activityRow.itemTypeColor
                            relationAction: activityRow.relationAction
                            hours: activityRow.hours
                            workDay: activityRow.workDay
                            workDayPretty: activityRow.workDayPretty
                            workHourAction: activityRow.workHourAction
                            workHourCategory: activityRow.workHourCategory
                            workHourStatus: activityRow.workHourStatus
                            workHourOwner: activityRow.workHourOwner
                            typeColor: activityRow.typeColor
                            processColor: activityRow.processColor
                            process: activityRow.process
                            context: activityRow.context
                            version: activityRow.version
                            statusBefore: activityRow.statusBefore
                            statusAfter: activityRow.statusAfter
                            statusBeforeColor: activityRow.statusBeforeColor
                            statusAfterColor: activityRow.statusAfterColor
                            changes: activityRow.changes
                            taskCode: activityRow.taskCode
                            serverGenerated: activityRow.serverGenerated
                            canOpenActivity: activityRow.canOpen && (
                                activityRow.searchKey.length > 0
                                || activityRow.taskCode.length > 0
                                || activityRow.kind === "publication"
                            )
                            canOpenTarget: activityRow.targetSearchKey.length > 0
                            onActivityRequested: sobjectInfoController.open_activity(
                                activityRow.index
                            )
                            onTargetRequested: activityRow.taskCode.length
                                ? sobjectInfoController.open_task(
                                    activityRow.taskCode,
                                    activityRow.process
                                )
                                : sobjectInfoController.open_search_key(
                                    activityRow.targetSearchKey
                                )
                        }
                    }
                }

                Controls.EmptyState {
                    objectName: "sobjectActivityEmptyState"
                    Layout.fillWidth: true
                    visible: activityRepeater.count === 0
                        && !sobjectInfoController.activityLoadingMore
                    theme: root.theme
                    iconName: "activity-feed"
                    message: qsTr("No recent activity")
                }

                Item {
                    objectName: "sobjectActivityPageLoading"
                    Layout.fillWidth: true
                    Layout.preferredHeight:
                        sobjectInfoController.activityLoadingMore ? 44 : 0
                    visible: sobjectInfoController.activityLoadingMore

                    Controls.BusyIndicator {
                        anchors.centerIn: parent
                        width: 24
                        height: 24
                        uiTheme: root.theme
                        running: parent.visible
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
        font.pointSize: Controls.Typography.label
        wrapMode: Text.WordWrap
    }

    ColumnLayout {
        anchors.centerIn: parent
        visible: !sobjectInfoController.hasObject && !sobjectInfoController.busy
        spacing: 12
        Controls.MaterialIcon { Layout.alignment: Qt.AlignHCenter; name: "sobject"; size: 42; color: root.theme.secondaryText }
        Label { text: qsTr("Select an sObject to view its report"); color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pixelSize: 12 }
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        visible: sobjectInfoController.busy
        theme: root.theme
        message: qsTr("Loading sObject report...")
    }
}
