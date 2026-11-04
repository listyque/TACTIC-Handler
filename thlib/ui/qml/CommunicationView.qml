import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "features/objects" as Objects
import "tactic_frame" as Frame
import "tactic_frame/features/objects/note.ui.mjs" as NoteUI

Item {
    id: root
    required property var theme
    readonly property bool presentationActive: parent ? parent.visible : visible
    property bool compact: false
    property string pendingNoteKey: ""
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
        id: timelinePosition
        view: history
        controller: communicationController
        model: noteModel
        presented: root.presentationActive
    }

    function messageMenuActions() {
        const actions = [
            {
                "title": "Copy sKey",
                "icon": "content-copy",
                "command": "copy_skey"
            }
        ];
        if (root.messageMenuCanEdit || root.messageMenuCanDelete)
            actions.push({
                "separator": true
            });
        if (root.messageMenuCanEdit) {
            actions.push({
                "title": "Edit note",
                "icon": "edit",
                "command": "edit"
            });
        }
        if (root.messageMenuCanDelete) {
            actions.push({
                "title": "Delete note",
                "icon": "delete",
                "command": "delete"
            });
        }
        return actions;
    }

    function scrollToLatest() {
        Qt.callLater(function () {
            if (history.count > 0)
                history.positionViewAtIndex(history.count - 1, ListView.End);
        });
    }

    function jumpToNote(noteId) {
        const row = communicationController.note_index(noteId);
        if (row < 0)
            return;
        Qt.callLater(function () {
            history.positionViewAtIndex(row, ListView.Center);
            history.currentIndex = row;
            noteFocusTimer.restart();
            communicationController.acknowledge_note_focus(noteId);
        });
    }

    function jumpToPendingNote() {
        const noteId = String(communicationController.pendingNoteFocus || "");
        if (noteId.length > 0)
            jumpToNote(noteId);
    }

    Timer {
        id: noteFocusTimer
        interval: 1800
        onTriggered: history.currentIndex = -1
    }

    Connections {
        target: communicationController
        enabled: root.presentationActive
        function onNoteFocusRequested(noteId) {
            root.jumpToNote(noteId);
        }
    }

    Component.onCompleted: {
        if (presentationActive)
            communicationController.mark_all_read();
        if (presentationActive) {
            jumpToPendingNote();
        }
    }
    onPresentationActiveChanged: {
        if (presentationActive) {
            communicationController.mark_all_read();
            jumpToPendingNote();
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
                tasksController.begin_edit_code(taskCode);
                dockModel.show_panel("tasks");
            }
        }

        Controls.SmoothListView {
            id: history
            theme: root.theme
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
            reuseItems: true
            boundsBehavior: Flickable.StopAtBounds

            Label {
                anchors.centerIn: parent
                visible: history.count === 0 && !communicationController.busy
                text: communicationController.hasTarget ? qsTr("No notes for this process") : qsTr("Select an sObject to view notes")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
            }

            delegate: Item {
                id: timelineRow
                required property int index
                required property string searchKey
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
                    color: Qt.rgba(timelineRow.statusColor.r, timelineRow.statusColor.g, timelineRow.statusColor.b, 0.42)
                }

                Rectangle {
                    id: statusRailAfter
                    visible: timelineRow.statusTimelineAfter
                    x: 13
                    y: bubble.height / 2
                    width: 1
                    height: parent.height - y + history.spacing / 2
                    color: Qt.rgba(timelineRow.statusColor.r, timelineRow.statusColor.g, timelineRow.statusColor.b, 0.42)
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
                    y: bubble.height + (history.spacing - height) / 2
                    size: root.theme.communicationListSpacing
                    name: "chevron-down"
                    color: root.theme.secondaryText
                    opacity: 0.82
                    z: 3
                }

                Rectangle {
                    id: bubble
                    objectName: "noteTimelineBubble"
                    readonly property bool statusEntry: timelineRow.entryType === "status"
                    readonly property bool rowSelected: history.currentIndex === timelineRow.index
                    readonly property var notePresentation: ({
                            status: statusEntry,
                            own: timelineRow.isOwn,
                            selected: rowSelected,
                            unread: timelineRow.unread,
                            author: timelineRow.author,
                            authorLabel: timelineRow.authorDisplay,
                            avatarUrl: timelineRow.avatarUrl,
                            initials: timelineRow.initials,
                            authorColor: String(timelineRow.authorColor),
                            statusColor: String(timelineRow.statusColor),
                            time: timelineRow.timePretty,
                            fullTime: timelineRow.timeSimple,
                            actionsVisible: bubbleHover.hovered || (messageOptionsMenu.opened && root.messageMenuRow === timelineRow.index),
                            busy: communicationController.busy
                        })
                    readonly property var geometry: NoteUI.geometry({
                        status: statusEntry,
                        own: timelineRow.isOwn
                    }, parent.width)
                    width: geometry.width
                    x: geometry.x
                    height: bubbleContent.implicitHeight + geometry.padding * 2
                    radius: geometry.radius
                    color: statusEntry ? Qt.rgba(timelineRow.statusColor.r, timelineRow.statusColor.g, timelineRow.statusColor.b, 48 / 255) : timelineRow.isOwn ? root.theme.secondaryContainer : root.theme.surfaceContainerHigh
                    border.width: rowSelected ? 2 : (statusEntry || timelineRow.unread ? 1 : 0)
                    border.color: rowSelected || !statusEntry ? root.theme.action : timelineRow.statusColor

                    HoverHandler {
                        id: bubbleHover
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: root.theme.communicationBubblePadding
                        spacing: root.theme.communicationAvatarSpacing

                        Controls.ItemPreview {
                            objectName: "noteAuthorAvatar"
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
                            animateAppearance: false
                        }

                        ColumnLayout {
                            id: bubbleContent
                            Layout.fillWidth: true
                            spacing: root.theme.communicationContentSpacing
                            Frame.FrameView {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 28
                                theme: root.theme
                                scene: NoteUI.header(bubble.notePresentation, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
                                onEvent: (event, source) => {
                                    if (event.type === "profile")
                                        userController.open_profile(event.login);
                                    else if (event.type === "menu") {
                                        root.messageMenuRow = timelineRow.index;
                                        root.messageMenuCanEdit = communicationController.can_change_note(timelineRow.index);
                                        root.messageMenuCanDelete = root.messageMenuCanEdit;
                                        root.pendingNoteKey = timelineRow.searchKey;
                                        root.pendingEditRow = timelineRow.index;
                                        root.pendingEditText = timelineRow.body;
                                        root.pendingDeleteRow = timelineRow.index;
                                        messageOptionsMenu.toggleBelow(source);
                                    }
                                }
                            }

                            Objects.NoteBody {
                                Layout.fillWidth: true
                                Layout.preferredHeight: implicitHeight
                                theme: root.theme
                                controller: communicationController
                                model: ({
                                        entryType: timelineRow.entryType,
                                        statusTo: timelineRow.statusTo,
                                        statusColor: timelineRow.statusColor,
                                        body: timelineRow.body,
                                        displayHtml: timelineRow.displayHtml,
                                        skeyPreviews: timelineRow.skeyPreviews,
                                        attachments: timelineRow.attachments
                                    })
                                onForwardedMessage: (conversationId, messageId) => messagesController.open_forwarded_message(conversationId, messageId)
                                onPreviewMenu: (anchor, record, localX, localY) => {
                                    root.skeyMenuValue = record.searchKey;
                                    root.skeyMenuFailed = record.status === "error";
                                    root.skeyMenuCanOpen = record.kind !== "message" || record.canOpen === true;
                                    skeyPreviewMenu.openAt(anchor, localX, localY);
                                }
                                onAttachmentMenu: (anchor, record, localX, localY) => {
                                    root.attachmentMenuToken = record.token;
                                    root.attachmentMenuLocal = record.local;
                                    root.attachmentMenuImage = ["JPG", "JPEG", "PNG", "WEBP", "GIF", "BMP"].indexOf(record.extension) >= 0;
                                    attachmentMenu.openAt(anchor, localX, localY);
                                }
                            }
                        }
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }
            onCountChanged: if (!timelinePosition.pending)
                root.scrollToLatest()
        }

        Controls.DockWorkspaceFooter {
            id: composerBar
            theme: root.theme
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(root.theme.dockWorkspaceFooterHeight, composerContent.implicitHeight + 14)
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
                        placeholderText: qsTr("Write a note · Enter to send · Ctrl+Enter for a new line")
                        enabled: communicationController.hasTarget
                        readOnly: !communicationController.hasTarget || communicationController.busy
                        text: communicationController.draftText
                        onTextChanged: communicationController.set_draft_text(text)
                        onSubmitRequested: communicationController.send(text)
                    }
                    MessageSendButton {
                        theme: root.theme
                        Layout.alignment: Qt.AlignVCenter
                        sending: (communicationController.busy && !communicationController.loading) || noteAttachments.busy
                        hasContent: communicationController.hasTarget && (replyInput.text.trim().length > 0 || noteAttachments.count > 0)
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
                        enabled: communicationController.hasTarget && !communicationController.busy
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
        enabled: communicationController.hasTarget && !communicationController.busy && !noteAttachments.busy
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
                communicationController.copy_skey(root.messageMenuRow);
            else if (command === "edit")
                editMessageDialog.open();
            else if (command === "delete")
                deleteDialog.open();
        }
        onClosed: root.messageMenuRow = -1
    }

    ActionMenu {
        id: attachmentMenu
        parent: Overlay.overlay
        theme: root.theme
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
        onTriggered: command => communicationController.attachment_action(root.attachmentMenuToken, command)
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
                communicationController.retry_skey_preview(root.skeyMenuValue);
            else if (command === "copy")
                communicationController.copy_skey_preview(root.skeyMenuValue);
            else
                communicationController.open_skey_preview(root.skeyMenuValue);
        }
    }

    Objects.NoteEditDialog {
        id: editMessageDialog
        theme: root.theme
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        width: Math.min(520, root.width - 32)
        controller: communicationController
        row: root.pendingEditRow
        searchKey: root.pendingNoteKey
        initialText: root.pendingEditText
    }
    Objects.NoteDeleteDialog {
        id: deleteDialog
        theme: root.theme
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        width: Math.min(380, root.width - 32)
        controller: communicationController
        row: root.pendingDeleteRow
        searchKey: root.pendingNoteKey
    }
}
