import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "features/objects" as Objects
import "tactic_frame" as Frame
import "tactic_frame/features/objects/report.ui.mjs" as UI

Item {
    id: root

    required property var theme
    readonly property var summary: sobjectInfoController.summary
    readonly property var metrics: sobjectInfoController.metrics
    readonly property string reportIdentity: String((summary && (summary.searchKey || summary.code)) || "")
    property int reportGeneration: 0
    readonly property color objectAccent: root.summary && root.summary.accent ? root.summary.accent : root.theme.action
    readonly property real pageWidth: Math.max(0, reportPages.width)
    readonly property var reportSections: UI.sections

    onReportIdentityChanged: reportGeneration += 1

    function requestMoreActivityIfNeeded() {
        if (reportTabs.currentIndex !== 4 || sobjectInfoController.busy || sobjectInfoController.activityLoadingMore || !sobjectInfoController.activityHasMore)
            return;
        const underfilled = reportScroll.contentHeight <= reportScroll.height + 1;
        if ((!underfilled && !reportScroll.atYEnd) || !reportScrollBar.takePaginationPermit(underfilled))
            return;
        sobjectInfoController.load_more_activity();
    }

    component SectionTitle: RowLayout {
        required property var theme
        property string iconName: "info"
        property string title: ""
        property string detail: ""
        spacing: 8

        Controls.MaterialIcon {
            name: parent.iconName
            size: 15
            color: parent.theme.action
        }
        Label {
            text: parent.title
            color: parent.theme.primaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
            font.letterSpacing: 0.45
        }
        Item {
            Layout.fillWidth: true
        }
        Label {
            visible: text.length > 0
            text: parent.detail
            color: parent.theme.secondaryText
            font.family: parent.theme.fontFamily
            font.pointSize: Controls.Typography.caption
        }
    }

    component ReportPageHost: Item {
        id: pageHost

        required property Component pageComponent
        required property bool current
        required property int generation
        property bool requested: false
        property int observedGeneration: -1
        implicitHeight: (pageLoader.item as Item)?.implicitHeight ?? 0

        function synchronizeRequest() {
            if (observedGeneration !== generation) {
                observedGeneration = generation;
                requested = current;
                return;
            }
            if (current)
                requested = true;
        }

        Component.onCompleted: synchronizeRequest()
        onCurrentChanged: synchronizeRequest()
        onGenerationChanged: synchronizeRequest()

        Loader {
            id: pageLoader
            width: pageHost.width
            height: (item as Item)?.implicitHeight ?? 0
            active: pageHost.requested
            sourceComponent: pageHost.pageComponent
        }
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    Flickable {
        id: reportScroll
        objectName: "sobjectInfoReportScroll"
        anchors.fill: parent
        clip: true
        contentWidth: width
        contentHeight: Math.max(height, reportContent.y + reportContent.height + 12)
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
                root.requestMoreActivityIfNeeded();
        }
        onContentHeightChanged: Qt.callLater(root.requestMoreActivityIfNeeded)

        ColumnLayout {
            id: reportContent
            objectName: "sobjectInfoReportContent"
            x: 12
            y: 12
            width: Math.max(0, reportScroll.width - 30)
            height: implicitHeight
            spacing: 10

            Objects.ObjectReportSurface {
                id: presentationHeader
                objectName: "sobjectInfoPresentationHeader"
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                theme: root.theme
                model: sobjectInfoController.presentation
                onEvent: action => {
                    if (action.type === "refresh")
                        sobjectInfoController.refresh();
                    else if (action.type === "open")
                        sobjectInfoController.open_search_key(root.summary.searchKey);
                }
            }
            Frame.FrameView {
                id: reportTabs
                objectName: "sobjectInfoTabs"
                property int currentIndex: 0
                readonly property string currentValue: UI.sections[currentIndex].value
                Layout.fillWidth: true
                Layout.preferredHeight: 36
                theme: root.theme
                scene: UI.tabs(UI.sections[currentIndex].value, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
                onEvent: action => {
                    currentIndex = UI.sections.findIndex(section => section.value === action.value);
                    Qt.callLater(root.requestMoreActivityIfNeeded);
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
                readonly property real currentPageHeight: currentIndex === 0 ? tasksPageHost.implicitHeight : currentIndex === 1 ? notesPageHost.implicitHeight : currentIndex === 2 ? childrenPageHost.implicitHeight : currentIndex === 3 ? snapshotsPageHost.implicitHeight : activityPageHost.implicitHeight

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
    function reportAction(action) {
        if (action.type === "task")
            sobjectInfoController.open_task(action.taskCode, action.process);
        else if (action.type === "note")
            sobjectInfoController.open_note(action.index);
        else if (action.type === "person")
            sobjectInfoController.open_participant(action.key);
        else if (action.type === "child")
            sobjectInfoController.open_search_key(action.key);
        else if (action.type === "filter")
            sobjectInfoController.open_tasks_filter(action.field, action.value);
    }
    Component {
        id: tasksPage
        Objects.ObjectReportSurface {
            objectName: "sobjectTasksPage"
            width: root.pageWidth
            theme: root.theme
            part: "page"
            model: Object.assign({}, sobjectInfoController.presentation, {
                page: "tasks"
            })
            onEvent: action => root.reportAction(action)
        }
    }
    Component {
        id: notesPage
        Objects.ObjectReportSurface {
            objectName: "sobjectNotesPage"
            width: root.pageWidth
            theme: root.theme
            part: "page"
            model: Object.assign({}, sobjectInfoController.presentation, {
                page: "notes"
            })
            onEvent: action => root.reportAction(action)
        }
    }
    Component {
        id: childrenPage
        Objects.ObjectReportSurface {
            objectName: "sobjectChildrenPage"
            width: root.pageWidth
            theme: root.theme
            part: "page"
            model: Object.assign({}, sobjectInfoController.presentation, {
                page: "children"
            })
            onEvent: action => root.reportAction(action)
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
                            canOpenActivity: activityRow.canOpen && (activityRow.searchKey.length > 0 || activityRow.taskCode.length > 0 || activityRow.kind === "publication")
                            canOpenTarget: activityRow.targetSearchKey.length > 0
                            onActivityRequested: sobjectInfoController.open_activity(activityRow.index)
                            onTargetRequested: activityRow.taskCode.length ? sobjectInfoController.open_task(activityRow.taskCode, activityRow.process) : sobjectInfoController.open_search_key(activityRow.targetSearchKey)
                        }
                    }
                }

                Controls.EmptyState {
                    objectName: "sobjectActivityEmptyState"
                    Layout.fillWidth: true
                    visible: activityRepeater.count === 0 && !sobjectInfoController.activityLoadingMore
                    theme: root.theme
                    iconName: "activity-feed"
                    message: qsTr("No recent activity")
                }

                Item {
                    objectName: "sobjectActivityPageLoading"
                    Layout.fillWidth: true
                    Layout.preferredHeight: sobjectInfoController.activityLoadingMore ? 44 : 0
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
        Controls.MaterialIcon {
            Layout.alignment: Qt.AlignHCenter
            name: "sobject"
            size: 42
            color: root.theme.secondaryText
        }
        Label {
            text: qsTr("Select an sObject to view its report")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 12
        }
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        visible: sobjectInfoController.busy
        theme: root.theme
        message: qsTr("Loading sObject report...")
    }
}
