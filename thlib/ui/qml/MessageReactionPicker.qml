import QtQuick

Loader {
    id: root

    required property var theme
    required property var catalog
    property string messageId: ""
    signal reactionSelected(string messageId, string emoji)

    objectName: "messageReactionPickerLoader"
    active: false

    function openFor(messageId, anchorItem) {
        root.messageId = String(messageId || "")
        root.active = true
        if (root.item)
            root.item.openFor(anchorItem)
    }

    function close() {
        if (root.item)
            root.item.close()
    }

    sourceComponent: EmojiPicker {
        objectName: "messageReactionPicker"
        theme: root.theme
        catalog: root.catalog
        onEmojiSelected: emoji =>
            root.reactionSelected(root.messageId, emoji)
        onClosed: {
            root.messageId = ""
            root.active = false
        }
    }
}
