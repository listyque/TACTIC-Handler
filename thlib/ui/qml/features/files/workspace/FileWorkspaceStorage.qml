import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/storage.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    readonly property var state: controller.view_data
    readonly property var status: state.storage_info || ({})
    readonly property var draft: state.storage_draft || ({})
    readonly property var gcTask: status.gc || ({})
    readonly property bool gcActive: ["queued", "running"].includes(gcTask.state)
    readonly property var fields: UI.fields
    property string notice: ""
    property bool indexing: false
    property bool resetting: false
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    function reset() {
        if (resetting || !status.policy_values)
            return;
        if (draft.revision === status.policy_revision && JSON.stringify(draft.policy) === JSON.stringify(status.policy_values) && JSON.stringify(state.storage_original) === JSON.stringify(status.policy_values)) {
            notice = "";
            return;
        }
        resetting = true;
        controller.set_value("storage_original", status.policy_values);
        controller.set_value("storage_draft", {
            revision: status.policy_revision,
            policy: status.policy_values
        });
        notice = "";
        resetting = false;
    }
    function change(key, value) {
        const policy = Object.assign({}, draft.policy);
        policy[key] = value;
        controller.set_value("storage_draft", {
            revision: draft.revision,
            policy: policy
        });
    }
    function act(operation, dry) {
        notice = "";
        indexing = operation === "storage_index";
        controller.action("storage_admin", {
            operation: operation,
            dry_run: dry === undefined ? true : dry
        });
    }
    function save() {
        for (const field of fields) {
            const value = draft.policy[field[0]];
            if (!/^[0-9]{1,19}$/.test(value) || (value.length === 19 && value > "9223372036854775807") || (field[0] === "max_parallel" && (Number(value) < 1 || Number(value) > 16))) {
                notice = qsTr("Enter non-negative whole numbers; parallel transfers must be from 1 to 16.");
                return;
            }
        }
        act("storage_policy");
    }
    function syncDraft() {
        if (!draft.policy || JSON.stringify(draft.policy) === JSON.stringify(state.storage_original || {}))
            reset();
    }

    // The owned timer cannot outlive a catalog that is being replaced.
    Timer {
        id: draftSync
        interval: 0
        onTriggered: root.syncDraft()
    }
    Component.onCompleted: draftSync.start()
    Connections {
        target: root.controller
        function onStateChanged() {
            if (!root.controller.busy)
                root.indexing = false;
            draftSync.restart();
        }
    }
    Timer {
        interval: 2000
        repeat: true
        running: root.visible && root.gcActive && !root.controller.busy
        onTriggered: root.act("storage_status")
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            status: root.status,
            draft: root.draft,
            indexing: root.indexing,
            busy: root.controller.busy,
            filesService: root.state.catalog_capabilities.files_service_configured,
            notice: root.notice
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "field")
                root.change(action.key, action.value);
            else if (action.type === "action")
                root.act(action.operation, action.dry);
            else if (action.type === "reset")
                root.reset();
            else if (action.type === "save")
                root.save();
            else if (action.type === "stop")
                root.controller.stop();
            else if (action.type === "confirmGc")
                confirmGc.open();
        }
    }
    Controls.Dialog {
        id: confirmGc
        theme: root.theme
        parent: Overlay.overlay
        modal: true
        anchors.centerIn: parent
        width: Math.min(480, parent ? parent.width - 24 : 480)
        title: qsTr("Run safe GC")
        contentItem: Frame.FrameView {
            theme: root.theme
            implicitHeight: confirmGc.width < 420 ? 250 : 200
            scene: UI.confirm({
                busy: root.controller.busy || root.gcActive || !root.status.indexed || !root.state.catalog_capabilities.files_service_configured
            }, width, height, root.language)
            onEvent: action => {
                if (action.type === "reject")
                    confirmGc.close();
                else if (action.type === "accept" && !root.controller.busy && !root.gcActive && root.status.indexed && root.state.catalog_capabilities.files_service_configured) {
                    confirmGc.close();
                    root.act("gc_begin", false);
                }
            }
        }
    }
}
