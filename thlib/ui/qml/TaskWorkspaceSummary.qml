import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/core/foundation.mjs" as Foundation
import "tactic_frame/features/tasks/summary.ui.mjs" as UI

Frame.FrameView {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var summary: tasksController.workspaceSummary
    readonly property bool management: tasksController.managementScope
    implicitHeight: scene.height
    scene: UI.describe(Object.assign({}, summary, {
        management: root.management
    }), width, language)
    views: ({
            presets: {
                component: presetPort
            },
            workload: {
                component: workloadPort
            },
            statuses: {
                component: statusPort
            }
        })
    FontMetrics {
        id: chipMetrics
        font.family: root.theme.fontFamily
        font.pixelSize: Foundation.textStyles.body
        font.weight: Font.DemiBold
        font.hintingPreference: Font.PreferVerticalHinting
    }
    function command(action) {
        if (action.type === "preset" || action.type === "unassigned")
            tasksController.apply_workspace_preset(action.type === "unassigned" ? "unassigned" : action.value);
        else
            tasksController.toggle_quick_filter(action.type === "status" ? "status" : "assigned", action.value);
    }
    Component {
        id: presetPort
        Flickable {
            id: presetFlick
            clip: true
            contentWidth: paint.scene.width
            contentHeight: height
            boundsBehavior: Flickable.StopAtBounds
            Frame.FrameView {
                id: paint
                theme: root.theme
                width: scene.width
                height: parent.height
                scene: UI.chips(Object.assign({}, root.summary, {
                    management: root.management,
                    height: presetFlick.height,
                    active: tasksController.activeQuickFilterCount,
                    selected: tasksController.activeQuickFilters.filter(row => row.group === "preset").map(row => row.key)
                }), root.language, text => chipMetrics.advanceWidth(text))
                views: ({
                        chip: {
                            component: chipPort,
                            nodeProps: true
                        }
                    })
            }
            ScrollBar.horizontal: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: presetFlick
            }
        }
    }
    Component {
        id: statusPort
        Flickable {
            id: statusFlick
            clip: true
            contentWidth: paint.scene.width
            contentHeight: height
            boundsBehavior: Flickable.StopAtBounds
            Frame.FrameView {
                id: paint
                theme: root.theme
                width: scene.width
                height: parent.height
                scene: UI.chips({
                    height: statusFlick.height,
                    statuses: tasksController.statusDistribution.map(row => ({
                                key: row.status,
                                text: row.label + "  " + row.count,
                                accent: row.color,
                                enabled: !!row.status
                            }))
                }, root.language, text => chipMetrics.advanceWidth(text))
                views: ({
                        chip: {
                            component: chipPort,
                            nodeProps: true
                        }
                    })
            }
            ScrollBar.horizontal: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: statusFlick
            }
        }
    }
    Component {
        id: chipPort
        QuickFilterChip {
            property var frameNode: ({
                    record: {}
                })
            theme: root.theme
            text: frameNode.record.text || ""
            checked: !!frameNode.record.selected
            accent: root.color(frameNode.record.accent || "action")
            enabled: frameNode.record.enabled !== false
            maximumChipWidth: width
            onClicked: root.command(frameNode.action)
        }
    }
    Component {
        id: workloadPort
        ListView {
            id: workloadList
            clip: true
            orientation: ListView.Horizontal
            spacing: 5
            reuseItems: true
            boundsBehavior: Flickable.StopAtBounds
            model: tasksController.workloadSummary
            delegate: Frame.FrameView {
                required property var modelData
                width: 148
                height: workloadList.height
                theme: root.theme
                scene: UI.workload(Object.assign({}, modelData, {
                    hovered: hover.hovered
                }), height, root.language)
                onEvent: action => root.command(action)
                HoverHandler {
                    id: hover
                }
            }
            ScrollBar.horizontal: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: workloadList
            }
        }
    }
}
