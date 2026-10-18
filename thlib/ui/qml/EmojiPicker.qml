import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/controls/forms/emoji.ui.mjs" as UI

Controls.Popup {
    id: root
    required property var catalog
    property string category: catalog.defaultCategory
    property string query: ""
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    readonly property var geometry: UI.layout(availableWidth, availableHeight)
    signal emojiSelected(string emoji)
    parent: Overlay.overlay
    width: UI.popup(parent ? parent.width : 376, parent ? parent.height : 400).width + effectiveShadowMargin * 2
    height: UI.popup(parent ? parent.width : 376, parent ? parent.height : 400).height + effectiveShadowMargin * 2
    padding: 10
    focus: true
    function refresh() {
        catalog.set_filter(category, query);
        emojiGrid.currentIndex = catalog.count > 0 ? 0 : -1;
    }
    function openFor(anchorItem) {
        refresh();
        toggleBelowItem(anchorItem, true, 6);
    }
    onOpened: {
        header.focusControl("emojiPickerSearchField");
    }
    onClosed: {
        query = "";
        category = catalog.defaultCategory;
    }
    contentItem: Item {
        Frame.FrameView {
            id: header
            x: root.geometry.header.x
            y: root.geometry.header.y
            width: root.geometry.header.width
            height: root.geometry.header.height
            theme: root.theme
            scene: UI.heading({
                query: root.query,
                category: root.category
            }, width, root.language)
            onEvent: action => {
                if (action.type === "query")
                    root.query = action.value;
                else if (action.type === "category") {
                    root.category = action.value;
                    root.query = "";
                }
                root.refresh();
                if (action.type === "category")
                    emojiGrid.forceActiveFocus();
            }
        }
        GridView {
            id: emojiGrid
            objectName: "emojiPickerGrid"
            x: root.geometry.grid.x
            y: root.geometry.grid.y
            width: root.geometry.grid.width
            height: root.geometry.grid.height
            clip: true
            model: root.catalog
            cellWidth: root.geometry.cell
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

                readonly property var cellSpec: UI.cell({
                    emoji,
                    emojiName
                }, root.geometry.cell)
                objectName: "emojiPickerCell"
                width: cellSpec.width
                height: cellSpec.height
                hoverEnabled: true
                Accessible.role: Accessible.Button
                Accessible.name: cellSpec.label
                background: Rectangle {
                    radius: root.theme.itemRadius
                    color: emojiCell.down ? root.theme.surfaceContainerHighest : emojiCell.hovered || emojiCell.activeFocus ? root.theme.surfaceContainerHigh : "transparent"
                    border.width: emojiCell.activeFocus ? 2 : 0
                    border.color: root.theme.action
                }
                contentItem: Text {
                    Accessible.ignored: true
                    text: emojiCell.emoji
                    font: Qt.font({
                        family: root.theme.emojiFontFamily,
                        pixelSize: cellSpec.fontSize
                    })
                    renderType: Text.NativeRendering
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: {
                    emojiGrid.currentIndex = index;
                    root.emojiSelected(emoji);
                }
            }
        }

        Frame.FrameView {
            theme: root.theme
            visible: root.catalog.count === 0
            x: root.geometry.grid.x
            y: root.geometry.grid.y
            width: root.geometry.grid.width
            height: root.geometry.grid.height
            scene: visible ? UI.empty(width, height, root.language) : ({
                    nodes: []
                })
        }
    }
}
