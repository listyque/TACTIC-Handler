import QtQuick
import QtQuick.Window
import "tactic_frame" as Frame
import "tactic_frame/features/support/connection/presets.ui.mjs" as UI

Item {
    id: root
    required property var theme
    readonly property bool presented: !!Window.window && Window.window.visible
    onPresentedChanged: if (!presented)
        values = Object.assign({}, values, {
            proxyPassword: ""
        })
    property string loadedPresetName: ""
    property var values: ({})
    property string newName: ""
    property bool editing: false
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            selected: serverPresetsController.selected_name,
            values,
            newName,
            editing,
            error: qsTr(serverPresetsController.error),
            style: theme.style
        })
    function loadSelected() {
        loadedPresetName = serverPresetsController.selected_name;
        values = serverPresetsController.selected_values;
    }
    function pushValues() {
        if (serverPresetsController.selected_name)
            serverPresetsController.update_selected(values);
    }
    function indexOf(name) {
        for (let index = 0; index < serverPresetsModel.count(); index++)
            if (serverPresetsModel.get(index).name === name)
                return index;
        return -1;
    }
    function dispatch(action) {
        if (action.type === "field") {
            const next = Object.assign({}, values);
            next[action.field] = action.value;
            values = next;
            pushValues();
        } else if (action.type === "newName")
            newName = action.value;
        else if (action.type === "add") {
            if (serverPresetsController.add(newName)) {
                newName = "";
                editing = true;
            }
        } else if (action.type === "select") {
            serverPresetsController.select(indexOf(action.name));
            editing = true;
        } else if (action.type === "remove") {
            const index = indexOf(action.name);
            if (index >= 0)
                serverPresetsController.remove(index);
        } else if (action.type === "back")
            editing = false;
        else if (action.type === "cancel") {
            serverPresetsController.cancel();
            values = ({});
            windowModel.close_window("server_presets");
        } else if (action.type === "save") {
            pushValues();
            if (serverPresetsController.save()) {
                values = ({});
                configurationController.begin_session();
                windowModel.close_window("server_presets");
            }
        } else if (action.type === "help")
            windowModel.open_help("server_configuration");
    }
    Component.onCompleted: {
        if (serverPresetsController.selected_name)
            loadSelected();
        else
            serverPresetsController.begin_session();
    }
    Connections {
        target: serverPresetsController
        function onStateChanged() {
            if (root.loadedPresetName !== serverPresetsController.selected_name)
                root.loadSelected();
        }
        function onSessionStarted() {
            root.loadSelected();
        }
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, root.width, root.height, root.language)
        models: ({
                presets: serverPresetsModel
            })
        describeRow: (list, record) => UI.row(record, list.width - 16, root.language)
        onEvent: action => root.dispatch(action)
    }
}
