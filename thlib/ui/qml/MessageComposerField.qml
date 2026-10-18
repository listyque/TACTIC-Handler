import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame/features/messages/messaging.state.mjs" as State
import "tactic_frame/features/messages/composer.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var attachmentController
    required property var emojiCatalogModel
    property alias text: editor.text
    property alias placeholderText: editor.placeholderText
    property alias cursorPosition: editor.cursorPosition
    property bool readOnly: false
    property bool phone: false
    property bool mentioning: false
    property int mentionCount: 0
    signal mentionStepped(int delta)
    signal mentionAccepted
    signal mentionDismissed
    readonly property int baseHeight: UI.metrics.minimum
    readonly property int maximumHeight: UI.metrics.maximum
    readonly property int contentPreferredHeight: Math.ceil(editor.contentHeight + editor.topPadding + editor.bottomPadding + UI.metrics.inset * 2)
    signal submitRequested
    signal mentionRequested(string query)

    implicitHeight: Math.min(maximumHeight, Math.max(baseHeight, contentPreferredHeight))

    Behavior on implicitHeight {
        NumberAnimation {
            duration: root.theme.motionFast
            easing.type: Easing.OutCubic
        }
    }

    function clear() {
        editor.clear();
    }

    function focusEditor() {
        editor.forceActiveFocus();
    }

    function insertMention(login) {
        const before = editor.text.slice(0, editor.cursorPosition);
        const match = before.match(/(^|\s)@([A-Za-z0-9_.-]*)$/);
        if (!match)
            return;
        const start = editor.cursorPosition - match[0].length;
        const value = match[1] + "@" + login + " ";
        editor.remove(start, editor.cursorPosition);
        editor.insert(start, value);
        editor.cursorPosition = start + value.length;
        editor.forceActiveFocus();
    }

    function insertEmoji(emoji) {
        if (root.readOnly || !emoji)
            return;
        const position = editor.cursorPosition;
        editor.insert(position, emoji);
        editor.cursorPosition = position + emoji.length;
        editor.forceActiveFocus();
    }

    function toggleEmojiPicker() {
        const currentPicker = emojiPickerLoader.item;
        if (currentPicker && currentPicker.opened) {
            currentPicker.close();
            return;
        }
        emojiPickerLoader.active = true;
        if (emojiPickerLoader.item)
            emojiPickerLoader.item.openFor(emojiButton);
    }

    function insertNewLine() {
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        if (start !== end)
            editor.remove(start, end);
        editor.insert(start, "\n");
        editor.cursorPosition = start + 1;
    }

    Rectangle {
        anchors.fill: parent
        radius: root.theme.surfaceRadius
        color: root.theme.surfaceContainerHigh
        border.width: editor.activeFocus ? 2 : 1
        border.color: editor.activeFocus ? root.theme.action : root.theme.outline

        Behavior on border.color {
            ColorAnimation {
                duration: root.theme.motionFast
            }
        }
    }

    ScrollView {
        id: scrollView
        anchors.fill: parent
        anchors.margins: UI.metrics.inset
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: scrollView.contentItem
        }

        Controls.TextArea {
            id: editor
            objectName: "messageComposerTextArea"
            width: scrollView.availableWidth
            height: Math.max(scrollView.availableHeight, contentHeight + topPadding + bottomPadding)
            theme: root.theme
            readOnly: root.readOnly
            background: null
            font.pointSize: Controls.Typography.bodyLarge
            topPadding: UI.metrics.paddingTop
            bottomPadding: UI.metrics.paddingBottom
            leftPadding: UI.metrics.paddingLeft
            rightPadding: UI.metrics.paddingRight
            wrapMode: TextEdit.Wrap

            onTextChanged: {
                const before = text.slice(0, cursorPosition);
                const match = before.match(/(^|\s)@([A-Za-z0-9_.-]*)$/);
                root.mentionRequested(match ? match[2] : "");
            }

            HoverHandler {
                cursorShape: Qt.IBeamCursor
            }

            Keys.onPressed: event => {
                const control = !!(event.modifiers & Qt.ControlModifier);
                const shift = !!(event.modifiers & Qt.ShiftModifier);
                const command = State.composerKey({
                    key: [Qt.Key_Return, Qt.Key_Enter].includes(event.key) ? "Enter" : event.key === Qt.Key_Up ? "ArrowUp" : event.key === Qt.Key_Down ? "ArrowDown" : event.key === Qt.Key_Escape ? "Escape" : "",
                    composing: editor.inputMethodComposing,
                    control,
                    meta: !!(event.modifiers & Qt.MetaModifier),
                    repeat: event.isAutoRepeat,
                    sending: root.readOnly
                }, root.phone, root.mentioning, root.mentionCount > 0);
                if (command !== "pass") {
                    if (command === "mention")
                        root.mentionAccepted();
                    else if (command === "dismiss")
                        root.mentionDismissed();
                    else if (command === "next" || command === "previous")
                        root.mentionStepped(command === "next" ? 1 : -1);
                    else if (command === "newline")
                        root.insertNewLine();
                    else if (command === "send")
                        root.submitRequested();
                    event.accepted = true;
                    return;
                }
                if ((event.key === Qt.Key_V && control) || (event.key === Qt.Key_Insert && shift)) {
                    const hasText = root.attachmentController.clipboard_has_text();
                    const hasImage = root.attachmentController.clipboard_has_image();
                    if (hasText)
                        editor.paste();
                    if (hasImage)
                        root.attachmentController.add_clipboard_image();
                    if (hasText || hasImage)
                        event.accepted = true;
                }
            }
        }
    }

    Controls.CompactIconButton {
        id: emojiButton
        objectName: "messageComposerEmojiButton"
        width: UI.metrics.emoji
        height: UI.metrics.emoji
        anchors.right: parent.right
        anchors.rightMargin: UI.metrics.emojiRight
        anchors.verticalCenter: parent.verticalCenter
        z: 2
        visible: !root.readOnly
        theme: root.theme
        iconName: "emoji"
        toolTip: qsTr("Insert emoji")
        onClicked: root.toggleEmojiPicker()
    }

    Loader {
        id: emojiPickerLoader
        objectName: "messageComposerEmojiPickerLoader"
        active: false
        sourceComponent: EmojiPicker {
            objectName: "messageComposerEmojiPicker"
            theme: root.theme
            catalog: root.emojiCatalogModel
            onEmojiSelected: emoji => root.insertEmoji(emoji)
            onClosed: emojiPickerLoader.active = false
        }
    }
}
