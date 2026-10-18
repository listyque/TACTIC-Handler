import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/knowledge/navigation.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    signal articleRequested(string identity)
    property string draggingIdentity: ""
    property int dropIndex: -1
    property string dropPlacement: ""

    function clearDropTarget() {
        root.dropIndex = -1;
        root.dropPlacement = "";
    }

    function updateDropTarget(sourceRow, point) {
        const contentPoint = sourceRow.mapToItem(navigationList.contentItem, point.x, point.y);
        const targetIndex = navigationList.indexAt(contentPoint.x, contentPoint.y);
        if (targetIndex < 0) {
            root.clearDropTarget();
            return;
        }
        const targetRow = navigationList.itemAtIndex(targetIndex);
        if (!targetRow || targetRow.identity === root.draggingIdentity) {
            root.clearDropTarget();
            return;
        }
        const localPoint = targetRow.mapFromItem(sourceRow, point.x, point.y);
        let placement = localPoint.y < targetRow.height * 0.34 ? "before" : localPoint.y > targetRow.height * 0.66 ? "after" : targetRow.section ? "inside" : "after";
        root.dropIndex = targetIndex;
        root.dropPlacement = placement;
    }

    function finishDrop() {
        const sourceIdentity = root.draggingIdentity;
        const targetRow = root.dropIndex >= 0 ? navigationList.itemAtIndex(root.dropIndex) : null;
        const targetIdentity = targetRow ? targetRow.identity : "";
        const placement = root.dropPlacement;
        root.draggingIdentity = "";
        root.clearDropTarget();
        if (sourceIdentity.length && targetIdentity.length)
            root.controller.move_entry(sourceIdentity, targetIdentity, placement);
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 7

        Controls.SearchField {
            id: searchField
            objectName: "knowledgeSearchField"
            Layout.fillWidth: true
            theme: root.theme
            placeholderText: qsTr("Search sections and articles")
            text: root.controller.query
            enabled: !root.controller.organizationDirty
            onSearchEdited: query => root.controller.set_query(query)
        }

        Controls.SmoothListView {
            id: navigationList
            objectName: "knowledgeNavigationList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            theme: root.theme
            model: knowledgeNavigationModel
            clip: true
            spacing: 1
            rightMargin: 12

            Controls.ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: navigationList
            }

            delegate: Controls.ItemSurface {
                id: navigationRow
                objectName: "knowledgeNavigationRow-" + navigationRow.identity
                required property string identity
                required property int index
                required property string title
                required property string description
                required property string excerpt
                required property string kind
                required property int depth
                required property bool hasChildren
                required property bool expanded
                required property bool draft
                required property bool localDraft
                readonly property bool section: kind === "section"
                readonly property bool dropInside: root.dropIndex === index && root.dropPlacement === "inside"
                selected: navigationRow.identity === root.controller.navigationIdentity
                hovered: rowHover.hovered
                pressed: false
                theme: root.theme

                width: navigationList.width - navigationList.rightMargin
                height: UI.rowHeight({
                    kind: kind,
                    description: description,
                    excerpt: excerpt
                }, root.controller.query)
                cornerRadius: root.theme.itemRadius
                normalColor: navigationRow.dropInside ? root.theme.blend(root.theme.action, root.theme.surfaceContainer, 0.14) : "transparent"
                selectedColor: root.theme.surfaceContainerHigh
                railVisible: false
                accent: root.theme.action
                separatorVisible: false
                borderWidth: 0
                opacity: rowReorder.active ? 0.66 : 1.0

                Frame.FrameView {
                    anchors.fill: parent
                    theme: root.theme
                    scene: UI.row({
                        identity: navigationRow.identity,
                        title: navigationRow.title,
                        description: navigationRow.description,
                        excerpt: navigationRow.excerpt,
                        kind: navigationRow.kind,
                        depth: navigationRow.depth,
                        hasChildren: navigationRow.hasChildren,
                        expanded: navigationRow.expanded,
                        draft: navigationRow.draft,
                        localDraft: navigationRow.localDraft
                    }, navigationRow.selected, root.controller.query, width, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
                    onEvent: action => {
                        if (action.type === "disclose")
                            root.controller.toggle_section(action.id);
                        else {
                            root.controller.select(action.id);
                            root.articleRequested(action.id);
                        }
                    }
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    y: root.dropPlacement === "before" ? -height / 2 : parent.height - height / 2
                    height: 3
                    radius: 1.5
                    color: root.theme.action
                    visible: root.dropIndex === navigationRow.index && root.dropPlacement !== "inside"
                    z: 4
                }

                HoverHandler {
                    id: rowHover
                }
                DragHandler {
                    id: rowReorder
                    target: null
                    enabled: root.controller.canEdit && !root.controller.busy && !root.controller.dirty && !navigationRow.localDraft && root.controller.query.length === 0
                    acceptedButtons: Qt.LeftButton
                    onActiveChanged: {
                        if (active) {
                            root.draggingIdentity = navigationRow.identity;
                            root.updateDropTarget(navigationRow, centroid.position);
                        } else if (root.draggingIdentity === navigationRow.identity) {
                            root.finishDrop();
                        }
                    }
                    onActiveTranslationChanged: {
                        if (active)
                            root.updateDropTarget(navigationRow, centroid.position);
                    }
                }
            }
        }

        Controls.EmptyState {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: knowledgeNavigationModel.count === 0 && !root.controller.busy
            theme: root.theme
            iconName: root.controller.query.length ? "search" : "file"
            title: root.controller.query.length ? qsTr("Nothing found") : qsTr("No articles yet")
            message: root.controller.query.length ? qsTr("Try another title or phrase from the article text.") : qsTr("Supervisors can create the first section or article here.")
        }
    }
}
