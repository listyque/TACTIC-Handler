import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/forms.ui.mjs" as UI

Controls.Dialog {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    readonly property var shelves: (controller.view_data.shelves || []).filter(row => operation !== "update_shelf" || row.owner === controller.current_user)
    objectName: "workspaceShelfDialog"
    required property var controller
    property string operation: "compare_shelf"
    property var shelf: ({})
    title: operation === "update_shelf" ? qsTr("Replace selected files in shelf") : qsTr("Compare pending with shelf")
    parent: Overlay.overlay
    modal: true
    draggable: true
    closePolicy: Popup.CloseOnEscape
    width: Math.min(560, parent ? parent.width - 24 : 560)
    onAboutToShow: {
        x = Qt.binding(() => Math.max(0, (parent.width - width) / 2));
        y = Qt.binding(() => Math.max(0, (parent.height - height) / 2));
    }
    footer: null
    signal chosen(var values)
    contentItem: Frame.FrameView {
        id: form
        theme: root.theme
        implicitHeight: Math.min(300, Math.max(160, (root.parent ? root.parent.height : 600) - 138))
        scene: UI.shelf({
            options: root.shelves.map(row => ({
                        value: row.code,
                        label: row.label
                    })),
            code: root.shelf.code || "",
            busy: root.controller.busy,
            after: root.controller.view_data.shelves_after
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "shelf")
                root.shelf = root.shelves.find(row => row.code === action.value) || ({});
            else if (action.type === "more")
                root.controller.action("shelf_targets_more", {});
            else if (action.type === "reject")
                root.reject();
            else if (action.type === "accept" && root.shelf.code && !root.controller.busy)
                root.accept();
        }
    }
    onAccepted: if (shelf.code)
        chosen({
            shelf: shelf.code,
            shelf_revision: String(shelf.edit_revision)
        })
}
