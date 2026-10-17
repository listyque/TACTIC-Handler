import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/search/editors.ui.mjs" as UI
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

// The controller supplies only entries this user may configure. Show hidden
// never exposes anything removed by the server visibility policy.
Item {
    id: root

    required property var theme
    required property string windowId
    property var controller: quickFilterEditorController
    property var windows: windowModel
    objectName: "quickFilterEditorView"
    property bool showHidden: false
    property real selectedChipHeight: 0
    property var selectionFlowView
    function updateChipHeight() {
        const next = selectionFlowView ? selectionFlowView.implicitHeight : 0;
        if (selectedChipHeight !== next)
            selectedChipHeight = next;
    }
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var selectedChips: {
        const chips = [];
        const groups = controller.standardSelections;
        for (let groupIndex = 0; groupIndex < groups.length; groupIndex++) {
            const group = groups[groupIndex];
            for (let optionIndex = 0; optionIndex < group.options.length; optionIndex++)
                chips.push(Object.assign({}, group.options[optionIndex], {
                    groupKey: group.key,
                    groupTitle: group.title
                }));
        }
        return chips;
    }
    readonly property var frameModel: ({
            busy: controller.busy,
            count: controller.standardSelectionCount,
            canEdit: controller.canEdit,
            canSaveDefaults: controller.canSaveDefaults,
            canCopy: controller.canSaveDefaults,
            chipHeight: selectedChipHeight,
            showHidden: showHidden
        })
    function command(action) {
        if (action.type === "showHidden")
            showHidden = action.value;
        else if (action.type === "copy")
            controller.use_current_as_standard();
        else if (action.type === "clear")
            controller.clear_standard();
        else if (action.type === "save")
            controller.save();
        else if (action.type === "defaults")
            controller.save_defaults();
        else if (action.type === "close")
            windows.close_window(windowId);
        else if (action.type === "group")
            controller.set_group_enabled(action.index, action.value);
        else if (action.type === "move")
            controller.move_group(action.index, action.delta);
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: UI.editor.inset
        spacing: UI.editor.gap

        Label {
            Layout.fillWidth: true
            text: root.controller.contextTitle
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }

        Label {
            Layout.fillWidth: true
            visible: root.controller.error.length > 0
            text: root.controller.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }

        Flickable {
            id: editorFlickable
            objectName: "quickFilterEditorScroll"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: editorContent.implicitHeight
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: editorContent
                objectName: "quickFilterEditorContent"
                width: Math.max(0, editorFlickable.width - editorScrollBar.reservedExtent - 8)
                spacing: UI.editor.gap

                Label {
                    objectName: "quickFilterEditorLoading"
                    Layout.fillWidth: true
                    visible: root.controller.busy
                    text: qsTr("Loading filters…")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.Wrap
                }
                Frame.FrameView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: scene.contentHeight
                    theme: root.theme
                    scene: UI.selection(root.frameModel, width, root.language)
                    views: ({
                            chips: selectionComponent
                        })
                    onEvent: action => root.command(action)
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: root.theme.outlineVariant
                }
                Frame.FrameView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: scene.contentHeight
                    theme: root.theme
                    scene: UI.available(root.frameModel, width, root.language)
                    onEvent: action => root.command(action)
                }
                Label {
                    objectName: "quickFilterEditorEmpty"
                    Layout.fillWidth: true
                    visible: !root.controller.busy && root.controller.groups.length === 0 && root.controller.error.length === 0
                    text: qsTr("No filters available")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.Wrap
                }

                Repeater {
                    model: root.controller.groups

                    delegate: ColumnLayout {
                        id: groupSection
                        required property int index
                        required property var modelData
                        objectName: "quickFilterGroup:" + modelData.key
                        Layout.fillWidth: true
                        spacing: 6
                        visible: Boolean(modelData.enabled) || root.showHidden

                        Frame.FrameView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: scene.contentHeight
                            theme: root.theme
                            scene: UI.group(Object.assign({}, groupSection.modelData, {
                                index: groupSection.index,
                                total: root.controller.groups.length,
                                busy: root.controller.busy,
                                canEdit: root.controller.canEdit
                            }), width, root.language)
                            onEvent: action => root.command(action)
                        }
                        Flow {
                            id: optionFlow
                            Layout.fillWidth: true
                            spacing: 7
                            visible: Boolean(groupSection.modelData.enabled)

                            Repeater {
                                model: groupSection.modelData.options

                                delegate: QuickFilterChip {
                                    required property var modelData
                                    objectName: "quickFilterOption:" + groupSection.modelData.key + ":" + modelData.key
                                    theme: root.theme
                                    text: String(modelData.title || "")
                                    maximumChipWidth: optionFlow.width
                                    accent: modelData.accent || root.theme.action
                                    showAccentMarker: Boolean(modelData.showAccentMarker)
                                    subtle: true
                                    checked: Boolean(modelData.selected)
                                    enabled: root.controller.canEdit && !root.controller.busy
                                    onClicked: root.controller.set_option_selected(groupSection.modelData.key, modelData.key, !checked)
                                }
                            }
                        }
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                id: editorScrollBar
                objectName: "quickFilterEditorScrollBar"
                theme: root.theme
                flickableTarget: editorFlickable
            }
        }

        Frame.FrameView {
            Layout.fillWidth: true
            Layout.preferredHeight: scene.contentHeight
            theme: root.theme
            scene: UI.footer(root.frameModel, width, root.language)
            onEvent: action => root.command(action)
        }
    }
    Component {
        id: selectionComponent
        Flow {
            width: parent.width
            spacing: UI.editor.optionGap
            onImplicitHeightChanged: Qt.callLater(root.updateChipHeight)
            Component.onCompleted: {
                root.selectionFlowView = this;
                Qt.callLater(root.updateChipHeight);
            }
            Repeater {
                model: root.selectedChips
                delegate: QuickFilterChip {
                    required property var modelData
                    objectName: "removeStandardFilter:" + modelData.groupKey + ":" + modelData.key
                    theme: root.theme
                    text: String(modelData.groupTitle) + ": " + modelData.title
                    maximumChipWidth: parent.width
                    iconName: "close"
                    checked: true
                    subtle: true
                    enabled: root.controller.canEdit && !root.controller.busy
                    Accessible.name: qsTr("Remove filter") + ": " + text
                    onClicked: root.controller.remove_standard_selection(modelData.groupKey, modelData.key)
                }
            }
        }
    }
}
