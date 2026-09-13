import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    required property var controller
    signal articleRequested(string identity)
    property string draggingIdentity: ""
    property int dropIndex: -1
    property string dropPlacement: ""

    function clearDropTarget() {
        root.dropIndex = -1
        root.dropPlacement = ""
    }

    function updateDropTarget(sourceRow, point) {
        const contentPoint = sourceRow.mapToItem(
            navigationList.contentItem, point.x, point.y)
        const targetIndex = navigationList.indexAt(
            contentPoint.x, contentPoint.y)
        if (targetIndex < 0) {
            root.clearDropTarget()
            return
        }
        const targetRow = navigationList.itemAtIndex(targetIndex)
        if (!targetRow || targetRow.identity === root.draggingIdentity) {
            root.clearDropTarget()
            return
        }
        const localPoint = targetRow.mapFromItem(
            sourceRow, point.x, point.y)
        let placement = localPoint.y < targetRow.height * 0.34
            ? "before" : localPoint.y > targetRow.height * 0.66
                ? "after" : targetRow.section ? "inside" : "after"
        root.dropIndex = targetIndex
        root.dropPlacement = placement
    }

    function finishDrop() {
        const sourceIdentity = root.draggingIdentity
        const targetRow = root.dropIndex >= 0
            ? navigationList.itemAtIndex(root.dropIndex) : null
        const targetIdentity = targetRow ? targetRow.identity : ""
        const placement = root.dropPlacement
        root.draggingIdentity = ""
        root.clearDropTarget()
        if (sourceIdentity.length && targetIdentity.length)
            root.controller.move_entry(
                sourceIdentity, targetIdentity, placement)
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
                readonly property bool dropInside: root.dropIndex === index
                    && root.dropPlacement === "inside"
                selected: navigationRow.identity
                    === root.controller.navigationIdentity
                hovered: rowHover.hovered
                pressed: rowActivation.pressed
                theme: root.theme

                width: navigationList.width - navigationList.rightMargin
                height: navigationContent.implicitHeight
                    + (navigationRow.section ? 10 : 8)
                cornerRadius: root.theme.itemRadius
                normalColor: navigationRow.dropInside
                    ? root.theme.blend(
                        root.theme.action,
                        root.theme.surfaceContainer,
                        0.14)
                    : "transparent"
                selectedColor: root.theme.surfaceContainerHigh
                railVisible: false
                accent: root.theme.action
                separatorVisible: false
                borderWidth: 0
                opacity: rowReorder.active ? 0.66 : 1.0

                RowLayout {
                    id: navigationContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 2 + navigationRow.depth * 18
                    anchors.rightMargin: 6
                    spacing: 4

                    Item {
                        id: disclosureSlot
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        Layout.alignment: Qt.AlignTop
                        Controls.CompactIconButton {
                            objectName: "knowledgeSectionDisclosure-"
                                + navigationRow.identity
                            anchors.fill: parent
                            visible: navigationRow.section
                                && navigationRow.hasChildren
                            theme: root.theme
                            iconName: navigationRow.expanded
                                ? "chevron-down" : "chevron-right"
                            iconColor: root.theme.secondaryText
                            toolTip: navigationRow.expanded
                                ? qsTr("Collapse section")
                                : qsTr("Expand section")
                            onClicked: root.controller.toggle_section(
                                navigationRow.identity)
                        }
                    }

                    Controls.MaterialIcon {
                        Layout.alignment: Qt.AlignTop
                        Layout.topMargin: 4
                        name: navigationRow.section
                            ? navigationRow.expanded ? "folder-open" : "folder"
                            : "file"
                        size: navigationRow.section ? 17 : 14
                        color: navigationRow.section
                            ? root.theme.tertiary : root.theme.action
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: navigationRow.section ? 1 : 0
                        Label {
                            objectName: "knowledgeNavigationTitle-"
                                + navigationRow.identity
                            Layout.fillWidth: true
                            text: navigationRow.title
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: navigationRow.kind === "section"
                                ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                        }
                        Label {
                            objectName: navigationRow.section
                                ? "knowledgeSectionDescription-" + navigationRow.identity
                                : "knowledgeArticleExcerpt-" + navigationRow.identity
                            Layout.fillWidth: true
                            visible: navigationRow.section
                                ? navigationRow.description.length > 0
                                : navigationRow.excerpt.length > 0
                                    && root.controller.query.length > 0
                            text: navigationRow.section
                                ? navigationRow.description
                                : navigationRow.excerpt
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            elide: Text.ElideRight
                        }
                    }
                    Label {
                        visible: navigationRow.draft
                            || navigationRow.localDraft
                        text: navigationRow.localDraft
                            ? qsTr("Local draft") : qsTr("Draft")
                        color: root.theme.tertiary
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.DemiBold
                    }
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    y: root.dropPlacement === "before"
                        ? -height / 2 : parent.height - height / 2
                    height: 3
                    radius: 1.5
                    color: root.theme.action
                    visible: root.dropIndex === navigationRow.index
                        && root.dropPlacement !== "inside"
                    z: 4
                }

                HoverHandler { id: rowHover }
                DragHandler {
                    id: rowReorder
                    target: null
                    enabled: root.controller.canEdit
                        && !root.controller.busy
                        && !root.controller.dirty
                        && !navigationRow.localDraft
                        && root.controller.query.length === 0
                    acceptedButtons: Qt.LeftButton
                    onActiveChanged: {
                        if (active) {
                            root.draggingIdentity = navigationRow.identity
                            root.updateDropTarget(
                                navigationRow, centroid.position)
                        } else if (root.draggingIdentity
                                === navigationRow.identity) {
                            root.finishDrop()
                        }
                    }
                    onActiveTranslationChanged: {
                        if (active)
                            root.updateDropTarget(
                                navigationRow, centroid.position)
                    }
                }
                Controls.ActivationHandler {
                    id: rowActivation
                    anchors.leftMargin: navigationRow.section
                            && navigationRow.hasChildren
                        ? disclosureSlot.x + disclosureSlot.width : 0
                    onActivated: {
                        root.controller.select(navigationRow.identity)
                        root.articleRequested(navigationRow.identity)
                    }
                }
            }
        }

        Controls.EmptyState {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: knowledgeNavigationModel.count === 0
                && !root.controller.busy
            theme: root.theme
            iconName: root.controller.query.length ? "search" : "file"
            title: root.controller.query.length
                ? qsTr("Nothing found") : qsTr("No articles yet")
            message: root.controller.query.length
                ? qsTr("Try another title or phrase from the article text.")
                : qsTr("Supervisors can create the first section or article here.")
        }
    }
}
