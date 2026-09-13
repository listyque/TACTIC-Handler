import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

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
            sourcePointer = pointer
            sourceDirection = row.sourceDirection
            transferKeys = row.selected && row.listSelectedKeys.length > 0
                ? row.listSelectedKeys.slice() : [row.searchKey]
            itemTitle = row.title
            previewUrl = row.previewUrl
            fallbackText = row.fallbackText
            accent = row.accent
            const point = parent.mapFromItem(row, mouse.x, mouse.y)
            x = point.x - Drag.hotSpot.x
            y = point.y - Drag.hotSpot.y
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
                    text: visible
                        ? qsTr("Selected objects") + ": "
                            + linkDragPreview.transferKeys.length
                        : ""
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
            windowModel.close_window("link_sobjects")
        }
    }

    Connections {
        target: sobjectLinkController
        function onSessionStarted() {
            availableSearch.text = ""
            linkedSearch.text = ""
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 68
            color: root.theme.panel

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 14
                spacing: 12

                Rectangle {
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38
                    radius: root.theme.itemRadius
                    color: root.theme.secondaryContainer

                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: "link"
                        size: 18
                        color: root.theme.action
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        Layout.fillWidth: true
                        text: {
                            const target = sobjectLinkController.target_title
                            const parent = sobjectLinkController.parent_title
                            if (!target || !parent)
                                return qsTr("Select an instance relation")
                            return qsTr("Objects") + ": " + target + "  →  "
                                + qsTr("Parent object") + ": " + parent
                        }
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }

                    Label {
                        Layout.fillWidth: true
                        text: {
                            const target = sobjectLinkController.target_code
                            const parentType =
                                sobjectLinkController.parent_type_title
                            const parentCode =
                                sobjectLinkController.parent_code
                            const parent = [parentType, parentCode].filter(
                                value => value.length > 0
                            ).join(" · ")
                            return target.length > 0 && parent.length > 0
                                ? target + "  →  " + parent
                                : qsTr("Choose objects to link")
                        }
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        elide: Text.ElideRight
                    }
                }

                RefreshIconButton {
                    theme: root.theme
                    enabled: !sobjectLinkController.busy
                    toolTip: qsTr("Reload related objects")
                    onClicked: sobjectLinkController.refresh()
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: root.theme.separator
            }
        }

        RowLayout {
            id: linkSplit

            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 14
            spacing: 0

            Rectangle {
                objectName: "availableLinkPane"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 250
                Layout.preferredWidth: 1
                color: root.theme.panel
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                antialiasing: true
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    TacticSearchField {
                        id: availableSearch
                        objectName: "availableLinkSearch"
                        Layout.fillWidth: true
                        theme: root.theme
                        controller:
                            sobjectLinkController.available_search_controller
                        suggestionModel: controller.suggestions
                        placeholderText: qsTr("Search available objects")
                    }

                    LinkList {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        title: qsTr("Available objects")
                        emptyText: availableSearch.text.length > 0
                            ? qsTr("No matching objects")
                            : qsTr("No available objects")
                        sourceModel: linkAvailableModel
                        loading: sobjectLinkController.loading_available
                        canLoadMore: sobjectLinkController.can_load_more
                        selectedKeys:
                            sobjectLinkController.available_selected_keys
                        dragPreview: linkDragPreview
                        dropDirection: "remove"
                        totalCount: sobjectLinkController.available_total
                        onRowSelected: function(row, modifiers) {
                            sobjectLinkController.select_available(
                                row, modifiers
                            )
                        }
                        onLoadMoreRequested:
                            sobjectLinkController.load_more_available()
                        onObjectsDropped: function(keys) {
                            sobjectLinkController.remove_keys(keys)
                        }
                    }
                }
            }

            Item {
                Layout.preferredWidth: 52
                Layout.fillHeight: true

                Controls.CompactIconButton {
                    objectName: "linkTransferButton"
                    anchors.centerIn: parent
                    width: 42
                    height: 42
                    z: 2
                    theme: root.theme
                    iconName: sobjectLinkController.transfer_direction
                        === "remove" ? "arrow-left" : "arrow-forward"
                    iconSize: 18
                    round: true
                    elevated: true
                    badgeCount: sobjectLinkController.selected_count
                    enabled: sobjectLinkController.can_transfer
                    toolTip: sobjectLinkController.transfer_direction
                        === "remove"
                        ? qsTr("Remove selected links")
                        : qsTr("Link selected objects")
                    onClicked: sobjectLinkController.transfer_selected()
                }
            }

            Rectangle {
                objectName: "linkedLinkPane"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 250
                Layout.preferredWidth: 1
                color: root.theme.panel
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                antialiasing: true
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    TacticSearchField {
                        id: linkedSearch
                        objectName: "linkedLinkSearch"
                        Layout.fillWidth: true
                        theme: root.theme
                        controller:
                            sobjectLinkController.linked_search_controller
                        suggestionModel: controller.suggestions
                        placeholderText: qsTr("Search linked objects")
                    }

                    LinkList {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        title: qsTr("Linked objects")
                        emptyText: linkedSearch.text.length > 0
                            ? qsTr("No matching linked objects")
                            : qsTr("No linked objects")
                        sourceModel: linkCurrentModel
                        loading: sobjectLinkController.loading_linked
                        selectedKeys:
                            sobjectLinkController.linked_selected_keys
                        dragPreview: linkDragPreview
                        dropDirection: "add"
                        totalCount: linkCurrentModel.count
                        onRowSelected: function(row, modifiers) {
                            sobjectLinkController.select_linked(
                                row, modifiers
                            )
                        }
                        onObjectsDropped: function(keys) {
                            sobjectLinkController.add_keys(keys)
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: sobjectLinkController.error.length > 0
                ? Math.max(44, errorLabel.implicitHeight + 20) : 0
            visible: sobjectLinkController.error.length > 0
            color: root.theme.errorContainer

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 10

                Controls.MaterialIcon {
                    name: "error"
                    size: 17
                    color: root.theme.error
                }

                Label {
                    id: errorLabel
                    Layout.fillWidth: true
                    text: sobjectLinkController.error
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            color: root.theme.panel

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: root.theme.separator
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 9

                Label {
                    Layout.fillWidth: true
                    text: {
                        const count = sobjectLinkController.selected_count
                        if (count > 0)
                            return qsTr("Selected") + ": " + count
                        return sobjectLinkController.dirty
                            ? qsTr("Links have unsaved changes")
                            : qsTr("Select objects and use the center button")
                    }
                    color: sobjectLinkController.dirty
                        ? root.theme.action : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    elide: Text.ElideRight
                }

                Controls.BusyIndicator {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    uiTheme: root.theme
                    visible: sobjectLinkController.busy
                    running: visible
                }

                Controls.Button {
                    theme: root.theme
                    text: qsTr("Close")
                    enabled: !sobjectLinkController.busy
                    onClicked: windowModel.close_window("link_sobjects")
                }

                Controls.Button {
                    theme: root.theme
                    text: qsTr("Save")
                    icon.name: "save"
                    highlighted: true
                    enabled: !sobjectLinkController.busy
                        && sobjectLinkController.dirty
                    onClicked: sobjectLinkController.save()
                }
            }
        }
    }
}
