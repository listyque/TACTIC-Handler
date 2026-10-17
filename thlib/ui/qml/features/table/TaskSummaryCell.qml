import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/cells.ui.mjs" as Cells

Frame.FrameView {
    id: root
    required property var controller
    required property string nodeId
    property var records: []
    scene: Cells.taskSummary(records, width, height)
    onEvent: action => {
        const task = records[action.index];
        if (task.taskCode)
            controller.open_process_task_details(nodeId, "tasks", task.process, task.taskCode);
        else
            controller.open_process_details(nodeId, "tasks", task.process);
    }
}
