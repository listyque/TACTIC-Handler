import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/empty.ui.mjs" as UI

Frame.FrameView {
    id: root
    objectName: "taskWorkspaceEmptyState"
    required property var controller
    required property var createTarget
    scene: UI.describe({
        filtered: controller.advancedFiltersActive,
        canCreate: controller.canCreateAdvancedTask,
        target: root.createTarget
    }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
    views: ({
            arrow: {
                component: arrowPort,
                nodeProps: true
            }
        })
    Component {
        id: arrowPort
        Canvas {
            property var frameNode: ({})
            readonly property color strokeColor: root.theme.action
            onFrameNodeChanged: requestPaint()
            onStrokeColorChanged: requestPaint()
            onPaint: {
                const n = frameNode, ctx = getContext("2d"), offset = -n.y;
                if (!n.source)
                    return;
                ctx.reset();
                ctx.strokeStyle = strokeColor;
                ctx.lineWidth = 2.5;
                ctx.lineCap = "round";
                ctx.lineJoin = "round";
                ctx.beginPath();
                ctx.moveTo(n.source[0], n.source[1] + offset);
                ctx.bezierCurveTo(n.first[0], n.first[1] + offset, n.second[0], n.second[1] + offset, n.target[0], n.target[1] + offset);
                ctx.stroke();
                ctx.beginPath();
                for (const tip of n.tips) {
                    ctx.moveTo(n.target[0], n.target[1] + offset);
                    ctx.lineTo(tip[0], tip[1] + offset);
                }
                ctx.stroke();
            }
        }
    }
}
