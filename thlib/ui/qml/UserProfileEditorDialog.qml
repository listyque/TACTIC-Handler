import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/support/identity/profile.editor.ui.mjs" as UI
import "tactic_frame/features/support/identity/profile.editor.state.mjs" as State

Controls.Dialog {
    id: root
    required property var controller
    property string mode: "profile"
    property var draft: null
    property var original: null
    property bool awaitingSave: false
    property bool creating: false
    property bool confirmClose: false
    property bool uncertain: false
    property url pendingAvatarUrl: ""
    property bool uploadAvatarAfterCreate: false
    readonly property bool dirty: State.dirty(draft, original, String(pendingAvatarUrl).length > 0)
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            draft,
            mode,
            creating,
            confirmClose,
            uncertain,
            canManage: controller.canManageUsers,
            saving: controller.editingBusy,
            error: qsTr(controller.editingError),
            displayName: controller.profile.displayName || "",
            avatarName: String(pendingAvatarUrl) ? qsTr("Avatar selected") : ""
        })
    title: creating ? qsTr("Add user") : mode === "groups" ? qsTr("Edit group membership") : qsTr("Edit user profile")
    width: Math.min(680, parent ? parent.width - 24 : 680)
    height: Math.min(690, parent ? parent.height - 24 : 690)
    padding: 0
    modal: true
    closePolicy: Popup.NoAutoClose
    function loadProfile() {
        const profile = creating ? {} : controller.profile;
        const fields = {
            login: "login",
            first_name: "firstName",
            last_name: "lastName",
            display_name: "displayName",
            department: "department",
            email: "email",
            phone_number: "phoneNumber",
            address: "address",
            upn: "upn",
            namespace: "namespace",
            s_status: "status",
            project_code: "accountProject",
            hourly_wage: "hourlyWage"
        };
        const values = {
            password: "",
            groups: [],
            accessLevels: {}
        };
        for (const key of Object.keys(fields))
            values[key] = String(profile[fields[key]] || "");
        for (let index = 0; index < userGroupModel.count(); index++) {
            const group = userGroupModel.get(index);
            if (!creating && group.member)
                values.groups.push(group.code);
            values.accessLevels[group.code] = String(group.accessLevel || "");
        }
        draft = State.begin(values);
        original = draft;
        pendingAvatarUrl = "";
        confirmClose = false;
        uncertain = false;
        awaitingSave = false;
    }
    function openForProfile() {
        creating = false;
        mode = "profile";
        loadProfile();
        open();
    }
    function openForGroups() {
        creating = false;
        mode = "groups";
        loadProfile();
        open();
    }
    function openForCreate() {
        creating = true;
        mode = "profile";
        loadProfile();
        open();
        Qt.callLater(() => frame.focusControl("profileField_login"));
    }
    function requestClose(force) {
        const decision = State.closeDecision({
            saving: controller.editingBusy,
            dirty,
            uncertain
        }, force);
        if (decision === "busy")
            return;
        if (decision === "confirm") {
            confirmClose = true;
            return;
        }
        draft = null;
        pendingAvatarUrl = "";
        original = null;
        close();
    }
    function save() {
        if (controller.editingBusy || uncertain)
            return;
        const values = Object.assign({}, draft);
        delete values.groups;
        delete values.accessLevels;
        uploadAvatarAfterCreate = creating && String(pendingAvatarUrl).length > 0;
        const membershipChanged = JSON.stringify(draft.groups) !== JSON.stringify(original.groups) || JSON.stringify(draft.accessLevels) !== JSON.stringify(original.accessLevels);
        if (creating)
            awaitingSave = controller.create_user(values, draft.groups);
        else if (controller.canManageUsers && membershipChanged)
            awaitingSave = controller.save_profile(values, draft.groups, draft.accessLevels);
        else
            awaitingSave = controller.save_profile(values);
        if (awaitingSave)
            draft = State.submitted(draft);
    }
    function dispatch(action) {
        if (["field", "group", "access"].indexOf(action.type) >= 0)
            draft = State.edit(draft, action);
        else if (action.type === "mode")
            mode = State.page(frameModel, action.value);
        else if (action.type === "avatar")
            avatarDialog.open();
        else if (action.type === "save")
            save();
        else if (action.type === "close")
            requestClose(false);
        else if (action.type === "discard")
            requestClose(true);
        else if (action.type === "keep")
            confirmClose = false;
        else if (action.type === "reload") {
            requestClose(true);
            controller.refresh();
        }
    }
    onClosed: {
        awaitingSave = false;
        original = null;
        confirmClose = false;
        uncertain = false;
        draft = null;
        pendingAvatarUrl = "";
    }
    Connections {
        target: root.controller
        function onProfileSaved() {
            if (root.awaitingSave) {
                if (root.uploadAvatarAfterCreate)
                    root.controller.queue_avatar(root.pendingAvatarUrl);
                root.awaitingSave = false;
                root.requestClose(true);
            }
        }
        function onStateChanged() {
            if (root.awaitingSave && !root.controller.editingBusy && root.controller.editingError) {
                root.awaitingSave = false;
                root.uncertain = true;
            }
        }
    }
    FileDialog {
        id: avatarDialog
        title: qsTr("Choose avatar image")
        nameFilters: [qsTr("Images (*.jpg *.jpeg *.png *.webp)")]
        onAccepted: {
            if (root.creating || root.controller.queue_avatar(selectedFile))
                root.pendingAvatarUrl = selectedFile;
        }
    }
    Component {
        id: avatarComponent
        Controls.ItemPreview {
            theme: root.theme
            source: String(root.pendingAvatarUrl) || root.controller.profile.avatarUrl || ""
            fallbackText: root.creating ? "?" : root.controller.profile.initials || "?"
            previewSize: 54
            round: true
            outlined: true
            accent: root.controller.profile.avatarColor || root.theme.action
        }
    }
    contentItem: Frame.FrameView {
        id: frame
        implicitHeight: 540
        implicitWidth: 640
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                groups: userGroupModel
            })
        views: ({
                avatar: avatarComponent
            })
        describeRow: (list, record) => UI.groupRow(root.frameModel, record, list.width - 16, root.language)
        onEvent: action => root.dispatch(action)
        Keys.onEscapePressed: root.requestClose(false)
    }
}
