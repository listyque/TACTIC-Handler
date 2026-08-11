import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls"

Item {
    id: root
    required property var theme

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            Md3ComboBox {
                id: section
                theme: root.theme
                Layout.preferredWidth: 220
                model: navigationModel
                textRole: "title"
                valueRole: "entryKey"
                delegate: ItemDelegate {
                    required property string entryKey
                    required property string title
                    required property string command
                    required property bool available
                    required property string entryType
                    width: section.width
                    text: title
                    enabled: available && entryType === "link"
                    onClicked: {
                        appController.select_navigation(entryKey, title, command)
                        section.popup.close()
                    }
                }
            }
            Md3TextField {
                id: query
                theme: root.theme
                Layout.fillWidth: true
                placeholderText: qsTr("Search current asset type")
                text: appController.current_search_text
                onAccepted: appController.search(text)
            }
            CompactIconButton {
                theme: root.theme
                iconName: "search"
                toolTip: qsTr("Search")
                onClicked: appController.search(query.text)
            }
            RefreshIconButton {
                theme: root.theme
                toolTip: qsTr("Refresh current search")
                onClicked: appController.refresh_current()
            }
            CompactIconButton {
                theme: root.theme
                iconName: appController.results_view_mode === "tiles"
                    ? "view_list" : "grid_view"
                toolTip: qsTr("Toggle cards/list")
                onClicked: appController.set_results_view_mode(
                    appController.results_view_mode === "tiles"
                        ? "continious" : "tiles")
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: appController.current_search_tab_title
                    + "  ·  " + appController.result_count + qsTr(" items")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 9
            }
            Label {
                visible: appController.search_state === "loading"
                text: qsTr("Loading…")
                color: root.theme.action
                font.pixelSize: 9
            }
        }
        Item {
            id: browserResults
            property string menuNodeId: ""
            Layout.fillWidth: true
            Layout.fillHeight: true
            GridView {
                id: cards
                readonly property bool interactionMoving: moving || flicking
                anchors.fill: parent
                visible: appController.results_view_mode === "tiles"
                model: workspaceModel
                clip: true
                cellWidth: 230
                cellHeight: appController.card_compact_level ? 178 : 258
                cacheBuffer: 900
                reuseItems: true
                boundsBehavior: Flickable.StopAtBounds
                onInteractionMovingChanged: {
                    if (interactionMoving && browserActionMenu.visible)
                        browserActionMenu.close()
                }
                delegate: WorkspaceCard {
                    width: cards.cellWidth - 18 + (expanded ? 56 : 0)
                    height: (nodeType === "process" || nodeType === "relation"
                        ? 160 : cards.cellHeight - 14) + (expanded ? 78 : 0)
                    z: expanded ? 40 : 1
                    theme: root.theme
                    externalMenuVisible: browserActionMenu.visible
                        && browserResults.menuNodeId === nodeId
                    selected: appController.selected_result_node_ids.indexOf(nodeId) >= 0
                    onActionMenuRequested: function(
                        id, actions, anchorItem, localX, localY, below
                    ) {
                        browserResults.menuNodeId = id
                        browserActionMenu.actions = actions
                        if (below)
                            browserActionMenu.openBelow(anchorItem)
                        else
                            browserActionMenu.openAt(
                                anchorItem, localX, localY
                            )
                    }
                }
                onAtYEndChanged: if (atYEnd && appController.has_more)
                    appController.load_more()
                ScrollBar.vertical: Md3ScrollBar {
                    theme: root.theme
                    flickableTarget: cards
                }
            }
            ListView {
                id: rows
                readonly property bool interactionMoving: moving || flicking
                anchors.fill: parent
                visible: !cards.visible
                model: workspaceModel
                clip: true
                spacing: 4
                cacheBuffer: 900
                reuseItems: true
                onInteractionMovingChanged: {
                    if (interactionMoving && browserActionMenu.visible)
                        browserActionMenu.close()
                }
                delegate: WorkspaceResultItem {
                    theme: root.theme
                    compactMode: appController.results_view_mode === "compact"
                    hideVersionSnapshots: false
                    externalMenuVisible: browserActionMenu.visible
                        && browserResults.menuNodeId === nodeId
                    selected: appController.selected_result_node_ids.indexOf(nodeId) >= 0
                    onActionMenuRequested: function(
                        id, actions, anchorItem, localX, localY, below
                    ) {
                        browserResults.menuNodeId = id
                        browserActionMenu.actions = actions
                        if (below)
                            browserActionMenu.openBelow(anchorItem)
                        else
                            browserActionMenu.openAt(anchorItem, localX, localY)
                    }
                    onSelectedRequested: function(id, key, type, modifiers, preserve) {
                        appController.select_result_node(
                            id, key, type, modifiers, preserve)
                    }
                }
                onAtYEndChanged: if (atYEnd && appController.has_more)
                    appController.load_more()
                ScrollBar.vertical: Md3ScrollBar {
                    theme: root.theme
                    flickableTarget: rows
                }
            }
            ActionMenu {
                id: browserActionMenu
                parent: Overlay.overlay
                theme: root.theme
                actions: []
                onTriggered: function(command) {
                    appController.invoke_item_action(
                        command, browserResults.menuNodeId
                    )
                }
                onSecondaryTriggered: function(command) {
                    appController.invoke_item_action(
                        command, browserResults.menuNodeId
                    )
                }
            }
            Label {
                anchors.centerIn: parent
                visible: appController.result_count === 0
                    && appController.search_state !== "loading"
                text: appController.search_error || qsTr("No assets found")
                color: appController.search_error
                    ? root.theme.red : root.theme.secondaryText
                font.pixelSize: 10
            }
        }
        ProgressBar {
            Layout.fillWidth: true
            visible: appController.search_state === "loading"
            indeterminate: true
        }
    }
}
