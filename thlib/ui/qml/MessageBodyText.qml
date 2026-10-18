import QtQuick
import "controls" as Controls
import "tactic_frame/features/messages/messaging.state.mjs" as State

TextEdit {
    id: root

    required property var theme
    property string sourceHtml: ""
    property string rawText: ""
    readonly property int emojiOnlyCount: State.emojiCount(rawText)
    readonly property bool stickerMode: emojiOnlyCount > 0

    text: sourceHtml.replace(/<a /g, "<a style=\"color:" + theme.action + ";\" ")
    textFormat: TextEdit.RichText
    color: theme.primaryText
    font.family: stickerMode ? theme.emojiFontFamily : theme.fontFamily
    font.pointSize: stickerMode ? (emojiOnlyCount === 1 ? 42 : emojiOnlyCount === 2 ? 36 : 31.5) : Controls.Typography.body
    wrapMode: TextEdit.Wrap
    topPadding: stickerMode ? 5 : 0
    bottomPadding: stickerMode ? 5 : 0
    readOnly: true
    selectByMouse: true
    activeFocusOnTab: true
}
