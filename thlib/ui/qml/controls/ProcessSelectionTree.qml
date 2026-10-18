import QtQuick
import "../tactic_frame" as Frame
import "../tactic_frame/features/search/visibility.ui.mjs" as UI
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Rectangle {
    id: root

    required property var theme
    required property var treeModel
    required property var treeController
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    property bool validContext: true
    property bool showVersionChooser: false
    property bool togglersExpanded: false
    property string emptyText: qsTr("Select a Search Type first")
    property string treeObjectName: "processSelectionTree"
    property string rowObjectName: "processSelectionTreeRow"

    radius: root.theme.itemRadius
    color: root.theme.surfaceContainerLow
    border.width: 1
    border.color: root.theme.outlineVariant
    clip: true

    ColumnLayout {
        visible: root.validContext
        anchors.fill: parent
        anchors.margins: 4
        spacing: 4

        Controls.SmoothListView {
            id: treeView
            theme: root.theme
            objectName: root.treeObjectName
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.treeModel

            delegate: Item {
                id: treeRow

                required property int index
                required property string title
                required property string kind
                required property int depth
                required property bool checkable
                required property bool checked
                required property bool expanded
                required property bool rowVisible
                required property bool selected
                required property string accent
                required property bool hasChildren

                objectName: root.rowObjectName
                width: Math.max(0, treeView.width - treeScrollBar.reservedExtent - 4)
                height: rowVisible ? 30 : 0
                visible: height > 0
                clip: true

                readonly property string displayTitle: treeRow.kind === "child" ? treeRow.title + qsTr(" (child)") : treeRow.kind === "builtin" ? treeRow.title + qsTr(" (builtin)") : treeRow.title
                readonly property bool showKindIcon: treeRow.kind === "child" || treeRow.kind === "process"

                readonly property var scene: UI.row({
                    title: title,
                    kind: kind,
                    depth: depth,
                    checkable: checkable,
                    checked: checked,
                    expanded: expanded,
                    selected: selected,
                    accent: accent,
                    hasChildren: hasChildren
                }, index, width, root.language)
                readonly property var parts: {
                    const result = {};
                    for (const node of scene.nodes)
                        result[node.id] = node;
                    return result;
                }
                Controls.ItemSurface {
                    anchors.fill: parent
                    theme: root.theme
                    selected: treeRow.selected
                    hovered: rowMouse.containsMouse
                    normalColor: root.theme[treeRow.parts.processVisibilitySelect.normalColor]
                    selectedColor: root.theme.contentSelection
                    railVisible: false
                    separatorVisible: false
                    cornerRadius: 0
                    MouseArea {
                        id: rowMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: mouse => root.treeController.select_row(treeRow.index, Boolean(mouse.modifiers & Qt.ControlModifier))
                    }
                }
                Controls.CompactIconButton {
                    readonly property var node: treeRow.parts.processVisibilityExpand
                    visible: !!node
                    x: node ? node.x : 0
                    y: node ? node.y : 0
                    width: node ? node.width : 0
                    height: node ? node.height : 0
                    theme: root.theme
                    iconName: node ? node.icon : ""
                    iconSize: node ? node.iconSize : 13
                    toolTip: node ? node.text : ""
                    onClickedWithModifiers: modifiers => root.treeController.toggle_expanded(treeRow.index, Boolean(modifiers & Qt.ShiftModifier))
                }
                Controls.CheckBox {
                    readonly property var node: treeRow.parts.processVisibilityCheck
                    visible: !!node
                    x: node ? node.x : 0
                    y: node ? node.y : 0
                    width: node ? node.width : 0
                    height: node ? node.height : 0
                    theme: root.theme
                    compact: true
                    checked: treeRow.checked
                    Accessible.name: node ? node.label : ""
                    onToggled: root.treeController.set_checked(treeRow.index, checked)
                }
                Controls.MaterialIcon {
                    objectName: "processSelectionIcon_" + treeRow.kind
                    readonly property var node: treeRow.parts.processVisibilityKind
                    visible: !!node
                    x: node ? node.x : 0
                    y: node ? node.y : 0
                    name: node ? node.icon : ""
                    size: node ? node.width : 16
                    forceSolid: treeRow.kind === "process"
                    color: treeRow.accent.length ? treeRow.accent : root.theme.secondaryText
                }
                Label {
                    objectName: "processSelectionTitle_" + treeRow.kind
                    readonly property var node: treeRow.parts["processSelectionTitle_" + treeRow.kind]
                    x: node.x
                    y: node.y
                    width: node.width
                    height: node.height
                    text: node.text
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: node.fontSize
                    textFormat: Text.PlainText
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                id: treeScrollBar
                theme: root.theme
                flickableTarget: treeView
            }
        }

        Frame.FrameView {
            Layout.fillWidth: true
            Layout.preferredHeight: scene.contentHeight
            theme: root.theme
            scene: UI.togglers({
                expanded: root.togglersExpanded,
                versionChooser: root.showVersionChooser
            }, width, root.language)
            views: ({
                    fullSync: syncComponent
                })
            onEvent: action => {
                if (action.type === "togglers")
                    root.togglersExpanded = !root.togglersExpanded;
                else if (action.type === "toggleKind")
                    root.treeController.toggle_kind(action.value);
            }
        }
        Component {
            id: syncComponent
            Controls.SegmentedButton {
                width: parent.width
                visible: root.showVersionChooser
                theme: root.theme
                segmentWidth: 145
                minimumSegmentWidth: 105
                currentValue: root.showVersionChooser && root.treeController.fullSync ? "full" : "versionless"
                model: [
                    {
                        label: "Versionless Sync",
                        value: "versionless"
                    },
                    {
                        label: "Full Sync",
                        value: "full"
                    }
                ]
                onActivated: value => root.treeController.set_full_sync(value === "full")
            }
        }
    }

    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        visible: !root.validContext
        scene: UI.empty(root.emptyText, width, height, root.language)
    }
}
