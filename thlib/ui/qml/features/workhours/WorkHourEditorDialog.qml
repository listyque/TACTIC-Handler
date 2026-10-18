import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/workhours/sheet.ui.mjs" as UI

Controls.Dialog {
    id: root

    required property var controller
    property var draft: ({})
    property bool editing: false
    property string entryCode: ""
    property string category: "regular"
    property bool awaitingSave: false
    property bool approvingSave: false

    title: editing ? qsTr("Edit work hours") : qsTr("Log work hours")
    width: 430
    height: Math.max(390, fields.implicitHeight + topPadding + bottomPadding + header.implicitHeight + spacing)
    x: Math.round((parent.width - width) / 2)
    y: Math.round((parent.height - height) / 2)
    closePolicy: Popup.CloseOnEscape

    function todayText() {
        const now = new Date();
        const month = String(now.getMonth() + 1).padStart(2, "0");
        const day = String(now.getDate()).padStart(2, "0");
        return now.getFullYear() + "-" + month + "-" + day;
    }

    function loginIndex(login) {
        for (let index = 0; index < userListModel.count(); ++index) {
            const value = userListModel.get(index);
            if (String(value.login || "") === String(login || ""))
                return index;
        }
        return -1;
    }

    function prepare(record) {
        const value = record || {};
        editing = String(value.entryCode || "").length > 0;
        entryCode = String(value.entryCode || "");
        draft = {
            day: editing ? String(value.day || "") : todayText(),
            hours: editing ? String(value.totalHours || "") : "",
            description: String(value.description || ""),
            category: String(value.category || "regular"),
            login: editing ? String(value.login || "") : controller.selectedLogin
        };
        awaitingSave = false;
        approvingSave = false;
    }

    function save(approve) {
        const login = controller.canManage ? root.draft.login : controller.selectedLogin;
        approvingSave = approve;
        awaitingSave = editing ? controller.update_time(entryCode, root.draft.day, root.draft.category, Number(String(root.draft.hours).replace(",", ".")), root.draft.description, String(login || ""), approve) : controller.log_time(root.draft.day, root.draft.category, Number(String(root.draft.hours).replace(",", ".")), root.draft.description, String(login || ""), approve);
    }

    function openForCreate() {
        prepare({});
        open();
        fields.focusControl("workHourDuration");
    }

    function openForEdit(record) {
        prepare(record);
        open();
        fields.focusControl("workHourDuration");
    }

    Connections {
        target: root.controller
        function onEntrySaved() {
            if (root.awaitingSave) {
                root.awaitingSave = false;
                root.close();
            }
        }
    }

    contentItem: Frame.FrameView {
        id: fields
        theme: root.theme
        scene: UI.editor(Object.assign({}, root.draft, {
            busy: root.controller.busy || root.awaitingSave,
            canManage: root.controller.canManage,
            error: root.controller.error,
            users: userListModel.records().map(row => Object.assign({}, row, {
                    value: row.login,
                    label: row.displayName || row.login
                }))
        }), width, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
        implicitHeight: scene.height
        onEvent: action => {
            if (action.type === "change")
                root.draft = Object.assign({}, root.draft, {
                    [action.field]: action.value
                });
            else if (action.type === "cancel")
                root.close();
            else
                root.save(action.type === "approve");
        }
    }
}
