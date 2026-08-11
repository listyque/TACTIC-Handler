import QtQuick
import QtQuick.Controls

Item {
    id: root
    required property var theme
    required property var attachmentController
    property alias text: editor.text
    property alias placeholderText: editor.placeholderText
    property alias cursorPosition: editor.cursorPosition
    property bool readOnly: false
    readonly property int baseHeight: 44
    readonly property int maximumHeight: 124
    readonly property int contentPreferredHeight: Math.ceil(
        editor.contentHeight + editor.topPadding + editor.bottomPadding + 4
    )
    signal submitRequested()
    signal mentionRequested(string query)

    implicitHeight: Math.min(
        maximumHeight, Math.max(baseHeight, contentPreferredHeight)
    )

    Behavior on implicitHeight {
        NumberAnimation {
            duration: root.theme.motionFast
            easing.type: Easing.OutCubic
        }
    }

    function clear() {
        editor.clear()
    }

    function focusEditor() {
        editor.forceActiveFocus()
    }

    function insertMention(login) {
        const before = editor.text.slice(0, editor.cursorPosition)
        const match = before.match(/(^|\s)@([A-Za-z0-9_.-]*)$/)
        if (!match)
            return
        const start = editor.cursorPosition - match[0].length
        const value = match[1] + "@" + login + " "
        editor.remove(start, editor.cursorPosition)
        editor.insert(start, value)
        editor.cursorPosition = start + value.length
        editor.forceActiveFocus()
    }

    function insertEmoji(emoji) {
        if (root.readOnly || !emoji)
            return
        const position = editor.cursorPosition
        editor.insert(position, emoji)
        editor.cursorPosition = position + emoji.length
        editor.forceActiveFocus()
    }

    Rectangle {
        anchors.fill: parent
        radius: root.theme.surfaceRadius
        color: root.theme.surfaceContainerHigh
        border.width: editor.activeFocus ? 2 : 1
        border.color: editor.activeFocus
            ? root.theme.action : root.theme.outline

        Behavior on border.color {
            ColorAnimation { duration: root.theme.motionFast }
        }
    }

    ScrollView {
        id: scrollView
        anchors.fill: parent
        anchors.margins: 2
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            flickableTarget: scrollView.contentItem
        }

        Md3TextArea {
            id: editor
            width: scrollView.availableWidth
            height: Math.max(
                scrollView.availableHeight,
                contentHeight + topPadding + bottomPadding
            )
            theme: root.theme
            readOnly: root.readOnly
            background: null
            font.pixelSize: 15
            topPadding: 8
            bottomPadding: 8
            rightPadding: 42
            wrapMode: TextEdit.Wrap

            onTextChanged: {
                const before = text.slice(0, cursorPosition)
                const match = before.match(/(^|\s)@([A-Za-z0-9_.-]*)$/)
                root.mentionRequested(match ? match[2] : "")
            }

            HoverHandler {
                cursorShape: Qt.IBeamCursor
            }

            Keys.onPressed: event => {
                const control = event.modifiers & Qt.ControlModifier
                const shift = event.modifiers & Qt.ShiftModifier
                if (event.key === Qt.Key_Return && control) {
                    root.submitRequested()
                    event.accepted = true
                    return
                }
                if ((event.key === Qt.Key_V && control)
                        || (event.key === Qt.Key_Insert && shift)) {
                    const hasText = root.attachmentController.clipboard_has_text()
                    const hasImage = root.attachmentController.clipboard_has_image()
                    if (hasText)
                        editor.paste()
                    if (hasImage)
                        root.attachmentController.add_clipboard_image()
                    if (hasText || hasImage)
                        event.accepted = true
                }
            }
        }
    }

    CompactIconButton {
        id: emojiButton
        anchors.right: parent.right
        anchors.rightMargin: 7
        anchors.verticalCenter: parent.verticalCenter
        z: 2
        visible: !root.readOnly
        theme: root.theme
        iconName: "emoji"
        toolTip: qsTr("Insert emoji")
        onClicked: {
            if (emojiPicker.opened)
                emojiPicker.close()
            else
                emojiPicker.openFor(emojiButton)
        }
    }

    EmojiPicker {
        id: emojiPicker
        theme: root.theme
        onEmojiSelected: emoji => root.insertEmoji(emoji)
    }
}
