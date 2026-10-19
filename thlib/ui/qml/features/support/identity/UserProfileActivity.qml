import QtQuick
import QtQuick.Layouts
import "../../.." as TH

Item {
    id: root
    required property var theme
    required property var controller
    required property var records
    property bool expanded: false
    readonly property real contentHeight: content.implicitHeight
    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 12
        Repeater {
            id: recentActivityRepeater

            model: root.records
            delegate: Loader {
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
                required property real hours
                required property string workDay
                required property string workDayPretty
                required property string workHourAction
                required property string workHourCategory
                required property string workHourStatus
                required property string workHourOwner
                required property bool serverGenerated
                readonly property bool inPreview: index < 6 || root.expanded

                active: inPreview
                visible: inPreview
                Layout.fillWidth: true
                Layout.preferredHeight: item ? item.implicitHeight : 0

                sourceComponent: TH.ActivityEventCard {
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
                    hours: activityRow.hours
                    workDay: activityRow.workDay
                    workDayPretty: activityRow.workDayPretty
                    workHourAction: activityRow.workHourAction
                    workHourCategory: activityRow.workHourCategory
                    workHourStatus: activityRow.workHourStatus
                    workHourOwner: activityRow.workHourOwner
                    serverGenerated: activityRow.serverGenerated
                    canOpenActivity: activityRow.searchKey.length > 0
                    canOpenTarget: activityRow.targetSearchKey.length > 0
                    onActivityRequested: activityRow.taskCode.length ? root.controller.open_task_activity(activityRow.targetSearchKey, activityRow.taskCode, activityRow.process) : root.controller.open_activity(activityRow.searchKey)
                    onTargetRequested: activityRow.taskCode.length ? root.controller.open_task_activity(activityRow.targetSearchKey, activityRow.taskCode, activityRow.process) : activityRow.kind === "message" ? root.controller.open_activity(activityRow.searchKey) : root.controller.open_activity_target(activityRow.targetSearchKey)
                }
            }
        }
    }
}
