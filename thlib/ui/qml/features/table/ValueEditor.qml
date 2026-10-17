import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/inline.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var descriptor
    required property string mode
    property real controlHeight: 36
    property int count: 1
    property var value: descriptor.fieldValue
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var scene: UI.describe({
        mode: mode,
        title: descriptor.fieldLabel || descriptor.fieldName || "",
        value: value,
        options: descriptor.fieldOptions || [],
        count: count,
        height: mode === "multiline" ? 260 : Math.max(36, controlHeight),
        busy: false,
        uncertain: false,
        error: descriptor.fieldError || ""
    }, width, language)
    implicitHeight: scene.height
    signal saved(var value)
    signal cancelled

    function dispatch(action) {
        if (action.type === "value" || action.type === "toggle") {
            value = UI.change(value, action);
            if (UI.savesOnChange(mode))
                saved(value);
        } else if (action.type === "save") {
            if (action.value !== undefined)
                value = action.value;
            saved(value);
        } else if (action.type === "cancel")
            cancelled();
    }
    function activate() {
        Qt.callLater(function () {
            body.focusControl("tableInlineValue");
        });
    }
    Frame.FrameView {
        id: body
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        onEvent: action => root.dispatch(action)
    }
    Keys.onEscapePressed: event => {
        event.accepted = true;
        root.cancelled();
    }
    Component.onCompleted: activate()
}
