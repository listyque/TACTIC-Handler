import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/messages/conversation.ui.mjs" as UI

Rectangle {
    id: root
    required property var theme
    required property var conversationModel
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    readonly property var geometry: UI.layout(width, height)
    signal newConversationRequested
    signal conversationSelected(int index)
    signal conversationContextRequested(int index, var source, real x, real y)
    function selectConversation(index) {
        const retainedY = conversations.contentY;
        root.conversationSelected(index);
        Qt.callLater(function () {
            const minimum = conversations.originY;
            const maximum = Math.max(minimum, conversations.originY + conversations.contentHeight - conversations.height);
            conversations.contentY = Math.max(minimum, Math.min(maximum, retainedY));
        });
    }

    SplitView.preferredWidth: UI.metrics.preferred
    SplitView.minimumWidth: UI.metrics.minimum
    radius: 12
    color: theme.panel
    border.width: 1
    border.color: theme.outlineVariant
    Frame.FrameView {
        theme: root.theme
        x: root.geometry.header.x
        y: root.geometry.header.y
        width: root.geometry.header.width
        height: root.geometry.header.height
        scene: UI.heading(width, false, root.language)
        onEvent: action => root.newConversationRequested()
    }
    ListView {
        id: conversations
        objectName: "messagesConversationListView"
        x: root.geometry.list.x
        y: root.geometry.list.y
        width: root.geometry.list.width
        height: root.geometry.list.height
        clip: true
        spacing: UI.metrics.rowGap
        model: root.conversationModel
        reuseItems: true
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: conversations
        }
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

            width: root.geometry.rowWidth
            height: UI.metrics.row
            Frame.FrameView {
                theme: root.theme
                anchors.fill: parent
                scene: UI.row({
                    index: conversation.index,
                    title: conversation.title,
                    status: conversation.status,
                    lastMessage: conversation.lastMessage,
                    lastMessageSummary: conversation.lastMessageSummary,
                    lastMessageLinkedCount: conversation.lastMessageLinkedCount,
                    lastSender: conversation.lastSender,
                    unread: conversation.unread,
                    mentionCount: conversation.mentionCount,
                    selected: conversation.selected,
                    avatarUrl: conversation.avatarUrl,
                    initials: conversation.initials,
                    participantCount: conversation.participantCount,
                    memberSummary: conversation.memberSummary,
                    acronym: conversation.acronym,
                    colorIndex: conversation.colorIndex,
                    isPersonalNotes: conversation.isPersonalNotes
                }, width, root.language)
                onEvent: action => root.selectConversation(conversation.index)
            }
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.RightButton
                onClicked: mouse => root.conversationContextRequested(conversation.index, conversation, mouse.x, mouse.y)
            }
        }
    }
}
