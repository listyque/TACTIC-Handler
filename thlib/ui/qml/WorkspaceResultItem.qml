pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import "tactic_frame/features/search/card.ui.mjs" as Card
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "features/search" as Search
import "tactic_frame/features/administration/layouts/layout.preview.mjs" as Composition

Item {
    id: root

    required property int index
    required property string nodeId
    required property string nodeType
    required property string searchKey
    required property string itemCode
    required property string title
    required property string subtitle
    required property string status
    required property string accent
    required property int comments
    required property int tasks
    required property int depth
    required property bool expanded
    required property bool hasChildren
    required property string context
    required property string version
    required property string filePath
    required property string fileSize
    required property var infoChips
    required property string parentId
    required property string process
    required property string author
    required property string timestamp
    required property string timestampPretty
    required property string timestampSimple
    required property string revision
    required property string repository
    required property string repositoryColor
    required property string previewUrl
    readonly property url dragImageSource: String(root.previewUrl).indexOf("pending-preview:") === 0 ? "" : root.previewUrl
    required property bool previewRevealed
    required property bool previewRequested
    required property string relationship
    required property string watchState
    required property bool fileExists
    required property bool isLatest
    required property bool isVersionless
    required property bool isMultiple
    required property bool needsSync
    required property int childCount
    required property var itemControls
    required property var progressItems
    required property bool nodeLoading

    required property var theme
    property var controller: null
    property bool selected: false
    property bool compactMode: false
    property bool hideVersionSnapshots: false
    property bool controlHoverActive: false
    property bool externalMenuVisible: false
    property bool commentsUpdated: false
    property bool tasksUpdated: false
    property bool transientAnimationsSuppressed: true
    property bool viewPooled: false
    property bool presentationActive: true
    property bool itemDragActive: false
    property var dragMimeData: ({})
    property var configuredLayout: null
    property var configuredRecord: ({})
    property bool layoutEditing: false
    property bool presentationReadOnly: false
    property string selectedLayoutElement: ""
    readonly property var compositionRecord: !configuredLayout ? null : ({
            kind: root.objectCard ? "object" : root.snapshotCard ? "snapshot" : root.branchRow ? "branch" : root.nodeType,
            depth: root.depth,
            title: root.title,
            subtitle: root.subtitle,
            record: Object.assign({}, root.configuredRecord, {
                __search_key__: root.searchKey
            }),
            preview: {
                image: String(root.dragImageSource),
                local: true
            },
            note_count: root.comments,
            task_count: root.tasks,
            branch: {
                kind: root.nodeType,
                count: root.childCount,
                relationship: root.relationship
            },
            snapshot_display: {
                version: root.version,
                author: root.author,
                exists: root.fileExists,
                size: root.fileSize
            }
        })
    readonly property bool configured: !!configuredLayout && configuredLayout.flow !== "contents" && Composition.supports(configuredLayout, compositionRecord, root.Window.window ? root.Window.window.width : root.width)
    signal layoutElementSelected(string name)
    signal layoutGeometryEdited(var change)

    signal selectedRequested(string nodeId, string searchKey, string nodeType, int modifiers, bool preserveSelection)
    signal actionMenuRequested(string nodeId, var actions, var anchorItem, real localX, real localY, bool below)

    function requestPreviewIfNeeded() {
        if (!root.presentationReadOnly && root.presentationActive && !root.viewPooled && root.largeItem && !root.previewRequested && !root.previewUrl)
            appController.request_item_preview(root.nodeId);
    }

    onPreviewUrlChanged: requestPreviewIfNeeded()
    onPreviewRequestedChanged: requestPreviewIfNeeded()
    signal processCountMenuRequested(string nodeId, string panel, var anchorItem)

    function armTransientAnimations() {
        root.transientAnimationsSuppressed = root.viewPooled || itemMouse.containsMouse;
    }

    function cancelTransientAnimationArm() {
        root.transientAnimationsSuppressed = true;
    }

    function releaseControlHover() {
        if (!root.menuVisible)
            root.controlHoverActive = false;
    }

    readonly property var cardModel: ({
            kind: nodeType === "sobject" ? "object" : nodeType,
            compact: compactMode,
            depth: depth,
            hasChildren: hasChildren,
            subtitle: compactSubtitle,
            selected: selected
        })
    readonly property var cardLayout: Card.layout(cardModel, width)
    readonly property real branchIndentStep: 24
    readonly property real inlineActionGap: root.compactMode ? 6 : 8
    readonly property real indent: depth * branchIndentStep
    readonly property bool isGroup: nodeType === "group"
    readonly property bool largeItem: nodeType === "sobject" || nodeType === "snapshot"
    readonly property bool objectCard: root.nodeType === "sobject"
    readonly property bool snapshotCard: root.nodeType === "snapshot"
    readonly property bool branchRow: root.nodeType === "process" || root.nodeType === "relation"
    readonly property bool canFilterChildren: !presentationReadOnly && branchRow && expanded && hasChildren && !nodeLoading && !!controller && typeof controller.child_filter_text === "function"
    readonly property bool indentedSurface: root.objectCard || root.snapshotCard || root.branchRow
    readonly property real surfaceLeft: root.indentedSurface ? cardLayout.surfaceLeft : 0
    readonly property bool compactBranchItem: nodeType === "process" || nodeType === "relation" || root.isGroup
    readonly property bool relationBranchItem: nodeType === "relation"
    readonly property string compactTitle: String(title || "").replace(/[\r\n\t]+/g, " ").replace(/\s{2,}/g, " ").trim()
    readonly property string compactSubtitle: {
        const value = String(subtitle || "").replace(/[\r\n\t]+/g, " ").replace(/\s{2,}/g, " ").trim();
        if (!appController.description_limit_enabled || value.length <= appController.description_limit)
            return value;
        return value.slice(0, appController.description_limit).trim() + "…";
    }
    readonly property bool fullObjectCard: root.objectCard && !root.compactMode
    readonly property bool compactObjectCard: root.objectCard && root.compactMode
    readonly property real relationCountTrailingReserve: root.nodeType === "relation" && root.childCount > 0 ? 13 + Math.ceil(relationCountMetrics.advanceWidth) : 7
    readonly property real contentTrailingReserve: {
        const communicationWidth = communicationControls.visible ? communicationControls.implicitWidth : 0;
        if (nodeType === "sobject" || nodeType === "process") {
            const hoverWidth = hoverControls.active ? hoverControls.implicitWidth + 4 : 0;
            if (root.fullObjectCard)
                return Math.max(170, communicationWidth + hoverWidth + 22);
            return Math.max(compactMode ? 76 : 84, communicationWidth + hoverWidth + 12);
        }
        return Math.max(112, hoverControls.implicitWidth + 8);
    }

    readonly property string typeIcon: root.isGroup ? (root.expanded ? "folder-open" : "folder") : nodeType === "process" ? (subtitle === "hierarchy" ? "code_branch" : "circle") : nodeType === "snapshot" ? (!searchKey && isVersionless ? "exclamation_circle" : isMultiple ? "folder" : "file") : nodeType === "file" ? (fileExists ? "file" : "exclamation_circle") : nodeType === "relation" ? "stream" : "sobject"
    readonly property bool hoverAllowed: {
        const view = root.ListView.view;
        return !view || !view.interactionMoving;
    }
    readonly property bool interactiveHovered: root.hoverAllowed && itemMouse.containsMouse
    readonly property bool menuVisible: root.externalMenuVisible
    readonly property bool showHoverTools: menuVisible || (!root.transientAnimationsSuppressed && root.hoverAllowed && (itemMouse.containsMouse || controlHoverActive))
    readonly property bool hasPersistentItemControls: {
        const controls = root.itemControls || [];
        for (let index = 0; index < controls.length; ++index) {
            if (controls[index].persistent)
                return true;
        }
        return false;
    }
    x: ListView.view ? 6 : 0
    width: ListView.view ? Math.max(0, ListView.view.width - 12) : 320
    readonly property bool versionRowHidden: hideVersionSnapshots && nodeType === "snapshot" && !isVersionless
    visible: !versionRowHidden
    // Card insets reserve room for elevation inside the delegate. Keep the
    // delegate clipped so malformed server text cannot paint over its neighbor.
    clip: true
    height: versionRowHidden ? 0 : configured ? configuredBody.height + 16 : cardLayout.height
    Drag.active: root.itemDragActive
    Drag.dragType: Drag.Automatic
    Drag.supportedActions: Qt.CopyAction
    Drag.mimeData: root.dragMimeData
    Drag.imageSource: root.dragImageSource
    Drag.hotSpot.x: Math.min(width / 2, 42 + root.indent)
    Drag.hotSpot.y: height / 2
    opacity: hierarchyReveal.progress

    Component.onCompleted: {
        root.requestPreviewIfNeeded();
        root.armTransientAnimations();
    }
    ListView.onPooled: {
        root.cancelTransientAnimationArm();
        root.viewPooled = true;
        root.transientAnimationsSuppressed = true;
        Controls.HoverReleaseCoordinator.cancel(root);
        root.controlHoverActive = false;
        root.itemDragActive = false;
        root.dragMimeData = ({});
        fileDropTarget.reset();
    }
    ListView.onReused: {
        root.viewPooled = false;
        root.transientAnimationsSuppressed = true;
        root.controlHoverActive = false;
        root.itemDragActive = false;
        root.dragMimeData = ({});
        fileDropTarget.reset();
        root.requestPreviewIfNeeded();
        root.armTransientAnimations();
    }
    onPresentationActiveChanged: {
        root.requestPreviewIfNeeded();
    }

    TextMetrics {
        id: relationCountMetrics
        text: root.childCount > 0 ? "|  " + root.childCount : ""
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.caption
    }

    DragHandler {
        id: itemDragHandler
        target: null
        acceptedButtons: Qt.LeftButton
        enabled: !root.presentationReadOnly && (root.nodeType === "sobject" || root.nodeType === "snapshot" || root.nodeType === "file")
        onActiveChanged: {
            root.itemDragActive = active;
            if (active)
                root.dragMimeData = appController.item_drag_payload(root.nodeId);
            else
                root.dragMimeData = ({});
        }
    }

    function toggleExpandedPreservingScroll(modifiers) {
        const view = root.ListView.view;
        const recursive = Boolean(modifiers & Qt.ShiftModifier);
        if (view && view.toggleResultNodePreservingScroll)
            view.toggleResultNodePreservingScroll(root.nodeId, recursive, !root.expanded);
        else
            appController.toggle_result_node_recursive(root.nodeId, recursive);
    }

    Loader {
        id: configuredBody
        x: root.indent + 44
        y: 8
        width: Math.max(1, root.width - x - 14)
        height: item ? item.implicitHeight : 0
        z: 5
        visible: root.configured
        active: root.configured
        sourceComponent: Search.ConfiguredItem {
            width: configuredBody.width
            height: implicitHeight
            theme: root.theme
            layout: root.configuredLayout || {
                elements: []
            }
            controller: root.controller
            nodeId: root.nodeId
            editing: root.layoutEditing
            readOnly: root.presentationReadOnly
            selectedElement: root.selectedLayoutElement
            record: root.compositionRecord
            onGeometryEdited: value => root.layoutGeometryEdited(value)
            onElementSelected: name => root.layoutElementSelected(name)
            onMenuRequested: (relations, anchor) => root.actionMenuRequested(root.nodeId, relations ? root.controller.relation_menu_actions(root.nodeId) : root.controller.item_menu_actions(root.nodeId), anchor || configuredBody, 0, 0, true)
        }
    }

    Controls.HierarchyReveal {
        id: hierarchyReveal
        theme: root.theme
        view: root.ListView.view
        identity: root.nodeId
        row: root.index
        pooled: root.viewPooled
    }

    Controls.ItemSurface {
        objectName: "workspaceItemSurface"
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.leftMargin: root.surfaceLeft
        theme: root.theme
        selected: root.selected && !root.isGroup
        // Every workspace entity uses the same quiet content selection.
        // Process, snapshot, file and relation rows must not fall back to the
        // brighter control/tab selection color.
        selectedColor: root.theme.contentSelection
        hovered: root.interactiveHovered || root.menuVisible
        pressed: itemMouse.pressed
        accent: root.accent
        railVisible: root.nodeType === "sobject" || root.nodeType === "relation"
        railX: root.objectCard || root.relationBranchItem ? inset + 3 : 36
        railWidth: root.objectCard ? (root.fullObjectCard ? 4 : 3) : 3
        railTopMargin: root.objectCard ? (root.fullObjectCard ? 12 : 8) : 5
        railBottomMargin: railTopMargin
        railOpacity: root.nodeType === "file" ? 0.24 : 1
        inset: root.objectCard ? (root.fullObjectCard ? 4 : 3) : root.snapshotCard ? 2 : 1
        cornerRadius: root.objectCard ? (root.fullObjectCard ? root.theme.surfaceRadius : root.theme.itemRadius) : root.snapshotCard ? root.theme.snapshotRadius : 8
        borderWidth: root.objectCard ? 1 : 0
        borderColor: root.theme.outlineVariant
        elevated: root.objectCard
        shadowVerticalOffset: root.fullObjectCard ? 3 : 2
        separatorVisible: false
        normalColor: root.objectCard ? root.theme.surfaceContainerLow : root.isGroup ? root.theme.panelRaised : root.theme.panel
    }

    Loader {
        anchors.fill: parent
        z: 2
        active: root.depth > 0
        sourceComponent: Controls.HierarchyGuide {
            objectName: "workspaceHierarchyGuide"
            theme: root.theme
            depth: root.depth
            indentStep: root.branchIndentStep
            revealProgress: hierarchyReveal.progress
        }
    }

    Controls.DisclosureButton {
        id: disclosureArea
        objectName: "workspaceDisclosureArea"
        x: root.cardLayout.disclosure.x
        width: root.cardLayout.disclosure.width
        height: parent.height
        z: 4
        theme: root.theme
        identity: root.nodeId
        expanded: root.expanded && (!root.ListView.view || root.ListView.view.treeCollapseOwnerId !== root.nodeId)
        hasChildren: root.hasChildren
        loading: root.nodeLoading
        iconSize: root.fullObjectCard ? 18 : root.compactObjectCard ? 14 : root.compactBranchItem ? 13 : 15
        indicatorSize: root.fullObjectCard ? 24 : root.compactObjectCard ? 20 : 18
        onActivated: function (modifiers) {
            root.toggleExpandedPreservingScroll(modifiers);
        }
    }

    Item {
        id: preview
        objectName: "workspaceItemPreview"
        x: root.cardLayout.preview.x
        y: root.cardLayout.preview.y
        width: root.cardLayout.preview.width
        height: width
        z: root.interactiveHovered && root.largeItem ? 6 : 1
        transform: Translate {
            y: !root.fullObjectCard && !root.compactMode
                && root.interactiveHovered && root.largeItem
                && root.theme.hoverAnimationsEnabled
                && !root.theme.suppressTransientMotion ? -3 : 0
            Behavior on y {
                enabled: root.theme.hoverAnimationsEnabled
                    && !root.theme.suppressTransientMotion
                NumberAnimation {
                    duration: root.theme.hoverMotionMedium
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: root.interactiveHovered
                        ? [0.34, 1.2, 0.64, 1, 1, 1]
                        : [0.215, 0.61, 0.355, 1, 1, 1]
                }
            }
        }
        visible: !root.configured && root.nodeType !== "file" && !root.canFilterChildren
        opacity: root.nodeLoading ? 0.42 : 1
        Behavior on opacity {
            enabled: !root.theme.suppressTransientMotion
            NumberAnimation {
                duration: theme.motionMedium
                easing.type: Easing.OutCubic
            }
        }
        Loader {
            anchors.fill: parent
            sourceComponent: root.largeItem ? previewImageComponent : root.nodeType === "process" || root.nodeType === "relation" || root.isGroup ? previewIconComponent : null
        }
        Component {
            id: previewImageComponent
            Controls.ItemPreview {
                theme: root.theme
                // A hidden retained Search Tab is not rendered by its parent,
                // but its decoded thumbnail must stay ready for an instant
                // return. Only ListView pooling releases the texture.
                active: !root.viewPooled
                effectsEnabled: root.hoverAllowed
                source: root.previewUrl
                accent: root.accent
                round: root.nodeType === "sobject"
                cornerRadius: root.nodeType === "sobject" ? preview.width / 2 : 8
                selected: root.selected
                previewSize: preview.width
                fallbackIcon: root.typeIcon
                fallbackText: root.nodeType === "sobject" ? appController.get_acronym(root.compactTitle) : ""
                animateAppearance: !root.previewRevealed && root.hoverAllowed
                selectedBorderColor: root.theme.contentSelectionText
                onImageReady: {
                    if (!root.previewRevealed)
                        appController.mark_item_preview_revealed(root.nodeId);
                }
            }
        }
        Component {
            id: previewIconComponent
            Controls.MaterialIcon {
                anchors.centerIn: parent
                name: root.typeIcon
                size: root.nodeType === "process" ? (root.subtitle === "hierarchy" ? 16 : 13) : root.compactBranchItem ? 15 : 21
                color: root.accent
                forceSolid: root.nodeType === "process"
            }
        }
    }

    Loader {
        x: root.cardLayout.preview.x
        y: root.cardLayout.preview.y
        width: 24
        height: 24
        z: 8
        active: root.canFilterChildren
        sourceComponent: Search.BranchFilter {
            theme: root.theme
            controller: root.controller
            nodeId: root.nodeId
        }
    }
    Item {
        id: content
        visible: !root.configured
        enabled: !root.presentationReadOnly
        x: root.cardLayout.content.x
        y: root.cardLayout.content.y
        width: root.cardLayout.content.width
        height: root.cardLayout.content.height
        readonly property var bodyScene: Card.body(root.nodeType === "sobject" ? Object.assign({}, root.cardModel, {
            reserve: root.contentTrailingReserve
        }) : root.cardModel, width, height)
        readonly property var bodyParts: {
            const parts = {};
            for (const item of bodyScene.nodes)
                parts[item.id] = item;
            return parts;
        }
        z: 4
        opacity: root.nodeLoading ? 0.42 : 1
        Behavior on opacity {
            enabled: !root.theme.suppressTransientMotion
            NumberAnimation {
                duration: theme.motionMedium
                easing.type: Easing.OutCubic
            }
        }

        Loader {
            anchors.fill: parent
            sourceComponent: root.isGroup ? groupBodyComponent : root.nodeType === "relation" ? relationBodyComponent : root.nodeType === "sobject" ? objectBodyComponent : root.compactMode ? compactBodyComponent : root.nodeType === "snapshot" ? snapshotBodyComponent : root.nodeType === "process" ? processBodyComponent : root.nodeType === "relation" ? relationBodyComponent : fileBodyComponent
        }

        Component {
            id: groupBodyComponent
            Item {
                anchors.fill: parent
                RowLayout {
                    anchors.fill: parent
                    spacing: 8
                    Label {
                        Layout.fillWidth: true
                        text: root.compactTitle
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        text: root.compactSubtitle
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                }
            }
        }

        Component {
            id: compactBodyComponent
            Item {
                anchors.fill: parent
                Label {
                    id: compactTitle
                    objectName: "workspaceCompactTitle"
                    anchors.left: parent.left
                    anchors.right: compactSnapshotSize.visible ? compactSnapshotSize.left : parent.right
                    anchors.rightMargin: compactSnapshotSize.visible ? 7 : root.contentTrailingReserve
                    y: content.bodyParts.resultTitle.y
                    height: content.bodyParts.resultTitle.height
                    verticalAlignment: Text.AlignVCenter
                    text: root.compactTitle
                    color: root.selected ? root.theme.contentSelectionText : root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: content.bodyParts.resultTitle.fontSize
                    font.weight: Font.DemiBold
                    maximumLineCount: 1
                    wrapMode: Text.NoWrap
                    elide: Text.ElideRight
                    rightPadding: root.nodeType === "snapshot" ? compactQuickActions.width : 0

                    HoverHandler {
                        id: compactTitleHover
                        enabled: root.nodeType === "snapshot" && root.hoverAllowed
                        cursorShape: Qt.PointingHandCursor
                    }

                    ItemQuickActions {
                        id: compactQuickActions
                        objectName: "workspaceSnapshotInlineSnapshotActions"
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        theme: root.theme
                        compact: true
                        selected: root.selected
                        leadingSpace: root.inlineActionGap
                        dccApplication: appController.selected_dcc_application
                        nodeId: root.nodeId
                        revealed: compactTitleHover.hovered && !root.nodeLoading
                        onActionRequested: command => appController.invoke_item_action(command, root.nodeId)
                    }
                }
                Controls.StatusChip {
                    id: compactSnapshotSize
                    objectName: "workspaceCompactSnapshotSizeBadge"
                    anchors.right: parent.right
                    // Compact snapshots have no persistent trailing controls.
                    // Keep the size at the card edge and elide the title before it.
                    anchors.rightMargin: 0
                    anchors.verticalCenter: parent.verticalCenter
                    visible: root.nodeType === "snapshot" && root.fileSize.length > 0
                    width: visible ? implicitWidth : 0
                    theme: root.theme
                    text: root.fileSize
                    accentColor: root.selected ? root.theme.contentSelectionText : root.theme.secondaryText
                }
            }
        }

        Component {
            id: objectBodyComponent
            Item {
                id: body
                objectName: "workspaceObjectBody"
                anchors.fill: parent
                // Hot list delegates bind the common nodes directly, retaining native controls and pooling.
                readonly property var scene: content.bodyScene
                readonly property var parts: content.bodyParts
                Label {
                    id: objectTitle
                    objectName: "workspaceObjectTitle"
                    readonly property real titleWidth: Math.ceil(objectTitleMetrics.advanceWidth)
                    readonly property bool actionsFit: parent.width >= titleWidth + objectQuickActions.width
                    width: Math.min(parent.width, titleWidth + (objectQuickActions.revealed ? objectQuickActions.width : 0))
                    x: body.parts.resultTitle.x
                    y: body.parts.resultTitle.y
                    height: body.parts.resultTitle.height
                    rightPadding: objectQuickActions.revealed ? objectQuickActions.width : 0
                    text: root.compactTitle
                    color: root.selected ? root.theme.contentSelectionText : root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: root.compactObjectCard ? 12 : 15
                    font.weight: Font.DemiBold
                    maximumLineCount: 1
                    wrapMode: Text.NoWrap
                    elide: Text.ElideRight

                    TextMetrics {
                        id: objectTitleMetrics
                        font: objectTitle.font
                        text: objectTitle.text
                    }

                    HoverHandler {
                        id: objectTitleHover
                        enabled: root.hoverAllowed
                        cursorShape: Qt.PointingHandCursor
                    }

                    ItemQuickActions {
                        id: objectQuickActions
                        objectName: "workspaceObjectInlineSnapshotActions"
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        theme: root.theme
                        compact: root.compactMode
                        selected: root.selected
                        leadingSpace: root.inlineActionGap
                        dccApplication: appController.selected_dcc_application
                        nodeId: root.nodeId
                        revealed: objectTitleHover.hovered && objectTitle.actionsFit && !root.nodeLoading
                        onActionRequested: command => appController.invoke_item_action(command, root.nodeId)
                    }
                }
                Label {
                    objectName: "workspaceObjectSubtitle"
                    readonly property var node: body.parts.workspaceObjectSubtitle
                    visible: !!node
                    x: node ? node.x : 0
                    y: node ? node.y : 0
                    width: node ? node.width : 0
                    height: node ? node.height : 0
                    text: node ? node.text : ""
                    color: root.selected ? root.theme.contentSelectionText : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: node ? node.fontSize : 11
                    textFormat: Text.PlainText
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                Loader {
                    objectName: "workspaceObjectMetadata"
                    width: body.parts.resultMetadata?.width ?? 0
                    height: body.parts.resultMetadata?.height ?? 0
                    x: body.parts.resultMetadata?.x ?? 0
                    y: body.parts.resultMetadata?.y ?? 0
                    active: (root.progressItems || []).length > 0 || (root.infoChips || []).length > 0
                    sourceComponent: Row {
                        anchors.fill: parent
                        spacing: root.compactObjectCard ? 4 : 6
                        clip: true
                        Controls.CompletionStrip {
                            height: parent.height
                            theme: root.theme
                            items: root.progressItems || []
                            maximumItems: root.compactObjectCard ? 1 : 0
                            dense: root.compactObjectCard
                            maximumWidth: root.compactObjectCard ? parent.width : 0
                            onCompletionRequested: searchType => {
                                if (root.controller)
                                    root.controller.open_completion(root.nodeId, searchType);
                            }
                        }
                        Label {
                            visible: (root.progressItems || []).length > 0 && (root.infoChips || []).length > 0
                            height: parent.height
                            text: "|"
                            color: root.theme.outline
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            verticalAlignment: Text.AlignVCenter
                        }
                        Controls.InfoValueStrip {
                            width: Math.max(0, parent.width - x)
                            height: parent.height
                            theme: root.theme
                            items: root.infoChips || []
                            selected: root.selected
                            separatorText: "|"
                        }
                    }
                }
            }
        }
        Component {
            id: snapshotBodyComponent
            Item {
                id: snapshotBody
                anchors.fill: parent
                readonly property var scene: content.bodyScene
                Item {
                    x: snapshotBody.scene.nodes[0].x
                    y: snapshotBody.scene.nodes[0].y
                    width: snapshotBody.scene.nodes[0].width
                    height: snapshotBody.scene.nodes[0].height

                    RowLayout {
                        anchors.left: parent.left
                        anchors.right: snapshotSizeBadge.left
                        anchors.rightMargin: 8
                        height: parent.height
                        spacing: 5

                        Label {
                            id: snapshotTitle
                            objectName: "workspaceSnapshotTitle"
                            Layout.preferredWidth: Math.min(implicitWidth, Math.max(48, parent.width - snapshotOffline.implicitWidth - parent.spacing))
                            Layout.maximumWidth: Math.max(48, parent.width - snapshotOffline.implicitWidth - parent.spacing)
                            rightPadding: snapshotQuickActions.width
                            text: root.compactTitle
                            color: root.selected ? root.theme.contentSelectionText : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.Normal
                            elide: Text.ElideMiddle

                            HoverHandler {
                                id: snapshotTitleHover
                                enabled: root.hoverAllowed
                                cursorShape: Qt.PointingHandCursor
                            }

                            ItemQuickActions {
                                id: snapshotQuickActions
                                objectName: "workspaceSnapshotInlineSnapshotActions"
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                theme: root.theme
                                compact: root.compactMode
                                selected: root.selected
                                leadingSpace: root.inlineActionGap
                                dccApplication: appController.selected_dcc_application
                                nodeId: root.nodeId
                                revealed: snapshotTitleHover.hovered && !root.nodeLoading
                                onActionRequested: command => appController.invoke_item_action(command, root.nodeId)
                            }
                        }

                        Label {
                            id: snapshotOffline
                            objectName: "workspaceSnapshotOffline"
                            visible: root.searchKey.length > 0 && !root.fileExists && root.compactTitle.length > 0
                            Layout.preferredWidth: visible ? implicitWidth : 0
                            text: "(" + qsTr("File Offline") + ")"
                            color: root.theme.missingFile
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.Normal
                        }

                        Item {
                            Layout.fillWidth: true
                        }
                    }

                    Controls.StatusChip {
                        id: snapshotSizeBadge
                        objectName: "workspaceSnapshotSizeBadge"
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        visible: root.fileSize.length > 0
                        width: visible ? implicitWidth : 0
                        theme: root.theme
                        text: root.fileSize
                        accentColor: root.selected ? root.theme.contentSelectionText : root.theme.secondaryText
                    }
                }
                Item {
                    // The old loader briefly remains alive while compact density replaces its scene.
                    x: snapshotBody.scene.nodes[1]?.x ?? 0
                    y: snapshotBody.scene.nodes[1]?.y ?? 0
                    width: snapshotBody.scene.nodes[1]?.width ?? 0
                    height: snapshotBody.scene.nodes[1]?.height ?? 0

                    Loader {
                        id: snapshotTechnicalInfo
                        anchors.left: parent.left
                        anchors.right: snapshotDate.left
                        anchors.rightMargin: 9
                        anchors.verticalCenter: parent.verticalCenter
                        height: parent.height
                        active: root.version.length > 0 || root.revision.length > 0 || root.repository.length > 0 || root.isLatest
                        sourceComponent: Row {
                            anchors.fill: parent
                            spacing: 8
                            clip: true

                            Label {
                                visible: root.version.length > 0
                                text: root.version
                                color: root.theme.action
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.Normal
                            }
                            Label {
                                visible: root.revision.length > 0
                                text: root.revision
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                            }
                            Label {
                                visible: root.repository.length > 0
                                text: root.repository
                                color: root.repositoryColor || root.accent
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                            }
                            Label {
                                visible: root.isLatest
                                text: qsTr("Latest")
                                color: root.theme.green
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.Normal
                            }
                        }
                    }

                    Loader {
                        id: snapshotDate
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        height: parent.height
                        width: Math.min(Math.max(84, implicitWidth), Math.max(84, parent.width * 0.42))
                        active: root.timestampSimple.length > 0 || root.timestampPretty.length > 0
                        sourceComponent: Label {
                            objectName: "workspaceSnapshotDate"
                            anchors.fill: parent
                            text: snapshotDateHover.hovered ? root.timestampSimple : root.timestampPretty
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            font.weight: Font.Normal
                            horizontalAlignment: Text.AlignRight
                            verticalAlignment: Text.AlignVCenter
                            maximumLineCount: 1
                            elide: Text.ElideRight

                            HoverHandler {
                                id: snapshotDateHover
                            }

                            Controls.ToolTip {
                                visible: snapshotDateHover.hovered && root.timestampSimple.length > 0
                                theme: root.theme
                                text: root.timestampSimple
                            }
                        }
                    }
                }
                Item {
                    x: snapshotBody.scene.nodes[2]?.x ?? 0
                    y: snapshotBody.scene.nodes[2]?.y ?? 0
                    width: snapshotBody.scene.nodes[2]?.width ?? 0
                    height: snapshotBody.scene.nodes[2]?.height ?? 0

                    Label {
                        id: snapshotAuthor
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        visible: root.author.length > 0
                        text: root.author + (root.compactSubtitle.length > 0 ? ":" : "")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.Normal
                        font.italic: true
                        elide: Text.ElideRight
                        width: visible ? Math.min(Math.ceil(snapshotAuthor.implicitWidth), parent.width * 0.34) : 0
                    }
                    Label {
                        anchors.left: snapshotAuthor.right
                        anchors.leftMargin: snapshotAuthor.visible ? 5 : 0
                        anchors.right: snapshotInfo.visible ? snapshotInfo.left : parent.right
                        anchors.rightMargin: snapshotInfo.visible ? 8 : 0
                        anchors.verticalCenter: parent.verticalCenter
                        text: root.compactSubtitle
                        color: root.selected ? root.theme.contentSelectionText : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.Normal
                        elide: Text.ElideRight
                    }
                    Controls.InfoValueStrip {
                        id: snapshotInfo
                        objectName: "workspaceSnapshotInfo"
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        visible: (root.infoChips || []).length > 0
                        width: visible ? Math.min(parent.width * 0.42, implicitWidth) : 0
                        height: 16
                        theme: root.theme
                        items: root.infoChips || []
                        selected: root.selected
                        separatorText: "|"
                    }
                }
            }
        }
        Component {
            id: processBodyComponent
            Item {
                anchors.fill: parent
                Label {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    y: content.bodyParts.resultTitle.y
                    height: content.bodyParts.resultTitle.height
                    verticalAlignment: Text.AlignVCenter
                    text: root.compactTitle
                    color: root.selected ? root.theme.contentSelectionText : root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: content.bodyParts.resultTitle.fontSize
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
            }
        }

        Component {
            id: relationBodyComponent
            Item {
                anchors.fill: parent
                Label {
                    anchors.left: parent.left
                    anchors.right: relationCount.visible ? relationCount.left : parent.right
                    anchors.rightMargin: (relationCount.visible ? 7 : 0) + (hoverControls.active ? hoverControls.implicitWidth + 4 : 0)
                    y: content.bodyParts.resultTitle.y
                    height: content.bodyParts.resultTitle.height
                    verticalAlignment: Text.AlignVCenter
                    text: root.compactTitle
                    color: root.selected ? root.theme.contentSelectionText : root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: content.bodyParts.resultTitle.fontSize
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    id: relationCount
                    objectName: "workspaceRelationChildCount"
                    anchors.right: parent.right
                    anchors.rightMargin: 0
                    anchors.verticalCenter: parent.verticalCenter
                    visible: root.childCount > 0
                    text: root.childCount > 0 ? "|  " + root.childCount : ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                }
            }
        }

        Component {
            id: fileBodyComponent
            Item {
                anchors.fill: parent
                Row {
                    y: content.bodyParts.resultTitle.y
                    width: parent.width
                    height: content.bodyParts.resultTitle.height
                    spacing: 7
                    Controls.MaterialIcon {
                        name: root.fileExists ? "description" : "priority_high"
                        size: 15
                        color: root.fileExists ? root.theme.secondaryText : root.theme.missingFile
                    }
                    Label {
                        width: Math.max(70, parent.width - fileKind.implicitWidth - fileBytes.implicitWidth - 38)
                        text: root.compactTitle
                        color: root.selected ? root.theme.contentSelectionText : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                        elide: Text.ElideMiddle
                    }
                    Label {
                        id: fileKind
                        text: root.compactSubtitle
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                    Label {
                        id: fileBytes
                        text: root.fileSize
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                }
                Label {
                    y: content.bodyParts.resultFilePath.y
                    width: parent.width
                    height: content.bodyParts.resultFilePath.height
                    text: root.filePath
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    elide: Text.ElideMiddle
                }
            }
        }
    }

    Loader {
        id: hoverControls
        objectName: "workspaceItemActions"
        anchors.right: communicationControls.visible ? communicationControls.left : parent.right
        anchors.rightMargin: root.nodeType === "relation" ? root.relationCountTrailingReserve : communicationControls.visible ? (root.compactObjectCard ? 4 : 6) : 10
        // ListView reuses this delegate for sObject and compact branch rows.
        // A stable y binding avoids stale mutually-exclusive anchors after
        // nodeType/compactMode changes on a pooled delegate.
        y: Math.round((root.height - height) / 2)
        z: 8
        active: !root.configured && !root.nodeLoading && (root.hasPersistentItemControls || root.showHoverTools) && (root.itemControls || []).length > 0
        enabled: !root.presentationReadOnly
        sourceComponent: hoverControlsComponent
    }
    Component {
        id: hoverControlsComponent
        Row {
            spacing: 2
            HoverHandler {
                onHoveredChanged: {
                    if (hovered) {
                        Controls.HoverReleaseCoordinator.cancel(root);
                        root.controlHoverActive = true;
                    } else {
                        Controls.HoverReleaseCoordinator.schedule(root, 500);
                    }
                }
            }
            Repeater {
                model: root.itemControls || []
                delegate: Controls.CompactIconButton {
                    id: actionButton
                    required property var modelData
                    objectName: "workspaceItemAction_" + modelData.command
                    visible: modelData.persistent || root.showHoverTools
                    width: visible ? (root.fullObjectCard ? 30 : root.compactObjectCard ? 25 : 27) : 0
                    height: root.fullObjectCard ? 30 : root.compactObjectCard ? 25 : 27
                    theme: root.theme
                    iconName: modelData.icon
                    iconSize: root.fullObjectCard ? 18 : root.compactObjectCard ? 14 : 16
                    round: false
                    backgroundColor: modelData.success ? "transparent" : modelData.active ? root.theme.contentSelection : "transparent"
                    iconColor: modelData.success ? root.theme.green : (modelData.active || root.selected) ? root.theme.contentSelectionText : root.theme.secondaryText
                    toolTip: modelData.tip || ""
                    onClicked: {
                        if (modelData.command === "relations") {
                            root.actionMenuRequested(root.nodeId, appController.relation_menu_actions(root.nodeId), actionButton, 0, 0, true);
                        } else if (modelData.command === "repo_sync") {
                            root.actionMenuRequested(root.nodeId, appController.repo_sync_menu_actions(root.nodeId), actionButton, 0, 0, true);
                        } else {
                            appController.invoke_item_action(modelData.command, root.nodeId);
                        }
                    }
                }
            }
        }
    }

    Loader {
        id: communicationControls
        anchors.right: parent.right
        anchors.rightMargin: root.fullObjectCard ? 12 : root.compactObjectCard ? 8 : 7
        width: item ? item.implicitWidth : 0
        height: item ? item.implicitHeight : 0
        y: Math.round((root.height - height) / 2)
        active: !root.configured && (root.nodeType === "sobject" || root.nodeType === "process")
        enabled: !root.presentationReadOnly
        visible: active
        z: 8
        sourceComponent: Row {
            objectName: "workspaceCommunicationControls"
            spacing: root.fullObjectCard ? 5 : root.compactObjectCard ? 2 : 3
            opacity: root.nodeLoading ? 0.25 : root.fullObjectCard || root.compactMode || root.comments > 0 || root.tasks > 0 || root.showHoverTools ? 1 : 0
            Behavior on opacity {
                enabled: !root.transientAnimationsSuppressed && !root.theme.suppressTransientMotion
                NumberAnimation {
                    duration: theme.motionSlow
                }
            }
            HoverHandler {
                onHoveredChanged: {
                    if (hovered) {
                        Controls.HoverReleaseCoordinator.cancel(root);
                        root.controlHoverActive = true;
                    } else {
                        Controls.HoverReleaseCoordinator.schedule(root, 500);
                    }
                }
            }
            Controls.ItemCountActionButton {
                id: taskCountButton
                objectName: "workspaceTaskCountButton"
                width: root.compactObjectCard ? 28 : implicitWidth
                height: root.compactObjectCard ? 28 : implicitHeight
                theme: root.theme
                iconName: "calendar_check"
                count: root.tasks
                activeColor: root.nodeType === "sobject" ? root.theme.secondaryText : root.theme.action
                badgeColor: root.tasksUpdated ? root.theme.error : activeColor
                toolTipsAllowed: root.hoverAllowed
                toolTip: qsTr("Open Tasks (") + root.tasks + ")"
                onClicked: root.processCountMenuRequested(root.nodeId, "tasks", taskCountButton)
            }
            Controls.ItemCountActionButton {
                id: noteCountButton
                objectName: "workspaceNoteCountButton"
                width: root.compactObjectCard ? 28 : implicitWidth
                height: root.compactObjectCard ? 28 : implicitHeight
                theme: root.theme
                iconName: "comment"
                count: root.comments
                activeColor: root.nodeType === "sobject" ? root.theme.secondaryText : root.theme.error
                badgeColor: root.commentsUpdated ? root.theme.error : activeColor
                toolTipsAllowed: root.hoverAllowed
                toolTip: qsTr("Open Notes (") + root.comments + ")"
                onClicked: root.processCountMenuRequested(root.nodeId, "notes", noteCountButton)
            }
        }
    }

    Controls.MaterialRipple {
        id: itemRipple
        theme: root.theme
        z: 3
        anchors.margins: root.objectCard ? (root.fullObjectCard ? 4 : 3) : root.snapshotCard ? 2 : 1
        anchors.leftMargin: root.indentedSurface ? root.surfaceLeft + (root.objectCard ? (root.fullObjectCard ? 4 : 3) : root.snapshotCard ? 2 : 1) : 1
        shapeRadius: root.objectCard ? (root.fullObjectCard ? root.theme.surfaceRadius : root.theme.itemRadius) : root.snapshotCard ? root.theme.snapshotRadius : 8
        color: root.theme.rippleStrong
    }
    MouseArea {
        id: itemMouse
        enabled: !root.presentationReadOnly
        anchors.fill: parent
        z: 2
        hoverEnabled: true
        onContainsMouseChanged: {
            if (!containsMouse && root.transientAnimationsSuppressed)
                root.transientAnimationsSuppressed = false;
        }
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: mouse => itemRipple.burst(mouse.x, mouse.y)
        onClicked: function (mouse) {
            const view = root.ListView.view;
            if (view)
                view.forceActiveFocus();
            if (root.isGroup) {
                if (mouse.button === Qt.LeftButton && root.hasChildren)
                    root.toggleExpandedPreservingScroll(mouse.modifiers);
                return;
            }

            root.selectedRequested(root.nodeId, root.searchKey, root.nodeType, mouse.modifiers, mouse.button === Qt.RightButton && root.selected);
            if (mouse.button === Qt.RightButton) {
                root.actionMenuRequested(root.nodeId, appController.item_menu_actions(root.nodeId), root, mouse.x, mouse.y, false);
            } else if (mouse.button === Qt.MiddleButton) {
                appController.invoke_item_action("new_tab", root.nodeId);
            }
        }
        onDoubleClicked: function (mouse) {
            if (root.isGroup)
                return;
            if (mouse.button !== Qt.LeftButton)
                return;
            if (root.nodeType === "snapshot") {
                appController.invoke_item_action("open", root.nodeId);
                return;
            }
            if (appController.handle_item_double_click(root.nodeId, mouse.modifiers))
                return;
            if (root.hasChildren && !root.nodeLoading)
                root.toggleExpandedPreservingScroll(mouse.modifiers);
            else if (root.nodeType === "file")
                appController.invoke_item_action("open", root.nodeId);
        }
    }

    WorkspaceFileDropTarget {
        id: fileDropTarget
        anchors.fill: parent
        theme: root.theme
        controller: appController
        nodeId: root.nodeId
        nodeType: root.nodeType
        nodeTitle: root.title
        targetProcess: root.process
    }
}
