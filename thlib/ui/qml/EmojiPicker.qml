import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Popup {
    id: root

    required property var catalog
    property string category: catalog.defaultCategory
    signal emojiSelected(string emoji)

    parent: Overlay.overlay
    width: Math.min(360, Math.max(330, parent ? parent.width - 20 : 360))
    height: Math.min(380, Math.max(300, parent ? parent.height - 20 : 380))
    padding: 10
    focus: true

    function categoryLabel(key) {
        if (key === "Smileys & Emotion")
            return qsTr("Smileys & Emotion")
        if (key === "People & Body")
            return qsTr("People & Body")
        if (key === "Component")
            return qsTr("Component")
        if (key === "Animals & Nature")
            return qsTr("Animals & Nature")
        if (key === "Food & Drink")
            return qsTr("Food & Drink")
        if (key === "Travel & Places")
            return qsTr("Travel & Places")
        if (key === "Activities")
            return qsTr("Activities")
        if (key === "Objects")
            return qsTr("Objects")
        if (key === "Symbols")
            return qsTr("Symbols")
        if (key === "Flags")
            return qsTr("Flags")
        return key
    }

    function categorySegments() {
        const source = root.catalog.categories || []
        const segments = []
        for (let index = 0; index < source.length; ++index) {
            const category = source[index]
            segments.push({
                "value": category.key,
                "label": root.categoryLabel(category.key),
                "translate": false,
                "icon": category.icon
            })
        }
        return segments
    }

    function refresh() {
        root.catalog.set_filter(root.category, searchField.text)
        emojiGrid.currentIndex = root.catalog.count > 0 ? 0 : -1
    }

    function openFor(anchorItem) {
        root.openBelowItem(anchorItem, true, 6)
    }

    onOpened: {
        root.refresh()
        searchField.forceActiveFocus()
    }
    onClosed: {
        searchField.clear()
        root.category = root.catalog.defaultCategory
    }

    contentItem: ColumnLayout {
        spacing: 8

        Controls.TextField {
            id: searchField
            objectName: "emojiPickerSearchField"
            Layout.fillWidth: true
            theme: root.theme
            placeholderText: qsTr("Search emoji")
            Accessible.name: placeholderText
            onTextEdited: root.refresh()
        }

        Controls.SegmentedButton {
            id: categorySwitcher
            objectName: "emojiCategorySwitcher"
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: implicitWidth
            Layout.preferredHeight: root.theme.compactControlHeight
            theme: root.theme
            model: root.categorySegments()
            currentValue: root.category
            segmentWidth: 32
            minimumSegmentWidth: 30
            contentPadding: 2
            iconOnly: true
            onActivated: value => {
                root.category = value
                searchField.clear()
                root.refresh()
                emojiGrid.forceActiveFocus()
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            GridView {
                id: emojiGrid
                objectName: "emojiPickerGrid"
                anchors.fill: parent
                clip: true
                model: root.catalog
                cellWidth: Math.floor(width / 8)
                cellHeight: cellWidth
                cacheBuffer: cellHeight * 2
                reuseItems: true
                keyNavigationWraps: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: emojiGrid
                }

                delegate: Controls.PopupAction {
                    id: emojiCell

                    required property int index
                    required property string emoji
                    required property string emojiName

                    objectName: "emojiPickerCell"
                    width: emojiGrid.cellWidth
                    height: emojiGrid.cellHeight
                    hoverEnabled: true
                    Accessible.role: Accessible.Button
                    Accessible.name: emojiName
                    background: Rectangle {
                        radius: root.theme.itemRadius
                        color: emojiCell.down
                            ? root.theme.surfaceContainerHighest
                            : emojiCell.hovered || emojiCell.activeFocus
                                ? root.theme.surfaceContainerHigh
                                : "transparent"
                        border.width: emojiCell.activeFocus ? 2 : 0
                        border.color: root.theme.action
                    }
                    contentItem: Text {
                        Accessible.ignored: true
                        text: emojiCell.emoji
                        font.family: root.theme.emojiFontFamily
                        font.pointSize: 19
                        renderType: Text.NativeRendering
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        emojiGrid.currentIndex = index
                        root.emojiSelected(emoji)
                    }
                }
            }

            Label {
                anchors.centerIn: parent
                visible: root.catalog.count === 0
                text: qsTr("No emoji found")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
            }
        }
    }
}
