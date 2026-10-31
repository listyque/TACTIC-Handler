import QtQuick
import QtQuick.Controls
import "../../../thlib/ui/qml" as TH
import "../../../thlib/ui/qml/controls" as Controls
import "../../../thlib/ui/qml/tactic_frame" as Frame
import "../../../thlib/ui/qml/tactic_frame/core/frame.mjs" as Contract

ApplicationWindow {
    id: window
    visible: true
    width: 360
    height: 650
    property bool dark: true
    property string styleName: "md3"
    property var records: []
    property var events: []
    readonly property var theme: controlTheme
    color: controlTheme.workspace
    function sceneJson() {
        return JSON.stringify(scene());
    }
    function activate(id) {
        events = events.concat([id]);
    }
    function scene() {
        const h = controlTheme.controlHeight;
        const main = Contract.node("Box", "mainTitlebar", Contract.rect(0, 0, width, 64), {
            titlebar: true,
            background: "surfaceContainerLow",
            radius: 0,
            children: [Contract.button("mainClose", Contract.rect(12, 12, h, h), "Close", "close", {
                    type: "test",
                    id: "mainClose"
                }, true, {
                    iconOnly: true
                }), Contract.button("mainSave", Contract.rect(60, 12, 140, h), "Save", "save", {
                    type: "test",
                    id: "mainSave"
                }, true)]
        });
        return {
            nodes: [main].concat(records.map((record, index) => {
                const options = Object.assign({}, record);
                delete options.id;
                return Contract.button(record.id, Contract.rect(12, 80 + index * 48, record.iconOnly ? h : 140, h), record.text, record.icon, {
                    type: "test",
                    id: record.id
                }, record.enabled !== false, options);
            }))
        };
    }
    TH.Theme {
        id: controlTheme
        dark: window.dark
        styleName: window.styleName
        clickAnimationsEnabled: false
        hoverAnimationsEnabled: false
        fadeAnimationsEnabled: false
        popupAnimationsEnabled: false
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: controlTheme
        scene: window.scene()
        onEvent: action => window.activate(action.id)
    }
    Controls.ItemCountActionButton {
        objectName: "serviceCount"
        x: 12
        y: 438
        width: 32
        height: 32
        theme: controlTheme
        iconName: "tasks"
        count: 7
        toolTip: "Task Manager"
        onClicked: window.activate("serviceCount")
    }
    TH.QuickFilterChip {
        objectName: "serviceFilter"
        x: 12
        y: 486
        width: 140
        height: 30
        theme: controlTheme
        text: "Filter"
        checked: true
        onClicked: window.activate("serviceFilter")
    }
    Controls.SummaryChip {
        objectName: "serviceSummary"
        x: 12
        y: 534
        width: 140
        height: 30
        theme: controlTheme
        label: "Tasks"
        count: 7
        clickable: true
        onClicked: window.activate("serviceSummary")
    }
    TH.MessageReactionChip {
        objectName: "serviceReaction"
        x: 12
        y: 582
        width: 70
        height: 28
        theme: controlTheme
        emoji: "✓"
        count: 2
        onClicked: window.activate("serviceReaction")
    }
}
