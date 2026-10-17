import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/objects/inspector.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var model
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    implicitHeight: scene.height
    scene: UI.quick(model, width, language)
    views: ({
            status: {
                component: statusPort,
                nodeProps: true
            },
            progress: {
                component: progressPort,
                nodeProps: true
            }
        })
    Component {
        id: statusPort
        Controls.ComboBox {
            property var frameNode
            theme: root.theme
            actionField: true
            model: frameNode ? frameNode.options : []
            textRole: "label"
            valueRole: "value"
            colorRole: "color"
            translateDisplayText: false
            enabled: frameNode ? frameNode.enabled : false
            currentIndex: frameNode ? (frameNode.options || []).findIndex(row => row.value === frameNode.value) : -1
            Accessible.name: qsTr("Status")
            onActivated: root.event({
                type: "change",
                field: "status",
                value: currentValue
            }, null)
        }
    }
    Component {
        id: progressPort
        Controls.Slider {
            property var frameNode
            theme: root.theme
            from: frameNode ? frameNode.minimum : 0
            to: frameNode ? frameNode.maximum : 100
            stepSize: frameNode ? frameNode.step : 5
            snapMode: Slider.SnapAlways
            value: frameNode ? frameNode.value : 0
            enabled: frameNode ? frameNode.enabled : false
            onMoved: if (frameNode)
                root.event(Object.assign({}, frameNode.action, {
                    value: Math.round(value)
                }), null)
        }
    }
}
