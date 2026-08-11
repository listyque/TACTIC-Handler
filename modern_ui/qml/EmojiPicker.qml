import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Md3Popup {
    id: root

    signal emojiSelected(string emoji)

    readonly property var emojiModel: [
        "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣",
        "😊", "🙂", "🙃", "😉", "😍", "🥰", "😘", "😎",
        "🤔", "🤨", "😐", "😑", "😏", "😒", "🙄", "😬",
        "😔", "😢", "😭", "😤", "😡", "🤯", "😱", "🥳",
        "👍", "👎", "👌", "✌️", "🤞", "👏", "🙌", "🙏",
        "💪", "👀", "❤️", "💔", "🔥", "✨", "🎉", "💯",
        "✅", "❌", "⚠️", "🚀", "💡", "📌", "🎨", "🎬"
    ]

    parent: Overlay.overlay
    width: Math.min(330, Math.max(246, parent ? parent.width - 20 : 330))
    height: Math.min(286, Math.max(188, parent ? parent.height - 20 : 286))
    padding: 10

    function openFor(anchorItem) {
        const overlay = Overlay.overlay
        if (!overlay || !anchorItem)
            return
        const point = anchorItem.mapToItem(overlay, 0, 0)
        root.x = Math.max(8, Math.min(
            overlay.width - root.width - 8,
            point.x + anchorItem.width - root.width
        ))
        const above = point.y - root.height - 6
        const below = point.y + anchorItem.height + 6
        root.y = above >= 8
            ? above : Math.min(overlay.height - root.height - 8, below)
        root.open()
    }

    contentItem: ColumnLayout {
        spacing: 7

        Label {
            Layout.fillWidth: true
            text: qsTr("EMOJI")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 10
            font.weight: Font.DemiBold
        }

        GridView {
            id: emojiGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.emojiModel
            cellWidth: Math.floor(width / 8)
            cellHeight: 39
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

            delegate: Item {
                id: emojiCell
                required property string modelData
                width: emojiGrid.cellWidth
                height: emojiGrid.cellHeight

                ItemSurface {
                    anchors.fill: parent
                    anchors.margins: 1
                    theme: root.theme
                    hovered: emojiMouse.containsMouse
                    pressed: emojiMouse.pressed
                    cornerRadius: 9
                    inset: 0
                    railVisible: false
                    separatorVisible: false
                }

                Text {
                    anchors.centerIn: parent
                    text: emojiCell.modelData
                    color: root.theme.primaryText
                    font.family: "Segoe UI Emoji"
                    font.pixelSize: 25
                    renderType: Text.NativeRendering
                }

                MouseArea {
                    id: emojiMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.emojiSelected(emojiCell.modelData)
                }
            }
        }
    }
}
