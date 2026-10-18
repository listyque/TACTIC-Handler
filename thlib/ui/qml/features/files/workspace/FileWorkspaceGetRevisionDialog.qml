import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/forms.ui.mjs" as UI

Controls.Dialog {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language

    objectName: "workspaceGetRevisionDialog"
    required property var controller
    property string scope: "workspace"
    property string target: ""
    property string selector: ""
    property string value: ""
    property bool force: false
    property var request: ({})
    readonly property bool valid: UI.validRevision({
        selector: selector,
        value: value
    })
    title: qsTr("Get Revision")
    modal: true
    width: Math.min(480, parent ? parent.width - 24 : 480)
    parent: Overlay.overlay
    anchors.centerIn: parent
    footer: null
    contentItem: Frame.FrameView {
        id: form
        theme: root.theme
        implicitHeight: Math.min(440, Math.max(160, (root.parent ? root.parent.height : 700) - 138))
        scene: UI.revision({
            target: root.target,
            selector: root.selector,
            value: root.value,
            force: root.force,
            busy: root.controller.busy
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "selector") {
                root.selector = action.value;
                root.value = "";
            } else if (action.type === "value")
                root.value = action.value;
            else if (action.type === "force")
                root.force = action.value;
            else if (action.type === "reject")
                root.reject();
            else if (action.type === "accept" && root.valid && !root.controller.busy)
                root.accept();
        }
    }
    onAccepted: {
        const values = Object.assign({}, request, {
            scope: scope,
            force: force
        });
        if (selector !== "")
            values[selector] = value.trim();
        controller.action("get_revision", values);
    }
}
