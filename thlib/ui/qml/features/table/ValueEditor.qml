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
    property bool busy: false
    property bool uncertain: false
    property bool explicitSave: false
    property string error: descriptor.fieldError || ""
    property var value: descriptor.fieldValue
    property string tagDraft: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var scene: UI.describe({
        mode: mode,
        title: descriptor.fieldLabel || descriptor.fieldName || "",
        value: value,
        draft: tagDraft,
        options: descriptor.fieldOptions || [],
        count: count,
        height: mode === "multiline" ? 260 : Math.max(36, controlHeight),
        busy: busy,
        uncertain: uncertain,
        explicitSave: explicitSave,
        error: error
    }, width, language)
    implicitHeight: scene.height
    signal saved(var value)
    signal checked(var value)
    signal cancelled

    function dispatch(action) {
        if (["tagDraft", "addTag", "removeTag"].indexOf(action.type) >= 0) {
            const next = UI.editTags(value, tagDraft, action);
            value = next.value;
            tagDraft = next.draft;
            if (action.type !== "tagDraft")
                activate();
        } else if (action.type === "value" || action.type === "toggle") {
            value = UI.change(value, action);
            if (!explicitSave && UI.savesOnChange(mode))
                saved(mode === "tags" ? UI.tagValue(value, tagDraft) : value);
        } else if (action.type === "save") {
            if (action.value !== undefined)
                value = action.value;
            saved(mode === "tags" ? UI.tagValue(value, tagDraft) : value);
        } else if (action.type === "check")
            checked(value);
        else if (action.type === "cancel")
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
