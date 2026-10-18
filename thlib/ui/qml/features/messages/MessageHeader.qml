import QtQuick
import QtQuick.Window
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/messages/message.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var model
    required property var controller
    required property var host
    property bool hovered: false
    property real padding: 13
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    readonly property bool focused: {
        let item = root.Window.window ? root.Window.window.activeFocusItem : null;
        while (item) {
            if (item === root)
                return true;
            item = item.parent;
        }
        return false;
    }
    implicitHeight: 18
    implicitWidth: UI.header(presentation, 0, language).naturalWidth
    readonly property var presentation: ({
            sender: model.sender,
            senderDisplay: model.senderDisplay,
            senderColor: String(model.senderColor),
            first: model.groupFirst,
            time: model.timePretty,
            fullTime: model.timeSimple,
            edited: model.edited,
            editedBy: model.editedBy,
            editedAt: model.editedAt,
            own: model.isOwn,
            recipientCount: model.deliveryRecipientCount,
            deliveredCount: model.deliveryDeliveredCount,
            readCount: model.deliveryReadCount,
            deliveryStatus: model.deliveryStatus,
            busy: controller.busy,
            pinned: model.pinned,
            selectionMode: controller.forwardSelectionCount > 0,
            selected: model.forwardSelected,
            canReact: !model.reactionPending,
            hovered,
            focused,
            padding
        })
    scene: UI.header(presentation, width, language)
    onEvent: (action, source) => {
        if (action.type === "profile")
            userController.open_profile(root.model.sender);
        else if (action.type === "select")
            controller.toggle_forward_selection(root.model.messageId);
        else if (action.type === "pin")
            controller.unpin_message(root.model.messageId);
        else if (action.type === "reaction")
            host.openReactionPicker(root.model.messageId, source);
        else if (action.type === "history") {
            host.selectedEditHistory = root.model.editHistory;
            host.openBelow(source, host.timelineEditHistory);
        } else if (action.type === "menu") {
            host.prepareMessageActions(root.model, source);
            host.timelineActions.toggleBelow(source);
        }
    }
}
