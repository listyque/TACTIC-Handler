import QtQuick
import "../.."
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/objects/snapshot.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var choices
    required property string imageMode
    property string mode: "side"
    property real position: 50
    property string leftToken: ""
    property string rightToken: ""
    readonly property var pair: UI.comparisonPair(choices, leftToken, rightToken)
    readonly property var alternatives: choices.filter(row => row.snapshotId !== pair[0]?.snapshotId)
    readonly property var layout: UI.comparisonLayout(width, height, mode, position)
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    signal closeRequested
    signal qualityRequested(string token)

    objectName: "snapshotComparison"
    focus: true
    Keys.onEscapePressed: closeRequested()

    Frame.FrameView {
        width: parent.width
        height: 44
        theme: root.theme
        scene: UI.comparisonToolbar(root.mode, width, root.language)
        onEvent: action => {
            if (action.type === "close")
                root.closeRequested();
            else if (action.type === "mode")
                root.mode = action.value;
        }
    }
    Repeater {
        model: 2
        Controls.ComboBox {
            id: picker
            required property int index
            readonly property var bounds: root.layout.pickers[index]
            objectName: index === 0 ? "snapshotCompareA" : "snapshotCompareB"
            theme: root.theme
            x: bounds.x
            y: bounds.y
            width: bounds.width
            height: bounds.height
            model: index === 0 ? root.choices : root.alternatives
            textRole: "label"
            valueRole: "value"
            translateDisplayText: false
            displayText: (index === 0 ? "A · " : "B · ") + (root.pair[index]?.label || "")
            currentIndex: model.findIndex(row => row.value === root.pair[index]?.value)
            Accessible.name: index === 0 ? qsTr("Snapshot A") : qsTr("Snapshot B")
            onActivated: {
                if (picker.index === 0)
                    root.leftToken = currentValue;
                else
                    root.rightToken = currentValue;
            }
        }
    }
    Repeater {
        model: 2
        Item {
            required property int index
            readonly property var bounds: index === 0 ? root.layout.a : root.layout.b
            readonly property var image: root.pair[index]
            x: bounds.x
            y: bounds.y
            width: bounds.width
            height: bounds.height
            clip: true
            SnapshotPreviewLayers {
                objectName: parent.index === 0 ? "snapshotComparisonImageA" : "snapshotComparisonImageB"
                theme: root.theme
                x: parent.index === 0 ? 0 : root.layout.bOffset
                width: parent.index === 0 ? parent.width : root.layout.bWidth
                height: parent.height
                currentUrl: parent.image?.url || ""
                currentQualityUrl: parent.image?.qualityUrl || ""
                currentQualityRequested: !!parent.image?.qualityRequested
                currentToken: parent.image?.token || ""
                viewMode: root.imageMode
                onQualityRequested: token => root.qualityRequested(token)
            }
        }
    }
    Rectangle {
        visible: root.mode === "divider"
        x: root.layout.line.x
        y: root.layout.line.y
        width: root.layout.line.width
        height: root.layout.line.height
        color: root.theme.outline
    }
    Controls.Slider {
        objectName: "snapshotCompareSlider"
        visible: root.mode === "divider"
        theme: root.theme
        x: root.layout.slider.x
        y: root.layout.slider.y
        width: root.layout.slider.width
        height: root.layout.slider.height
        from: 0
        to: 100
        value: root.position
        Accessible.name: qsTr("Image divider")
        onMoved: root.position = value
    }
}
