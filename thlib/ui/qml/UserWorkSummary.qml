import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/support/identity/profile.ui.mjs" as UI

Item {
    id: root
    objectName: "userWorkSummary"
    required property var theme
    required property var userController
    required property var tasksController
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            profile: userController.profile,
            taskSummary: userController.taskSummary,
            tasksBusy: userController.tasksBusy,
            statusSummary: userController.taskStatusSummary,
            processSummary: userController.taskProcessSummary,
            viewWorkHours: userController.canViewWorkHours,
            workHourSummary: userController.workHourSummary
        })
    readonly property var content: UI.work(frameModel, width, language)
    implicitHeight: content.height
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: ({
                nodes: root.content.nodes
            })
        onEvent: action => {
            if (action.type === "tasks") {
                if (action.key)
                    root.tasksController.open_for_user_filter(root.userController.profile.login, action.key, action.value);
                else
                    root.tasksController.open_for_user(root.userController.profile.login);
            }
        }
    }
}
