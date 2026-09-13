import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls

Item {
    id: root
    required property var theme
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
    property bool actionMessagePinned: false
    property var actionMessageEditHistory: []
    property var actionMessageAnchor: null
    property string mentionQuery: ""
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
        root.draft = String(messagesController.draftText || "")
    }

    function beginConversationPresentation(conversationId) {
        messages.cancelScrollAnimation()
        messages.currentIndex = -1
        root.pendingPresentationConversationId = String(conversationId || "")
        root.messagePresentationReady = false
    }

    function finishConversationPresentation() {
        const conversationId = String(messagesController.conversationId || "")
        if (!conversationId.length) {
            root.pendingPresentationConversationId = ""
            root.messagePresentationReady = true
            return
        }
        if (root.pendingPresentationConversationId !== conversationId)
            return
        root.pendingPresentationConversationId = ""
        messages.settleAtLatest()
        root.messagePresentationReady = true
        messages.presented = true
    }

    function openBelow(source, popup) {
        popup.openBelowItem(source, false, 6)
    }

    function jumpToMessage(messageId) {
        const row = messagesController.message_index(messageId)
        if (row < 0)
            return
        messages.positionViewAtIndex(row, ListView.Center)
        messages.currentIndex = row
        focusClearTimer.restart()
    }

    function prepareMessageActions(messageRow, anchorItem) {
        root.actionMessageId = messageRow.messageId
        root.actionMessageBody = messageRow.body
        root.actionMessageCanEdit = messageRow.canEdit
        root.actionMessagePinned = messageRow.pinned
        root.actionMessageEditHistory = messageRow.editHistory
        root.actionMessageAnchor = anchorItem || null
    }

    function openReactionPicker(messageId, anchorItem) {
        if (!messageId || !anchorItem)
            return
        reactionPicker.openFor(messageId, anchorItem)
    }

    function setForwardTarget(conversationId, selected) {
        const values = Object.assign({}, root.forwardTargets)
        if (selected)
            values[conversationId] = true
        else
            delete values[conversationId]
        root.forwardTargets = values
    }

    function forwardTargetIds() {
        return Object.keys(root.forwardTargets).filter(
            conversationId => root.forwardTargets[conversationId])
    }

    function formatFileSize(bytes) {
        const value = Math.max(0, Number(bytes) || 0)
        if (value === 0)
            return ""
        const units = ["B", "KB", "MB", "GB", "TB"]
        const unit = Math.min(
            units.length - 1, Math.floor(Math.log(value) / Math.log(1024)))
        const scaled = value / Math.pow(1024, unit)
        return (unit === 0 ? Math.round(scaled) : scaled.toFixed(1))
            + " " + units[unit]
    }

    Timer {
        id: focusClearTimer
        interval: 1800
        onTriggered: messages.currentIndex = -1
    }

    function chatColor(index) {
        return [
            root.theme.action,
            root.theme.green,
            root.theme.cyan,
            root.theme.violet,
            root.theme.yellow
        ][Math.max(0, Number(index) || 0) % 5]
    }

    function mentionMatches(member) {
        const query = root.mentionQuery.toLowerCase()
        return query.length === 0
            || String(member.login || "").toLowerCase().indexOf(query) >= 0
            || String(member.displayName || "").toLowerCase().indexOf(query) >= 0
    }

    function syncReadState() {
        messagesController.set_visible(
            root.visible && !!root.hostWindow
            && root.hostWindow.visible
            && root.hostWindow.active
        )
    }

    Component.onCompleted: {
        root.activateConversationDraft(messagesController.conversationId)
        root.syncReadState()
        messagesController.load()
        if (messagesController.conversationId.length > 0
                && messages.count > 0) {
            root.beginConversationPresentation(
                messagesController.conversationId)
            root.finishConversationPresentation()
        }
    }
    Component.onDestruction: {
        messagesController.set_draft_text(root.draft)
        messagesController.set_visible(false)
    }
    onVisibleChanged: root.syncReadState()

    Connections {
        target: root.hostWindow
        enabled: !!root.hostWindow

        function onVisibleChanged() { root.syncReadState() }
        function onActiveChanged() { root.syncReadState() }
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
            root.activateConversationDraft(conversationId)
            root.beginConversationPresentation(conversationId)
        }

        function onConversationRestored(conversationId) {
            root.activateConversationDraft(conversationId)
            root.pendingPresentationConversationId = ""
            root.messagePresentationReady = true
            messages.cancelScrollAnimation()
            if (!messages.presented) {
                messages.positionCachedAtLatest()
                messages.presented = true
            }
        }

        function onConversationLoaded() {
            root.finishConversationPresentation()
        }

        function onMessageFocusRequested(messageId) {
            root.jumpToMessage(String(messageId || ""))
        }

        function onReplyStarted() {
            composer.focusEditor()
        }

        function onForwardStarted() {
            root.forwardTargets = ({})
            forwardDialog.open()
        }
    }

    Rectangle { anchors.fill: parent; color: root.theme.workspace }

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
        width: Math.min(460, Math.max(320, root.width - 32))
        height: Math.min(560, Math.max(390, root.height - 32))
        padding: 14

        contentItem: ColumnLayout {
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Controls.MaterialIcon {
                    name: "group-add"
                    size: 22
                    color: root.theme.action
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("New conversation")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Find people and start a direct or group chat")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                }
            }
            UserPicker {
                id: newConversationUsers
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                selectedLogins: root.selectedRecipients
                onSelectionChanged: logins => root.selectedRecipients = logins
            }
            Controls.TextField {
                id: newChatTitle
                visible: root.selectedRecipients.length > 1
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Group chat title")
            }
            Label {
                Layout.fillWidth: true
                visible: root.selectedRecipients.length > 1
                    && !messagesController.canCreateGroup
                text: qsTr("Group chats can be created by administrators and supervisors")
                color: root.theme.yellow
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: root.selectedRecipients.length + qsTr(" selected")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Item { Layout.fillWidth: true }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: {
                        newConversationUsers.reset()
                        newChatTitle.clear()
                        conversationPopup.close()
                    }
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Create")
                    highlighted: true
                    enabled: root.selectedRecipients.length > 0
                        && (root.selectedRecipients.length === 1
                            || messagesController.canCreateGroup)
                        && (root.selectedRecipients.length === 1
                            || newChatTitle.text.trim().length > 0)
                        && !messagesController.busy
                    onClicked: {
                        if (messagesController.create_conversation(
                                root.selectedRecipients,
                                newChatTitle.text)) {
                            root.selectedRecipients = []
                            newConversationUsers.reset()
                            newChatTitle.clear()
                            conversationPopup.close()
                        }
                    }
                }
            }
        }
    }

    Controls.Popup {
        id: membersPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(330, root.width - 24)
        height: Math.min(390, root.height - 30)
        padding: 14
        contentItem: ColumnLayout {
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: qsTr("CHAT MEMBERS")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            ListView {
                id: membersList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: messagesController.conversationMembers
                ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
                delegate: Controls.PopupAction {
                    id: memberAction
                    required property var modelData
                    width: ListView.view.width
                    height: 58
                    hoverEnabled: true
                    leftPadding: 10
                    rightPadding: 10
                    Accessible.name:
                        modelData.displayName || modelData.login
                    background: Controls.ItemSurface {
                        theme: root.theme
                        hovered: memberAction.hovered
                        pressed: memberAction.down
                        cornerRadius: 12
                        railVisible: false
                        separatorVisible: false
                    }
                    contentItem: RowLayout {
                        spacing: 10
                        Controls.ItemPreview {
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                            theme: root.theme
                            source: modelData.avatarUrl || ""
                            fallbackIcon: "person"
                            fallbackText: modelData.initials || "?"
                            previewSize: 34
                            round: true
                            outlined: true
                            accent: modelData.avatarColor
                                || root.theme.action
                        }
                        ColumnLayout {
                            id: memberContent
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: modelData.displayName || modelData.login
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: modelData.current
                                    ? qsTr("You") : modelData.login
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                    }
                    onClicked:
                        userController.open_profile(modelData.login)
                }
            }
        }
    }

    Controls.Popup {
        id: filesPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(380, root.width - 24)
        height: Math.min(430, root.height - 30)
        padding: 14
        contentItem: ColumnLayout {
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: qsTr("CHAT FILES")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    font.weight: Font.DemiBold
                }
                Label {
                    text: messagesController.conversationAttachments.length
                        + qsTr(" loaded")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                }
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
                    if (atYEnd && messagesController.hasMore
                            && !messagesController.busy
                            && chatFilesScrollBar.takePaginationPermit(false)) {
                        messagesController.load_more()
                    }
                }
                delegate: Controls.PopupAction {
                    id: fileAction
                    required property var modelData
                    width: ListView.view.width
                    height: 60
                    hoverEnabled: true
                    leftPadding: 12
                    rightPadding: 12
                    Accessible.name: modelData.title || qsTr("File")
                    background: Controls.ItemSurface {
                        theme: root.theme
                        hovered: fileAction.hovered
                        pressed: fileAction.down
                        cornerRadius: 12
                        inset: 1
                    }
                    contentItem: RowLayout {
                        spacing: 10
                        Controls.MaterialIcon {
                            name: modelData.previewUrl ? "image" : "description"
                            size: 18
                            color: root.theme.action
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: modelData.title || qsTr("File")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideMiddle
                            }
                            Label {
                                Layout.fillWidth: true
                                text: (modelData.sender || qsTr("Unknown"))
                                    + (modelData.timestamp
                                        ? "  ·  " + modelData.timestamp : "")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                    }
                    onClicked: {
                        root.jumpToMessage(modelData.messageId)
                        filesPopup.close()
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
        width: Math.min(360, root.width - 24)
        padding: 14
        onOpened: {
            messageSearchField.text = messagesController.messageSearch
            messageSearchField.forceActiveFocus()
        }
        contentItem: ColumnLayout {
            spacing: 10
            Label {
                Layout.fillWidth: true
                text: qsTr("SEARCH THIS CONVERSATION")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 7
                Controls.TextField {
                    id: messageSearchField
                    Layout.fillWidth: true
                    theme: root.theme
                    placeholderText: qsTr("Type a message or phrase")
                    onAccepted: {
                        messagesController.search_messages(text)
                        messageSearchPopup.close()
                    }
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "close"
                    toolTip: qsTr("Clear search")
                    enabled: messagesController.messageSearch.length > 0
                    onClicked: {
                        messageSearchField.clear()
                        messagesController.search_messages("")
                        messageSearchPopup.close()
                    }
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "search"
                    toolTip: qsTr("Search")
                    onClicked: messageSearchField.accepted()
                }
            }
        }
    }

    Controls.Popup {
        id: addMembersPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(460, Math.max(320, root.width - 32))
        height: Math.min(560, Math.max(390, root.height - 32))
        padding: 14
        onOpened: {
            root.editedMembers = Array.from(
                messagesController.selectedConversation.recipients || []
            )
            addMemberUsers.setSelection(root.editedMembers)
        }

        contentItem: ColumnLayout {
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Controls.MaterialIcon {
                    name: "manage-accounts"
                    size: 22
                    color: root.theme.action
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Add or remove members")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Select everyone who should remain in this chat")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                }
            }
            UserPicker {
                id: addMemberUsers
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                selectedLogins: root.editedMembers
                onSelectionChanged: logins => root.editedMembers = logins
            }
            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: root.editedMembers.length
                        + qsTr(" members selected")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Item { Layout.fillWidth: true }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: addMembersPopup.close()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Save members")
                    highlighted: true
                    enabled: root.editedMembers.length > 0
                        && !messagesController.busy
                    onClicked: {
                        if (messagesController.set_members(root.editedMembers))
                            addMembersPopup.close()
                    }
                }
            }
        }
    }

    Controls.Popup {
        id: renameChatPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(390, root.width - 32)

        contentItem: ColumnLayout {
            spacing: 10
            Label {
                text: qsTr("RENAME CHAT")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            Controls.TextField {
                id: chatTitleField
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Chat title")
                onAccepted: renameChatButton.clicked()
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: renameChatPopup.close()
                }
                Controls.Button {
                    id: renameChatButton
                    theme: root.theme
                    text: qsTr("Rename")
                    highlighted: true
                    enabled: chatTitleField.text.trim().length > 0
                        && !messagesController.busy
                    onClicked: {
                        if (messagesController.rename_conversation(
                                chatTitleField.text))
                            renameChatPopup.close()
                    }
                }
            }
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

        contentItem: ColumnLayout {
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: qsTr("The chat will be archived for every participant. Message history and attachments remain available for audit.")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: deleteChatDialog.close()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Delete chat")
                    destructive: true
                    enabled: !messagesController.busy
                    onClicked: {
                        if (messagesController.delete_conversation())
                            deleteChatDialog.close()
                    }
                }
            }
        }
    }

    Controls.Dialog {
        id: clearNotesDialog
        theme: root.theme
        parent: Overlay.overlay
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(420, root.width - 40)
        title: qsTr("Clear notes?")
        standardButtons: Dialog.NoButton

        contentItem: ColumnLayout {
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: qsTr("All messages in your personal notes will be cleared. The Notes chat itself will remain.")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: clearNotesDialog.close()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Clear messages")
                    destructive: true
                    enabled: !messagesController.busy
                    onClicked: {
                        if (messagesController.clear_personal_chat())
                            clearNotesDialog.close()
                    }
                }
            }
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
        onOpened: {
            editMessageField.text = root.pendingEditBody
            editMessageField.forceActiveFocus()
        }
        onClosed: {
            root.pendingEditMessageId = ""
            root.pendingEditBody = ""
        }

        contentItem: ColumnLayout {
            spacing: 12
            Controls.TextArea {
                id: editMessageField
                Layout.fillWidth: true
                Layout.preferredHeight: 130
                theme: root.theme
                placeholderText: qsTr("Message")
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: editMessageDialog.close()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Save")
                    highlighted: true
                    enabled: editMessageField.text.trim().length > 0
                        && !messagesController.busy
                    onClicked: {
                        if (messagesController.edit_message(
                                root.pendingEditMessageId,
                                editMessageField.text))
                            editMessageDialog.close()
                    }
                }
            }
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
            root.forwardTargets = ({})
            if (!messagesController.busy)
                messagesController.clear_forward_selection()
        }

        contentItem: ColumnLayout {
            spacing: 12

            Label {
                Layout.fillWidth: true
                text: qsTr("Choose one or more destination chats")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.Wrap
            }

            ListView {
                id: forwardConversations
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: messageConversationModel
                ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

                delegate: Item {
                    required property string conversationId
                    required property string title
                    required property int participantCount
                    required property bool isPersonalNotes
                    width: ListView.view.width
                    height: 54

                    Controls.ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        hovered: targetMouse.containsMouse
                        pressed: targetMouse.pressed
                        selected: !!root.forwardTargets[conversationId]
                        cornerRadius: 12
                        inset: 1
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 12
                        spacing: 9

                        Controls.CheckBox {
                            id: targetCheck
                            theme: root.theme
                            checked: !!root.forwardTargets[conversationId]
                            onClicked: root.setForwardTarget(
                                conversationId, checked)
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: isPersonalNotes
                                    ? qsTr("Your personal notes")
                                    : participantCount + (participantCount === 1
                                        ? qsTr(" member") : qsTr(" members"))
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                            }
                        }
                    }

                    MouseArea {
                        id: targetMouse
                        anchors.fill: parent
                        anchors.leftMargin: 38
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.setForwardTarget(
                            conversationId,
                            !root.forwardTargets[conversationId])
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: messagesController.forwardSelectionCount
                        + (messagesController.forwardSelectionCount === 1
                            ? qsTr(" message selected")
                            : qsTr(" messages selected"))
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: forwardDialog.close()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Forward")
                    highlighted: true
                    enabled: root.forwardTargetIds().length > 0
                        && messagesController.forwardSelectionCount > 0
                        && !messagesController.busy
                    onClicked: {
                        if (messagesController.forward_messages(
                                root.forwardTargetIds()))
                            forwardDialog.close()
                    }
                }
            }
        }
    }

    Controls.Popup {
        id: editHistoryPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(420, Math.max(280, root.width - 32))
        height: Math.min(360, Math.max(180, root.height - 40))
        padding: 14

        contentItem: ColumnLayout {
            spacing: 10
            Label {
                Layout.fillWidth: true
                text: qsTr("EDIT HISTORY")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: root.selectedEditHistory
                ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width
                    height: revisionContent.implicitHeight + 16
                    radius: 10
                    color: root.theme.surfaceContainer
                    ColumnLayout {
                        id: revisionContent
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 4
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Edited by ")
                                + String(modelData.editedBy || qsTr("unknown"))
                                + "  ·  " + String(modelData.editedAt || "")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }
                        Label {
                            Layout.fillWidth: true
                            text: String(modelData.body || "")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            wrapMode: Text.Wrap
                            textFormat: Text.PlainText
                        }
                    }
                }
            }
        }
    }

    Controls.Popup {
        id: pinHistoryPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(420, Math.max(280, root.width - 32))
        height: Math.min(360, Math.max(180, root.height - 40))
        padding: 14
        contentItem: ColumnLayout {
            spacing: 10
            Label {
                Layout.fillWidth: true
                text: qsTr("PIN HISTORY")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: messagesController.pinHistory
                ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
                delegate: Controls.PopupAction {
                    id: pinHistoryEntry
                    required property var modelData
                    width: ListView.view.width
                    height: pinRevision.implicitHeight + 16
                    hoverEnabled: true
                    enabled: String(modelData.messageId || "").length > 0
                    padding: 8
                    Accessible.name: String(
                        modelData.summary || qsTr("Pinned message")
                    )
                    background: Controls.ItemSurface {
                        theme: root.theme
                        hovered: pinHistoryEntry.hovered
                        pressed: pinHistoryEntry.down
                        cornerRadius: 10
                        inset: 1
                    }
                    contentItem: ColumnLayout {
                        id: pinRevision
                        spacing: 4
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Pinned by ")
                                + String(modelData.pinnedBy || qsTr("unknown"))
                                + "  ·  " + String(modelData.pinnedAt || "")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }
                        Label {
                            Layout.fillWidth: true
                            text: String(modelData.summary
                                || qsTr("Pinned message"))
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            wrapMode: Text.Wrap
                        }
                    }
                    onClicked: {
                        const messageId = String(modelData.messageId || "")
                        if (messagesController.show_message(messageId))
                            pinHistoryPopup.close()
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
        contentItem: ListView {
            id: mentionList
            clip: true
            spacing: 0
            model: messagesController.conversationMembers
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
            delegate: Controls.PopupAction {
                id: mentionAction
                required property var modelData
                readonly property bool matches: root.mentionMatches(modelData)
                width: ListView.view.width
                height: matches ? 46 : 0
                visible: matches
                hoverEnabled: true
                leftPadding: 8
                rightPadding: 8
                Accessible.name: String(
                    modelData.displayName || modelData.login || ""
                )
                background: Controls.ItemSurface {
                    theme: root.theme
                    hovered: mentionAction.hovered
                    pressed: mentionAction.down
                    cornerRadius: 10
                    railVisible: false
                    separatorVisible: false
                }
                contentItem: RowLayout {
                    spacing: 8
                    Controls.ItemPreview {
                        Layout.preferredWidth: 30
                        Layout.preferredHeight: 30
                        theme: root.theme
                        source: String(modelData.avatarUrl || "")
                        fallbackIcon: "person"
                        fallbackText: String(modelData.initials || "")
                        previewSize: 30
                        round: true
                        accent: modelData.avatarColor || root.theme.action
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            Layout.fillWidth: true
                            text: String(modelData.displayName || modelData.login || "")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("@") + String(modelData.login || "")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }
                    }
                }
                onClicked: {
                    composer.insertMention(String(modelData.login || ""))
                    mentionPopup.close()
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

        contentItem: ColumnLayout {
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: qsTr("The message will be removed from the conversation for every participant.")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: deleteMessageDialog.close()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Delete message")
                    destructive: true
                    enabled: root.pendingDeleteMessageId.length > 0
                        && !messagesController.busy
                    onClicked: {
                        if (messagesController.delete_message(
                                root.pendingDeleteMessageId))
                            deleteMessageDialog.close()
                    }
                }
            }
        }
    }

    MessageReactionPicker {
        id: reactionPicker
        theme: root.theme
        catalog: emojiCatalog
        onReactionSelected: (messageId, emoji) => {
            if (messagesController.toggle_reaction(messageId, emoji))
                reactionPicker.close()
        }
    }

    function selectedConversationPresenceText() {
        const conversation = messagesController.selectedConversation || ({})
        if (!String(conversation.peerLogin || "").length)
            return ""
        if (!conversation.presenceKnown)
            return qsTr("Status unavailable")
        if (conversation.online)
            return qsTr("Online")
        const lastSeen = String(conversation.lastSeenPretty || "")
        return lastSeen.length
            ? qsTr("Last seen %1").arg(lastSeen) : qsTr("Offline")
    }

    ActionMenu {
        id: chatActions
        theme: root.theme
        parent: Overlay.overlay
        preferredWidth: 230
        actions: [
            {
                "title": "Rename chat", "icon": "edit", "command": "rename",
                "enabled": !!messagesController.selectedConversation.canRename
            },
            {
                "title": "Change preview", "icon": "image", "command": "preview",
                "enabled": !!messagesController.selectedConversation.canManage
            },
            {
                "title": "Add or remove members", "icon": "manage-accounts", "command": "members",
                "enabled": !!messagesController.selectedConversation.canAddMembers
            },
            {"separator": true},
            {
                "title": messagesController.selectedConversation.canClearPersonal
                    ? "Clear notes" : "Delete chat",
                "icon": messagesController.selectedConversation.canClearPersonal
                    ? "delete-sweep" : "delete",
                "command": messagesController.selectedConversation.canClearPersonal
                    ? "clear" : "delete",
                "enabled": !!messagesController.selectedConversation.canClearPersonal
                    || !!messagesController.selectedConversation.canDelete
            }
        ]
        onTriggered: command => {
            if (command === "rename") {
                chatTitleField.text =
                    messagesController.selectedConversation.title || ""
                renameChatPopup.openCenteredIn(Overlay.overlay)
                chatTitleField.forceActiveFocus()
            } else if (command === "preview") {
                chatPreviewDialog.open()
            } else if (command === "members") {
                addMembersPopup.openCenteredIn(Overlay.overlay)
            } else if (command === "clear") {
                clearNotesDialog.open()
            } else if (command === "delete") {
                deleteChatDialog.open()
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
                "title": "Reply", "icon": "reply", "command": "reply",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "title": "Forward", "icon": "share", "command": "forward",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "title": "Add reaction", "icon": "emoji", "command": "reaction",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "title": "Select messages", "icon": "check-circle",
                "command": "select_forward",
                "enabled": root.actionMessageId.length > 0
            },
            {"separator": true},
            {
                "title": messagesController.forwardSelectionCount > 1
                    ? "Copy selected sKeys" : "Copy sKey",
                "icon": "content-copy", "command": "copy_skey",
                "enabled": root.actionMessageId.length > 0
            },
            {"separator": true},
            {
                "title": root.actionMessagePinned ? "Unpin message" : "Pin message",
                "icon": "push-pin",
                "command": "pin",
                "enabled": root.actionMessageId.length > 0
            },
            {
                "title": "Edit message", "icon": "edit", "command": "edit",
                "enabled": root.actionMessageCanEdit
            },
            {
                "title": "Edit history", "icon": "history", "command": "history",
                "enabled": root.actionMessageEditHistory.length > 0
            },
            {"separator": true},
            {
                "title": "Delete message", "icon": "delete", "command": "delete",
                "enabled": messagesController.canDeleteMessages
            }
        ]
        onTriggered: command => {
            if (command === "reply") {
                messagesController.begin_reply(root.actionMessageId)
            } else if (command === "forward") {
                messagesController.begin_forward(root.actionMessageId)
            } else if (command === "reaction") {
                root.openReactionPicker(
                    root.actionMessageId, root.actionMessageAnchor)
            } else if (command === "select_forward") {
                messagesController.toggle_forward_selection(root.actionMessageId)
            } else if (command === "copy_skey") {
                messagesController.copy_message_skey(root.actionMessageId)
            } else if (command === "pin") {
                if (root.actionMessagePinned)
                    messagesController.unpin_message(root.actionMessageId)
                else
                    messagesController.pin_message(root.actionMessageId)
            } else if (command === "edit") {
                root.pendingEditMessageId = root.actionMessageId
                root.pendingEditBody = root.actionMessageBody
                editMessageDialog.open()
            } else if (command === "history") {
                root.selectedEditHistory = root.actionMessageEditHistory
                editHistoryPopup.openCenteredIn(Overlay.overlay)
            } else if (command === "delete") {
                root.pendingDeleteMessageId = root.actionMessageId
                deleteMessageDialog.open()
            }
        }
    }

    ActionMenu {
        id: attachmentMenu
        theme: root.theme
        parent: Overlay.overlay
        actions: [
            {"title": "Download", "icon": "download", "command": "download", "enabled": !root.attachmentMenuLocal},
            {"title": "Show folder", "icon": "folder_open", "command": "folder", "enabled": root.attachmentMenuLocal},
            {"title": root.attachmentMenuLocal ? "Open file" : "Download and open", "icon": "open_in_new", "command": "open"},
            {"separator": true},
            {"title": "Copy file path", "icon": "content_copy", "command": "copy_path"},
            {"title": "Copy web link", "icon": "link", "command": "copy_web"},
            {"title": "Copy image", "icon": "image", "command": "copy_image", "enabled": root.attachmentMenuLocal && root.attachmentMenuImage}
        ]
        onTriggered: command => messagesController.attachment_action(
            root.attachmentMenuToken, command)
    }

    ActionMenu {
        id: skeyPreviewMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {
                "title": root.skeyMenuFailed ? "Retry preview"
                    : root.skeyMenuCanOpen ? "Open linked item"
                    : "Source conversation is unavailable",
                "icon": root.skeyMenuFailed ? "refresh" : "open_in_new",
                "command": root.skeyMenuFailed ? "retry" : "open",
                "enabled": root.skeyMenuFailed || root.skeyMenuCanOpen
            },
            {"title": "Copy sKey", "icon": "content_copy", "command": "copy"}
        ]
        onTriggered: command => {
            if (command === "retry")
                messagesController.retry_skey_preview(root.skeyMenuValue)
            else if (command === "copy")
                messagesController.copy_skey_preview(root.skeyMenuValue)
            else
                messagesController.open_skey_preview(root.skeyMenuValue)
        }
    }

    SplitView {
        id: messagesWorkspaceSplit
        objectName: "messagesWorkspaceSplit"
        anchors.fill: parent
        anchors.margins: 12
        orientation: Qt.Horizontal
        handle: Rectangle {
            implicitWidth: 8
            color: "transparent"
        }

        MessagesConversationList {
            objectName: "messagesConversationPane"
            theme: root.theme
            conversationModel: messageConversationModel
            onNewConversationRequested: {
                root.selectedRecipients = []
                newConversationUsers.reset()
                newChatTitle.clear()
                conversationPopup.openCenteredIn(Overlay.overlay)
            }
            onConversationSelected: index =>
                messagesController.select_conversation(index)
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

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    radius: 9
                    color: root.theme.surfaceContainerHigh
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 10
                        spacing: 8
                        Controls.ItemPreview {
                            visible: messagesController.conversationId.length > 0
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                            theme: root.theme
                            source:
                                messagesController.selectedConversation.isPersonalNotes
                                ? ""
                                : messagesController.selectedConversation.avatarUrl || ""
                            fallbackIcon:
                                messagesController.selectedConversation.isPersonalNotes
                                ? "bookmark" : "group"
                            fallbackText:
                                messagesController.selectedConversation.isPersonalNotes
                                ? ""
                                : messagesController.selectedConversation.acronym || "?"
                            previewSize: 34
                            round: true
                            outlined: true
                            accent: root.chatColor(
                                messagesController.selectedConversation.colorIndex
                            )
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: messagesController.conversationId.length
                                    ? messagesController.selectedConversation.title
                                    : qsTr("Select a conversation")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            RowLayout {
                                visible: messagesController.conversationId.length > 0
                                Layout.fillWidth: true
                                spacing: 5

                                Rectangle {
                                    visible: String(
                                        messagesController.selectedConversation.peerLogin
                                            || ""
                                    ).length > 0
                                    Layout.preferredWidth: 7
                                    Layout.preferredHeight: 7
                                    radius: 4
                                    color:
                                        messagesController.selectedConversation.online
                                        ? root.theme.green
                                        : root.theme.disabledText
                                }
                                Label {
                                    visible: String(
                                        messagesController.selectedConversation.peerLogin
                                            || ""
                                    ).length > 0
                                    text: root.selectedConversationPresenceText()
                                    color:
                                        messagesController.selectedConversation.online
                                        ? root.theme.green
                                        : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                                Label {
                                    visible: String(
                                        messagesController.selectedConversation.peerLogin
                                            || ""
                                    ).length > 0
                                    text: "·"
                                    color: root.theme.disabledText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: messagesController.selectedConversation.isPersonalNotes
                                    ? qsTr("Your personal notes  ·  ") + Number(
                                        messagesController.selectedConversation.messageCount || 0
                                    ) + qsTr(" notes")
                                    : String(
                                        messagesController.selectedConversation.peerLogin
                                            || ""
                                    ).length > 0
                                    ? Number(
                                        messagesController.selectedConversation.messageCount || 0
                                    ) + qsTr(" messages")
                                    : Number(
                                        messagesController.selectedConversation.participantCount || 0
                                    ) + qsTr(" members  ·  ") + Number(
                                        messagesController.selectedConversation.messageCount || 0
                                    ) + qsTr(" messages")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                        }
                        Controls.CompactIconButton {
                            id: membersButton
                            visible: messagesController.conversationId.length > 0
                                && !messagesController.selectedConversation.isPersonalNotes
                            theme: root.theme
                            iconName: "group"
                            badgeCount: Number(
                                messagesController.selectedConversation.participantCount
                                || 0
                            )
                            toolTip: qsTr("Chat members")
                            onClicked: root.openBelow(membersButton, membersPopup)
                        }
                        Controls.CompactIconButton {
                            id: filesButton
                            visible: messagesController.conversationId.length > 0
                            theme: root.theme
                            iconName: "attach-file"
                            badgeCount: Number(
                                messagesController.selectedConversation.attachmentCount
                                || 0
                            )
                            enabled: !messagesController.busy
                            toolTip: qsTr("Chat files")
                            onClicked: {
                                if (messagesController.messageSearch.length > 0)
                                    messagesController.search_messages("")
                                root.openBelow(filesButton, filesPopup)
                            }
                        }
                        Controls.CompactIconButton {
                            id: searchMessagesButton
                            visible: messagesController.conversationId.length > 0
                            theme: root.theme
                            iconName: "search"
                            iconColor: messagesController.messageSearch.length > 0
                                ? root.theme.action : root.theme.primaryText
                            enabled: !messagesController.busy
                            toolTip: messagesController.messageSearch.length > 0
                                ? qsTr("Change message search")
                                : qsTr("Search messages")
                            onClicked: root.openBelow(
                                searchMessagesButton, messageSearchPopup
                            )
                        }
                        RefreshIconButton {
                            theme: root.theme
                            enabled: !messagesController.busy
                            toolTip: qsTr("Refresh conversations and messages")
                            onClicked: messagesController.refresh_current()
                        }
                        Controls.CompactIconButton {
                            id: chatActionsButton
                            visible: messagesController.conversationId.length > 0
                            theme: root.theme
                            iconName: "more-vert"
                            toolTip: qsTr("Chat actions")
                            onClicked: chatActions.toggleBelow(chatActionsButton)
                        }
                        Item {
                            Layout.preferredWidth: 20
                            Layout.preferredHeight: 20
                            Controls.BusyIndicator {
                                uiTheme: root.theme
                                anchors.fill: parent
                                visible: messagesController.busy
                                running: visible
                            }
                        }
                    }
                }

                Rectangle {
                    id: pinnedMessageBar
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    visible: String(messagesController.pinnedMessage.messageId || "").length > 0
                    radius: 12
                    color: pinnedMessageHover.hovered
                        ? root.theme.surfaceContainerHighest
                        : root.theme.surfaceContainerHigh
                    border.width: 1
                    border.color: root.theme.outlineVariant
                    Behavior on color {
                        ColorAnimation {
                            duration: root.theme.hoverMotionFast
                            easing.type: Easing.OutCubic
                        }
                    }
                    HoverHandler {
                        id: pinnedMessageHover
                        cursorShape: Qt.PointingHandCursor
                    }
                    Controls.ActivationHandler {
                        onActivated: messagesController.show_message(
                            String(messagesController.pinnedMessage.messageId || ""))
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        spacing: 9
                        Rectangle {
                            Layout.preferredWidth: 28
                            Layout.preferredHeight: 28
                            Layout.alignment: Qt.AlignVCenter
                            radius: 9
                            color: root.theme.tertiaryContainer
                            Controls.MaterialIcon {
                                anchors.centerIn: parent
                                name: "push-pin"
                                size: 16
                                color: root.theme.tertiary
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: String(
                                    messagesController.pinnedMessage.summary
                                        || qsTr("Pinned message"))
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: {
                                    const sender = String(
                                        messagesController.pinnedMessage.senderDisplay || "")
                                    const pinnedBy = String(
                                        messagesController.pinnedMessage.pinnedBy || "")
                                    return (sender.length ? sender + "  ·  " : "")
                                        + qsTr("Pinned by ") + pinnedBy
                                }
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                        RowLayout {
                            spacing: 3
                            visible: Number(
                                messagesController.pinnedMessage.linkedCount || 0
                            ) > 0
                            Controls.MaterialIcon {
                                name: Number(
                                    messagesController.pinnedMessage.linkedMessageCount || 0
                                ) === Number(
                                    messagesController.pinnedMessage.linkedCount || 0
                                ) ? "chat" : "link"
                                size: 15
                                color: root.theme.tertiary
                            }
                            Label {
                                text: String(
                                    messagesController.pinnedMessage.linkedCount || "")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                            }
                        }
                        RowLayout {
                            spacing: 3
                            visible: Number(
                                messagesController.pinnedMessage.attachmentCount || 0
                            ) > 0
                            Controls.MaterialIcon {
                                name: "attach-file"
                                size: 15
                                color: root.theme.tertiary
                            }
                            Label {
                                text: String(
                                    messagesController.pinnedMessage.attachmentCount || "")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                            }
                        }
                        Controls.MaterialIcon {
                            visible: messagesController.pinnedMessage.hasReply === true
                            name: "reply"
                            size: 15
                            color: root.theme.secondaryText
                        }
                        Controls.MaterialIcon {
                            visible: messagesController.pinnedMessage.forwarded === true
                            name: "share"
                            size: 15
                            color: root.theme.secondaryText
                        }
                        Controls.CompactIconButton {
                            id: pinHistoryButton
                            theme: root.theme
                            iconName: "history"
                            toolTip: qsTr("Pin history")
                            onClicked: root.openBelow(pinHistoryButton, pinHistoryPopup)
                        }
                    }
                }

                Label {
                    visible: false
                    Layout.fillWidth: true
                    text: qsTr("Created by ") + String(
                        messagesController.selectedConversation.createdBy || "unknown"
                    ) + "  ·  Created " + String(
                        messagesController.selectedConversation.createdPretty || "unknown"
                    ) + "  ·  Active " + String(
                        messagesController.selectedConversation.activePretty || "never"
                    )
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    opacity: 0.76
                    elide: Text.ElideRight
                }

                Rectangle {
                    visible: messagesController.error.length > 0
                        || messageAttachments.error.length > 0
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
                            text: messagesController.error
                                || messageAttachments.error
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
                                messagesController.dismiss_error()
                                messageAttachments.dismiss_error()
                            }
                        }
                    }
                    Controls.ToolTip {
                        theme: root.theme
                        visible: messageErrorMouse.containsMouse
                            && messageErrorLabel.truncated
                            && !root.theme.suppressToolTips
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
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.leftMargin: 12
                    Layout.rightMargin: 12
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
                                root.messages = conversationTimeline
                        }
                        Component.onCompleted: {
                            if (current)
                                root.messages = conversationTimeline
                        }
                    }
                }

                Rectangle {
                    anchors.fill: parent
                    z: 240
                    visible: !root.messagePresentationReady
                        && (root.pendingPresentationConversationId.length > 0
                            || messagesController.conversationId.length > 0)
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
                            text: messagesController.forwardSelectionCount
                                + (messagesController.forwardSelectionCount === 1
                                    ? qsTr(" message selected")
                                    : qsTr(" messages selected"))
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "content-copy"
                            toolTip: messagesController.forwardSelectionCount === 1
                                ? qsTr("Copy selected sKey")
                                : qsTr("Copy selected sKeys")
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
                    visible: String(
                        messagesController.replyTarget.messageId || ""
                    ).length > 0
                    Layout.fillWidth: true
                    theme: root.theme
                    sender: String(
                        messagesController.replyTarget.senderDisplay || ""
                    )
                    body: String(messagesController.replyTarget.body || "")
                    dismissible: true
                    onActivated: messagesController.show_message(
                        String(messagesController.replyTarget.messageId || ""))
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
                    MessageComposerField {
                        id: composer
                        Layout.fillWidth: true
                        Layout.preferredHeight: implicitHeight
                        Layout.alignment: Qt.AlignVCenter
                        theme: root.theme
                        emojiCatalogModel: emojiCatalog
                        attachmentController: messageAttachments
                        placeholderText: qsTr(
                            "Write a reply · Enter to send · Ctrl+Enter for a new line"
                        )
                        text: root.draft
                        readOnly: messagesController.sending
                            || messageAttachments.busy
                        onTextChanged: {
                            root.draft = text
                            messagesController.set_draft_text(text)
                        }
                        onMentionRequested: query => {
                            root.mentionQuery = query
                            if (query.length >= 0 && text.slice(
                                    0, cursorPosition).match(
                                        /(^|\s)@[A-Za-z0-9_.-]*$/)) {
                                if (!mentionPopup.opened)
                                    root.openBelow(composer, mentionPopup)
                            } else {
                                mentionPopup.close()
                            }
                        }
                        onSubmitRequested: sendButton.clicked()
                    }
                    MessageSendButton {
                        id: sendButton
                        theme: root.theme
                        Layout.alignment: Qt.AlignVCenter
                        sending: messagesController.sending
                        hasContent: !messagesController.busy
                            && (root.draft.trim().length > 0
                                || messageAttachments.count > 0)
                        onClicked: messagesController.send(root.draft)
                    }
                }
            }

            Controls.AttachmentDropArea {
                id: chatDropArea
                anchors.fill: parent
                z: 20
                theme: root.theme
                attachmentController: messageAttachments
                enabled: messagesController.conversationId.length > 0
                    && !messageAttachments.busy
            }
        }
    }

    Connections {
        target: messagesController
        function onMessageSentForConversation(conversationId) {
            root.draft = String(messagesController.draftText || "")
        }

        function onDraftChanged() {
            const value = String(messagesController.draftText || "")
            if (root.draft !== value)
                root.draft = value
        }

        function onMessageAppendedForConversation(conversationId) {
            if (String(conversationId || "")
                    !== String(messagesController.conversationId || ""))
                return
            messages.scrollToLatest()
        }
    }
}
