import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/table.ui.mjs" as UI

Frame.FrameView {
    id: header
    required property var table
    required property var controller
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    objectName: "taskTableHeader"
    x: -table.horizontalContentOffset
    width: table.tableGeometry.width
    height: UI.metrics.header
    theme: table.theme
    scene: UI.header({
        allSelected: controller.advancedAllVisibleChecked,
        someSelected: controller.advancedCheckedCount > 0,
        busy: controller.advancedBusy || controller.advancedSaving
    }, table.tableGeometry, language)
    views: ({
            header_object: {
                component: headerInput,
                nodeProps: true
            },
            header_status: {
                component: headerInput,
                nodeProps: true
            },
            header_assignee: {
                component: headerInput,
                nodeProps: true
            },
            header_dates: {
                component: headerInput,
                nodeProps: true
            },
            header_progress: {
                component: headerInput,
                nodeProps: true
            },
            header_hours: {
                component: headerInput,
                nodeProps: true
            },
            header_notes: {
                component: headerInput,
                nodeProps: true
            },
            header_priority: {
                component: headerInput,
                nodeProps: true
            },
            header_milestone: {
                component: headerInput,
                nodeProps: true
            },
            header_supervisor: {
                component: headerInput,
                nodeProps: true
            }
        })
    onEvent: (action, source) => {
        if (action.type === "select-all")
            controller.set_all_advanced_checked(action.value);
        else if (action.type === "columns-press")
            table.columnsPressed();
        else if (action.type === "columns")
            table.columnsRequested(source);
    }
    Component {
        id: headerInput
        Item {
            id: input
            property var frameNode
            MouseArea {
                objectName: "taskColumnContextArea_" + (input.frameNode ? input.frameNode.column.key : "")
                anchors.fill: parent
                acceptedButtons: Qt.RightButton
                cursorShape: Qt.PointingHandCursor
                onClicked: if (input.frameNode)
                    table.columnContextRequested(input, input.frameNode.column.sourceKey, input.frameNode.column.label)
            }
        }
    }
}
