import QtQuick
import QtQuick.Controls
import "../../../thlib/ui/qml" as TH
import "../../../thlib/ui/qml/controls" as Controls
import "../../../thlib/ui/qml/tactic_frame" as Frame
import "../../../thlib/ui/qml/tactic_frame/controls/catalog.ui.mjs" as BaseCatalog
import "../../../thlib/ui/qml/tactic_frame/controls/catalog/variants.mjs" as Variants

ApplicationWindow {
    id: window
    visible: true
    width: 360
    height: 520
    readonly property bool softwareRenderer: GraphicsInfo.api === GraphicsInfo.Software
    property bool interactive: false
    property bool dark: true
    property string styleName: "md3"
    property string language: "en"
    property string status: "idle"
    property var model: Variants.initial("button")
    readonly property var example: Variants.find(model.id)
    color: controlTheme.workspace
    function configure(id, state) {
        view.active = false;
        model = Variants.initial(id);
        status = state || "idle";
        view.active = true;
        focusSink.forceActiveFocus();
    }
    function userRecordsJson() {
        return JSON.stringify(BaseCatalog.users.map(user => Object.assign({
                avatarUrl: "",
                avatarColor: "",
                current: false,
                retired: false
            }, user)));
    }
    function directKindsJson() {
        return JSON.stringify(Variants.directKinds);
    }
    function event(action) {
        model = Variants.transition(model, action);
    }
    function examplesJson() {
        return JSON.stringify(Variants.examples);
    }
    function sceneJson() {
        return JSON.stringify(view.item.scene);
    }
    function modelJson() {
        return JSON.stringify(model);
    }
    Item {
        id: focusSink
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
    Loader {
        id: view
        anchors.fill: parent
        anchors.bottomMargin: window.interactive ? 60 : 0
        sourceComponent: Component {
            Frame.FrameView {
                anchors.fill: parent
                theme: controlTheme
                scene: Variants.describe(window.model, width, height, window.language, window.status)
                models: ({
                        cells: controlCells,
                        sourceEditor: sourceEditor,
                        treeRows: BaseCatalog.treeRows(window.model)
                    })
                describeRow: function (list, record) {
                    return Variants.row(list, record, window.model, window.language, window.status);
                }
                describeCell: function (grid, record, row, column) {
                    return Variants.cell(grid, record, row, column, window.model, window.status);
                }
                views: ({
                        example: exampleBrick
                    })
                onEvent: action => window.event(action)
            }
        }
    }
    Row {
        visible: window.interactive
        anchors.bottom: parent.bottom
        anchors.margins: 10
        height: 40
        spacing: 8
        Controls.ComboBox {
            width: 280
            theme: controlTheme
            model: Variants.examples
            textRole: "id"
            valueRole: "id"
            translateDisplayText: false
            currentIndex: model.findIndex(example => example.id === window.model.id)
            onActivated: window.configure(currentValue, window.status)
        }
        Controls.ComboBox {
            width: 140
            theme: controlTheme
            model: ["idle", "disabled", "readonly", "error", "loading"]
            onActivated: window.status = currentText
        }
        Controls.ComboBox {
            width: 140
            theme: controlTheme
            model: ["md3", "material5", "fluent"]
            onActivated: window.styleName = currentText
        }
        Controls.Button {
            theme: controlTheme
            text: window.dark ? "Light" : "Dark"
            onClicked: window.dark = !window.dark
        }
        Controls.Button {
            theme: controlTheme
            text: window.language === "en" ? "RU" : "EN"
            onClicked: window.language = window.language === "en" ? "ru" : "en"
        }
    }
    Component {
        id: exampleBrick
        ControlExample {
            language: window.language
            theme: controlTheme
            example: Variants.find(window.model.id)
            value: window.model.value
            disabled: window.status === "disabled" || window.status === "loading"
            readOnly: window.status === "readonly"
            onEvent: action => window.event(action)
        }
    }
}
