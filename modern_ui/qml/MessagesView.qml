import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Item {
    id: root
    required property var theme
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
    property string reactionMessageId: ""
    property string mentionQuery: ""
    property string attachmentMenuToken: ""
    property bool attachmentMenuLocal: false
    property bool attachmentMenuImage: false
    property string skeyMenuValue: ""
    property bool skeyMenuFailed: false
    property bool skeyMenuCanOpen: true
    property var forwardTargets: ({})
    property var conversationDrafts: ({})
    property string draftConversationId: ""
    property bool messagePresentationReady: true
    property string pendingPresentationConversationId: ""
    readonly property var hostWindow: root.Window.window

    function activateConversationDraft(conversationId) {
        const nextId = String(conversationId || "")
        const values = Object.assign({}, root.conversationDrafts)
        if (root.draftConversationId.length)
            values[root.draftConversationId] = root.draft
        root.conversationDrafts = values
        root.draftConversationId = nextId
        root.draft = String(values[nextId] || "")
    }

    function beginConversationPresentation(conversationId) {
        messageSettleTimer.stop()
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
        messageSettleTimer.passes = 0
        messageSettleTimer.stablePasses = 0
        messageSettleTimer.lastContentHeight = -1
        messageSettleTimer.restart()
    }

    function openBelow(source, popup) {
        const top = source.mapToItem(Overlay.overlay, 0, 0)
        const point = source.mapToItem(Overlay.overlay, 0, source.height + 6)
        popup.x = Math.max(6, Math.min(
            Overlay.overlay.width - popup.width - 6, point.x
        ))
        popup.y = point.y + popup.height <= Overlay.overlay.height - 6
            ? point.y : Math.max(6, top.y - popup.height - 6)
        popup.open()
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
        root.reactionMessageId = messageId
        reactionPicker.openFor(anchorItem)
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

    Timer {
        id: messageSettleTimer
        property int passes: 0
        property int stablePasses: 0
        property real lastContentHeight: -1
        interval: 16
        repeat: true
        onTriggered: {
            const conversationId = String(
                messagesController.conversationId || "")
            if (conversationId
                    !== root.pendingPresentationConversationId) {
                stop()
                return
            }
            if (messages.height <= 0)
                return
            messages.forceLayout()
            if (messages.count > 0) {
                messages.positionViewAtIndex(
                    messages.count - 1, ListView.End)
                messages.positionViewAtEnd()
            }
            const currentHeight = messages.contentHeight
            stablePasses = Math.abs(
                currentHeight - lastContentHeight) < 0.5
                ? stablePasses + 1 : 0
            lastContentHeight = currentHeight
            passes += 1
            if (stablePasses < 3 && passes < 20)
                return
            messages.settleAtLatest()
            root.messagePresentationReady = true
            root.pendingPresentationConversationId = ""
            stop()
        }
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
        root.draftConversationId = String(
            messagesController.conversationId || "")
        Qt.callLater(root.syncReadState)
        messagesController.refresh()
        Qt.callLater(function() {
            if (messagesController.conversationId.length > 0
                    && messages.count > 0) {
                root.beginConversationPresentation(
                    messagesController.conversationId)
                root.finishConversationPresentation()
            }
        })
    }
    Component.onDestruction: messagesController.set_visible(false)
    onVisibleChanged: root.syncReadState()

    Connections {
        target: root.hostWindow
        enabled: !!root.hostWindow

        function onVisibleChanged() { root.syncReadState() }
        function onActiveChanged() { root.syncReadState() }
    }

    Connections {
        target: messagesController

        function onConversationChanging(conversationId) {
            root.activateConversationDraft(conversationId)
            root.beginConversationPresentation(conversationId)
        }

        function onConversationRestored(conversationId) {
            root.activateConversationDraft(conversationId)
            messageSettleTimer.stop()
            root.pendingPresentationConversationId = ""
            root.messagePresentationReady = true
            messages.cancelScrollAnimation()
            messages.positionCachedAtLatest()
            Qt.callLater(messages.positionCachedAtLatest)
        }

        function onConversationLoaded() {
            Qt.callLater(root.finishConversationPresentation)
        }

        function onMessageFocusRequested(messageId) {
            Qt.callLater(function() { root.jumpToMessage(messageId) })
        }

        function onReplyStarted() {
            Qt.callLater(function() { composer.focusEditor() })
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

    Md3Popup {
        id: conversationPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(460, Math.max(320, root.width - 32))
        height: Math.min(560, Math.max(390, root.height - 32))
        padding: 14
        x: Math.max(16, (parent.width - width) / 2)
        y: Math.max(16, (parent.height - height) / 2)

        contentItem: ColumnLayout {
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                MaterialIcon {
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
                        font.pixelSize: 9
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
            Md3TextField {
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
                font.pixelSize: 9
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: root.selectedRecipients.length + qsTr(" selected")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 9
                }
                Item { Layout.fillWidth: true }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: {
                        newConversationUsers.reset()
                        newChatTitle.clear()
                        conversationPopup.close()
                    }
                }
                Md3Button {
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

    Md3Popup {
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
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
            ListView {
                id: membersList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: messagesController.conversationMembers
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
                delegate: Item {
                    required property var modelData
                    width: ListView.view.width
                    height: 58
                    ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        hovered: memberMouse.containsMouse
                        pressed: memberMouse.pressed
                        cornerRadius: 12
                        railVisible: false
                        separatorVisible: false
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 10
                        ItemPreview {
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                            theme: root.theme
                            source: modelData.avatarUrl || ""
                            fallbackIcon: "person"
                            fallbackText: modelData.initials || "?"
                            previewSize: 34
                            round: true
                            outlined: true
                            accent: root.theme.action
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
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: modelData.current
                                    ? qsTr("You") : modelData.login
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 8
                                elide: Text.ElideRight
                            }
                        }
                    }
                    MouseArea {
                        id: memberMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: userController.open_profile(modelData.login)
                    }
                }
            }
        }
    }

    Md3Popup {
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
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                }
                Label {
                    text: messagesController.conversationAttachments.length
                        + qsTr(" loaded")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 8
                }
            }
            ListView {
                id: chatFilesList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: messagesController.conversationAttachments
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
                onAtYEndChanged: {
                    if (atYEnd && messagesController.hasMore
                            && !messagesController.busy)
                        messagesController.load_more()
                }
                delegate: Item {
                    required property var modelData
                    width: ListView.view.width
                    height: 60
                    ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        hovered: fileMouse.containsMouse
                        pressed: fileMouse.pressed
                        cornerRadius: 12
                        inset: 1
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10
                        MaterialIcon {
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
                                font.pixelSize: 10
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
                                font.pixelSize: 8
                                elide: Text.ElideRight
                            }
                        }
                    }
                    MouseArea {
                        id: fileMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.jumpToMessage(modelData.messageId)
                            filesPopup.close()
                        }
                    }
                }
                Label {
                    anchors.centerIn: parent
                    visible: chatFilesList.count === 0
                    text: qsTr("No files in loaded messages")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 10
                }
            }
            Md3Button {
                Layout.alignment: Qt.AlignHCenter
                visible: messagesController.hasMore
                theme: root.theme
                text: qsTr("Load earlier messages")
                enabled: !messagesController.busy
                onClicked: messagesController.load_more()
            }
        }
    }

    Md3Popup {
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
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 7
                Md3TextField {
                    id: messageSearchField
                    Layout.fillWidth: true
                    theme: root.theme
                    placeholderText: qsTr("Type a message or phrase")
                    onAccepted: {
                        messagesController.search_messages(text)
                        messageSearchPopup.close()
                    }
                }
                CompactIconButton {
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
                CompactIconButton {
                    theme: root.theme
                    iconName: "search"
                    toolTip: qsTr("Search")
                    onClicked: messageSearchField.accepted()
                }
            }
        }
    }

    Md3Popup {
        id: addMembersPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(460, Math.max(320, root.width - 32))
        height: Math.min(560, Math.max(390, root.height - 32))
        padding: 14
        x: Math.max(16, (parent.width - width) / 2)
        y: Math.max(16, (parent.height - height) / 2)
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
                MaterialIcon {
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
                        font.pixelSize: 9
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
                    font.pixelSize: 9
                }
                Item { Layout.fillWidth: true }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: addMembersPopup.close()
                }
                Md3Button {
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

    Md3Popup {
        id: renameChatPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(390, root.width - 32)
        x: Math.max(16, (parent.width - width) / 2)
        y: Math.max(16, (parent.height - height) / 2)

        contentItem: ColumnLayout {
            spacing: 10
            Label {
                text: qsTr("RENAME CHAT")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
            Md3TextField {
                id: chatTitleField
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Chat title")
                onAccepted: renameChatButton.clicked()
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: renameChatPopup.close()
                }
                Md3Button {
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

    Md3Dialog {
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
                font.pixelSize: 10
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: deleteChatDialog.close()
                }
                Md3Button {
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

    Md3Dialog {
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
                font.pixelSize: 10
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: clearNotesDialog.close()
                }
                Md3Button {
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

    Md3Dialog {
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
            Md3TextArea {
                id: editMessageField
                Layout.fillWidth: true
                Layout.preferredHeight: 130
                theme: root.theme
                placeholderText: qsTr("Message")
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: editMessageDialog.close()
                }
                Md3Button {
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

    Md3Dialog {
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
                font.pixelSize: 10
                wrapMode: Text.Wrap
            }

            ListView {
                id: forwardConversations
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: messageConversationModel
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

                delegate: Item {
                    required property string conversationId
                    required property string title
                    required property int participantCount
                    required property bool isPersonalNotes
                    width: ListView.view.width
                    height: 54

                    ItemSurface {
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

                        Md3CheckBox {
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
                                font.pixelSize: 10
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
                                font.pixelSize: 8
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
                    font.pixelSize: 9
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: forwardDialog.close()
                }
                Md3Button {
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

    Md3Popup {
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
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: root.selectedEditHistory
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
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
                            font.pixelSize: 8
                        }
                        Label {
                            Layout.fillWidth: true
                            text: String(modelData.body || "")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 10
                            wrapMode: Text.Wrap
                            textFormat: Text.PlainText
                        }
                    }
                }
            }
        }
    }

    Md3Popup {
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
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: messagesController.pinHistory
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
                delegate: Item {
                    id: pinHistoryEntry
                    required property var modelData
                    width: ListView.view.width
                    height: pinRevision.implicitHeight + 16
                    ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        hovered: pinHistoryMouse.containsMouse
                        pressed: pinHistoryMouse.pressed
                        cornerRadius: 10
                        inset: 1
                    }
                    ColumnLayout {
                        id: pinRevision
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 4
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Pinned by ")
                                + String(modelData.pinnedBy || qsTr("unknown"))
                                + "  ·  " + String(modelData.pinnedAt || "")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 8
                        }
                        Label {
                            Layout.fillWidth: true
                            text: String(modelData.summary
                                || qsTr("Pinned message"))
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 10
                            wrapMode: Text.Wrap
                        }
                    }
                    MouseArea {
                        id: pinHistoryMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: String(modelData.messageId || "").length > 0
                            ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onClicked: {
                            const messageId = String(modelData.messageId || "")
                            if (messageId && messagesController.show_message(messageId))
                                pinHistoryPopup.close()
                        }
                    }
                }
            }
        }
    }

    Md3Popup {
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
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
            delegate: Item {
                required property var modelData
                readonly property bool matches: root.mentionMatches(modelData)
                width: ListView.view.width
                height: matches ? 46 : 0
                visible: matches
                ItemSurface {
                    anchors.fill: parent
                    theme: root.theme
                    hovered: mentionMouse.containsMouse
                    pressed: mentionMouse.pressed
                    cornerRadius: 10
                    railVisible: false
                    separatorVisible: false
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 8
                    ItemPreview {
                        Layout.preferredWidth: 30
                        Layout.preferredHeight: 30
                        theme: root.theme
                        source: String(modelData.avatarUrl || "")
                        fallbackIcon: "person"
                        fallbackText: String(modelData.initials || "")
                        previewSize: 30
                        round: true
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            Layout.fillWidth: true
                            text: String(modelData.displayName || modelData.login || "")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("@") + String(modelData.login || "")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 8
                        }
                    }
                }
                MouseArea {
                    id: mentionMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        composer.insertMention(String(modelData.login || ""))
                        mentionPopup.close()
                    }
                }
            }
        }
    }

    Md3Dialog {
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
                font.pixelSize: 10
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: deleteMessageDialog.close()
                }
                Md3Button {
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

    EmojiPicker {
        id: reactionPicker
        theme: root.theme
        onEmojiSelected: emoji => {
            if (messagesController.toggle_reaction(
                    root.reactionMessageId, emoji))
                reactionPicker.close()
        }
        onClosed: root.reactionMessageId = ""
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
                renameChatPopup.open()
                chatTitleField.forceActiveFocus()
            } else if (command === "preview") {
                chatPreviewDialog.open()
            } else if (command === "members") {
                addMembersPopup.open()
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
                editHistoryPopup.x = Math.max(8,
                    (Overlay.overlay.width - editHistoryPopup.width) / 2)
                editHistoryPopup.y = Math.max(8,
                    (Overlay.overlay.height - editHistoryPopup.height) / 2)
                editHistoryPopup.open()
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
        anchors.fill: parent
        anchors.margins: 12
        orientation: Qt.Horizontal
        handle: Rectangle {
            implicitWidth: 8
            color: "transparent"
        }

        Rectangle {
            SplitView.preferredWidth: 252
            SplitView.minimumWidth: 210
            radius: 12
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("CONVERSATIONS")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "group-add"
                        toolTip: qsTr("New conversation")
                        onClicked: {
                            root.selectedRecipients = []
                            newConversationUsers.reset()
                            newChatTitle.clear()
                            conversationPopup.open()
                        }
                    }
                }
                ListView {
                    id: conversations
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 6
                    model: messageConversationModel
                    ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
                    delegate: Item {
                        id: conversation
                        required property int index
                        required property string title
                        required property string status
                        required property string lastMessage
                        required property string lastMessageSummary
                        required property int lastMessageLinkedCount
                        required property string lastSender
                        required property int unread
                        required property int mentionCount
                        required property bool selected
                        required property string avatarUrl
                        required property string initials
                        required property int participantCount
                        required property string memberSummary
                        required property string acronym
                        required property int colorIndex
                        required property bool isPersonalNotes
                        width: conversations.width
                        height: 68
                        ItemSurface {
                            anchors.fill: parent
                            theme: root.theme
                            selected: conversation.selected
                            hovered: conversationMouse.containsMouse
                            pressed: conversationMouse.pressed
                            accent: root.chatColor(conversation.colorIndex)
                            cornerRadius: 10
                            separatorVisible: false
                            railVisible: conversation.unread > 0
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 9
                            anchors.rightMargin: 9
                            spacing: 8
                            ItemPreview {
                                Layout.preferredWidth: 34
                                Layout.preferredHeight: 34
                                theme: root.theme
                                source: conversation.isPersonalNotes
                                    ? "" : conversation.avatarUrl
                                fallbackIcon: conversation.isPersonalNotes
                                    ? "bookmark" : "group"
                                fallbackText: conversation.isPersonalNotes
                                    ? "" : conversation.acronym
                                previewSize: 34
                                round: true
                                outlined: true
                                selected: conversation.selected
                                accent: root.chatColor(conversation.colorIndex)
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    Layout.fillWidth: true
                                    text: conversation.title
                                    color: conversation.selected
                                        ? root.theme.selectedText
                                        : root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 10
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: conversation.isPersonalNotes
                                        ? qsTr("Your personal notes")
                                        : conversation.participantCount + (
                                            conversation.participantCount === 1
                                                ? qsTr(" member")
                                                : qsTr(" members")
                                        )
                                    color: conversation.selected
                                        ? root.theme.selectedText
                                        : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 8
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: conversation.lastMessageSummary
                                        ? (conversation.lastSender
                                            ? conversation.lastSender + ": " : "")
                                            + conversation.lastMessageSummary
                                            + (conversation.lastMessageLinkedCount > 0
                                                ? "  ·  "
                                                    + conversation.lastMessageLinkedCount
                                                    + (conversation.lastMessageLinkedCount === 1
                                                        ? " link" : " links")
                                                : "")
                                        : conversation.status || "No messages yet"
                                    color: conversation.selected
                                        ? root.theme.selectedText
                                        : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 8
                                    opacity: 0.82
                                    maximumLineCount: 1
                                    wrapMode: Text.NoWrap
                                    elide: Text.ElideRight
                                    clip: true
                                }
                            }
                            Rectangle {
                                visible: conversation.mentionCount > 0
                                implicitWidth: 18
                                implicitHeight: 18
                                radius: 9
                                color: conversation.selected
                                    ? root.theme.selectedText
                                    : root.theme.tertiary
                                Label {
                                    anchors.centerIn: parent
                                    text: qsTr("@")
                                    color: conversation.selected
                                        ? root.theme.tertiary
                                        : root.theme.selectedText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 10
                                    font.weight: Font.Bold
                                }
                            }
                            Rectangle {
                                visible: conversation.unread > 0
                                implicitWidth: Math.max(
                                    18, unreadLabel.implicitWidth + 8
                                )
                                implicitHeight: 18
                                radius: 9
                                color: conversation.selected
                                    ? root.theme.selectedText : root.theme.action
                                Label {
                                    id: unreadLabel
                                    anchors.centerIn: parent
                                    text: conversation.unread > 99
                                        ? "99+" : String(conversation.unread)
                                    color: conversation.selected
                                        ? root.theme.action : root.theme.selectedText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 8
                                    font.weight: Font.Bold
                                }
                            }
                        }
                        MouseArea {
                            id: conversationMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: messagesController.select_conversation(
                                conversation.index
                            )
                        }
                    }
                }
            }
        }

        Rectangle {
            SplitView.fillWidth: true
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
                        ItemPreview {
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
                            Label {
                                visible: messagesController.conversationId.length > 0
                                Layout.fillWidth: true
                                text: messagesController.selectedConversation.isPersonalNotes
                                    ? qsTr("Your personal notes  ·  ") + Number(
                                        messagesController.selectedConversation.messageCount || 0
                                    ) + qsTr(" notes")
                                    : Number(
                                        messagesController.selectedConversation.participantCount || 0
                                    ) + qsTr(" members  ·  ") + Number(
                                        messagesController.selectedConversation.messageCount || 0
                                    ) + qsTr(" messages")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 8
                                elide: Text.ElideRight
                            }
                        }
                        CompactIconButton {
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
                        CompactIconButton {
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
                        CompactIconButton {
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
                        CompactIconButton {
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
                            BusyIndicator {
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
                            duration: root.theme.motionFast
                            easing.type: Easing.OutCubic
                        }
                    }
                    HoverHandler {
                        id: pinnedMessageHover
                        cursorShape: Qt.PointingHandCursor
                    }
                    TapHandler {
                        onTapped: messagesController.show_message(
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
                            MaterialIcon {
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
                                font.pixelSize: 10
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
                                font.pixelSize: 8
                                elide: Text.ElideRight
                            }
                        }
                        RowLayout {
                            spacing: 3
                            visible: Number(
                                messagesController.pinnedMessage.linkedCount || 0
                            ) > 0
                            MaterialIcon {
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
                                font.pixelSize: 9
                            }
                        }
                        RowLayout {
                            spacing: 3
                            visible: Number(
                                messagesController.pinnedMessage.attachmentCount || 0
                            ) > 0
                            MaterialIcon {
                                name: "attach-file"
                                size: 15
                                color: root.theme.tertiary
                            }
                            Label {
                                text: String(
                                    messagesController.pinnedMessage.attachmentCount || "")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 9
                            }
                        }
                        MaterialIcon {
                            visible: messagesController.pinnedMessage.hasReply === true
                            name: "reply"
                            size: 15
                            color: root.theme.secondaryText
                        }
                        MaterialIcon {
                            visible: messagesController.pinnedMessage.forwarded === true
                            name: "share"
                            size: 15
                            color: root.theme.secondaryText
                        }
                        CompactIconButton {
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
                    font.pixelSize: 8
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
                        MaterialIcon {
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
                            font.pixelSize: 9
                            elide: Text.ElideRight
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            toolTip: qsTr("Dismiss error")
                            onClicked: {
                                messagesController.dismiss_error()
                                messageAttachments.dismiss_error()
                            }
                        }
                    }
                    Md3ToolTip {
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

                ListView {
                    id: messages
                    anchors.fill: parent
                    property real wheelTargetY: contentY
                    readonly property real maximumContentY: Math.max(
                        originY, originY + contentHeight - height)
                    readonly property bool awayFromEnd: contentHeight > height
                        && contentY < maximumContentY - 36
                    clip: true
                    opacity: root.messagePresentationReady ? 1 : 0
                    spacing: 12
                    model: tacticMessageModel
                    boundsBehavior: Flickable.StopAtBounds
                    flickDeceleration: 3600
                    maximumFlickVelocity: 4800
                    pixelAligned: false
                    cacheBuffer: 900
                    reuseItems: true
                    ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

                    Image {
                        parent: messages
                        anchors.fill: parent
                        z: -100
                        source: root.theme.dark
                            ? "../img/chat_bg_dark.png"
                            : "../img/chat_bg_light.png"
                        fillMode: Image.Tile
                        asynchronous: true
                        cache: true
                        smooth: true
                        mipmap: true
                    }

                    Rectangle {
                        parent: messages
                        anchors.fill: parent
                        z: -99
                        color: root.theme.dark
                            ? root.theme.workspace
                            : root.theme.primaryText
                        opacity: root.theme.dark ? 0.74 : 0.82
                    }

                    function cancelScrollAnimation() {
                        wheelScroll.stop()
                        jumpToLatestAnimation.stop()
                        wheelTargetY = contentY
                    }

                    function scrollWithWheel(pixelDelta, angleDelta) {
                        const delta = pixelDelta !== 0
                            ? pixelDelta * 1.65
                            : (angleDelta / 120) * 148
                        if (delta === 0)
                            return
                        jumpToLatestAnimation.stop()
                        const baseY = wheelScroll.running
                            ? wheelTargetY : contentY
                        wheelTargetY = Math.max(
                            originY,
                            Math.min(maximumContentY, baseY - delta)
                        )
                        wheelScroll.stop()
                        wheelScroll.to = wheelTargetY
                        wheelScroll.start()
                    }

                    function scrollToLatest() {
                        wheelScroll.stop()
                        jumpToLatestAnimation.stop()
                        cancelFlick()
                        if (count <= 0)
                            return
                        forceLayout()
                        const startY = contentY
                        positionViewAtIndex(count - 1, ListView.End)
                        positionViewAtEnd()
                        const endY = contentY
                        const distance = Math.abs(endY - startY)
                        if (distance > height * 2.5) {
                            settleAtLatest()
                            return
                        }
                        contentY = startY
                        jumpToLatestAnimation.to = endY
                        jumpToLatestAnimation.start()
                    }

                    function settleAtLatest() {
                        if (count <= 0)
                            return
                        forceLayout()
                        positionViewAtIndex(count - 1, ListView.End)
                        positionViewAtEnd()
                        wheelTargetY = contentY
                    }

                    function positionCachedAtLatest() {
                        if (count <= 0)
                            return
                        positionViewAtIndex(count - 1, ListView.End)
                        positionViewAtEnd()
                        wheelTargetY = contentY
                    }

                    NumberAnimation {
                        id: wheelScroll
                        target: messages
                        property: "contentY"
                        duration: 115
                        easing.type: Easing.OutCubic
                    }

                    NumberAnimation {
                        id: jumpToLatestAnimation
                        target: messages
                        property: "contentY"
                        duration: 150
                        easing.type: Easing.OutCubic
                        onFinished: Qt.callLater(messages.settleAtLatest)
                    }

                    WheelHandler {
                        target: null
                        blocking: true
                        onWheel: function(event) {
                            messages.scrollWithWheel(
                                event.pixelDelta.y,
                                event.angleDelta.y
                            )
                            event.accepted = true
                        }
                    }

                    onFlickStarted: cancelScrollAnimation()
                    onCountChanged: {
                        if (!root.messagePresentationReady)
                            messageSettleTimer.stablePasses = 0
                    }
                    onContentHeightChanged: {
                        if (!root.messagePresentationReady)
                            messageSettleTimer.stablePasses = 0
                    }
                    header: Item {
                        width: messages.width
                        height: messagesController.hasMore ? 56 : 12
                        Md3Button {
                            anchors.centerIn: parent
                            visible: messagesController.hasMore
                            theme: root.theme
                            text: qsTr("Earlier messages")
                            icon.name: "history"
                            tonal: true
                            enabled: !messagesController.busy
                            onClicked: messagesController.load_more()
                        }
                    }
                    footer: Item {
                        width: messages.width
                        height: 12
                    }
                    Column {
                        anchors.centerIn: parent
                        visible: messages.count === 0
                            && !messagesController.busy
                        spacing: 8
                        MaterialIcon {
                            anchors.horizontalCenter: parent.horizontalCenter
                            name: messagesController.conversationId.length > 0
                                ? "chat" : "forum"
                            size: 30
                            color: root.theme.secondaryText
                            opacity: 0.7
                        }
                        Label {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: messagesController.conversationId.length > 0
                                ? (messagesController.messageSearch.length > 0
                                    ? qsTr("No matching messages")
                                    : qsTr("No messages yet"))
                                : qsTr("Select a conversation")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 11
                        }
                        Label {
                            anchors.horizontalCenter: parent.horizontalCenter
                            visible: messagesController.conversationId.length > 0
                            text: messagesController.messageSearch.length > 0
                                ? qsTr("Try another search phrase")
                                : qsTr("Start the conversation below")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 9
                            opacity: 0.7
                        }
                    }
                    delegate: Item {
                        id: messageRow
                        required property string messageId
                        required property int index
                        required property string sender
                        required property string senderDisplay
                        required property string avatarUrl
                        required property string initials
                        required property color senderColor
                        required property string body
                        required property string bodyHtml
                        required property string displayHtml
                        required property var skeyPreviews
                        required property string timestamp
                        required property string timePretty
                        required property string timeSimple
                        required property bool isOwn
                        required property bool unread
                        required property var attachments
                        required property bool canEdit
                        required property bool edited
                        required property bool pinned
                        required property string editedBy
                        required property string editedAt
                        required property var editHistory
                        required property var replyTo
                        required property var forwardedFrom
                        required property bool forwardSelected
                        required property var reactions
                        required property bool reactionPending
                        width: messages.width
                        height: messageBubble.height

                        Rectangle {
                            id: messageBubble
                            width: Math.min(
                                parent.width * 0.82,
                                Math.max(0, parent.width - 32),
                                560
                            )
                            height: messageContent.implicitHeight + 24
                            x: messageRow.isOwn
                                ? Math.max(16, parent.width - width - 16)
                                : 16
                            radius: 14
                            color: messageRow.isOwn
                                ? root.theme.secondaryContainer
                                : root.theme.surfaceContainerHigh
                            border.width: messageRow.forwardSelected
                                || messages.currentIndex === messageRow.index
                                ? 2 : messageRow.unread ? 1 : 0
                            border.color: messageRow.forwardSelected
                                ? root.theme.tertiary : root.theme.action

                            Behavior on border.width {
                                NumberAnimation {
                                    duration: root.theme.motionFast
                                    easing.type: Easing.OutCubic
                                }
                            }

                            HoverHandler { id: messageHover }

                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.RightButton
                                cursorShape: Qt.ArrowCursor
                                onPressed: mouse => {
                                    root.prepareMessageActions(
                                        messageRow, messageBubble)
                                    messageActions.openAt(
                                        messageBubble, mouse.x, mouse.y)
                                    mouse.accepted = true
                                }
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10

                                ItemPreview {
                                    Layout.preferredWidth: 32
                                    Layout.preferredHeight: 32
                                    Layout.alignment: Qt.AlignTop
                                    theme: root.theme
                                    source: messageRow.avatarUrl
                                    fallbackIcon: "person"
                                    fallbackText: messageRow.initials
                                    previewSize: 32
                                    round: true
                                    outlined: true
                                    accent: root.theme.action
                                    animateAppearance: false
                                }

                                ColumnLayout {
                                    id: messageContent
                                    Layout.fillWidth: true
                                    spacing: 7

                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label {
                                            Layout.fillWidth: true
                                            text: messageRow.senderDisplay
                                                + (messageRow.sender
                                                    && messageRow.senderDisplay !== messageRow.sender
                                                    ? " (" + messageRow.sender + ")" : "")
                                            color: messageRow.senderColor
                                            font.family: root.theme.fontFamily
                                            font.pixelSize: 9
                                            font.weight: Font.DemiBold
                                            font.underline: senderMouse.containsMouse
                                            elide: Text.ElideRight
                                            MouseArea {
                                                id: senderMouse
                                                anchors.fill: parent
                                                enabled: messageRow.sender.length > 0
                                                hoverEnabled: true
                                                cursorShape: enabled
                                                    ? Qt.PointingHandCursor : Qt.ArrowCursor
                                                onClicked: userController.open_profile(
                                                    messageRow.sender)
                                            }
                                        }
                                        Label {
                                            text: messageTimeMouse.containsMouse
                                                ? messageRow.timeSimple
                                                : messageRow.timePretty
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pixelSize: 8
                                            MouseArea {
                                                id: messageTimeMouse
                                                anchors.fill: parent
                                                hoverEnabled: true
                                            }
                                        }
                                        Label {
                                            id: editedLabel
                                            visible: messageRow.edited
                                            text: qsTr("Edited")
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pixelSize: 8
                                            font.underline: editedMouse.containsMouse
                                            MouseArea {
                                                id: editedMouse
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    root.selectedEditHistory =
                                                        messageRow.editHistory
                                                    root.openBelow(
                                                        editedLabel, editHistoryPopup
                                                    )
                                                }
                                            }
                                            Md3ToolTip {
                                                theme: root.theme
                                                visible: editedMouse.containsMouse
                                                text: qsTr("Last edited by ")
                                                    + messageRow.editedBy + "  ·  "
                                                    + messageRow.editedAt
                                            }
                                        }
                                        CompactIconButton {
                                            visible: messagesController.forwardSelectionCount > 0
                                            theme: root.theme
                                            iconName: messageRow.forwardSelected
                                                ? "check-circle" : "circle"
                                            iconColor: messageRow.forwardSelected
                                                ? root.theme.tertiary
                                                : root.theme.secondaryText
                                            toolTip: messageRow.forwardSelected
                                                ? qsTr("Remove from forwarding")
                                                : qsTr("Add to forwarding")
                                            enabled: !messagesController.busy
                                            onClicked: messagesController.toggle_forward_selection(
                                                messageRow.messageId)
                                        }
                                        CompactIconButton {
                                            visible: messageRow.pinned
                                            theme: root.theme
                                            iconName: "push-pin"
                                            iconColor: root.theme.tertiary
                                            backgroundColor: root.theme.tertiaryContainer
                                            round: true
                                            toolTip: qsTr("Unpin message")
                                            enabled: !messagesController.busy
                                            onClicked: messagesController.unpin_message(
                                                messageRow.messageId)
                                        }
                                        CompactIconButton {
                                            id: addReactionButton
                                            opacity: messageHover.hovered
                                                || root.reactionMessageId
                                                    === messageRow.messageId
                                                ? 1 : 0
                                            enabled: opacity > 0
                                                && !messageRow.reactionPending
                                            theme: root.theme
                                            iconName: "emoji"
                                            toolTip: qsTr("Add reaction")
                                            Behavior on opacity {
                                                NumberAnimation {
                                                    duration: root.theme.motionFast
                                                    easing.type: Easing.OutCubic
                                                }
                                            }
                                            onClicked: root.openReactionPicker(
                                                messageRow.messageId,
                                                addReactionButton)
                                        }
                                        CompactIconButton {
                                            id: messageActionsButton
                                            opacity: messageHover.hovered ? 1 : 0
                                            enabled: opacity > 0
                                                && !messagesController.busy
                                            theme: root.theme
                                            iconName: "more-vert"
                                            toolTip: qsTr("Message actions")
                                            Behavior on opacity {
                                                NumberAnimation {
                                                    duration: root.theme.motionFast
                                                    easing.type: Easing.OutCubic
                                                }
                                            }
                                            onClicked: {
                                                root.prepareMessageActions(
                                                    messageRow, messageActionsButton)
                                                messageActions.toggleBelow(
                                                    messageActionsButton)
                                            }
                                        }
                                    }

                                    MessageReplyPreview {
                                        visible: messageRow.replyTo
                                            && String(
                                                messageRow.replyTo.messageId || ""
                                            ).length > 0
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        sender: String(
                                            messageRow.replyTo.senderDisplay || ""
                                        )
                                        body: String(messageRow.replyTo.body || "")
                                        available: messageRow.replyTo.available !== false
                                        onActivated: messagesController.show_message(
                                            String(messageRow.replyTo.messageId || ""))
                                    }

                                    MessageForwardPreview {
                                        visible: messageRow.forwardedFrom
                                            && String(
                                                messageRow.forwardedFrom.messageId || ""
                                            ).length > 0
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        sender: String(
                                            messageRow.forwardedFrom.senderDisplay || ""
                                        )
                                        body: String(
                                            messageRow.forwardedFrom.body || ""
                                        )
                                        attachmentCount: (
                                            messageRow.forwardedFrom.attachments || []
                                        ).length
                                        available: messageRow.forwardedFrom.available !== false
                                        onActivated: messagesController.open_forwarded_message(
                                            String(
                                                messageRow.forwardedFrom.conversationId || ""
                                            ),
                                            String(
                                                messageRow.forwardedFrom.messageId || ""
                                            ))
                                    }

                                    MessageBodyText {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: contentHeight
                                        theme: root.theme
                                        sourceHtml: messageRow.displayHtml
                                        rawText: messageRow.body
                                        visible: sourceHtml.length > 0
                                        onLinkActivated: link =>
                                            messagesController.open_link(link)
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        visible: messageRow.skeyPreviews
                                            && messageRow.skeyPreviews.length > 0
                                        spacing: 6
                                        Repeater {
                                            model: messageRow.skeyPreviews
                                            delegate: SKeyPreviewCard {
                                                id: skeyCard
                                                required property var modelData
                                                Layout.fillWidth: true
                                                theme: root.theme
                                                preview: modelData
                                                animatePreview: false
                                                onActivated: {
                                                    const conversationId = String(
                                                        modelData.conversationId || "")
                                                    const messageId = String(
                                                        modelData.itemCode
                                                            || modelData.searchKey || "")
                                                    if (!conversationId.length
                                                            || !messageId.length)
                                                        return
                                                    if (conversationId
                                                            === messagesController.conversationId)
                                                        messagesController.show_message(messageId)
                                                    else
                                                        messagesController.open_forwarded_message(
                                                            conversationId, messageId)
                                                }
                                                onRetryRequested: messagesController.retry_skey_preview(
                                                    modelData.searchKey)
                                                onNestedActivated: searchKey =>
                                                    messagesController.open_skey_preview(searchKey)
                                                onNestedRetryRequested: searchKey =>
                                                    messagesController.retry_skey_preview(searchKey)
                                                onContextRequested: (localX, localY) => {
                                                    root.skeyMenuValue = modelData.searchKey
                                                    root.skeyMenuFailed = modelData.status === "error"
                                                    root.skeyMenuCanOpen = modelData.kind !== "message"
                                                        || modelData.canOpen === true
                                                    skeyPreviewMenu.openAt(
                                                        skeyCard, localX, localY)
                                                }
                                            }
                                        }
                                    }

                                    ResponsiveFlow {
                                        id: messageAttachmentFlow
                                        Layout.fillWidth: true
                                        visible: messageRow.attachments
                                            && messageRow.attachments.length > 0
                                        minimumCellWidth: 210
                                        preferredCellWidth: 240
                                        maximumColumns: 2
                                        spacing: 8
                                        Repeater {
                                            model: messageRow.attachments
                                            delegate: AttachmentCard {
                                                id: attachmentCard
                                                required property string token
                                                required property int size
                                                width: imageAttachment
                                                    ? messageAttachmentFlow.width
                                                    : messageAttachmentFlow.cellWidth()
                                                theme: root.theme
                                                sizeText: root.formatFileSize(size)
                                                animatePreview: false
                                                onActivated:
                                                    messagesController.attachment_action(
                                                        token, "open")
                                                onContextRequested: (localX, localY) => {
                                                    root.attachmentMenuToken = token
                                                    root.attachmentMenuLocal = local
                                                    root.attachmentMenuImage = [
                                                        "JPG", "JPEG", "PNG", "WEBP", "GIF", "BMP"
                                                    ].indexOf(extension) >= 0
                                                    attachmentMenu.openAt(
                                                        attachmentCard, localX, localY)
                                                }
                                            }
                                        }
                                    }

                                    Flow {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: visible
                                            ? childrenRect.height : 0
                                        visible: messageRow.reactions
                                            && messageRow.reactions.length > 0
                                        layoutDirection: Qt.RightToLeft
                                        spacing: 5
                                        Repeater {
                                            model: messageRow.reactions || []
                                            delegate: MessageReactionChip {
                                                required property var modelData
                                                width: implicitWidth
                                                height: implicitHeight
                                                theme: root.theme
                                                emoji: String(modelData.emoji || "")
                                                count: Number(modelData.count || 0)
                                                checked: modelData.reactedByMe === true
                                                toolTip: String(
                                                    modelData.namesText || "")
                                                enabled: !messageRow.reactionPending
                                                onClicked:
                                                    messagesController.toggle_reaction(
                                                        messageRow.messageId,
                                                        String(modelData.emoji || ""))
                                            }
                                        }
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                z: 100
                                visible: messagesController.forwardSelectionCount > 0
                                acceptedButtons: Qt.LeftButton
                                cursorShape: Qt.PointingHandCursor
                                onClicked: messagesController.toggle_forward_selection(
                                    messageRow.messageId)
                            }

                        }
                    }

                    CompactIconButton {
                        parent: messages
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.rightMargin: 16
                        anchors.bottomMargin: 16
                        z: 200
                        width: 44
                        height: 44
                        opacity: messages.awayFromEnd ? 1 : 0
                        visible: opacity > 0
                        enabled: opacity > 0
                        theme: root.theme
                        iconName: "keyboard_arrow_down"
                        iconSize: 23
                        iconColor: root.theme.primaryText
                        backgroundColor: root.theme.surfaceContainerHighest
                        round: true
                        elevated: true
                        toolTip: qsTr("Jump to latest message")

                        Behavior on opacity {
                            NumberAnimation {
                                duration: root.theme.motionMedium
                                easing.type: Easing.OutCubic
                            }
                        }

                        onClicked: messages.scrollToLatest()
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
                        BusyIndicator {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 30
                            height: 30
                            running: parent.parent.visible
                            palette.highlight: root.theme.action
                        }
                        Label {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: qsTr("Loading conversation")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 10
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
                        MaterialIcon {
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
                            font.pixelSize: 10
                            font.weight: Font.DemiBold
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "content-copy"
                            toolTip: messagesController.forwardSelectionCount === 1
                                ? qsTr("Copy selected sKey")
                                : qsTr("Copy selected sKeys")
                            enabled: !messagesController.busy
                            onClicked: messagesController.copy_message_skey("")
                        }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Forward")
                            highlighted: true
                            enabled: !messagesController.busy
                            onClicked: messagesController.request_forward()
                        }
                        CompactIconButton {
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
                        attachmentController: messageAttachments
                        placeholderText: qsTr("Write a reply")
                        text: root.draft
                        readOnly: messagesController.sending
                            || messageAttachments.busy
                        onTextChanged: root.draft = text
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

            DropArea {
                id: chatDropArea
                anchors.fill: parent
                z: 20
                enabled: messagesController.conversationId.length > 0
                    && !messageAttachments.busy
                onDropped: drop => {
                    if (drop.hasUrls) {
                        messageAttachments.add_files(drop.urls)
                        drop.acceptProposedAction()
                    }
                }
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 6
                    visible: chatDropArea.containsDrag
                    radius: 10
                    color: root.theme.surfaceContainerHigh
                    opacity: 0.94
                    border.width: 2
                    border.color: root.theme.action
                    Column {
                        anchors.centerIn: parent
                        spacing: 7
                        MaterialIcon {
                            anchors.horizontalCenter: parent.horizontalCenter
                            name: "attach-file"
                            size: 30
                            color: root.theme.action
                        }
                        Label {
                            text: qsTr("Drop files to attach")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }
                    }
                }
            }
        }
    }

    Connections {
        target: messagesController
        function onMessageSentForConversation(conversationId) {
            const values = Object.assign({}, root.conversationDrafts)
            delete values[String(conversationId || "")]
            root.conversationDrafts = values
            if (String(conversationId || "")
                    === root.draftConversationId)
                root.draft = ""
        }
    }
}
