import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/objects/links.ui.mjs" as UI

Item {
    id: root

    required property var theme

    Item {
        id: linkDragPreview
        objectName: "linkDragPreview"
        width: Math.min(276, Math.max(210, root.width * 0.32))
        height: 58
        z: 100
        visible: Drag.active
        clip: true
        property var sourcePointer: null
        property string sourceDirection: ""
        property var transferKeys: []
        property string itemTitle: ""
        property string previewUrl: ""
        property string fallbackText: ""
        property color accent: root.theme.action
        Drag.active: sourcePointer ? sourcePointer.drag.active : false
        Drag.dragType: Drag.Internal
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        Drag.keys: ["tactic-handler-link-sobjects"]
        Drag.source: linkDragPreview
        Drag.hotSpot.x: 24
        Drag.hotSpot.y: height / 2

        function prepare(row, pointer, mouse) {
            sourcePointer = pointer;
            sourceDirection = row.sourceDirection;
            transferKeys = row.selected && row.listSelectedKeys.length > 0 ? row.listSelectedKeys.slice() : [row.searchKey];
            itemTitle = row.title;
            previewUrl = row.previewUrl;
            fallbackText = row.fallbackText;
            accent = row.accent;
            const point = parent.mapFromItem(row, mouse.x, mouse.y);
            x = point.x - Drag.hotSpot.x;
            y = point.y - Drag.hotSpot.y;
        }

        Controls.ItemSurface {
            anchors.fill: parent
            theme: root.theme
            selected: true
            hovered: false
            pressed: false
            accent: linkDragPreview.accent
            railVisible: true
            railX: 0
            railWidth: 3
            inset: 0
            cornerRadius: root.theme.itemRadius
            separatorVisible: false
            normalColor: root.theme.surfaceContainerHigh
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 7
            spacing: 9
            Controls.ItemPreview {
                objectName: "linkDragItemPreview"
                Layout.preferredWidth: 42
                Layout.preferredHeight: 42
                theme: root.theme
                previewSize: 42
                source: linkDragPreview.previewUrl
                fallbackIcon: "sobject"
                fallbackText: linkDragPreview.fallbackText
                accent: linkDragPreview.accent
                selected: true
                outlined: true
                cornerRadius: root.theme.itemRadius
                animateAppearance: false
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    objectName: "linkDragTitle"
                    Layout.fillWidth: true
                    text: linkDragPreview.itemTitle
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    wrapMode: Text.NoWrap
                }
                Label {
                    objectName: "linkDragDetails"
                    Layout.fillWidth: true
                    visible: linkDragPreview.transferKeys.length > 1
                    text: visible ? qsTr("Selected objects") + ": " + linkDragPreview.transferKeys.length : ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    wrapMode: Text.NoWrap
                }
            }
        }
    }

    Connections {
        target: sobjectLinkController
        function onSaved() {
            windowModel.close_window("link_sobjects");
        }
    }

    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var model: ({
            targetTitle: sobjectLinkController.target_title,
            parentTitle: sobjectLinkController.parent_title,
            subtitle: sobjectLinkController.target_code + " → " + [sobjectLinkController.parent_type_title, sobjectLinkController.parent_code].filter(value => value.length > 0).join(" · "),
            direction: sobjectLinkController.transfer_direction,
            selectedCount: sobjectLinkController.selected_count,
            canTransfer: sobjectLinkController.can_transfer,
            dirty: sobjectLinkController.dirty,
            busy: sobjectLinkController.busy,
            saving: sobjectLinkController.busy,
            error: sobjectLinkController.error,
            uncertain: sobjectLinkController.uncertain
        })
    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.model, width, height, root.language)
        views: ({
                availableSearch: availableSearchPort,
                linkedSearch: linkedSearchPort,
                availableList: availableListPort,
                linkedList: linkedListPort
            })
        onEvent: event => {
            if (event.type === "refresh")
                sobjectLinkController.refresh();
            else if (event.type === "transfer")
                sobjectLinkController.transfer_selected();
            else if (event.type === "close")
                windowModel.close_window("link_sobjects");
            else if (event.type === "save")
                sobjectLinkController.save();
        }
    }
    Component {
        id: availableSearchPort
        TacticSearchField {
            objectName: "availableLinkSearch"
            theme: root.theme
            controller: sobjectLinkController.available_search_controller
            suggestionModel: controller.suggestions
            placeholderText: qsTr("Search available objects")
        }
    }
    Component {
        id: linkedSearchPort
        TacticSearchField {
            objectName: "linkedLinkSearch"
            theme: root.theme
            controller: sobjectLinkController.linked_search_controller
            suggestionModel: controller.suggestions
            placeholderText: qsTr("Search linked objects")
        }
    }
    Component {
        id: availableListPort
        LinkList {
            theme: root.theme
            title: qsTr("Available objects")
            emptyText: sobjectLinkController.available_search_controller.current_search_text.length > 0 ? qsTr("No matching objects") : qsTr("No available objects")
            sourceModel: linkAvailableModel
            loading: sobjectLinkController.loading_available
            canLoadMore: sobjectLinkController.can_load_more
            selectedKeys: sobjectLinkController.available_selected_keys
            dragPreview: linkDragPreview
            dropDirection: "remove"
            totalCount: sobjectLinkController.available_total
            onRowSelected: (row, modifiers) => sobjectLinkController.select_available(row, modifiers)
            onLoadMoreRequested: sobjectLinkController.load_more_available()
            onObjectsDropped: keys => sobjectLinkController.remove_keys(keys)
        }
    }
    Component {
        id: linkedListPort
        LinkList {
            theme: root.theme
            title: qsTr("Linked objects")
            emptyText: sobjectLinkController.linked_search_controller.current_search_text.length > 0 ? qsTr("No matching linked objects") : qsTr("No linked objects")
            sourceModel: linkCurrentModel
            loading: sobjectLinkController.loading_linked
            selectedKeys: sobjectLinkController.linked_selected_keys
            dragPreview: linkDragPreview
            dropDirection: "add"
            totalCount: linkCurrentModel.count
            onRowSelected: (row, modifiers) => sobjectLinkController.select_linked(row, modifiers)
            onObjectsDropped: keys => sobjectLinkController.add_keys(keys)
        }
    }
}
