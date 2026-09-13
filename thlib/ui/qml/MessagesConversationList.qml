import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Rectangle {
    id: root
    required property var theme
    required property var conversationModel

    signal newConversationRequested()
    signal conversationSelected(int index)

    function chatColor(index) {
        return [
            root.theme.action,
            root.theme.green,
            root.theme.cyan,
            root.theme.violet,
            root.theme.yellow
        ][Math.max(0, Number(index) || 0) % 5]
    }

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
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "group-add"
                toolTip: qsTr("New conversation")
                onClicked: root.newConversationRequested()
            }
        }
        ListView {
            id: conversations
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: root.conversationModel
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
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
                Controls.ItemSurface {
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
                    Controls.ItemPreview {
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
                            font.pointSize: Controls.Typography.body
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
                            font.pointSize: Controls.Typography.caption
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
                                                ? qsTr(" link") : qsTr(" links"))
                                        : "")
                                : conversation.status || qsTr("No messages yet")
                            color: conversation.selected
                                ? root.theme.selectedText
                                : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
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
                            font.pointSize: Controls.Typography.body
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
                            font.pointSize: Controls.Typography.caption
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
