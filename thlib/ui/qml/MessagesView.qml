import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls
import "features/messages" as MessagesFeature
import "tactic_frame" as Frame
import "tactic_frame/features/messages/conversation.ui.mjs" as ConversationUI
import "tactic_frame/controls/forms/people.ui.mjs" as PeopleUI
import "tactic_frame/features/messages/message.ui.mjs" as MessageUI
import "tactic_frame/features/messages/panels.ui.mjs" as PanelsUI
import "tactic_frame/features/messages/messaging.state.mjs" as Messaging
import "tactic_frame/features/messages/composer.ui.mjs" as ComposerUI

Item {
    id: root
    required property var theme
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    property var messages: null
    readonly property var timelineActions: messageActions
    readonly property var timelineEditHistory: editHistoryPopup
    readonly property var timelineReactions: reactionPicker
    readonly property var timelineSkeyMenu: skeyPreviewMenu
    readonly property var timelineAttachmentMenu: attachmentMenu
    property string draft: ""
    property var selectedRecipients: []
    property var editedMembers: []
    property string pendingDeleteMessageId: ""
    property string pendingEditMessageId: ""
    property string pendingEditBody: ""
    property var selectedEditHistory: []
    property string actionMessageId: ""
    property string actionMessageBody: ""
    property bool actionMessageCanEdit: false
    property bool actionMessageCanDelete: false
    property bool actionMessagePinned: false
    property var actionMessageEditHistory: []
    property var actionMessageAnchor: null
    property string mentionQuery: ""
    readonly property var mentionRows: (messagesController.conversationMembers || []).filter(row => root.mentionMatches(row))
    property string attachmentMenuToken: ""
    property bool attachmentMenuLocal: false
    property bool attachmentMenuImage: false
    property string skeyMenuValue: ""
    property bool skeyMenuFailed: false
    property bool skeyMenuCanOpen: true
    property var forwardTargets: ({})
    property bool messagePresentationReady: true
    property string pendingPresentationConversationId: ""
    readonly property var hostWindow: root.Window.window

    function activateConversationDraft(conversationId) {
        root.draft = String(messagesController.draftText || "");
    }

    function beginConversationPresentation(conversationId) {
        messages.cancelWheelScroll();
        messages.currentIndex = -1;
        root.pendingPresentationConversationId = String(conversationId || "");
        root.messagePresentationReady = false;
    }

    function finishConversationPresentation() {
        // Model notifications precede ListView's delegate layout. Position
        // the new conversation only after that update, while it is concealed.
        Qt.callLater(root.completeConversationPresentation);
    }

    function completeConversationPresentation() {
        const conversationId = String(messagesController.conversationId || "");
        if (!conversationId.length) {
            root.pendingPresentationConversationId = "";
            root.messagePresentationReady = true;
            return;
        }
        if (root.pendingPresentationConversationId !== conversationId)
            return;
        if (messages.count === 0 && messagesController.busy)
            return;
        messages.revealLatestOnce();
        root.pendingPresentationConversationId = "";
        root.messagePresentationReady = true;
        messages.presented = true;
    }

    function revealLatestMessage() {
        if (root.visible && root.hostWindow && root.hostWindow.visible && root.hostWindow.active && root.messagePresentationReady && messages && messages.current)
            messages.revealLatestOnce();
    }

    function openBelow(source, popup) {
        popup.openBelowItem(source, false, 6);
    }

    function jumpToMessage(messageId) {
        const row = messagesController.message_index(messageId);
        if (row < 0)
            return;
        messages.focusMessage(row);
        focusClearTimer.restart();
    }

    function prepareMessageActions(messageRow, anchorItem) {
        root.actionMessageId = messageRow.messageId;
        root.actionMessageBody = messageRow.body;
        root.actionMessageCanEdit = messagesController.can_change_message(messageRow.messageId);
        root.actionMessageCanDelete = root.actionMessageCanEdit;
        root.actionMessagePinned = messageRow.pinned;
        root.actionMessageEditHistory = messageRow.editHistory;
        root.actionMessageAnchor = anchorItem || null;
    }

    function openReactionPicker(messageId, anchorItem) {
        if (!messageId || !anchorItem)
            return;
        reactionPicker.openFor(messageId, anchorItem);
    }

    function setForwardTarget(conversationId, selected) {
        const values = Object.assign({}, root.forwardTargets);
        if (selected)
            values[conversationId] = true;
        else
            delete values[conversationId];
        root.forwardTargets = values;
    }

    function forwardTargetIds() {
        return Object.keys(root.forwardTargets).filter(conversationId => root.forwardTargets[conversationId]);
    }

    function formatFileSize(bytes) {
        const value = Math.max(0, Number(bytes) || 0);
        if (value === 0)
            return "";
        const units = ["B", "KB", "MB", "GB", "TB"];
        const unit = Math.min(units.length - 1, Math.floor(Math.log(value) / Math.log(1024)));
        const scaled = value / Math.pow(1024, unit);
        return (unit === 0 ? Math.round(scaled) : scaled.toFixed(1)) + " " + units[unit];
    }

    Timer {
        id: focusClearTimer
        interval: 1800
        onTriggered: messages.currentIndex = -1
    }

    function chatColor(index) {
        return [root.theme.action, root.theme.green, root.theme.cyan, root.theme.violet, root.theme.yellow][Math.max(0, Number(index) || 0) % 5];
    }

    function mentionMatches(member) {
        const query = root.mentionQuery.toLowerCase();
        return query.length === 0 || String(member.login || "").toLowerCase().indexOf(query) >= 0 || String(member.displayName || "").toLowerCase().indexOf(query) >= 0;
    }

    function syncReadState() {
        messagesController.set_visible(root.visible && !!root.hostWindow && root.hostWindow.visible && root.hostWindow.active);
    }

    Component.onCompleted: {
        root.activateConversationDraft(messagesController.conversationId);
        root.syncReadState();
        messagesController.load();
        if (messagesController.conversationId.length > 0 && messages.count > 0) {
            root.beginConversationPresentation(messagesController.conversationId);
            root.finishConversationPresentation();
        }
    }
    Component.onDestruction: {
        messagesController.set_draft_text(root.draft);
        messagesController.set_visible(false);
    }
    onVisibleChanged: root.syncReadState()

    Connections {
        target: root.hostWindow
        enabled: !!root.hostWindow

        function onVisibleChanged() {
            root.syncReadState();
        }
        function onActiveChanged() {
            root.syncReadState();
        }
    }

    CollaborationInitializationState {
        anchors.fill: parent
        z: 100
        visible: !messagesController.initialized
        theme: root.theme
        canInitialize: messagesController.canInitialize
        busy: messagesController.busy
        error: messagesController.error
        featureIcon: "message"
        featureTitle: qsTr("Messages are not initialized")
        featureMessage: qsTr("Initialize the collaboration schema before starting conversations.")
        projectCode: messagesController.projectCode
        onInitializeRequested: messagesController.initialize()
    }

    Connections {
        target: messagesController

        function onConversationChanging(conversationId) {
            root.activateConversationDraft(conversationId);
            root.beginConversationPresentation(conversationId);
        }

        function onConversationRestored(conversationId) {
            root.activateConversationDraft(conversationId);
            root.pendingPresentationConversationId = "";
            root.messagePresentationReady = true;
            messages.cancelWheelScroll();
            if (!messages.presented) {
                root.beginConversationPresentation(conversationId);
                root.finishConversationPresentation();
            }
            Qt.callLater(root.revealLatestMessage);
        }

        function onConversationLoaded() {
            root.finishConversationPresentation();
            Qt.callLater(root.revealLatestMessage);
        }

        function onVisibilityChanged(visible) {
            if (visible)
                Qt.callLater(root.revealLatestMessage);
        }

        function onMessageFocusRequested(messageId) {
            Qt.callLater(function () {
                root.jumpToMessage(String(messageId || ""));
            });
        }

        function onReplyStarted() {
            composer.focusEditor();
        }

        function onForwardStarted() {
            root.forwardTargets = ({});
            forwardDialog.open();
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    FileDialog {
        id: chatPreviewDialog
        title: qsTr("Choose chat preview")
        fileMode: FileDialog.OpenFile
        nameFilters: ["Images (*.jpg *.jpeg *.png *.webp)"]
        onAccepted: messagesController.set_conversation_preview(selectedFile)
    }

    Controls.Popup {
        id: conversationPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(Messaging.popup("create").width + effectiveShadowMargin * 2, Math.max(320, root.width - 32))
        height: Math.min(560, Math.max(390, root.height - 32))
        padding: 14

        contentItem: MessagesFeature.MessageForm {
            id: newChatTitle
            theme: root.theme
            mode: "create"
            availableBodyHeight: conversationPopup.availableHeight
            selectedLogins: root.selectedRecipients
            busy: messagesController.busy
            canCreateGroup: messagesController.canCreateGroup
            valid: root.selectedRecipients.length > 0 && (root.selectedRecipients.length === 1 || (messagesController.canCreateGroup && text.trim().length > 0))
            onSelectionChanged: logins => root.selectedRecipients = logins
            onCancelled: {
                reset();
                conversationPopup.close();
            }
            onSubmitted: {
                if (messagesController.create_conversation(root.selectedRecipients, text)) {
                    root.selectedRecipients = [];
                    reset();
                    conversationPopup.close();
                }
            }
        }
    }

    Controls.Popup {
        id: membersPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(Messaging.popup("view-members").width + effectiveShadowMargin * 2, root.width - 24)
        height: Math.min(390, root.height - 30)
        padding: 14
        contentItem: ColumnLayout {
            spacing: Messaging.popup("view-members").spacing
            Frame.FrameView {
                theme: root.theme
                Layout.fillWidth: true
                Layout.preferredHeight: 18
                scene: PanelsUI.heading("view-members", width, 0, root.language)
            }
            ListView {
                id: membersList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: messagesController.conversationMembers
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                }
                delegate: Frame.FrameView {
                    required property var modelData
                    width: Math.max(0, membersList.width - 14)
                    height: 58
                    theme: root.theme
                    scene: PeopleUI.row(Object.assign({}, modelData, {
                        current: !!modelData.current
                    }), width, root.language)
                    onEvent: action => {
                        membersPopup.close();
                        userController.open_profile(action.login);
                    }
                }
            }
        }
    }

    Controls.Popup {
        id: filesPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(Messaging.popup("files").width + effectiveShadowMargin * 2, root.width - 24)
        height: Math.min(430, root.height - 30)
        padding: 14
        contentItem: ColumnLayout {
            spacing: Messaging.popup("files").spacing
            Frame.FrameView {
                theme: root.theme
                Layout.fillWidth: true
                Layout.preferredHeight: 18
                scene: PanelsUI.heading("files", width, messagesController.conversationAttachments.length, root.language)
            }
            ListView {
                id: chatFilesList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: messagesController.conversationAttachments
                ScrollBar.vertical: Controls.ScrollBar {
                    id: chatFilesScrollBar
                    theme: root.theme
                }
                onAtYEndChanged: {
                    if (atYEnd && messagesController.hasMore && !messagesController.busy && chatFilesScrollBar.takePaginationPermit(false)) {
                        messagesController.load_more();
                    }
                }
                delegate: Frame.FrameView {
                    required property var modelData
                    theme: root.theme
                    width: Math.max(0, chatFilesList.width - 14)
                    height: 60
                    scene: PanelsUI.gallery(Object.assign({}, modelData, {
                        preview: !!modelData.previewUrl,
                        time: modelData.timestamp,
                        actions: true,
                        busy: messagesController.busy
                    }), width, root.language)
                    onEvent: (action, source) => {
                        if (action.type === "jump") {
                            root.jumpToMessage(modelData.messageId);
                            filesPopup.close();
                        } else if (action.type === "menu") {
                            root.attachmentMenuToken = String(modelData.token || "");
                            root.attachmentMenuLocal = !!modelData.local;
                            root.attachmentMenuImage = /^(png|jpe?g|webp|gif|bmp)$/i.test(String(modelData.extension || ""));
                            attachmentMenu.toggleBelow(source);
                        }
                    }
                }
                Label {
                    anchors.centerIn: parent
                    visible: chatFilesList.count === 0
                    text: qsTr("No files in loaded messages")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
            }
            Controls.Button {
                Layout.alignment: Qt.AlignHCenter
                visible: messagesController.hasMore
                theme: root.theme
                text: qsTr("Load earlier messages")
                enabled: !messagesController.busy
                onClicked: messagesController.load_more()
            }
        }
    }

    Controls.Popup {
        id: messageSearchPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(Messaging.popup("search").width + effectiveShadowMargin * 2, root.width - 24)
        padding: 14
        onAboutToShow: messageSearchField.text = messagesController.messageSearch
        onOpened: Qt.callLater(messageSearchField.focusEditor)
        contentItem: MessagesFeature.MessageForm {
            id: messageSearchField
            theme: root.theme
            mode: "search"
            busy: messagesController.busy
            activeSearch: messagesController.messageSearch.length > 0
            onSubmitted: {
                messagesController.search_messages(text);
                messageSearchPopup.close();
            }
            onSearchCleared: {
                text = "";
                messagesController.search_messages("");
                messageSearchPopup.close();
            }
        }
    }

    Controls.Popup {
        id: addMembersPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(Messaging.popup("members").width + effectiveShadowMargin * 2, Math.max(320, root.width - 32))
        height: Math.min(560, Math.max(390, root.height - 32))
        padding: 14
        onAboutToShow: {
            root.editedMembers = Array.from(messagesController.selectedConversation.recipients || []);
            addMemberUsers.setSelection(root.editedMembers);
        }

        contentItem: MessagesFeature.MessageForm {
            id: addMemberUsers
            theme: root.theme
            mode: "members"
            availableBodyHeight: addMembersPopup.availableHeight
            selectedLogins: root.editedMembers
            busy: messagesController.busy
            valid: root.editedMembers.length > 0
            onSelectionChanged: logins => root.editedMembers = logins
            onCancelled: addMembersPopup.close()
            onSubmitted: if (messagesController.set_members(root.editedMembers))
                addMembersPopup.close()
        }
    }

    Controls.Popup {
        id: renameChatPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(Messaging.popup("rename").width + effectiveShadowMargin * 2, root.width - 32)

        contentItem: MessagesFeature.MessageForm {
            id: chatTitleField
            theme: root.theme
            mode: "rename"
            busy: messagesController.busy
            valid: text.trim().length > 0
            onCancelled: renameChatPopup.close()
            onSubmitted: if (messagesController.rename_conversation(text))
                renameChatPopup.close()
        }
    }

    Controls.Dialog {
        id: deleteChatDialog
        theme: root.theme
        parent: Overlay.overlay
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(420, root.width - 40)
        title: qsTr("Delete chat?")
        standardButtons: Dialog.NoButton

        contentItem: MessagesFeature.MessageForm {
            theme: root.theme
            mode: "delete"
            busy: messagesController.busy
            onCancelled: deleteChatDialog.close()
            onSubmitted: if (messagesController.delete_conversation())
                deleteChatDialog.close()
        }
    }

    Controls.Dialog {
        id: clearNotesDialog
        theme: root.theme
        parent: Overlay.overlay
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(420, root.width - 40)
        title: qsTr("Clear favorites?")
        standardButtons: Dialog.NoButton

        contentItem: MessagesFeature.MessageForm {
            theme: root.theme
            mode: "clear"
            busy: messagesController.busy
            onCancelled: clearNotesDialog.close()
            onSubmitted: if (messagesController.clear_personal_chat())
                clearNotesDialog.close()
        }
    }

    Controls.Dialog {
        id: editMessageDialog
        theme: root.theme
        parent: Overlay.overlay
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(480, root.width - 40)
        title: qsTr("Edit message")
        standardButtons: Dialog.NoButton
        onAboutToShow: editMessageField.text = root.pendingEditBody
        onOpened: Qt.callLater(editMessageField.focusEditor)
        onClosed: {
            root.pendingEditMessageId = "";
            root.pendingEditBody = "";
        }

        contentItem: MessagesFeature.MessageForm {
            id: editMessageField
            theme: root.theme
            mode: "edit"
            busy: messagesController.busy
            valid: text.trim().length > 0
            onCancelled: editMessageDialog.close()
            onSubmitted: if (messagesController.edit_message(root.pendingEditMessageId, text))
                editMessageDialog.close()
        }
    }

    Controls.Dialog {
        id: forwardDialog
        theme: root.theme
        parent: Overlay.overlay
        modal: false
        anchors.centerIn: Overlay.overlay
        width: Math.min(460, Overlay.overlay.width - 32)
        height: Math.min(540, Overlay.overlay.height - 32)
        title: qsTr("Forward messages")
        standardButtons: Dialog.NoButton
        onClosed: {
            root.forwardTargets = ({});
            if (!messagesController.busy)
                messagesController.clear_forward_selection();
        }

        contentItem: MessagesFeature.MessageForward {
            theme: root.theme
            conversations: messageConversationModel
            targets: root.forwardTargets
            selectionCount: messagesController.forwardSelectionCount
            busy: messagesController.busy
            valid: root.forwardTargetIds().length > 0 && messagesController.forwardSelectionCount > 0
            onTargetToggled: key => root.setForwardTarget(key, !root.forwardTargets[key])
            onCancelled: forwardDialog.close()
            onSubmitted: if (messagesController.forward_messages(root.forwardTargetIds()))
                forwardDialog.close()
        }
    }

    Controls.Popup {
        id: editHistoryPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(Messaging.popup("history").width + effectiveShadowMargin * 2, Math.max(280, root.width - 32))
        height: Math.min(360, Math.max(180, root.height - 40))
        padding: 14

        contentItem: ColumnLayout {
            spacing: Messaging.popup("history").spacing
            Frame.FrameView {
                theme: root.theme
                Layout.fillWidth: true
                Layout.preferredHeight: 18
                scene: PanelsUI.heading("history", width, 0, root.language)
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: root.selectedEditHistory
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                }
                delegate: MessagesFeature.MessageRevision {
                    required property var modelData
                    theme: root.theme
                    width: Math.max(0, ListView.view.width - 14)
                    height: implicitHeight
                    record: modelData
                    mode: "history"
                    busy: messagesController.busy
                    onActivated: messageId => {
                        root.jumpToMessage(messageId);
                        editHistoryPopup.close();
                    }
                }
            }
        }
    }

    Controls.Popup {
        id: pinHistoryPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(Messaging.popup("pin-history").width + effectiveShadowMargin * 2, Math.max(280, root.width - 32))
        height: Math.min(360, Math.max(180, root.height - 40))
        padding: 14
        contentItem: ColumnLayout {
            spacing: Messaging.popup("pin-history").spacing
            Frame.FrameView {
                theme: root.theme
                Layout.fillWidth: true
                Layout.preferredHeight: 18
                scene: PanelsUI.heading("pin-history", width, 0, root.language)
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: messagesController.pinHistory
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                }
                delegate: MessagesFeature.MessageRevision {
                    required property var modelData
                    theme: root.theme
                    width: Math.max(0, ListView.view.width - 14)
                    height: implicitHeight
                    record: modelData
                    mode: "pin-history"
                    busy: messagesController.busy
                    onActivated: messageId => {
                        root.jumpToMessage(messageId);
                        pinHistoryPopup.close();
                    }
                }
            }
        }
    }

    Controls.Popup {
        id: mentionPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(320, Math.max(240, root.width - 32))
        height: Math.min(250, Math.max(120, root.height - 40))
        padding: 8
        focus: false
        onAboutToShow: mentionList.currentIndex = 0
        contentItem: ListView {
            id: mentionList
            clip: true
            spacing: 0
            model: root.mentionRows
            currentIndex: 0
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }
            delegate: Frame.FrameView {
                required property var modelData
                required property int index
                theme: root.theme
                width: Math.max(0, mentionList.width - 14)
                height: 46
                scene: PanelsUI.mention(Object.assign({}, modelData, {
                    selected: index === mentionList.currentIndex
                }), width)
                onEvent: action => {
                    composer.insertMention(action.login);
                    mentionPopup.close();
                }
            }
        }
    }

    Controls.Dialog {
        id: deleteMessageDialog
        theme: root.theme
        parent: Overlay.overlay
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(420, root.width - 40)
        title: qsTr("Delete message?")
        standardButtons: Dialog.NoButton
        onClosed: root.pendingDeleteMessageId = ""

        contentItem: MessagesFeature.MessageForm {
            theme: root.theme
            mode: "delete-message"
            busy: messagesController.busy
            valid: root.pendingDeleteMessageId.length > 0
            onCancelled: deleteMessageDialog.close()
            onSubmitted: if (messagesController.delete_message(root.pendingDeleteMessageId))
                deleteMessageDialog.close()
        }
    }

    MessageReactionPicker {
        id: reactionPicker
        theme: root.theme
        catalog: emojiCatalog
        onReactionSelected: (messageId, emoji) => {
            if (messagesController.toggle_reaction(messageId, emoji))
                reactionPicker.close();
        }
    }

    function selectedConversationPresenceText() {
        const conversation = messagesController.selectedConversation || ({});
        if (!String(conversation.peerLogin || "").length)
            return "";
        if (!conversation.presenceKnown)
            return qsTr("Status unavailable");
        if (conversation.online)
            return qsTr("Online");
        const lastSeen = String(conversation.lastSeenPretty || "");
        return lastSeen.length ? qsTr("Last seen %1").arg(lastSeen) : qsTr("Offline");
    }

    ActionMenu {
        id: chatActions
        objectName: "chatActionsMenu"
        theme: root.theme
        parent: Overlay.overlay
        preferredWidth: 230
        actions: [
            {
                "title": "Rename chat",
                "icon": "edit",
                "command": "rename",
                "enabled": !!messagesController.selectedConversation.canRename
            },
            {
                "title": "Change preview",
                "icon": "image",
                "command": "preview",
                "enabled": !!messagesController.selectedConversation.canManage
            },
            {
                "title": "Add or remove members",
                "icon": "manage-accounts",
                "command": "members",
                "enabled": !!messagesController.selectedConversation.canAddMembers
            },
            {
                "separator": true
            },
            {
                "title": messagesController.selectedConversation.canClearPersonal ? "Clear favorites" : "Delete chat",
                "icon": messagesController.selectedConversation.canClearPersonal ? "delete-sweep" : "delete",
                "command": messagesController.selectedConversation.canClearPersonal ? "clear" : "delete",
                "enabled": !!messagesController.selectedConversation.canClearPersonal || !!messagesController.selectedConversation.canDelete
            }
        ]
        onTriggered: command => {
            if (command === "rename") {
                chatTitleField.text = messagesController.selectedConversation.title || "";
                renameChatPopup.openCenteredIn(Overlay.overlay);
                Qt.callLater(chatTitleField.focusEditor);
            } else if (command === "preview") {
                chatPreviewDialog.open();
            } else if (command === "members") {
                addMembersPopup.openCenteredIn(Overlay.overlay);
            } else if (command === "clear") {
                clearNotesDialog.open();
            } else if (command === "delete") {
                deleteChatDialog.open();
            }
        }
    }

    ActionMenu {
        id: messageActions
        theme: root.theme
        parent: Overlay.overlay
        preferredWidth: 210
        actions: [
            {
                "title": "Reply",
                "icon": "reply",
                "command": "reply",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "title": "Forward",
                "icon": "share",
                "command": "forward",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "title": "Add reaction",
                "icon": "emoji",
                "command": "reaction",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "title": "Select messages",
                "icon": "check-circle",
                "command": "select_forward",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "separator": true
            },
            {
                "title": messagesController.forwardSelectionCount > 1 ? "Copy selected sKeys" : "Copy sKey",
                "icon": "content-copy",
                "command": "copy_skey",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "separator": true
            },
            {
                "title": root.actionMessagePinned ? "Unpin message" : "Pin message",
                "icon": "push-pin",
                "command": "pin",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "title": "Edit message",
                "icon": "edit",
                "command": "edit",
                "visible": root.actionMessageCanEdit
            },
            {
                "title": "Edit history",
                "icon": "history",
                "command": "history",
                "enabled": root.actionMessageEditHistory.length > 0
            },
            {
                "separator": true,
                "visible": root.actionMessageCanDelete
            },
            {
                "title": "Delete message",
                "icon": "delete",
                "command": "delete",
                "visible": root.actionMessageCanDelete
            }
        ]
        onTriggered: command => {
            if (command === "reply") {
                messagesController.begin_reply(root.actionMessageId);
            } else if (command === "forward") {
                messagesController.begin_forward(root.actionMessageId);
            } else if (command === "reaction") {
                root.openReactionPicker(root.actionMessageId, root.actionMessageAnchor);
            } else if (command === "select_forward") {
                messagesController.toggle_forward_selection(root.actionMessageId);
            } else if (command === "copy_skey") {
                messagesController.copy_message_skey(root.actionMessageId);
            } else if (command === "pin") {
                if (root.actionMessagePinned)
                    messagesController.unpin_message(root.actionMessageId);
                else
                    messagesController.pin_message(root.actionMessageId);
            } else if (command === "edit") {
                root.pendingEditMessageId = root.actionMessageId;
                root.pendingEditBody = root.actionMessageBody;
                editMessageDialog.open();
            } else if (command === "history") {
                root.selectedEditHistory = root.actionMessageEditHistory;
                editHistoryPopup.openCenteredIn(Overlay.overlay);
            } else if (command === "delete") {
                root.pendingDeleteMessageId = root.actionMessageId;
                deleteMessageDialog.open();
            }
        }
    }

    ActionMenu {
        id: attachmentMenu
        theme: root.theme
        parent: Overlay.overlay
        actions: [
            {
                "title": "Download",
                "icon": "download",
                "command": "download",
                "enabled": !root.attachmentMenuLocal
            },
            {
                "title": "Show folder",
                "icon": "folder_open",
                "command": "folder",
                "enabled": root.attachmentMenuLocal
            },
            {
                "title": root.attachmentMenuLocal ? "Open file" : "Download and open",
                "icon": "open_in_new",
                "command": "open"
            },
            {
                "separator": true
            },
            {
                "title": "Copy file path",
                "icon": "content_copy",
                "command": "copy_path"
            },
            {
                "title": "Copy web link",
                "icon": "link",
                "command": "copy_web"
            },
            {
                "title": "Copy image",
                "icon": "image",
                "command": "copy_image",
                "enabled": root.attachmentMenuLocal && root.attachmentMenuImage
            }
        ]
        onTriggered: command => messagesController.attachment_action(root.attachmentMenuToken, command)
    }

    ActionMenu {
        id: skeyPreviewMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {
                "title": root.skeyMenuFailed ? "Retry preview" : root.skeyMenuCanOpen ? "Open linked item" : "Source conversation is unavailable",
                "icon": root.skeyMenuFailed ? "refresh" : "open_in_new",
                "command": root.skeyMenuFailed ? "retry" : "open",
                "enabled": root.skeyMenuFailed || root.skeyMenuCanOpen
            },
            {
                "title": "Copy sKey",
                "icon": "content_copy",
                "command": "copy"
            }
        ]
        onTriggered: command => {
            if (command === "retry")
                messagesController.retry_skey_preview(root.skeyMenuValue);
            else if (command === "copy")
                messagesController.copy_skey_preview(root.skeyMenuValue);
            else
                messagesController.open_skey_preview(root.skeyMenuValue);
        }
    }

    SplitView {
        id: messagesWorkspaceSplit
        objectName: "messagesWorkspaceSplit"
        anchors.fill: parent
        anchors.margins: 12
        orientation: Qt.Horizontal
        handle: Controls.SplitterHandle {
            theme: root.theme
        }

        MessagesConversationList {
            objectName: "messagesConversationPane"
            theme: root.theme
            conversationModel: messageConversationModel
            onNewConversationRequested: {
                root.selectedRecipients = [];
                newChatTitle.reset();
                newChatTitle.clear();
                conversationPopup.openCenteredIn(Overlay.overlay);
            }
            onConversationSelected: index => messagesController.select_conversation(index)
            onConversationContextRequested: (index, source, x, y) => {
                messagesController.select_conversation(index);
                chatActions.openAt(source, x, y);
            }
        }
        Rectangle {
            objectName: "messagesTimelinePane"
            SplitView.fillWidth: true
            SplitView.minimumWidth: 440
            radius: 12
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Frame.FrameView {
                    objectName: "messagesChatHeader"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    theme: root.theme
                    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
                    readonly property var conversation: messagesController.selectedConversation
                    readonly property string subtitle: {
                        if (!messagesController.conversationId.length)
                            return "";
                        if (conversation.isPersonalNotes)
                            return qsTr("Your personal notes") + " · " + Number(conversation.messageCount || 0) + qsTr(" notes");
                        return (conversation.peerLogin ? "" : Number(conversation.participantCount || 0) + qsTr(" members") + " · ") + Number(conversation.messageCount || 0) + qsTr(" messages");
                    }
                    TextMetrics {
                        id: presenceMetrics
                        text: root.selectedConversationPresenceText()
                        font: Qt.font({
                            family: root.theme.fontFamily,
                            pixelSize: 11
                        })
                    }
                    scene: ConversationUI.header(Object.assign({}, conversation, {
                        conversationId: messagesController.conversationId,
                        busy: messagesController.busy,
                        search: messagesController.messageSearch.length > 0,
                        subtitle,
                        presence: conversation.peerLogin ? root.selectedConversationPresenceText() : "",
                        presenceWidth: Math.ceil(presenceMetrics.advanceWidth)
                    }), width, language)
                    onEvent: (action, source) => {
                        if (action.type === "menu")
                            chatActions.toggleBelow(source);
                        else if (action.type === "refresh")
                            messagesController.refresh_current();
                        else if (action.type === "search")
                            root.openBelow(source, messageSearchPopup);
                        else if (action.type === "members")
                            root.openBelow(source, membersPopup);
                        else if (action.type === "files") {
                            if (messagesController.messageSearch.length > 0)
                                messagesController.search_messages("");
                            root.openBelow(source, filesPopup);
                        }
                    }
                    Item {
                        objectName: "chatBusySlot"
                        visible: messagesController.busy
                        x: parent.width - 32
                        y: 19
                        width: 20
                        height: 20
                        Controls.BusyIndicator {
                            uiTheme: root.theme
                            anchors.fill: parent
                            running: parent.visible
                        }
                    }
                }

                Frame.FrameView {
                    id: pinnedMessageBar
                    theme: root.theme
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    visible: !!messagesController.pinnedMessage.messageId
                    scene: MessageUI.pinned(messagesController.pinnedMessage, width, root.language)
                    onEvent: (action, source) => {
                        if (action.type === "open")
                            messagesController.show_message(String(messagesController.pinnedMessage.messageId || ""));
                        else if (action.type === "history")
                            root.openBelow(source, pinHistoryPopup);
                    }
                }

                Label {
                    visible: false
                    Layout.fillWidth: true
                    text: qsTr("Created by ") + String(messagesController.selectedConversation.createdBy || "unknown") + "  ·  Created " + String(messagesController.selectedConversation.createdPretty || "unknown") + "  ·  Active " + String(messagesController.selectedConversation.activePretty || "never")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    opacity: 0.76
                    elide: Text.ElideRight
                }

                Rectangle {
                    visible: messagesController.error.length > 0 || messageAttachments.error.length > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: 44
                    radius: 10
                    color: root.theme.surfaceContainerHigh
                    border.width: 1
                    border.color: root.theme.error
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        spacing: 10
                        Controls.MaterialIcon {
                            name: "error"
                            size: 17
                            color: root.theme.error
                        }
                        Label {
                            id: messageErrorLabel
                            Layout.fillWidth: true
                            text: messagesController.error || messageAttachments.error
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            elide: Text.ElideRight
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            toolTip: qsTr("Dismiss error")
                            onClicked: {
                                messagesController.dismiss_error();
                                messageAttachments.dismiss_error();
                            }
                        }
                    }
                    Controls.ToolTip {
                        theme: root.theme
                        visible: messageErrorMouse.containsMouse && messageErrorLabel.truncated && !root.theme.suppressToolTips
                        text: messageErrorLabel.text
                    }
                    MouseArea {
                        id: messageErrorMouse
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.rightMargin: 38
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton
                    }
                }

                Item {
                    id: messageViewport
                    objectName: "messageViewport"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.topMargin: 10
                    Layout.bottomMargin: 10
                    clip: true

                    Repeater {
                        model: messageSurfaceModel
                        delegate: MessagesTimeline {
                            id: conversationTimeline
                            required property var messageModel
                            required property string conversationId
                            theme: root.theme
                            host: root
                            controller: messagesController
                            timelineModel: messageModel
                            onCurrentChanged: {
                                if (current)
                                    root.messages = conversationTimeline;
                                else {
                                    conversationTimeline.cancelWheelScroll();
                                    conversationTimeline.cancelFlick();
                                }
                            }
                            Component.onCompleted: {
                                if (current)
                                    root.messages = conversationTimeline;
                            }
                        }
                    }

                    Rectangle {
                        anchors.fill: parent
                        z: 240
                        visible: !root.messagePresentationReady && (root.pendingPresentationConversationId.length > 0 || messagesController.conversationId.length > 0)
                        color: root.theme.workspace

                        Column {
                            anchors.centerIn: parent
                            spacing: 9
                            Controls.BusyIndicator {
                                uiTheme: root.theme
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: 30
                                height: 30
                                running: parent.parent.visible
                            }
                            Label {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: qsTr("Loading conversation")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                            }
                        }
                    }
                }

                Rectangle {
                    visible: messagesController.forwardSelectionCount > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    radius: 10
                    color: root.theme.surfaceContainerHigh
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        spacing: 8
                        Controls.MaterialIcon {
                            name: "share"
                            size: 17
                            color: root.theme.tertiary
                        }
                        Label {
                            Layout.fillWidth: true
                            text: messagesController.forwardSelectionCount + (messagesController.forwardSelectionCount === 1 ? qsTr(" message selected") : qsTr(" messages selected"))
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "content-copy"
                            toolTip: messagesController.forwardSelectionCount === 1 ? qsTr("Copy selected sKey") : qsTr("Copy selected sKeys")
                            enabled: !messagesController.busy
                            onClicked: messagesController.copy_message_skey("")
                        }
                        Controls.Button {
                            theme: root.theme
                            text: qsTr("Forward")
                            highlighted: true
                            enabled: !messagesController.busy
                            onClicked: messagesController.request_forward()
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            toolTip: qsTr("Cancel selection")
                            onClicked: messagesController.clear_forward_selection()
                        }
                    }
                }

                MessageReplyPreview {
                    visible: String(messagesController.replyTarget.messageId || "").length > 0
                    Layout.fillWidth: true
                    theme: root.theme
                    sender: String(messagesController.replyTarget.senderDisplay || "")
                    body: String(messagesController.replyTarget.body || "")
                    dismissible: true
                    onActivated: messagesController.show_message(String(messagesController.replyTarget.messageId || ""))
                    onDismissed: messagesController.cancel_reply()
                }

                RowLayout {
                    visible: messagesController.conversationId.length > 0
                    Layout.fillWidth: true
                    spacing: 10
                    Layout.topMargin: 2
                    AttachmentComposerControls {
                        theme: root.theme
                        controller: messageAttachments
                        attachmentModel: messageAttachmentDraftModel
                        Layout.alignment: Qt.AlignVCenter
                    }
                    Item {
                        id: composerRow
                        Layout.fillWidth: true
                        Layout.preferredHeight: geometry.height
                        readonly property var geometry: ComposerUI.layout(width, composer.implicitHeight)
                        MessageComposerField {
                            id: composer
                            mentioning: mentionPopup.opened
                            mentionCount: root.mentionRows.length
                            onMentionStepped: delta => {
                                const count = root.mentionRows.length;
                                if (count) {
                                    mentionList.currentIndex = (mentionList.currentIndex + delta + count) % count;
                                    mentionList.positionViewAtIndex(mentionList.currentIndex, ListView.Contain);
                                }
                            }
                            onMentionAccepted: {
                                const row = root.mentionRows[Math.max(0, mentionList.currentIndex)];
                                if (row) {
                                    composer.insertMention(String(row.login));
                                    mentionPopup.close();
                                }
                            }
                            onMentionDismissed: mentionPopup.close()
                            x: composerRow.geometry.field.x
                            y: composerRow.geometry.field.y
                            width: composerRow.geometry.field.width
                            height: composerRow.geometry.field.height
                            theme: root.theme
                            emojiCatalogModel: emojiCatalog
                            attachmentController: messageAttachments
                            placeholderText: qsTr("Write a reply · Enter to send · Ctrl+Enter for a new line")
                            text: root.draft
                            readOnly: messagesController.sending || messageAttachments.busy
                            onTextChanged: {
                                root.draft = text;
                                messagesController.set_draft_text(text);
                            }
                            onMentionRequested: query => {
                                root.mentionQuery = query;
                                if (query.length >= 0 && text.slice(0, cursorPosition).match(/(^|\s)@[A-Za-z0-9_.-]*$/)) {
                                    if (!mentionPopup.opened)
                                        root.openBelow(composer, mentionPopup);
                                } else {
                                    mentionPopup.close();
                                }
                            }
                            onSubmitRequested: sendButton.clicked()
                        }
                        MessageSendButton {
                            id: sendButton
                            theme: root.theme
                            x: composerRow.geometry.send.x
                            y: composerRow.geometry.send.y
                            width: composerRow.geometry.send.width
                            height: composerRow.geometry.send.height
                            compact: composerRow.geometry.compact
                            sending: messagesController.sending
                            hasContent: !messagesController.busy && (root.draft.trim().length > 0 || messageAttachments.count > 0)
                            onClicked: messagesController.send(root.draft)
                        }
                    }
                }
            }

            Controls.AttachmentDropArea {
                id: chatDropArea
                anchors.fill: parent
                z: 20
                theme: root.theme
                attachmentController: messageAttachments
                enabled: messagesController.conversationId.length > 0 && !messageAttachments.busy
            }
        }
    }

    Connections {
        target: messagesController
        function onMessageSentForConversation(conversationId) {
            root.draft = String(messagesController.draftText || "");
        }

        function onDraftChanged() {
            const value = String(messagesController.draftText || "");
            if (root.draft !== value)
                root.draft = value;
        }

        function onMessageAppendedForConversation(conversationId) {
            if (String(conversationId || "") !== String(messagesController.conversationId || ""))
                return;
            Qt.callLater(root.revealLatestMessage);
        }
    }
}
