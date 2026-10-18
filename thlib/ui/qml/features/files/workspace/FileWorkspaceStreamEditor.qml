import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/stream_editor.ui.mjs" as UI

Controls.Dialog {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property var draft: ({
            code: "",
            title: "",
            description: "",
            parent: "",
            depot: "",
            stream_type: "",
            locked: false
        })
    objectName: "workspaceStreamEditor"
    required property var controller
    property var original: ({})
    property var choices: ({
            types: [],
            depots: [],
            parents: []
        })
    property string request: ""
    property string notice: ""
    property string initializedRequest: ""
    property bool loading: false
    property bool saving: false
    property bool creating: true
    property string parentCode: ""
    readonly property var editorResult: controller.view_data.stream_editor || ({})
    modal: true
    draggable: true
    parent: Overlay.overlay
    width: Math.min(660, parent ? parent.width - 24 : 660)
    height: Math.min(660, parent ? parent.height - 24 : 660)
    title: creating ? qsTr("New stream") : qsTr("Edit stream: %1").arg(original.code || "")
    closePolicy: saving ? Popup.NoAutoClose : Popup.CloseOnEscape
    onWidthChanged: if (visible && parent)
        x = (parent.width - width) / 2
    onHeightChanged: if (visible && parent)
        y = (parent.height - height) / 2
    function center() {
        if (visible && parent) {
            x = (parent.width - width) / 2;
            y = (parent.height - height) / 2;
        }
    }
    onOpened: center()
    Connections {
        target: root.parent
        function onWidthChanged() {
            root.center();
        }
        function onHeightChanged() {
            root.center();
        }
    }
    function openSpec(row, child) {
        original = row || {};
        creating = child || !original.code;
        parentCode = child ? original.code : original.parent || "";
        notice = "";
        loading = true;
        saving = false;
        request = String(Date.now()) + Math.random();
        open();
        controller.action("stream_editor", {
            request: request,
            stream: creating ? "" : original.code
        });
    }
    onEditorResultChanged: {
        if (!visible || editorResult.request !== request)
            return;
        loading = false;
        saving = false;
        if (editorResult.error) {
            notice = editorResult.error;
            return;
        }
        if (editorResult.saved) {
            close();
            controller.action("catalog_page", {});
            return;
        }
        if (initializedRequest === request)
            return;
        initializedRequest = request;
        choices = editorResult;
        if (!creating) {
            original = editorResult.info;
            parentCode = original.parent || "";
        }
        const preferredType = creating ? (parentCode ? original.stream_type === "release" ? "release" : "development" : "mainline") : original.stream_type;
        draft = {
            code: creating ? "" : original.code,
            title: creating ? "" : original.title || original.code,
            description: creating ? "" : original.description || "",
            depot: (choices.depots.find(row => row.code === original.depot) || choices.depots[0] || {}).code || "",
            stream_type: choices.types.includes(preferredType) ? preferredType : choices.types[0] || "",
            parent: parentCode,
            locked: !creating && Boolean(original.locked)
        };
    }
    function save() {
        const values = {
            request: String(Date.now()) + Math.random(),
            title: draft.title,
            description: draft.description,
            stream_type: draft.stream_type,
            parent: draft.stream_type === "mainline" ? null : draft.parent.trim(),
            locked: draft.locked
        };
        if (creating) {
            values.code = draft.code.trim();
            values.depot = draft.depot;
        } else {
            values.stream = original.code;
            values.spec_revision = String(original.spec_revision);
        }
        request = values.request;
        saving = true;
        notice = "";
        controller.action("save_stream", values);
    }
    footer: null
    contentItem: Frame.FrameView {
        theme: root.theme
        scene: UI.describe({
            draft: root.draft,
            choices: root.choices,
            creating: root.creating,
            owner: root.original.owner,
            notice: root.notice,
            loading: root.loading,
            saving: root.saving
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "field") {
                const next = Object.assign({}, root.draft);
                next[action.key] = action.value;
                root.draft = next;
            } else if (action.type === "reject" && !root.saving)
                root.close();
            else if (action.type === "save" && !root.loading && !root.saving)
                root.save();
        }
    }
}
