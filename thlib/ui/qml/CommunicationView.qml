import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    readonly property bool presentationActive:
        parent ? parent.visible : visible
    property bool compact: false
    property int pendingDeleteRow: -1
    property int pendingEditRow: -1
    property string pendingEditText: ""
    property int messageMenuRow: -1
    property bool messageMenuCanEdit: false
    property bool messageMenuCanDelete: false
    property string attachmentMenuToken: ""
    property bool attachmentMenuLocal: false
    property bool attachmentMenuImage: false
    property string skeyMenuValue: ""
    property bool skeyMenuFailed: false
    property bool skeyMenuCanOpen: true

    NotesTimelinePosition {
        view: history
        controller: communicationController
        model: noteModel
        presented: root.presentationActive
    }

    function messageMenuActions() {
        const actions = [{
            "title": "Copy sKey", "icon": "content-copy", "command": "copy_skey"
        }]
        if (root.messageMenuCanEdit || root.messageMenuCanDelete)
            actions.push({"separator": true})
        if (root.messageMenuCanEdit) {
            actions.push({
                "title": "Edit note", "icon": "edit", "command": "edit"
            })
        }
        if (root.messageMenuCanDelete) {
            actions.push({
                "title": "Delete note", "icon": "delete",
                "command": "delete"
            })
        }
        return actions
    }

    function scrollToLatest() {
        Qt.callLater(function() {
            if (history.count > 0)
                history.positionViewAtIndex(history.count - 1, ListView.End)
        })
    }

    function jumpToNote(noteId) {
        const row = communicationController.note_index(noteId)
        if (row < 0)
            return
        Qt.callLater(function() {
            history.positionViewAtIndex(row, ListView.Center)
            history.currentIndex = row
            noteFocusTimer.restart()
            communicationController.acknowledge_note_focus(noteId)
        })
    }

    function jumpToPendingNote() {
        const noteId = String(communicationController.pendingNoteFocus || "")
        if (noteId.length > 0)
            jumpToNote(noteId)
    }

    Timer {
        id: noteFocusTimer
        interval: 1800
        onTriggered: history.currentIndex = -1
    }

    Connections {
        target: communicationController
        enabled: root.presentationActive
        function onNoteFocusRequested(noteId) { root.jumpToNote(noteId) }
    }

    Component.onCompleted: {
        if (presentationActive)
            communicationController.mark_all_read()
        if (presentationActive) {
            jumpToPendingNote()
        }
    }
    onPresentationActiveChanged: {
        if (presentationActive) {
            communicationController.mark_all_read()
            jumpToPendingNote()
        }
    }
    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TaskInspector {
            Layout.fillWidth: true
            theme: root.theme
            controller: communicationController
            onEditRequested: taskCode => {
                tasksController.begin_edit_code(taskCode)
                dockModel.show_panel("tasks")
            }
        }

        Controls.SmoothListView {
            theme: root.theme
            id: history
            objectName: "notesTimelineList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 8
            Layout.rightMargin: 8
            Layout.topMargin: 6
            Layout.bottomMargin: 5
            model: noteModel
            currentIndex: -1
            enabled: communicationController.hasTarget
            clip: true
            spacing: root.theme.communicationListSpacing
            bottomAnchored: true
            boundsBehavior: Flickable.StopAtBounds

            Label {
                anchors.centerIn: parent
                visible: history.count === 0 && !communicationController.busy
                text: communicationController.hasTarget
                    ? qsTr("No notes for this process")
                    : qsTr("Select an sObject to view notes")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
            }

            delegate: Item {
                id: timelineRow
                required property int index
                required property string author
                required property string authorDisplay
                required property string avatarUrl
                required property string initials
                required property string time
                required property string timePretty
                required property string timeSimple
                required property string body
                required property string bodyHtml
                required property string displayHtml
                required property var skeyPreviews
                required property string process
                required property bool isOwn
                required property bool unread
                required property var attachments
                required property int attachmentCount
                required property string entryType
                required property color authorColor
                required property string statusFrom
                required property string statusTo
                required property color statusColor
                required property bool canEdit
                required property bool canDelete
                required property bool statusTimelineBefore
                required property bool statusTimelineAfter

                width: history.width
                height: bubble.height

                Rectangle {
                    id: statusRailBefore
                    visible: timelineRow.statusTimelineBefore
                    x: 13
                    y: -history.spacing / 2
                    width: 1
                    height: bubble.height / 2 + history.spacing / 2
                    color: Qt.rgba(
                        timelineRow.statusColor.r,
                        timelineRow.statusColor.g,
                        timelineRow.statusColor.b,
                        0.42
                    )
                }

                Rectangle {
                    id: statusRailAfter
                    visible: timelineRow.statusTimelineAfter
                    x: 13
                    y: bubble.height / 2
                    width: 1
                    height: parent.height - y + history.spacing / 2
                    color: Qt.rgba(
                        timelineRow.statusColor.r,
                        timelineRow.statusColor.g,
                        timelineRow.statusColor.b,
                        0.42
                    )
                }

                Rectangle {
                    visible: timelineRow.entryType === "status"
                    x: 13 - width / 2
                    y: bubble.height / 2 - height / 2
                    width: 13
                    height: 13
                    radius: width / 2
                    color: root.theme.surfaceContainer
                    border.width: 2
                    border.color: timelineRow.statusColor
                    z: 2

                    Rectangle {
                        anchors.centerIn: parent
                        width: 5
                        height: 5
                        radius: width / 2
                        color: timelineRow.statusColor
                    }
                }

                Controls.MaterialIcon {
                    visible: timelineRow.statusTimelineAfter
                    x: 13 - width / 2
                    y: bubble.height
                        + (history.spacing - height) / 2
                    size: root.theme.communicationListSpacing
                    name: "chevron-down"
                    color: root.theme.secondaryText
                    opacity: 0.82
                    z: 3
                }

                Rectangle {
                    id: bubble
                    objectName: "noteTimelineBubble"
                    width: Math.min(
                        Math.max(0, parent.width
                            - (timelineRow.entryType === "status" ? 48 : 20))
                            * (timelineRow.entryType === "status" ? 0.90 : 0.82),
                        timelineRow.entryType === "status" ? 640 : 560
                    )
                    height: bubbleContent.implicitHeight
                        + root.theme.communicationBubblePadding * 2
                    x: timelineRow.entryType === "status"
                        ? 34 : timelineRow.isOwn
                        ? Math.max(10, parent.width - width - 10)
                        : 10
                    radius: 14
                    color: timelineRow.entryType === "status"
                        ? Qt.rgba(timelineRow.statusColor.r,
                            timelineRow.statusColor.g,
                            timelineRow.statusColor.b, 48 / 255)
                        : timelineRow.isOwn
                            ? root.theme.secondaryContainer
                            : root.theme.surfaceContainerHigh
                    border.width: history.currentIndex === timelineRow.index
                        ? 2 : timelineRow.entryType === "status"
                            ? 1 : timelineRow.unread ? 1 : 0
                    border.color: history.currentIndex === timelineRow.index
                        ? root.theme.action : timelineRow.entryType === "status"
                            ? timelineRow.statusColor : root.theme.action

                    HoverHandler { id: bubbleHover }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins:
                            root.theme.communicationBubblePadding
                        spacing: root.theme.communicationAvatarSpacing

                        Controls.ItemPreview {
                            Layout.preferredWidth: 32
                            Layout.preferredHeight: 32
                            Layout.alignment: Qt.AlignTop
                            theme: root.theme
                            source: timelineRow.avatarUrl
                            fallbackIcon: "person"
                            fallbackText: timelineRow.initials
                            previewSize: 32
                            round: true
                            outlined: true
                            accent: timelineRow.authorColor
                        }

                        ColumnLayout {
                            id: bubbleContent
                            Layout.fillWidth: true
                            spacing: root.theme.communicationContentSpacing
                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    id: authorLabel
                                    Layout.fillWidth: true
                                    text: timelineRow.authorDisplay
                                        + (timelineRow.author && timelineRow.authorDisplay !== timelineRow.author
                                            ? " (" + timelineRow.author + ")" : "")
                                    color: timelineRow.authorColor
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                    font.underline: authorMouse.containsMouse
                                    MouseArea {
                                        id: authorMouse
                                        anchors.fill: parent
                                        enabled: timelineRow.author.length > 0
                                        hoverEnabled: true
                                        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                        onClicked: userController.open_profile(timelineRow.author)
                                    }
                                }
                                Label {
                                    id: timeLabel
                                    text: timeMouse.containsMouse
                                        ? timelineRow.timeSimple : timelineRow.timePretty
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    MouseArea {
                                        id: timeMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                    }
                                }
                                Item {
                                    visible: timelineRow.entryType === "note"
                                    Layout.preferredWidth: visible ? 28 : 0
                                    Layout.preferredHeight: 28
                                    Controls.CompactIconButton {
                                        id: messageOptionsButton
                                        anchors.fill: parent
                                        theme: root.theme
                                        iconName: "more_vert"
                                        toolTip: qsTr("Note actions")
                                        opacity: bubbleHover.hovered
                                            || (messageOptionsMenu.opened
                                                && root.messageMenuRow === timelineRow.index)
                                            ? 1 : 0
                                        enabled: opacity > 0
                                        Behavior on opacity {
                                            NumberAnimation {
                                                duration: root.theme.hoverMotionFast
                                                easing.type: Easing.OutCubic
                                            }
                                        }
                                        onClicked: {
                                            root.messageMenuRow = timelineRow.index
                                            root.messageMenuCanEdit = timelineRow.canEdit
                                            root.messageMenuCanDelete = timelineRow.canDelete
                                            root.pendingEditRow = timelineRow.index
                                            root.pendingEditText = timelineRow.body
                                            root.pendingDeleteRow = timelineRow.index
                                            messageOptionsMenu.toggleBelow(
                                                messageOptionsButton)
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                visible: timelineRow.entryType === "status"
                                spacing: root.theme.communicationAvatarSpacing

                                Controls.MaterialIcon {
                                    name: "status"
                                    size: 22
                                    color: timelineRow.statusColor
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: timelineRow.statusTo
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: Font.Medium
                                    wrapMode: Text.WordWrap
                                }
                            }

                            MessageBodyText {
                                objectName: "noteBodyText"
                                Layout.fillWidth: true
                                Layout.preferredHeight: contentHeight
                                theme: root.theme
                                sourceHtml: timelineRow.displayHtml
                                rawText: timelineRow.body
                                visible: timelineRow.entryType === "note"
                                    && sourceHtml.length > 0
                                onLinkActivated: link => communicationController.open_link(link)
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                visible: timelineRow.skeyPreviews
                                    && timelineRow.skeyPreviews.length > 0
                                spacing: 6
                                Repeater {
                                    model: timelineRow.skeyPreviews
                                    delegate: SKeyPreviewCard {
                                        id: skeyCard
                                        required property var modelData
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        preview: modelData
                                        onActivated: {
                                            if (modelData.kind !== "message") {
                                                communicationController.open_skey_preview(
                                                    modelData.searchKey)
                                                return
                                            }
                                            const conversationId = String(
                                                modelData.conversationId || "")
                                            const messageId = String(
                                                modelData.itemCode
                                                    || modelData.searchKey || "")
                                            if (conversationId.length
                                                    && messageId.length)
                                                messagesController.open_forwarded_message(
                                                    conversationId, messageId)
                                        }
                                        onRetryRequested: communicationController.retry_skey_preview(
                                            modelData.searchKey)
                                        onNestedActivated: searchKey =>
                                            communicationController.open_skey_preview(searchKey)
                                        onNestedRetryRequested: searchKey =>
                                            communicationController.retry_skey_preview(searchKey)
                                        onContextRequested: (localX, localY) => {
                                            root.skeyMenuValue = modelData.searchKey
                                            root.skeyMenuFailed = modelData.status === "error"
                                            root.skeyMenuCanOpen = modelData.kind !== "message"
                                                || modelData.canOpen === true
                                            skeyPreviewMenu.openAt(skeyCard, localX, localY)
                                        }
                                    }
                                }
                            }

                            Controls.ResponsiveFlow {
                                id: noteAttachmentFlow
                                Layout.fillWidth: true
                                visible: timelineRow.attachmentCount > 0
                                minimumCellWidth: 210
                                preferredCellWidth: 240
                                maximumColumns: 2
                                spacing: 6
                                Repeater {
                                    model: timelineRow.attachments
                                    delegate: AttachmentCard {
                                        id: attachmentCard
                                        required property var modelData
                                        width: imageAttachment
                                            ? noteAttachmentFlow.width
                                            : noteAttachmentFlow.cellWidth()
                                        theme: root.theme
                                        title: String(modelData.title || "Attachment")
                                        extension: String(modelData.extension || "")
                                        previewUrl: String(modelData.previewUrl || "")
                                        sizeText: String(modelData.size || "")
                                        local: !!modelData.local
                                        onActivated: communicationController.attachment_action(
                                            modelData.token, "open")
                                        onContextRequested: (localX, localY) => {
                                            root.attachmentMenuToken = modelData.token
                                            root.attachmentMenuLocal = modelData.local
                                            root.attachmentMenuImage = [
                                                "JPG", "JPEG", "PNG", "WEBP", "GIF", "BMP"
                                            ].indexOf(modelData.extension) >= 0
                                            attachmentMenu.openAt(
                                                attachmentCard, localX, localY)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
            onCountChanged: root.scrollToLatest()
        }

        Controls.DockWorkspaceFooter {
            id: composerBar
            theme: root.theme
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(
                root.theme.dockWorkspaceFooterHeight,
                composerContent.implicitHeight + 14
            )
            ColumnLayout {
                id: composerContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 7
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    AttachmentComposerControls {
                        theme: root.theme
                        controller: noteAttachments
                        attachmentModel: noteAttachmentDraftModel
                        enabled: communicationController.hasTarget
                        Layout.alignment: Qt.AlignVCenter
                    }
                    MessageComposerField {
                        id: replyInput
                        theme: root.theme
                        emojiCatalogModel: emojiCatalog
                        attachmentController: noteAttachments
                        Layout.fillWidth: true
                        Layout.preferredHeight: implicitHeight
                        Layout.alignment: Qt.AlignVCenter
                        placeholderText: qsTr(
                            "Write a note · Enter to send · Ctrl+Enter for a new line"
                        )
                        enabled: communicationController.hasTarget
                        readOnly: !communicationController.hasTarget
                            || communicationController.busy
                        text: communicationController.draftText
                        onTextChanged:
                            communicationController.set_draft_text(text)
                        onSubmitRequested: communicationController.send(text)
                    }
                    MessageSendButton {
                        theme: root.theme
                        Layout.alignment: Qt.AlignVCenter
                        sending: (communicationController.busy
                            && !communicationController.loading)
                            || noteAttachments.busy
                        hasContent: communicationController.hasTarget
                            && (replyInput.text.trim().length > 0
                                || noteAttachments.count > 0)
                        onClicked: communicationController.send(replyInput.text)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    visible: communicationController.error.length > 0
                    Label {
                        Layout.fillWidth: true
                        text: communicationController.error
                        color: root.theme.error
                        wrapMode: Text.WordWrap
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Retry")
                        enabled: communicationController.hasTarget
                            && !communicationController.busy
                        onClicked: communicationController.reload()
                    }
                }
            }
        }
    }

    Controls.AttachmentDropArea {
        id: noteDropArea
        anchors.fill: parent
        z: 90
        theme: root.theme
        attachmentController: noteAttachments
        enabled: communicationController.hasTarget
            && !communicationController.busy
            && !noteAttachments.busy
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        anchors.bottomMargin: composerBar.height
        z: 100
        visible: communicationController.loading
        theme: root.theme
        message: qsTr("Loading task and notes…")
        cancellable: true
        onCancelRequested: communicationController.cancel_loading()
    }

    ActionMenu {
        id: messageOptionsMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 210
        actions: root.messageMenuActions()
        onTriggered: command => {
            if (command === "copy_skey")
                communicationController.copy_skey(root.messageMenuRow)
            else if (command === "edit")
                editMessageDialog.open()
            else if (command === "delete")
                deleteDialog.open()
        }
        onClosed: root.messageMenuRow = -1
    }

    ActionMenu {
        id: attachmentMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {"title": "Download", "icon": "download", "command": "download", "enabled": !root.attachmentMenuLocal},
            {"title": "Show folder", "icon": "folder_open", "command": "folder", "enabled": root.attachmentMenuLocal},
            {"title": root.attachmentMenuLocal ? "Open file" : "Download and open", "icon": "open_in_new", "command": "open"},
            {"separator": true},
            {"title": "Copy file path", "icon": "content_copy", "command": "copy_path"},
            {"title": "Copy web link", "icon": "link", "command": "copy_web"},
            {"title": "Copy image", "icon": "image", "command": "copy_image", "enabled": root.attachmentMenuLocal && root.attachmentMenuImage}
        ]
        onTriggered: command => communicationController.attachment_action(
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
                communicationController.retry_skey_preview(root.skeyMenuValue)
            else if (command === "copy")
                communicationController.copy_skey_preview(root.skeyMenuValue)
            else
                communicationController.open_skey_preview(root.skeyMenuValue)
        }
    }

    Controls.Dialog {
        id: editMessageDialog
        theme: root.theme
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        width: Math.min(520, root.width - 32)
        title: qsTr("Edit note")
        standardButtons: Dialog.NoButton
        onOpened: {
            editMessageText.text = root.pendingEditText
            editMessageText.forceActiveFocus()
        }
        contentItem: ColumnLayout {
            spacing: 12
            Controls.TextArea {
                id: editMessageText
                theme: root.theme
                Layout.fillWidth: true
                Layout.preferredHeight: 150
                wrapMode: TextEdit.Wrap
                placeholderText: qsTr("Note text")
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
                    enabled: editMessageText.text.trim().length > 0
                        && !communicationController.busy
                    onClicked: {
                        if (communicationController.edit(
                                root.pendingEditRow, editMessageText.text))
                            editMessageDialog.close()
                    }
                }
            }
        }
    }

    Controls.Dialog {
        id: deleteDialog
        theme: root.theme
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(380, root.width - 32)
        title: qsTr("Delete note?")
        standardButtons: Dialog.NoButton
        contentItem: RowLayout {
            Item { Layout.fillWidth: true }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: deleteDialog.close()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                destructive: true
                onClicked: {
                    communicationController.remove(root.pendingDeleteRow)
                    deleteDialog.close()
                }
            }
        }
    }
}
