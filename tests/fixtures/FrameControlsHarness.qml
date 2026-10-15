import QtQuick
import QtQuick.Controls
import "../../thlib/ui/qml" as TH
import "../../thlib/ui/qml/controls" as Controls
import "../../thlib/ui/qml/tactic_frame" as Frame
import "../../thlib/ui/qml/tactic_frame/controls/catalog.ui.mjs" as Catalog

ApplicationWindow {
    id: window
    width: 900
    height: 900
    visible: true
    property bool dark: true
    property string styleName: "md3"
    property string language: "en"
    property string status: "idle"
    property var model: Catalog.initial()
    color: controlTheme.workspace
    function event(action) {
        model = Catalog.transition(model, action);
        if (action.type === "treeKey")
            Qt.callLater(function () {
                view.focusControl("tree_" + model.treeSelected);
            });
    }
    function sceneJson() {
        return JSON.stringify(view.scene);
    }
    function blur() {
        focusSink.forceActiveFocus(Qt.OtherFocusReason);
    }
    Item {
        id: focusSink
        objectName: "catalogFocusSink"
    }
    function focus(name) {
        return view.focusControl(name);
    }
    TH.Theme {
        id: controlTheme
        dark: window.dark
        styleName: window.styleName
        clickAnimationsEnabled: false
        hoverAnimationsEnabled: false
        popupAnimationsEnabled: false
        fadeAnimationsEnabled: false
    }
    Rectangle {
        anchors.fill: parent
        color: controlTheme.workspace
    }
    Frame.FrameView {
        id: view
        anchors.fill: parent
        theme: controlTheme
        scene: Catalog.describe(window.model, width, height, window.language, window.status)
        models: ({
                cells: controlCells,
                treeRows: Catalog.treeRows(window.model)
            })
        views: ({
                menu: menuBrick,
                busy: busyBrick,
                slider: sliderBrick
            })
        describeRow: function (list, record) {
            return Catalog.row(list, record, window.model, window.language, window.status);
        }
        describeCell: Catalog.cell
        onEvent: action => window.event(action)
    }
    Component {
        id: menuBrick
        Item {
            Controls.CompactIconButton {
                id: trigger
                width: 36
                height: 36
                theme: controlTheme
                iconName: "more_vert"
                toolTip: qsTr("Actions")
                enabled: window.status !== "disabled" && window.status !== "loading"
                onClicked: popup.toggleBelowItem(trigger, false, 4)
            }
            TH.ActionMenu {
                id: popup
                theme: controlTheme
                preferredWidth: 244
                actions: Catalog.menuActions(window.language)
                onTriggered: command => window.event({
                        type: command
                    })
            }
        }
    }
    Component {
        id: busyBrick
        Item {
            Controls.BusyIndicator {
                width: 22
                height: 22
                anchors.verticalCenter: parent.verticalCenter
                uiTheme: controlTheme
                running: window.status === "loading"
            }
        }
    }
    Component {
        id: sliderBrick
        Controls.Slider {
            theme: controlTheme
            from: 0
            to: 100
            value: 50
            enabled: window.status !== "disabled" && window.status !== "loading"
        }
    }
}
