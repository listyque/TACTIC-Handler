import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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
    required property string revision
    required property string repository
    required property string repositoryColor
    required property string previewUrl
    required property bool previewRevealed
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
    property bool selected: false
    property bool compactMode: false
    property bool hideVersionSnapshots: false
    property bool controlHoverActive: false
    property bool externalMenuVisible: false
    property bool transientAnimationsSuppressed: true
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

    readonly property real indent: depth * 18
    readonly property bool largeItem: nodeType === "sobject" || nodeType === "snapshot"
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
    readonly property bool stackedObjectActions:
        root.nodeType === "sobject" && !root.compactMode
    readonly property real relationActionReserve: {
        if (root.nodeType !== "relation")
            return 0
        const count = root.itemControls ? root.itemControls.length : 0
        return count > 0 ? count * 27 + Math.max(0, count - 1) * 2 + 10 : 0
    }
    readonly property real contentTrailingReserve: {
        const communicationWidth = communicationControls.visible
            ? communicationControls.implicitWidth : 0
        if (nodeType === "sobject" || nodeType === "process") {
            const hoverWidth = hoverControls.active
                ? hoverControls.implicitWidth + 4 : 0
            if (root.stackedObjectActions)
                return Math.max(
                    84,
                    communicationWidth + 12,
                    hoverWidth + 12
                )
            return Math.max(
                compactMode ? 76 : 84,
                communicationWidth + hoverWidth + 12
            )
        }
        return Math.max(112, hoverControls.implicitWidth + 8)
    }
    readonly property string typeIcon: nodeType === "process"
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
    // Search rows intentionally stay compact. Malformed or multiline server
    // metadata must never paint over the next tree item.
    clip: true
    height: versionRowHidden ? 0 : compactMode
        ? (nodeType === "sobject" || nodeType === "snapshot" ? 52 : 42)
        : nodeType === "sobject" ? 76
        : nodeType === "snapshot" ? 76
        : nodeType === "process" || nodeType === "relation" ? 47 : 49
    Drag.active: itemDragHandler.active
    Drag.dragType: Drag.Automatic
    Drag.supportedActions: Qt.CopyAction
    Drag.mimeData: root.dragMimeData
    Drag.imageSource: root.previewUrl
    Drag.hotSpot.x: Math.min(width / 2, 42 + root.indent)
    Drag.hotSpot.y: height / 2

    Component.onCompleted: {
        if (root.largeItem)
            appController.request_item_preview(root.nodeId)
        transientAnimationArm.restart()
    }
    ListView.onPooled: {
        transientAnimationArm.stop()
        root.transientAnimationsSuppressed = true
        controlHoverRelease.stop()
        root.controlHoverActive = false
        root.dragMimeData = ({})
        fileDrop.activeZone = -1
    }
    ListView.onReused: {
        root.transientAnimationsSuppressed = true
        root.controlHoverActive = false
        root.dragMimeData = ({})
        fileDrop.activeZone = -1
        if (root.largeItem)
            appController.request_item_preview(root.nodeId)
        transientAnimationArm.restart()
    }

    Timer {
        id: transientAnimationArm
        interval: 0
        onTriggered: {
            if (!itemMouse.containsMouse)
                root.transientAnimationsSuppressed = false
        }
    }

    DragHandler {
        id: itemDragHandler
        target: null
        acceptedButtons: Qt.LeftButton
        enabled: root.nodeType === "sobject"
            || root.nodeType === "snapshot"
            || root.nodeType === "file"
        onActiveChanged: {
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
            view.toggleResultNodePreservingScroll(root.nodeId, recursive)
        else
            appController.toggle_result_node_recursive(
                root.nodeId, recursive
            )
    }

    Timer {
        id: controlHoverRelease
        interval: 500
        onTriggered: {
            if (!root.menuVisible)
                root.controlHoverActive = false
        }
    }

    ItemSurface {
        anchors.fill: parent
        theme: root.theme
        selected: root.selected
        // Every workspace entity uses the same quiet content selection.
        // Process, snapshot, file and relation rows must not fall back to the
        // brighter control/tab selection color.
        selectedColor: root.theme.contentSelection
        hovered: root.interactiveHovered || root.menuVisible
        pressed: itemMouse.pressed
        accent: root.nodeType === "snapshot" ? Qt.darker(root.accent, 1.25) : root.accent
        railX: 36 + root.indent
        railOpacity: root.nodeType === "file" ? 0.24 : 1
        inset: 1
        cornerRadius: 8
        separatorVisible: false
        normalColor: root.index % 2 === 0
            ? root.theme.panel
            : root.theme.row
    }

    Item {
        x: root.indent
        width: 36
        height: parent.height
        z: 4
        Rectangle {
            anchors.centerIn: parent
            width: 30
            height: 30
            radius: 15
            color: root.selected ? root.theme.action : root.theme.primaryText
            opacity: disclosureMouse.pressed ? 0.08
                : root.hoverAllowed && disclosureMouse.containsMouse ? 0.04 : 0
            Behavior on opacity {
                NumberAnimation { duration: 110; easing.type: Easing.OutCubic }
            }
        }
        Item {
            id: disclosureButton
            anchors.centerIn: parent
            width: 30
            height: 30
            MaterialIcon {
                anchors.centerIn: parent
                name: root.expanded ? "keyboard_arrow_down" : "chevron_right"
                size: 15
                color: root.selected ? root.theme.selectedText : root.theme.secondaryText
                visible: root.hasChildren && !root.nodeLoading
                opacity: root.nodeLoading ? 0 : 1
                scale: disclosureMouse.pressed ? 0.82 : 1
                Behavior on opacity { NumberAnimation { duration: 120 } }
                Behavior on scale { NumberAnimation { duration: 90 } }
            }
            Item {
                id: itemLoadingSpinner
                anchors.centerIn: parent
                width: 26
                height: 26
                visible: opacity > 0
                opacity: root.nodeLoading ? 1 : 0
                scale: root.nodeLoading ? 1 : 0.72
                antialiasing: true
                smooth: true
                Md3BusyIndicator {
                    uiTheme: root.theme
                    anchors.fill: parent
                    running: root.nodeLoading
                }
                Behavior on opacity { NumberAnimation { duration: 150 } }
                Behavior on scale {
                    NumberAnimation { duration: 180; easing.type: Easing.OutBack }
                }
            }
        }
        MouseArea {
            id: disclosureMouse
            anchors.fill: parent
            enabled: root.hasChildren
            hoverEnabled: true
            cursorShape: root.nodeLoading ? Qt.BusyCursor : Qt.PointingHandCursor
            onClicked: function(mouse) {
                if (!root.nodeLoading)
                    root.toggleExpandedPreservingScroll(mouse.modifiers)
            }
        }
    }

    Item {
        id: preview
        x: 45 + root.indent
        anchors.verticalCenter: parent.verticalCenter
        width: root.compactMode
            ? (root.largeItem ? 38 : 24) : root.largeItem ? 58 : 28
        height: width
        z: root.interactiveHovered && root.largeItem ? 6 : 1
        scale: !root.compactMode
            && root.interactiveHovered && root.largeItem ? 1.15 : 1
        Behavior on scale {
            NumberAnimation { duration: 130; easing.type: Easing.OutCubic }
        }
        visible: root.nodeType !== "file"
        opacity: root.nodeLoading ? 0.42 : 1
        Behavior on opacity {
            NumberAnimation { duration: 160; easing.type: Easing.OutCubic }
        }
        Loader {
            anchors.fill: parent
            sourceComponent: root.largeItem
                ? previewImageComponent
                : root.nodeType === "process" || root.nodeType === "relation"
                    ? previewIconComponent : null
        }
        Component {
            id: previewImageComponent
            ItemPreview {
                theme: root.theme
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
                onAppearanceCompleted:
                    appController.mark_item_preview_revealed(root.nodeId)
            }
        }
        Component {
            id: previewIconComponent
            MaterialIcon {
                anchors.centerIn: parent
                name: root.typeIcon
                size: root.nodeType === "process"
                    ? (root.subtitle === "hierarchy" ? 18 : 15) : 21
                color: root.accent
                forceSolid: root.nodeType === "process"
            }
        }
    }

    Item {
        id: content
        anchors.left: preview.visible ? preview.right : parent.left
        anchors.leftMargin: preview.visible ? 9 : 47 + root.indent
        anchors.right: parent.right
        anchors.rightMargin: 9
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        opacity: root.nodeLoading ? 0.42 : 1
        Behavior on opacity {
            NumberAnimation { duration: 160; easing.type: Easing.OutCubic }
        }

        Loader {
            anchors.fill: parent
            sourceComponent: root.compactMode
                ? compactBodyComponent
                : root.nodeType === "sobject"
                ? objectBodyComponent
                : root.nodeType === "snapshot"
                    ? snapshotBodyComponent
                    : root.nodeType === "process"
                        ? processBodyComponent
                        : root.nodeType === "relation"
                            ? relationBodyComponent
                            : fileBodyComponent
        }

        Component {
          id: compactBodyComponent
          Item {
            anchors.fill: parent
            Label {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.rightMargin: root.contentTrailingReserve
                anchors.verticalCenter: parent.verticalCenter
                text: root.compactTitle
                color: root.selected
                    ? root.theme.selectedText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: root.nodeType === "process" ? 9 : 12
                font.weight: Font.DemiBold
                maximumLineCount: 1
                wrapMode: Text.NoWrap
                elide: Text.ElideRight
            }
          }
        }

        Component {
          id: objectBodyComponent
          Item {
            anchors.fill: parent
            Column {
              id: objectBody
              anchors.left: parent.left
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              spacing: 5
            Label {
                width: Math.max(48, parent.width - root.contentTrailingReserve)
                text: root.compactTitle
                color: root.selected ? root.theme.selectedText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                font.weight: Font.DemiBold
                maximumLineCount: 1
                wrapMode: Text.NoWrap
                elide: Text.ElideRight
            }
            Label {
                width: Math.max(48, parent.width - root.contentTrailingReserve)
                visible: root.compactSubtitle.length > 0
                text: root.compactSubtitle
                color: root.selected ? "#e2edf3" : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.label
                maximumLineCount: 1
                wrapMode: Text.NoWrap
                elide: Text.ElideRight
            }
            Row {
                width: Math.max(48, parent.width - root.contentTrailingReserve)
                height: 17
                spacing: 4
                clip: true
                Repeater {
                    model: root.progressItems || []
                    delegate: Row {
                        required property var modelData
                        height: 16
                        spacing: 3
                        MaterialIcon { name: "donut_small"; size: 13; color: modelData.color }
                        Label { text: modelData.label; color: root.selected ? root.theme.selectedText : root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.caption }
                    }
                }
                Repeater {
                    model: root.infoChips || []
                    delegate: Rectangle {
                        required property var modelData
                        height: 16
                        width: Math.min(126, chipText.implicitWidth + 10)
                        radius: 8
                        color: root.selected ? root.theme.selected : "transparent"
                        border.color: root.selected ? root.theme.action : root.theme.outline
                        border.width: 1
                        Label {
                            id: chipText
                            anchors.centerIn: parent
                            width: parent.width - 8
                            text: modelData.label + ": " + modelData.value
                            color: root.selected ? root.theme.selectedText : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.caption
                            elide: Text.ElideRight
                        }
                    }
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

                Item {
                  anchors.left: parent.left
                  anchors.right: snapshotSizeBackdrop.left
                  anchors.rightMargin: 8
                  height: parent.height

                  RowLayout {
                    anchors.fill: parent
                    spacing: 5

                    Label {
                      id: snapshotTitle
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
                      text: root.compactTitle
                      color: root.selected
                        ? root.theme.selectedText : root.theme.primaryText
                      font.family: root.theme.fontFamily
                      font.pointSize: Typography.body
                      font.weight: Font.Normal
                      elide: Text.ElideMiddle
                    }

                    Label {
                      id: snapshotOffline
                      visible: !root.fileExists
                        && root.compactTitle.length > 0
                      Layout.preferredWidth: visible ? implicitWidth : 0
                      text: "(" + qsTr("File Offline") + ")"
                      color: root.theme.missingFile
                      font.family: root.theme.fontFamily
                      font.pointSize: Typography.label
                      font.weight: Font.Normal
                    }

                    Item { Layout.fillWidth: true }
                  }
                }

                Rectangle {
                  id: snapshotSizeBackdrop
                  anchors.right: parent.right
                  anchors.verticalCenter: parent.verticalCenter
                  width: Math.max(92, snapshotSize.implicitWidth + 22)
                  height: 22
                  radius: root.theme.itemRadius
                  color: "transparent"
                  gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop {
                      position: 0
                      color: Qt.rgba(
                        root.theme.panelDeep.r,
                        root.theme.panelDeep.g,
                        root.theme.panelDeep.b,
                        0
                      )
                    }
                    GradientStop {
                      position: 0.42
                      color: Qt.rgba(
                        root.theme.panelDeep.r,
                        root.theme.panelDeep.g,
                        root.theme.panelDeep.b,
                        0.30
                      )
                    }
                    GradientStop {
                      position: 0.76
                      color: Qt.rgba(
                        root.theme.panelDeep.r,
                        root.theme.panelDeep.g,
                        root.theme.panelDeep.b,
                        0.68
                      )
                    }
                    GradientStop {
                      position: 1
                      color: Qt.rgba(
                        root.theme.panelDeep.r,
                        root.theme.panelDeep.g,
                        root.theme.panelDeep.b,
                        0.88
                      )
                    }
                  }

                  Label {
                    id: snapshotSize
                    anchors.right: parent.right
                    anchors.rightMargin: 4
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.fileSize
                    color: root.selected
                      ? root.theme.selectedText : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.caption
                    font.weight: Font.Normal
                    horizontalAlignment: Text.AlignRight
                  }
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
                    font.pointSize: Typography.label
                    font.weight: Font.Normal
                  }
                  Label {
                    visible: root.revision.length > 0
                    text: root.revision
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                  }
                  Label {
                    visible: root.repository.length > 0
                    text: root.repository
                    color: root.repositoryColor || root.accent
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                  }
                  Label {
                    visible: root.isLatest
                    text: qsTr("Latest")
                    color: root.theme.green
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.caption
                    font.weight: Font.Normal
                  }
                }

                Label {
                  id: snapshotDate
                  anchors.right: parent.right
                  anchors.verticalCenter: parent.verticalCenter
                  width: Math.max(84, implicitWidth)
                  text: root.timestamp.replace(" ", "\n")
                  color: root.theme.secondaryText
                  font.family: root.theme.fontFamily
                  font.pointSize: Typography.caption
                  font.weight: Font.Normal
                  horizontalAlignment: Text.AlignRight
                  verticalAlignment: Text.AlignVCenter
                  maximumLineCount: 2
                  lineHeight: 0.88
                }
              }

              Item {
                width: parent.width
                height: 20

                Label {
                  id: snapshotAuthor
                  anchors.left: parent.left
                  anchors.verticalCenter: parent.verticalCenter
                  visible: root.author.length > 0
                  text: root.author
                    + (root.compactSubtitle.length > 0 ? ":" : "")
                  color: root.theme.secondaryText
                  font.family: root.theme.fontFamily
                  font.pointSize: Typography.label
                  font.weight: Font.Normal
                  font.italic: true
                  elide: Text.ElideRight
                  width: visible
                    ? Math.min(implicitWidth, parent.width * 0.34) : 0
                }
                Label {
                  anchors.left: snapshotAuthor.right
                  anchors.leftMargin: snapshotAuthor.visible ? 5 : 0
                  anchors.right: parent.right
                  anchors.verticalCenter: parent.verticalCenter
                  text: root.compactSubtitle
                  color: root.selected
                    ? root.theme.selectedText : root.theme.primaryText
                  font.family: root.theme.fontFamily
                  font.pointSize: Typography.label
                  font.weight: Font.Normal
                  elide: Text.ElideRight
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
                color: root.selected ? root.theme.selectedText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.body
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
                anchors.rightMargin: relationCount.visible ? 7 : 0
                anchors.verticalCenter: parent.verticalCenter
                text: root.compactTitle
                color: root.selected ? root.theme.selectedText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.body
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                id: relationCount
                anchors.right: parent.right
                anchors.rightMargin: root.relationActionReserve
                anchors.verticalCenter: parent.verticalCenter
                visible: root.childCount > 0
                text: root.childCount > 0 ? "|  " + root.childCount : ""
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.label
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
                MaterialIcon { name: root.fileExists ? "description" : "priority_high"; size: 15; color: root.fileExists ? root.theme.secondaryText : root.theme.missingFile }
                Label {
                    width: Math.max(70, parent.width - fileKind.implicitWidth - fileBytes.implicitWidth - 38)
                    text: root.compactTitle
                    color: root.selected ? root.theme.selectedText : root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                    font.weight: Font.DemiBold
                    elide: Text.ElideMiddle
                }
                Label { id: fileKind; text: root.compactSubtitle; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.caption }
                Label { id: fileBytes; text: root.fileSize; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.caption }
            }
            Label {
                width: parent.width
                text: root.filePath
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
                elide: Text.ElideMiddle
            }
          }
        }
    }

    Loader {
        id: hoverControls
        anchors.right: !root.stackedObjectActions
                && communicationControls.visible
            ? communicationControls.left : parent.right
        anchors.rightMargin: !root.stackedObjectActions
                && communicationControls.visible ? 4 : 7
        anchors.top: root.stackedObjectActions ? parent.top : undefined
        anchors.topMargin: root.stackedObjectActions ? 7 : 0
        anchors.verticalCenter: root.stackedObjectActions
            ? undefined : parent.verticalCenter
        z: 8
        active: !root.nodeLoading
            && (root.hasPersistentItemControls
                || (!root.compactMode && root.showHoverTools))
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
                    controlHoverRelease.stop()
                    root.controlHoverActive = true
                } else {
                    controlHoverRelease.restart()
                }
            }
        }
        Repeater {
            model: root.itemControls || []
            delegate: CompactIconButton {
                id: actionButton
                required property var modelData
                visible: modelData.persistent
                    || (!root.compactMode && root.showHoverTools)
                width: visible ? 27 : 0
                height: 27
                theme: root.theme
                iconName: modelData.icon
                iconSize: 16
                round: true
                backgroundColor: modelData.success ? "transparent"
                    : modelData.active ? root.theme.selected : "transparent"
                iconColor: modelData.success ? root.theme.green
                    : modelData.active ? root.theme.action
                    : root.selected ? root.theme.selectedText
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

    Row {
        id: communicationControls
        anchors.right: parent.right
        anchors.rightMargin: 7
        anchors.bottom: root.stackedObjectActions ? parent.bottom : undefined
        anchors.bottomMargin: root.stackedObjectActions ? 7 : 0
        anchors.verticalCenter: root.stackedObjectActions
            ? undefined : parent.verticalCenter
        spacing: 3
        visible: root.nodeType === "sobject" || root.nodeType === "process"
        z: 8
        opacity: root.nodeLoading ? 0.25
            : root.compactMode || root.comments > 0
                || root.tasks > 0 || root.showHoverTools ? 1 : 0
        Behavior on opacity {
            enabled: !root.transientAnimationsSuppressed
            NumberAnimation { duration: 200 }
        }
        HoverHandler {
            onHoveredChanged: {
                if (hovered) {
                    controlHoverRelease.stop()
                    root.controlHoverActive = true
                } else {
                    controlHoverRelease.restart()
                }
            }
        }
        ItemCountActionButton {
            theme: root.theme
            iconName: "calendar_check"
            count: root.tasks
            badgeColor: root.theme.action
            toolTipsAllowed: root.hoverAllowed
            toolTip: qsTr("Open Tasks (") + root.tasks + ")"
            onClicked: appController.invoke_item_action("tasks", root.nodeId)
        }
        ItemCountActionButton {
            theme: root.theme
            iconName: "comment_alt"
            count: root.comments
            badgeColor: root.theme.error
            toolTipsAllowed: root.hoverAllowed
            toolTip: qsTr("Open Notes (") + root.comments + ")"
            onClicked: appController.invoke_item_action("notes", root.nodeId)
        }
    }

    MaterialRipple {
        id: itemRipple
        z: 3
        anchors.margins: 1
        shapeRadius: 8
        color: root.theme.dark ? "#2effffff" : "#1e000000"
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

    DropArea {
        id: fileDrop
        property int activeZone: -1
        function updateZone(xPosition) {
            if (root.nodeType === "process") {
                activeZone = 0
                return
            }
            activeZone = xPosition < width / 3
                ? 0 : xPosition >= width * 2 / 3 ? 2 : 1
        }
        anchors.fill: parent
        z: 12
        enabled: root.nodeType === "sobject" || root.nodeType === "process"
        keys: ["text/uri-list"]
        onEntered: function(drag) { updateZone(drag.x) }
        onPositionChanged: function(drag) { updateZone(drag.x) }
        onExited: activeZone = -1
        onDropped: function(drop) {
            let target = root.process || "publish"
            if (root.nodeType === "sobject") {
                if (activeZone === 0)
                    target = "icon"
                else if (activeZone === 2)
                    target = "attachment"
            }
            appController.queue_dropped_files(root.nodeId, drop.urls, target)
            activeZone = -1
            drop.acceptProposedAction()
        }
    }
    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        radius: 12
        z: 13
        visible: opacity > 0
        color: root.theme.panelRaised
        border.width: 0
        opacity: fileDrop.containsDrag ? 0.98 : 0
        scale: fileDrop.containsDrag ? 1 : 0.985
        Behavior on opacity {
            NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
        }
        Behavior on scale {
            NumberAnimation { duration: 170; easing.type: Easing.OutCubic }
        }
        Row {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 4
            Repeater {
                model: root.nodeType === "process"
                    ? [{"title": "Drop File to " + (root.process || root.title), "icon": "publish"}]
                    : [
                        {"title": "Add Icon", "icon": "image"},
                        {"title": "Publish File", "icon": "publish"},
                        {"title": "Attach File", "icon": "attachment"}
                    ]
                delegate: Rectangle {
                    required property int index
                    required property var modelData
                    readonly property bool active:
                        index === fileDrop.activeZone
                    width: (
                        parent.width
                        - parent.spacing * (root.nodeType === "process" ? 0 : 2)
                    ) / (root.nodeType === "process" ? 1 : 3)
                    height: parent.height
                    radius: 9
                    color: active ? root.theme.selected : "transparent"
                    border.width: active ? 1 : 0
                    border.color: root.theme.action
                    scale: active ? 1 : 0.96
                    opacity: active ? 1 : 0.58
                    Behavior on color { ColorAnimation { duration: 110 } }
                    Behavior on scale {
                        NumberAnimation {
                            duration: 130
                            easing.type: Easing.OutCubic
                        }
                    }
                    Behavior on opacity { NumberAnimation { duration: 110 } }
                    Column {
                        anchors.centerIn: parent
                        spacing: 3
                        MaterialIcon {
                            anchors.horizontalCenter: parent.horizontalCenter
                            name: modelData.icon
                            size: active ? 21 : 18
                            color: active
                                ? root.theme.action : root.theme.secondaryText
                            Behavior on size {
                                NumberAnimation { duration: 120 }
                            }
                        }
                        Label {
                            text: modelData.title
                            color: active
                                ? root.theme.selectedText
                                : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.label
                            font.weight: active ? Font.Bold : Font.DemiBold
                        }
                    }
                }
            }
        }
    }

}
