import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/editor.ui.mjs" as UI

Controls.ScrollablePopup {
    id: root
    objectName: "taskInlinePopup"
    required property var controller
    required property var record
    required property string field
    readonly property string taskCode: record.taskCode || ""
    readonly property string parentKey: record.parentKey || ""
    parent: Overlay.overlay
    preferredSurfaceWidth: field === "dates" ? 440 : 340
    minimumSurfaceWidth: 240
    maximumSurfaceHeight: 500
    contentSpacing: 0
    function openBelow(source) {
        openBelowItem(source, false, 6);
    }
    readonly property var fields: (field === "dates" ? ["bid_start_date", "bid_end_date"] : field === "hours" ? ["bid_duration"] : ["progress"]).map(name => ({
                name,
                editable: true
            }))
    Frame.FrameView {
        theme: root.theme
        width: parent.width
        height: scene.height
        scene: UI.describe({
            fields: root.fields,
            inline: true,
            immediate: true,
            title: "Edit task cell",
            busy: root.controller.advancedBusy || root.controller.advancedSaving
        }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        views: ({
                bid_start_date: {
                    component: startPort
                },
                bid_end_date: {
                    component: endPort
                },
                bid_duration: {
                    component: hoursPort
                },
                progress: {
                    component: progressPort
                },
                field: {
                    component: fieldPort,
                    nodeProps: true
                }
            })
        onEvent: action => {
            if (action.type === "cancel")
                root.close();
        }
    }
    Component {
        id: fieldPort
        Loader {
            property var frameNode: ({
                    field: {}
                })
            sourceComponent: frameNode.field.name === "bid_start_date" ? startPort : frameNode.field.name === "bid_end_date" ? endPort : frameNode.field.name === "bid_duration" ? hoursPort : progressPort
        }
    }
    Component {
        id: startPort
        Controls.DateField {
            objectName: "taskInlineStart"
            theme: root.theme
            includeTime: true
            text: root.record.start || ""
            onAccepted: value => root.controller.stage_advanced_context_value(root.taskCode, root.parentKey, "start", value)
            onEditingFinished: root.controller.stage_advanced_context_value(root.taskCode, root.parentKey, "start", text)
        }
    }
    Component {
        id: endPort
        Controls.DateField {
            objectName: "taskInlineDeadline"
            theme: root.theme
            includeTime: true
            text: root.record.end || ""
            onAccepted: value => root.controller.stage_advanced_context_value(root.taskCode, root.parentKey, "end", value)
            onEditingFinished: root.controller.stage_advanced_context_value(root.taskCode, root.parentKey, "end", text)
        }
    }
    Component {
        id: hoursPort
        RowLayout {
            spacing: 8
            Controls.MaterialIcon {
                name: "schedule"
                size: 18
                color: root.theme.secondaryText
            }
            Controls.SpinBox {
                objectName: "taskInlineHours"
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                decimals: 2
                from: 0
                to: 10000000
                stepSize: 25
                value: Math.round((root.record.plannedHours || 0) * 100)
                onValueModified: root.controller.stage_advanced_context_value(root.taskCode, root.parentKey, "plannedHours", String(realValue))
            }
            Text {
                text: qsTr("h")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
            }
        }
    }
    Component {
        id: progressPort
        RowLayout {
            spacing: 8
            Controls.Slider {
                id: progressSlider
                objectName: "taskInlineProgress"
                Layout.fillWidth: true
                theme: root.theme
                from: 0
                to: 100
                stepSize: 1
                value: root.record.progress || 0
                Accessible.name: qsTr("Progress")
                onMoved: root.controller.stage_advanced_context_value(root.taskCode, root.parentKey, "progress", String(Math.round(value)))
            }
            Text {
                text: Math.round(progressSlider.value) + "%"
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                Layout.minimumWidth: 32
                horizontalAlignment: Text.AlignRight
            }
        }
    }
}
