pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

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
    readonly property url dragImageSource:
        String(root.previewUrl).indexOf("pending-preview:") === 0
            ? "" : root.previewUrl
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

    signal selectedRequested(
        string nodeId,
        string searchKey,
        string nodeType,
        int modifiers,
        bool preserveSelection
    )
    signal actionMenuRequested(
        string nodeId,
        var actions,
        var anchorItem,
        real localX,
        real localY,
        bool below
    )

    function requestPreviewIfNeeded() {
        if (root.presentationActive && !root.viewPooled && root.largeItem
                && !root.previewRequested && !root.previewUrl)
            appController.request_item_preview(root.nodeId)
    }

    onPreviewUrlChanged: requestPreviewIfNeeded()
    onPreviewRequestedChanged: requestPreviewIfNeeded()
    signal processCountMenuRequested(
        string nodeId,
        string panel,
        var anchorItem
    )

    function armTransientAnimations() {
        root.transientAnimationsSuppressed = root.viewPooled
            || itemMouse.containsMouse
    }

    function cancelTransientAnimationArm() {
        root.transientAnimationsSuppressed = true
    }

    function releaseControlHover() {
        if (!root.menuVisible)
            root.controlHoverActive = false
    }

    readonly property real branchIndentStep: 24
    readonly property real inlineActionGap: root.compactMode ? 6 : 8
    readonly property real indent: depth * branchIndentStep
    readonly property bool isGroup: nodeType === "group"
    readonly property bool largeItem: nodeType === "sobject" || nodeType === "snapshot"
    readonly property bool objectCard: root.nodeType === "sobject"
    readonly property bool snapshotCard: root.nodeType === "snapshot"
    readonly property bool branchRow: root.nodeType === "process"
        || root.nodeType === "relation"
    readonly property bool indentedSurface: root.objectCard
        || root.snapshotCard || root.branchRow
    readonly property real surfaceLeft: root.indentedSurface
        ? root.indent + (root.branchRow ? 32 : 0) : 0
    readonly property bool compactBranchItem:
        nodeType === "process" || nodeType === "relation"
        || root.isGroup
    readonly property bool relationBranchItem: nodeType === "relation"
    readonly property string compactTitle:
        String(title || "").replace(/[\r\n\t]+/g, " ")
            .replace(/\s{2,}/g, " ").trim()
    readonly property string compactSubtitle: {
        const value = String(subtitle || "").replace(/[\r\n\t]+/g, " ")
            .replace(/\s{2,}/g, " ").trim()
        if (!appController.description_limit_enabled
                || value.length <= appController.description_limit)
            return value
        return value.slice(0, appController.description_limit).trim() + "…"
    }
    readonly property bool fullObjectCard:
        root.objectCard && !root.compactMode
    readonly property bool compactObjectCard:
        root.objectCard && root.compactMode
    readonly property real relationCountTrailingReserve:
        root.nodeType === "relation" && root.childCount > 0
            ? 13 + Math.ceil(relationCountMetrics.advanceWidth) : 7
    readonly property real contentTrailingReserve: {
        const communicationWidth = communicationControls.visible
            ? communicationControls.implicitWidth : 0
        if (nodeType === "sobject" || nodeType === "process") {
            const hoverWidth = hoverControls.active
                ? hoverControls.implicitWidth + 4 : 0
            if (root.fullObjectCard)
                return Math.max(170, communicationWidth + hoverWidth + 22)
            return Math.max(
                compactMode ? 76 : 84,
                communicationWidth + hoverWidth + 12
            )
        }
        return Math.max(112, hoverControls.implicitWidth + 8)
    }

    readonly property string typeIcon: root.isGroup
        ? (root.expanded ? "folder-open" : "folder")
        : nodeType === "process"
        ? (subtitle === "hierarchy" ? "code_branch" : "circle")
        : nodeType === "snapshot"
            ? (!searchKey && isVersionless
                ? "exclamation_circle" : isMultiple ? "folder" : "file")
        : nodeType === "file"
            ? (fileExists ? "file" : "exclamation_circle")
        : nodeType === "relation" ? "stream" : "sobject"
    readonly property bool hoverAllowed: {
        const view = root.ListView.view
        return !view || !view.interactionMoving
    }
    readonly property bool interactiveHovered:
        root.hoverAllowed && itemMouse.containsMouse
    readonly property bool menuVisible: root.externalMenuVisible
    readonly property bool showHoverTools: menuVisible || (
        !root.transientAnimationsSuppressed
        && root.hoverAllowed
        && (itemMouse.containsMouse || controlHoverActive)
    )
    readonly property bool hasPersistentItemControls: {
        const controls = root.itemControls || []
        for (let index = 0; index < controls.length; ++index) {
            if (controls[index].persistent)
                return true
        }
        return false
    }
    x: ListView.view ? 6 : 0
    width: ListView.view ? Math.max(0, ListView.view.width - 12) : 320
    readonly property bool versionRowHidden: hideVersionSnapshots
        && nodeType === "snapshot" && !isVersionless
    visible: !versionRowHidden
    // Card insets reserve room for elevation inside the delegate. Keep the
    // delegate clipped so malformed server text cannot paint over its neighbor.
    clip: true
    height: versionRowHidden ? 0
        : root.isGroup ? 40
        : relationBranchItem ? 38
        : compactBranchItem ? 32
        : compactMode
        ? (nodeType === "sobject" ? 64
            : nodeType === "snapshot" ? 56 : 42)
        : nodeType === "sobject" ? 100
        : nodeType === "snapshot" ? 84
        : 49
    Drag.active: root.itemDragActive
    Drag.dragType: Drag.Automatic
    Drag.supportedActions: Qt.CopyAction
    Drag.mimeData: root.dragMimeData
    Drag.imageSource: root.dragImageSource
    Drag.hotSpot.x: Math.min(width / 2, 42 + root.indent)
    Drag.hotSpot.y: height / 2
    opacity: hierarchyReveal.progress

    Component.onCompleted: {
        root.requestPreviewIfNeeded()
        root.armTransientAnimations()
    }
    ListView.onPooled: {
        root.cancelTransientAnimationArm()
        root.viewPooled = true
        root.transientAnimationsSuppressed = true
        Controls.HoverReleaseCoordinator.cancel(root)
        root.controlHoverActive = false
        root.itemDragActive = false
        root.dragMimeData = ({})
        fileDropTarget.reset()
    }
    ListView.onReused: {
        root.viewPooled = false
        root.transientAnimationsSuppressed = true
        root.controlHoverActive = false
        root.itemDragActive = false
        root.dragMimeData = ({})
        fileDropTarget.reset()
        root.requestPreviewIfNeeded()
        root.armTransientAnimations()
    }
    onPresentationActiveChanged: {
        root.requestPreviewIfNeeded()
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
        enabled: root.nodeType === "sobject"
            || root.nodeType === "snapshot"
            || root.nodeType === "file"
        onActiveChanged: {
            root.itemDragActive = active
            if (active)
                root.dragMimeData =
                    appController.item_drag_payload(root.nodeId)
            else
                root.dragMimeData = ({})
        }
    }

    function toggleExpandedPreservingScroll(modifiers) {
        const view = root.ListView.view
        const recursive = Boolean(modifiers & Qt.ShiftModifier)
        if (view && view.toggleResultNodePreservingScroll)
            view.toggleResultNodePreservingScroll(
                root.nodeId, recursive, !root.expanded
            )
        else
            appController.toggle_result_node_recursive(
                root.nodeId, recursive
            )
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
        railVisible: root.nodeType === "sobject"
            || root.nodeType === "relation"
        railX: root.objectCard || root.relationBranchItem ? inset + 3 : 36
        railWidth: root.objectCard
            ? (root.fullObjectCard ? 4 : 3) : 3
        railTopMargin: root.objectCard
            ? (root.fullObjectCard ? 12 : 8) : 5
        railBottomMargin: railTopMargin
        railOpacity: root.nodeType === "file" ? 0.24 : 1
        inset: root.objectCard ? (root.fullObjectCard ? 4 : 3)
            : root.snapshotCard ? 2 : 1
        cornerRadius: root.objectCard
            ? (root.fullObjectCard
                ? root.theme.surfaceRadius : root.theme.itemRadius)
            : root.snapshotCard ? root.theme.snapshotRadius : 8
        borderWidth: root.objectCard ? 1 : 0
        borderColor: root.theme.outlineVariant
        elevated: root.objectCard
        shadowVerticalOffset: root.fullObjectCard ? 3 : 2
        separatorVisible: false
        normalColor: root.objectCard ? root.theme.surfaceContainerLow
            : root.isGroup ? root.theme.panelRaised
            : root.theme.panel
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
        x: root.snapshotCard ? root.indent + 9
            : root.branchRow ? root.indent + 2
            : root.indent + (root.fullObjectCard ? 24
                : root.compactObjectCard ? 12 : 0)
        width: root.fullObjectCard ? 36
            : root.compactObjectCard ? 30
            : root.compactBranchItem ? 28 : 30
        height: parent.height
        z: 4
        theme: root.theme
        identity: root.nodeId
        expanded: root.expanded && (!root.ListView.view
            || root.ListView.view.treeCollapseOwnerId !== root.nodeId)
        hasChildren: root.hasChildren
        loading: root.nodeLoading
        iconSize: root.fullObjectCard ? 18
            : root.compactObjectCard ? 14
            : root.compactBranchItem ? 13 : 15
        indicatorSize: root.fullObjectCard ? 24
            : root.compactObjectCard ? 20 : 18
        onActivated: function(modifiers) {
            root.toggleExpandedPreservingScroll(modifiers)
        }
    }

    Item {
        id: preview
        objectName: "workspaceItemPreview"
        x: root.objectCard ? disclosureArea.x + disclosureArea.width
                + (root.fullObjectCard ? 18 : 8)
            : root.snapshotCard
                ? root.indent + (root.hasChildren ? 45 : 14)
                : root.branchRow ? root.indent + 45
                : 45 + root.indent
        anchors.verticalCenter: parent.verticalCenter
        width: root.fullObjectCard ? 68
            : root.compactObjectCard ? 42
            : root.compactBranchItem ? 24
            : root.compactMode
            ? (root.largeItem ? 38 : 24) : root.largeItem ? 58 : 28
        height: width
        z: root.interactiveHovered && root.largeItem ? 6 : 1
        scale: !root.fullObjectCard && !root.compactMode
            && root.interactiveHovered && root.largeItem ? 1.15 : 1
        Behavior on scale {
            enabled: !root.theme.suppressTransientMotion
            NumberAnimation { duration: theme.hoverMotionFast; easing.type: Easing.OutCubic }
        }
        visible: root.nodeType !== "file"
        opacity: root.nodeLoading ? 0.42 : 1
        Behavior on opacity {
            enabled: !root.theme.suppressTransientMotion
            NumberAnimation { duration: theme.motionMedium; easing.type: Easing.OutCubic }
        }
        Loader {
            anchors.fill: parent
            sourceComponent: root.largeItem
                ? previewImageComponent
                : root.nodeType === "process" || root.nodeType === "relation"
                    || root.isGroup
                    ? previewIconComponent : null
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
                cornerRadius: root.nodeType === "sobject"
                    ? preview.width / 2 : 8
                selected: root.selected
                previewSize: preview.width
                fallbackIcon: root.typeIcon
                fallbackText: root.nodeType === "sobject"
                    ? appController.get_acronym(root.compactTitle) : ""
                animateAppearance:
                    !root.previewRevealed && root.hoverAllowed
                selectedBorderColor: root.theme.contentSelectionText
                onImageReady: {
                    if (!root.previewRevealed)
                        appController.mark_item_preview_revealed(root.nodeId)
                }
            }
        }
        Component {
            id: previewIconComponent
            Controls.MaterialIcon {
                anchors.centerIn: parent
                name: root.typeIcon
                size: root.nodeType === "process"
                    ? (root.subtitle === "hierarchy" ? 16 : 13)
                    : root.compactBranchItem ? 15 : 21
                color: root.accent
                forceSolid: root.nodeType === "process"
            }
        }
    }

    Item {
        id: content
        anchors.left: preview.visible ? preview.right : parent.left
        z: 4
        anchors.leftMargin: preview.visible
            ? (root.fullObjectCard ? 26
                : root.compactObjectCard ? 10
                : root.snapshotCard ? 12 : 9)
            : 47 + root.indent
        anchors.right: parent.right
        anchors.rightMargin: root.snapshotCard ? 14 : 9
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        opacity: root.nodeLoading ? 0.42 : 1
        Behavior on opacity {
            enabled: !root.theme.suppressTransientMotion
            NumberAnimation { duration: theme.motionMedium; easing.type: Easing.OutCubic }
        }

        Loader {
            anchors.fill: parent
            sourceComponent: root.isGroup ? groupBodyComponent
                : root.nodeType === "relation" ? relationBodyComponent
                : root.nodeType === "sobject"
                ? objectBodyComponent
                : root.compactMode ? compactBodyComponent
                : root.nodeType === "snapshot"
                    ? snapshotBodyComponent
                    : root.nodeType === "process"
                        ? processBodyComponent
                        : root.nodeType === "relation"
                            ? relationBodyComponent
                            : fileBodyComponent
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
                anchors.right: compactSnapshotSize.visible
                    ? compactSnapshotSize.left : parent.right
                anchors.rightMargin: compactSnapshotSize.visible
                    ? 7 : root.contentTrailingReserve
                anchors.verticalCenter: parent.verticalCenter
                text: root.compactTitle
                color: root.selected
                    ? root.theme.contentSelectionText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: root.nodeType === "process"
                    ? Controls.Typography.body : Controls.Typography.label
                font.weight: Font.DemiBold
                maximumLineCount: 1
                wrapMode: Text.NoWrap
                elide: Text.ElideRight
                rightPadding: root.nodeType === "snapshot"
                    ? compactQuickActions.width : 0

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
                    onActionRequested: command =>
                        appController.invoke_item_action(command, root.nodeId)
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
                visible: root.nodeType === "snapshot"
                    && root.fileSize.length > 0
                width: visible ? implicitWidth : 0
                theme: root.theme
                text: root.fileSize
                accentColor: root.selected
                    ? root.theme.contentSelectionText : root.theme.secondaryText
            }
          }
        }

        Component {
          id: objectBodyComponent
          Item {
            anchors.fill: parent
            Column {
              id: objectBody
              objectName: "workspaceObjectBody"
              anchors.left: parent.left
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              spacing: root.compactObjectCard ? 1 : 3
              Label {
                id: objectTitle
                objectName: "workspaceObjectTitle"
                readonly property real titleWidth:
                    Math.ceil(objectTitleMetrics.advanceWidth)
                readonly property bool actionsFit:
                    parent.width >= titleWidth + objectQuickActions.width
                width: Math.min(
                    parent.width,
                    titleWidth
                        + (objectQuickActions.revealed
                            ? objectQuickActions.width : 0)
                )
                rightPadding: objectQuickActions.revealed
                    ? objectQuickActions.width : 0
                text: root.compactTitle
                color: root.selected
                    ? root.theme.contentSelectionText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: root.compactObjectCard ? 13 : 15
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
                  revealed: objectTitleHover.hovered
                      && objectTitle.actionsFit && !root.nodeLoading
                  onActionRequested: command =>
                      appController.invoke_item_action(command, root.nodeId)
                }
              }
              Label {
                objectName: "workspaceObjectSubtitle"
                width: Math.max(48, parent.width - root.contentTrailingReserve)
                visible: root.compactSubtitle.length > 0
                text: root.compactSubtitle
                color: root.selected
                    ? root.theme.contentSelectionText
                    : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: root.compactObjectCard
                    ? Controls.Typography.label : Controls.Typography.body
                maximumLineCount: 1
                wrapMode: Text.NoWrap
                elide: Text.ElideRight
              }
              Row {
                objectName: "workspaceObjectMetadata"
                width: Math.max(48, parent.width - root.contentTrailingReserve)
                height: 24
                spacing: root.compactObjectCard ? 4 : 6
                clip: true
                Controls.CompletionStrip {
                  height: parent.height
                  theme: root.theme
                  items: root.progressItems || []
                  maximumItems: root.compactObjectCard ? 1 : 0
                  onCompletionRequested: searchType => {
                    if (root.controller)
                      root.controller.open_completion(root.nodeId, searchType)
                  }
                }
                Label {
                  visible: (root.progressItems || []).length > 0
                      && (root.infoChips || []).length > 0
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
            anchors.fill: parent

            Column {
              anchors.left: parent.left
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              spacing: 0

              Item {
                width: parent.width
                height: 24

                RowLayout {
                  anchors.left: parent.left
                  anchors.right: snapshotSizeBadge.left
                  anchors.rightMargin: 8
                  height: parent.height
                  spacing: 5

                    Label {
                      id: snapshotTitle
                      objectName: "workspaceSnapshotTitle"
                      Layout.preferredWidth: Math.min(
                        implicitWidth,
                        Math.max(
                          48,
                          parent.width - snapshotOffline.implicitWidth
                            - parent.spacing
                        )
                      )
                      Layout.maximumWidth: Math.max(
                        48,
                        parent.width - snapshotOffline.implicitWidth
                          - parent.spacing
                      )
                      rightPadding: snapshotQuickActions.width
                      text: root.compactTitle
                      color: root.selected
                        ? root.theme.contentSelectionText
                        : root.theme.primaryText
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
                        revealed: snapshotTitleHover.hovered
                            && !root.nodeLoading
                        onActionRequested: command =>
                            appController.invoke_item_action(
                                command, root.nodeId
                            )
                      }
                    }

                    Label {
                      id: snapshotOffline
                      visible: !root.fileExists
                        && root.compactTitle.length > 0
                      Layout.preferredWidth: visible ? implicitWidth : 0
                      text: "(" + qsTr("File Offline") + ")"
                      color: root.theme.missingFile
                      font.family: root.theme.fontFamily
                      font.pointSize: Controls.Typography.label
                      font.weight: Font.Normal
                    }

                    Item { Layout.fillWidth: true }
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
                  accentColor: root.selected
                    ? root.theme.contentSelectionText
                    : root.theme.secondaryText
                }
              }

              Item {
                width: parent.width
                height: 24

                Row {
                  id: snapshotTechnicalInfo
                  anchors.left: parent.left
                  anchors.right: snapshotDate.left
                  anchors.rightMargin: 9
                  anchors.verticalCenter: parent.verticalCenter
                  height: parent.height
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

                Label {
                  id: snapshotDate
                  objectName: "workspaceSnapshotDate"
                  anchors.right: parent.right
                  anchors.verticalCenter: parent.verticalCenter
                  width: Math.min(
                    Math.max(84, implicitWidth),
                    Math.max(84, parent.width * 0.42)
                  )
                  text: snapshotDateHover.hovered
                    ? root.timestampSimple : root.timestampPretty
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
                    theme: root.theme
                    visible: snapshotDateHover.hovered
                      && root.timestampSimple.length > 0
                    text: root.timestampSimple
                  }
                }
              }

              Item {
                width: parent.width
                height: 20

                TextMetrics {
                  id: snapshotAuthorMetrics
                  text: root.author
                    + (root.compactSubtitle.length > 0 ? ":" : "")
                  font.family: root.theme.fontFamily
                  font.pointSize: Controls.Typography.label
                  font.weight: Font.Normal
                  font.italic: true
                }

                Label {
                  id: snapshotAuthor
                  anchors.left: parent.left
                  anchors.verticalCenter: parent.verticalCenter
                  visible: root.author.length > 0
                  text: root.author
                    + (root.compactSubtitle.length > 0 ? ":" : "")
                  color: root.theme.secondaryText
                  font.family: root.theme.fontFamily
                  font.pointSize: Controls.Typography.label
                  font.weight: Font.Normal
                  font.italic: true
                  elide: Text.ElideRight
                  width: visible
                    ? Math.min(
                        Math.ceil(snapshotAuthorMetrics.advanceWidth),
                        parent.width * 0.34
                      ) : 0
                }
                Label {
                  anchors.left: snapshotAuthor.right
                  anchors.leftMargin: snapshotAuthor.visible ? 5 : 0
                  anchors.right: snapshotInfo.visible
                    ? snapshotInfo.left : parent.right
                  anchors.rightMargin: snapshotInfo.visible ? 8 : 0
                  anchors.verticalCenter: parent.verticalCenter
                  text: root.compactSubtitle
                  color: root.selected
                    ? root.theme.contentSelectionText : root.theme.primaryText
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
                  width: visible
                    ? Math.min(parent.width * 0.42, implicitWidth) : 0
                  height: 16
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
          id: processBodyComponent
          Item {
            anchors.fill: parent
            Label {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                text: root.compactTitle
                color: root.selected
                    ? root.theme.contentSelectionText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
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
                anchors.right: relationCount.visible
                    ? relationCount.left : parent.right
                anchors.rightMargin: (relationCount.visible ? 7 : 0)
                    + (hoverControls.active
                        ? hoverControls.implicitWidth + 4 : 0)
                anchors.verticalCenter: parent.verticalCenter
                text: root.compactTitle
                color: root.selected
                    ? root.theme.contentSelectionText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
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
          Column {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Row {
                width: parent.width
                spacing: 7
                Controls.MaterialIcon { name: root.fileExists ? "description" : "priority_high"; size: 15; color: root.fileExists ? root.theme.secondaryText : root.theme.missingFile }
                Label {
                    width: Math.max(70, parent.width - fileKind.implicitWidth - fileBytes.implicitWidth - 38)
                    text: root.compactTitle
                    color: root.selected
                        ? root.theme.contentSelectionText
                        : root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    font.weight: Font.DemiBold
                    elide: Text.ElideMiddle
                }
                Label { id: fileKind; text: root.compactSubtitle; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.caption }
                Label { id: fileBytes; text: root.fileSize; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Controls.Typography.caption }
            }
            Label {
                width: parent.width
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
        anchors.right: communicationControls.visible
            ? communicationControls.left : parent.right
        anchors.rightMargin: root.nodeType === "relation"
                ? root.relationCountTrailingReserve
                : communicationControls.visible
                    ? (root.compactObjectCard ? 4 : 6) : 10
        // ListView reuses this delegate for sObject and compact branch rows.
        // A stable y binding avoids stale mutually-exclusive anchors after
        // nodeType/compactMode changes on a pooled delegate.
        y: Math.round((root.height - height) / 2)
        z: 8
        active: !root.nodeLoading
            && (root.hasPersistentItemControls
                || root.showHoverTools)
            && (root.itemControls || []).length > 0
        sourceComponent: hoverControlsComponent
    }
    Component {
      id: hoverControlsComponent
      Row {
        spacing: 2
        HoverHandler {
            onHoveredChanged: {
                if (hovered) {
                    Controls.HoverReleaseCoordinator.cancel(root)
                    root.controlHoverActive = true
                } else {
                    Controls.HoverReleaseCoordinator.schedule(root, 500)
                }
            }
        }
        Repeater {
            model: root.itemControls || []
            delegate: Controls.CompactIconButton {
                id: actionButton
                required property var modelData
                objectName: "workspaceItemAction_" + modelData.command
                visible: modelData.persistent
                    || root.showHoverTools
                width: visible ? (root.fullObjectCard ? 30
                    : root.compactObjectCard ? 25 : 27) : 0
                height: root.fullObjectCard ? 30
                    : root.compactObjectCard ? 25 : 27
                theme: root.theme
                iconName: modelData.icon
                iconSize: root.fullObjectCard ? 18
                    : root.compactObjectCard ? 14 : 16
                round: true
                backgroundColor: modelData.success ? "transparent"
                    : modelData.active
                        ? root.theme.contentSelection : "transparent"
                iconColor: modelData.success ? root.theme.green
                    : (modelData.active || root.selected)
                        ? root.theme.contentSelectionText
                        : root.theme.secondaryText
                toolTip: modelData.tip || ""
                onClicked: {
                    if (modelData.command === "relations") {
                        root.actionMenuRequested(
                            root.nodeId,
                            appController.relation_menu_actions(root.nodeId),
                            actionButton, 0, 0, true
                        )
                    } else if (modelData.command === "repo_sync") {
                        root.actionMenuRequested(
                            root.nodeId,
                            appController.repo_sync_menu_actions(root.nodeId),
                            actionButton, 0, 0, true
                        )
                    } else {
                        appController.invoke_item_action(
                            modelData.command, root.nodeId
                        )
                    }
                }
            }
        }
      }
    }

    Loader {
        id: communicationControls
        anchors.right: parent.right
        anchors.rightMargin: root.fullObjectCard ? 12
            : root.compactObjectCard ? 8 : 7
        width: item ? item.implicitWidth : 0
        height: item ? item.implicitHeight : 0
        y: Math.round((root.height - height) / 2)
        active: root.nodeType === "sobject" || root.nodeType === "process"
        visible: active
        z: 8
        sourceComponent: Row {
            objectName: "workspaceCommunicationControls"
            spacing: root.fullObjectCard ? 5
                : root.compactObjectCard ? 2 : 3
            opacity: root.nodeLoading ? 0.25
                : root.fullObjectCard || root.compactMode
                    || root.comments > 0 || root.tasks > 0
                    || root.showHoverTools ? 1 : 0
            Behavior on opacity {
                enabled: !root.transientAnimationsSuppressed
                    && !root.theme.suppressTransientMotion
                NumberAnimation { duration: theme.motionSlow }
            }
            HoverHandler {
                onHoveredChanged: {
                    if (hovered) {
                        Controls.HoverReleaseCoordinator.cancel(root)
                        root.controlHoverActive = true
                    } else {
                        Controls.HoverReleaseCoordinator.schedule(root, 500)
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
                activeColor: root.nodeType === "sobject"
                    ? root.theme.secondaryText : root.theme.action
                badgeColor: root.tasksUpdated
                    ? root.theme.error : activeColor
                toolTipsAllowed: root.hoverAllowed
                toolTip: qsTr("Open Tasks (") + root.tasks + ")"
                onClicked: root.processCountMenuRequested(
                    root.nodeId, "tasks", taskCountButton
                )
            }
            Controls.ItemCountActionButton {
                id: noteCountButton
                objectName: "workspaceNoteCountButton"
                width: root.compactObjectCard ? 28 : implicitWidth
                height: root.compactObjectCard ? 28 : implicitHeight
                theme: root.theme
                iconName: "comment"
                count: root.comments
                activeColor: root.nodeType === "sobject"
                    ? root.theme.secondaryText : root.theme.error
                badgeColor: root.commentsUpdated
                    ? root.theme.error : activeColor
                toolTipsAllowed: root.hoverAllowed
                toolTip: qsTr("Open Notes (") + root.comments + ")"
                onClicked: root.processCountMenuRequested(
                    root.nodeId, "notes", noteCountButton
                )
            }
        }
    }

    Controls.MaterialRipple {
        id: itemRipple
        theme: root.theme
        z: 3
        anchors.margins: root.objectCard
            ? (root.fullObjectCard ? 4 : 3)
            : root.snapshotCard ? 2 : 1
        anchors.leftMargin: root.indentedSurface
            ? root.surfaceLeft + (root.objectCard
                ? (root.fullObjectCard ? 4 : 3)
                : root.snapshotCard ? 2 : 1)
            : 1
        shapeRadius: root.objectCard
            ? (root.fullObjectCard
                ? root.theme.surfaceRadius : root.theme.itemRadius)
            : root.snapshotCard ? root.theme.snapshotRadius : 8
        color: root.theme.rippleStrong
    }
    MouseArea {
        id: itemMouse
        anchors.fill: parent
        z: 2
        hoverEnabled: true
        onContainsMouseChanged: {
            if (!containsMouse && root.transientAnimationsSuppressed)
                root.transientAnimationsSuppressed = false
        }
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: mouse => itemRipple.burst(mouse.x, mouse.y)
        onClicked: function(mouse) {
            const view = root.ListView.view
            if (view)
                view.forceActiveFocus()
            if (root.isGroup) {
                if (mouse.button === Qt.LeftButton && root.hasChildren)
                    root.toggleExpandedPreservingScroll(mouse.modifiers)
                return
            }

            root.selectedRequested(
                root.nodeId,
                root.searchKey,
                root.nodeType,
                mouse.modifiers,
                mouse.button === Qt.RightButton && root.selected
            )
            if (mouse.button === Qt.RightButton) {
                root.actionMenuRequested(
                    root.nodeId,
                    appController.item_menu_actions(root.nodeId),
                    root, mouse.x, mouse.y, false
                )
            } else if (mouse.button === Qt.MiddleButton) {
                appController.invoke_item_action("new_tab", root.nodeId)
            }
        }
        onDoubleClicked: function(mouse) {
            if (root.isGroup)
                return
            if (mouse.button !== Qt.LeftButton)
                return
            if (root.nodeType === "snapshot") {
                appController.invoke_item_action("open", root.nodeId)
                return
            }
            if (appController.handle_item_double_click(
                    root.nodeId, mouse.modifiers))
                return
            if (root.hasChildren && !root.nodeLoading)
                root.toggleExpandedPreservingScroll(mouse.modifiers)
            else if (root.nodeType === "file")
                appController.invoke_item_action("open", root.nodeId)
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
