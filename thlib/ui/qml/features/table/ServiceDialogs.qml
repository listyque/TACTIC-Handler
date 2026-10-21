import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/actions.state.mjs" as Actions
import "../../tactic_frame/controls/feedback/confirmation.ui.mjs" as Confirmation

Item {
    id: root
    required property var theme
    required property var controller
    property string scriptQuestion: ""
    property string templateCode: ""
    property string objectAction: ""
    property var objectCell: ({})
    Connections {
        target: root.controller
        function onStateChanged() {
            if (!root.controller.busy) {
                scriptConfirm.close();
                templateConfirm.close();
                statusConfirm.close();
                discard.close();
            }
        }
        function onScriptConfirmation(message) {
            root.scriptQuestion = message;
            scriptConfirm.open();
        }
        function onScriptCommands(commands) {
            try {
                const ports = commands.map(Actions.route);
                for (const command of ports)
                    root.controller.open_port(command);
            } catch (error) {
                root.controller.report_error(String(error));
            }
        }
        function onPreferenceOpened(anchor) {
            popup.openBelowItem(anchor, true, 4);
        }
        function onPreferenceClosed() {
            popup.close();
        }
        function onObjectActionOpened(action, cell) {
            root.objectAction = action;
            root.objectCell = cell;
            statusConfirm.open();
        }
        function onConnectionRemovalOpened() {
            connectionConfirm.open();
        }
        function onConnectionRemovalClosed() {
            connectionConfirm.close();
        }
        function onTemplateOpened(code) {
            root.templateCode = code;
            templateConfirm.open();
        }
    }
    Controls.Dialog {
        id: scriptConfirm
        objectName: "tableConfirmation_scriptConfirm"
        parent: Overlay.overlay
        modal: true
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(480, parent.width - 24)
        height: 220
        onRejected: root.controller.confirm_script(false)
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: Confirmation.describe({
                message: root.scriptQuestion
            }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: action => {
                scriptConfirm.close();
                root.controller.confirm_script(action.type === "accept");
            }
        }
    }
    Controls.ScrollablePopup {
        id: popup
        parent: Overlay.overlay
        theme: root.theme
        padding: 10
        preferredSurfaceWidth: 380
        maximumSurfaceHeight: 520
        settledClosePolicy: root.controller.busy || root.controller.uncertain ? Popup.NoAutoClose : Popup.CloseOnEscape
        onClosed: root.controller.cancel_preference()
        Loader {
            width: parent.width
            height: item ? item.implicitHeight : 0
            active: !!root.controller.preference.preferenceKey
            sourceComponent: ValueEditor {
                width: parent.width
                theme: root.theme
                descriptor: ({
                        fieldName: root.controller.preference.preferenceKey,
                        fieldValue: root.controller.preference.text,
                        fieldOptions: root.controller.preference.preferenceOptions || []
                    })
                mode: descriptor.fieldOptions.length ? "select" : "text"
                explicitSave: true
                busy: root.controller.busy
                uncertain: root.controller.uncertain
                error: root.controller.error
                onSaved: value => root.controller.save_preference(String(value), false)
                onChecked: value => root.controller.save_preference(String(value), true)
                onCancelled: {
                    if (root.controller.busy)
                        return;
                    if (root.controller.uncertain)
                        discard.open();
                    else
                        root.controller.cancel_preference();
                }
            }
        }
    }
    Controls.Dialog {
        id: discard
        parent: Overlay.overlay
        modal: true
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(400, parent.width - 24)
        height: 220
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: Confirmation.describe({
                message: qsTr("Discard this draft? Some changes may already have been saved."),
                accept: "Discard",
                destructive: true
            }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: action => {
                discard.close();
                if (action.type === "accept")
                    root.controller.cancel_preference();
            }
        }
    }
    Controls.Dialog {
        id: templateConfirm
        objectName: "tableConfirmation_templateConfirm"
        parent: Overlay.overlay
        modal: true
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(420, parent.width - 24)
        height: 220
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: Confirmation.describe({
                message: qsTr("Update the template archive for %1?").arg(root.templateCode)
            }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: action => {
                templateConfirm.close();
                if (action.type === "accept")
                    root.controller.export_template(root.templateCode);
            }
        }
    }

    Controls.Dialog {
        id: connectionConfirm
        objectName: "tableConfirmation_connectionConfirm"
        parent: Overlay.overlay
        modal: true
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(420, parent.width - 24)
        height: 220
        onRejected: root.controller.confirm_connection_removal(false)
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: Confirmation.describe({
                message: qsTr("Remove this connection? The connected objects will be kept."),
                accept: "Remove connection",
                destructive: true
            }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: action => root.controller.confirm_connection_removal(action.type === "accept")
        }
    }

    Controls.Dialog {
        id: statusConfirm
        objectName: "tableConfirmation_statusConfirm"
        parent: Overlay.overlay
        modal: true
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(420, parent.width - 24)
        height: 220
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: Confirmation.describe({
                message: root.objectAction === "retire" ? qsTr("Retire this object?") : qsTr("Reactivate this object?"),
                accept: root.objectAction === "retire" ? "Retire" : "Reactivate",
                destructive: root.objectAction === "retire"
            }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: action => {
                statusConfirm.close();
                if (action.type === "accept")
                    root.controller.change_object_status(root.objectAction, root.objectCell);
            }
        }
    }
}
