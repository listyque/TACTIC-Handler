import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/schedule.ui.mjs" as UI

Controls.Dialog {
    id: root
    required property var controller
    property var record: ({})
    property var form: ({})
    property string baseline: ""
    property string error: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var scene: UI.describe(Object.assign({}, form, {
        dates: true,
        busy: controller.advancedBusy,
        error,
        progressField: controller.progressSupported,
        workingDays: controller.ganttWorkingDays,
        multi: record.checked && controller.advancedCheckedCount > 1
    }), Math.max(0, width - leftPadding - rightPadding), language)
    title: qsTr("Edit schedule")
    modal: true
    draggable: true
    closePolicy: Popup.NoAutoClose
    width: Math.min(420, parent ? parent.width - 24 : 420)
    height: implicitHeaderHeight + scene.height + topPadding + bottomPadding + spacing

    function showRecord(value) {
        record = value;
        form = {
            start: value.start ? value.start.slice(0, 10) : Qt.formatDate(new Date(), "yyyy-MM-dd"),
            duration: value.ganttDurationDays || 1,
            progress: value.progress || 0,
            move: false
        };
        baseline = JSON.stringify(form);
        error = "";
        open();
    }
    function requestClose() {
        if (controller.advancedBusy)
            return;
        if (JSON.stringify(form) !== baseline)
            discard.open();
        else
            close();
    }
    function apply() {
        if (!scene.nodes.find(node => node.id === "ganttEditorApply").enabled)
            return;
        const current = taskGanttModel.lookup("taskCode", record.taskCode);
        if (current.parentKey !== record.parentKey || current.start !== record.start || current.end !== record.end || current.progress !== record.progress) {
            error = qsTr("The task changed while this editor was open. Close and reopen the schedule.");
            return;
        }
        const day = Math.round((Date.parse(form.start + "T12:00:00Z") - Date.parse(controller.ganttRange.rangeStart + "T12:00:00Z")) / 86400000);
        const staged = controller.stage_gantt_schedule(record.taskCode, day, Number(form.duration), form.move ? "move" : "editor", controller.progressSupported ? Number(form.progress) : -1);
        if (staged || JSON.stringify(form) === baseline)
            close();
        else
            error = controller.advancedError || qsTr("The schedule could not be staged.");
    }
    Shortcut {
        sequence: "Escape"
        enabled: root.opened && !discard.opened
        onActivated: root.requestClose()
    }
    contentItem: Frame.FrameView {
        theme: root.theme
        scene: root.scene
        implicitHeight: scene.height
        onEvent: action => {
            if (action.type === "change")
                root.form = Object.assign({}, root.form, {
                    [action.field]: action.value
                });
            else if (action.type === "working")
                root.controller.set_gantt_working_days(action.value);
            else if (action.type === "cancel")
                root.requestClose();
            else if (action.type === "apply")
                root.apply();
        }
    }
    Controls.Dialog {
        id: discard
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        title: qsTr("Discard unsaved task changes?")
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                theme: root.theme
                text: qsTr("Keep editing")
                onClicked: discard.close()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Discard changes")
                destructive: true
                onClicked: {
                    discard.close();
                    root.close();
                }
            }
        }
    }
}
