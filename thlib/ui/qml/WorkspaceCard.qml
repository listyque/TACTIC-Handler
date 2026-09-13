pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects
import "controls" as Controls

Item {
    id: root

    required property int index
    required property string nodeId
    required property string nodeType
    required property string searchKey
    required property string title
    required property string subtitle
    required property string status
    required property string accent
    required property int comments
    required property int tasks
    required property int childCount
    required property bool isLatest
    required property bool hasChildren
    required property string process
    required property string author
    required property string timestamp
    required property string version
    required property string repository
    required property string cardPreviewUrl
    required property bool previewRevealed
    required property bool cardPreviewRequested
    required property var progressItems
    required property var infoChips
    required property var itemControls
    required property bool nodeLoading
    required property var theme
    property var controller: null
    property bool selected: false
    property bool externalMenuVisible: false
    property bool commentsUpdated: false
    property bool tasksUpdated: false
    property bool transientAnimationsSuppressed: true
    property bool viewPooled: false
    property bool presentationActive: true
    readonly property bool expanded: false
    signal actionMenuRequested(
        string nodeId,
        var actions,
        var anchorItem,
        real localX,
        real localY,
        bool below
    )
    signal processCountMenuRequested(
        string nodeId,
        string panel,
        var anchorItem
    )

    function requestCardPreviewIfNeeded() {
        if (root.presentationActive && !root.viewPooled && root.hasLargePreview
                && !root.cardPreviewRequested && !root.cardPreviewUrl)
            appController.request_item_card_preview(root.nodeId)
    }

    onCardPreviewUrlChanged: requestCardPreviewIfNeeded()
    onCardPreviewRequestedChanged: requestCardPreviewIfNeeded()

    function armTransientAnimations() {
        root.transientAnimationsSuppressed = root.viewPooled
            || cardHover.hovered
    }

    function cancelTransientAnimationArm() {
        root.transientAnimationsSuppressed = true
    }

    readonly property bool isProcess: nodeType === "process"
    readonly property bool isSnapshot: nodeType === "snapshot"
    readonly property bool isSobject: nodeType === "sobject"
    readonly property bool isRelation: nodeType === "relation"
    readonly property bool hasLargePreview: isSobject || isSnapshot
        || nodeType === "file"
    readonly property bool hasPersistentItemControls: {
        const controls = root.itemControls || []
        for (let index = 0; index < controls.length; ++index) {
            if (controls[index].persistent)
                return true
        }
        return false
    }
    readonly property string entityName: {
        if (isRelation)
            return title || "Related items"
        if (!isSobject)
            return ""
        const typePart = String(searchKey || "").split("?")[0]
            .split("/").pop().replace(/_/g, " ")
        return typePart
            ? typePart.charAt(0).toUpperCase() + typePart.slice(1)
            : "SObject"
    }
    readonly property string typeLabel: isSobject ? entityName
        : isProcess ? "PROCESS"
        : isSnapshot ? "SNAPSHOT"
        : isRelation ? entityName
        : nodeType === "file" ? "FILE" : nodeType.toUpperCase()
    readonly property string typeIcon: isSobject ? "sobject"
        : isProcess ? "cogs"
        : isSnapshot ? "camera"
        : nodeType === "relation" ? "project-diagram" : "file"
    readonly property color typeColor: isProcess || isRelation ? root.accent
        : isSnapshot ? root.theme.cyan
        : isSobject ? root.accent : root.theme.secondaryText
    readonly property bool hoverAllowed: {
        const view = root.GridView.view
        return !view || !view.interactionMoving
    }
    readonly property bool interactiveHovered:
        !root.transientAnimationsSuppressed
        && root.hoverAllowed && cardHover.hovered
    readonly property bool hovered:
        root.interactiveHovered || root.externalMenuVisible
    readonly property real expansionOffsetX: {
        if (!expanded || !GridView.view)
            return 0
        const view = GridView.view
        const inset = 4
        const minimumLeft = view.contentX + inset
        const maximumRight = view.contentX + view.width - inset
        let offset = -28
        if (root.x + offset < minimumLeft)
            offset = minimumLeft - root.x
        if (root.x + root.width + offset > maximumRight)
            offset = maximumRight - root.x - root.width
        return offset
    }
    readonly property string snapshotExtension: {
        const match = String(title || "").match(/\.([^.\\/\s]+)$/)
        return match ? match[1].toUpperCase() : "FILE"
    }
    readonly property string displayedSubtitle: {
        const value = String(root.subtitle || root.timestamp || "")
        if (!appController.description_limit_enabled
                || value.length <= appController.description_limit)
            return value
        return value.slice(0, appController.description_limit).trim() + "…"
    }

    function openCard(modifiers) {
        if (root.nodeType === "snapshot") {
            appController.invoke_item_action("open", root.nodeId)
            return
        }
        if (appController.handle_item_double_click(
                root.nodeId, modifiers || Qt.NoModifier))
            return
        if (root.hasChildren && !root.nodeLoading)
            appController.enter_card_node(root.nodeId)
        else if (root.nodeType === "file")
            appController.invoke_item_action("open", root.nodeId)
    }

    transform: Translate {
        x: root.expansionOffsetX
        y: root.expanded ? -8 : 0
    }
    HoverHandler {
        id: cardHover
        onHoveredChanged: {
            if (!hovered && root.transientAnimationsSuppressed)
                root.transientAnimationsSuppressed = false
        }
    }

    Component.onCompleted: {
        root.requestCardPreviewIfNeeded()
        root.armTransientAnimations()
    }
    GridView.onPooled: {
        root.cancelTransientAnimationArm()
        root.viewPooled = true
        root.transientAnimationsSuppressed = true
        cardFileDropTarget.reset()
    }
    GridView.onReused: {
        root.viewPooled = false
        root.transientAnimationsSuppressed = true
        cardFileDropTarget.reset()
        root.requestCardPreviewIfNeeded()
        root.armTransientAnimations()
    }
    onPresentationActiveChanged: {
        root.requestCardPreviewIfNeeded()
    }

    Loader {
        anchors.fill: cardBackground
        active: root.interactiveHovered
        sourceComponent: DropShadow {
            anchors.fill: parent
            source: cardBackground
            horizontalOffset: 2
            verticalOffset: 4
            radius: 9
            samples: 19
            color: root.theme.popupShadow
            transparentBorder: true
        }
    }
    Rectangle {
        id: cardBackground
        anchors.fill: parent
        radius: 12
        color: root.selected
            ? root.theme.contentSelection
            : root.theme.panelRaised
        border.width: root.selected ? 1 : 0
        border.color: root.selected
            ? root.theme.contentAccent
            : "transparent"
        Behavior on color {
            enabled: !root.theme.suppressTransientMotion
            ColorAnimation {
                duration: root.theme.clickMotionFast
                easing.type: Easing.OutCubic
            }
        }
        Behavior on border.color {
            enabled: !root.theme.suppressTransientMotion
            ColorAnimation {
                duration: root.theme.clickMotionFast
                easing.type: Easing.OutCubic
            }
        }
    }
    Controls.ItemPreview {
        id: cardPreviewBackground
        anchors.fill: cardBackground
        visible: root.isSobject
        theme: root.theme
        active: !root.viewPooled
        effectsEnabled: root.hoverAllowed
        source: visible ? root.cardPreviewUrl : ""
        accent: root.accent
        round: false
        cornerRadius: cardBackground.radius
        previewSize: Math.max(width, height)
        fillMode: Image.PreserveAspectCrop
        selected: root.selected
        selectedBorderColor: root.isSobject
            ? root.theme.contentAccent : root.theme.selectedText
        fallbackIcon: root.typeIcon
        fallbackText: ""
        animateAppearance: !root.previewRevealed && root.hoverAllowed
        onImageReady: {
            if (!root.previewRevealed)
                appController.mark_item_preview_revealed(root.nodeId)
        }
    }
    Rectangle {
        anchors.fill: cardBackground
        visible: root.isSobject
        radius: cardBackground.radius
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop {
                position: 0.32
                color: Qt.rgba(
                    root.theme.panelRaised.r,
                    root.theme.panelRaised.g,
                    root.theme.panelRaised.b,
                    0
                )
            }
            GradientStop {
                position: 0.58
                color: Qt.rgba(
                    (root.selected
                        ? root.theme.contentSelection
                        : root.theme.panelRaised).r,
                    (root.selected
                        ? root.theme.contentSelection
                        : root.theme.panelRaised).g,
                    (root.selected
                        ? root.theme.contentSelection
                        : root.theme.panelRaised).b,
                    0.34
                )
            }
            GradientStop {
                position: 0.78
                color: Qt.rgba(
                    (root.selected
                        ? root.theme.contentSelection
                        : root.theme.panelRaised).r,
                    (root.selected
                        ? root.theme.contentSelection
                        : root.theme.panelRaised).g,
                    (root.selected
                        ? root.theme.contentSelection
                        : root.theme.panelRaised).b,
                    0.86
                )
            }
            GradientStop {
                position: 1
                color: root.selected
                    ? root.theme.contentSelection : root.theme.panelRaised
            }
        }
    }
    Column {
        z: 3
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        anchors.topMargin: 8
        anchors.bottomMargin: 11
        spacing: 4

        Item {
            width: parent.width
            height: root.hasLargePreview ? 158 : 76

            Loader {
                anchors.fill: parent
                sourceComponent: root.isSnapshot
                    ? snapshotPreviewComponent
                    : root.isSobject
                        ? emptyPreviewComponent
                    : root.hasLargePreview
                        ? imagePreviewComponent
                        : root.isProcess
                            ? processPreviewComponent
                            : relationPreviewComponent
            }

            Rectangle {
                id: openTypeButton
                z: 6
                anchors.left: parent.left
                anchors.top: parent.top
                height: 22
                width: visible ? 22 : 0
                radius: 11
                visible: root.hasChildren || root.isSnapshot
                    || root.nodeType === "file"
                color: root.typeColor
                Controls.MaterialIcon {
                    anchors.centerIn: parent
                            name: "chevron_right"
                    size: 12
                    color: root.theme.readableText(root.typeColor)
                    forceSolid: true
                }
                MouseArea {
                    id: openTypeMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.openCard(Qt.NoModifier)
                    Controls.ToolTip {
                        theme: root.theme
                        visible: openTypeMouse.containsMouse
                            && !root.theme.suppressToolTips
                        text: root.hasChildren
                            ? qsTr("Open card contents")
                            : root.nodeType === "snapshot"
                                ? qsTr("Open snapshot") : qsTr("Open item")
                        delay: 400
                    }
                }
            }
            Rectangle {
                z: 6
                anchors.left: openTypeButton.right
                anchors.leftMargin: openTypeButton.visible ? 4 : 0
                anchors.top: parent.top
                height: 22
                width: typeRow.implicitWidth + 12
                radius: 7
                color: root.typeColor
                Row {
                    id: typeRow
                    anchors.centerIn: parent
                    spacing: 4
                    Controls.MaterialIcon {
                        name: root.typeIcon
                        size: 12
                        color: root.theme.readableText(root.typeColor)
                        forceSolid: true
                    }
                    Label {
                        text: root.typeLabel
                        color: root.theme.readableText(root.typeColor)
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.Bold
                    }
                }
            }
            Controls.BusyIndicator {
                uiTheme: root.theme
                anchors.centerIn: parent
                width: 28
                height: 28
                visible: root.nodeLoading
                running: visible
            }
        }

        Component {
            id: emptyPreviewComponent
            Item {}
        }
        Component {
            id: imagePreviewComponent
            Item {
                Controls.ItemPreview {
                    width: 154
                    height: 154
                    anchors.centerIn: parent
                    theme: root.theme
                    active: !root.viewPooled
                    effectsEnabled: root.hoverAllowed
                    source: root.cardPreviewUrl
                    accent: root.accent
                    round: false
                    cornerRadius: 11
                    previewSize: 154
                    selected: root.selected
                    fallbackIcon: root.typeIcon
                    fallbackText: ""
                    animateAppearance:
                        !root.previewRevealed && root.hoverAllowed
                    onImageReady: {
                        if (!root.previewRevealed)
                            appController.mark_item_preview_revealed(root.nodeId)
                    }
                }
            }
        }
        Component {
            id: snapshotPreviewComponent
            Item {
                width: 154
                height: 154
                anchors.centerIn: parent

                Controls.ItemPreview {
                    anchors.fill: parent
                    theme: root.theme
                    active: !root.viewPooled
                    effectsEnabled: root.hoverAllowed
                    source: root.cardPreviewUrl
                    accent: root.typeColor
                    cornerRadius: 11
                    previewSize: 154
                    fillMode: Image.PreserveAspectCrop
                    selected: root.selected
                    selectedBorderColor: root.theme.contentSelectionText
                    fallbackIcon: "file"
                    fallbackText: root.snapshotExtension
                    animateAppearance:
                        !root.previewRevealed && root.hoverAllowed
                    onImageReady: {
                        if (!root.previewRevealed)
                            appController.mark_item_preview_revealed(root.nodeId)
                    }
                }
                Rectangle {
                    visible: root.isLatest
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 8
                    width: latestLabel.implicitWidth + 12
                    height: 20
                    radius: 10
                    color: root.theme.action
                    Label {
                        id: latestLabel
                        anchors.centerIn: parent
                        text: qsTr("LATEST")
                        color: root.theme.readableText(root.theme.action)
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.Bold
                    }
                }
            }
        }
        Component {
            id: processPreviewComponent
            Rectangle {
                anchors.fill: parent
                radius: 10
                color: root.theme.panel
                border.width: 1
                border.color: root.typeColor
                Row {
                    anchors.centerIn: parent
                    spacing: 8
                    Repeater {
                        model: 4
                        Rectangle {
                            required property int index
                            width: index === 1 ? 22 : 15
                            height: width
                            radius: width / 2
                            color: index === 1
                                ? root.typeColor : root.theme.outline
                        }
                    }
                }
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 8
                    text: root.childCount + (root.childCount === 1
                        ? qsTr(" check-in") : qsTr(" check-ins"))
                    color: root.typeColor
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
            }
        }
        Component {
            id: relationPreviewComponent
            Rectangle {
                anchors.fill: parent
                radius: 10
                color: root.theme.panel
                border.width: 1
                border.color: root.typeColor
                Column {
                    anchors.centerIn: parent
                    spacing: 6
                    Repeater {
                        model: 3
                        Rectangle {
                            required property int index
                            width: 78 - index * 13
                            height: 7
                            radius: 3
                            color: index === 0
                                ? root.typeColor : root.theme.outline
                        }
                    }
                }
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 8
                    text: root.childCount > 0
                        ? root.childCount + (root.childCount === 1
                            ? qsTr(" related item")
                            : qsTr(" related items"))
                        : ""
                    color: root.typeColor
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
            }
        }

        Label {
            id: titleLabel
            width: parent.width
            text: String(root.title || root.searchKey || qsTr("Untitled"))
                .replace(/[\r\n\t]+/g, " ")
            color: root.selected
                ? root.theme.contentSelectionText : root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 14
            font.weight: Font.Bold
            elide: Text.ElideRight
            Controls.ToolTip {
                theme: root.theme
                visible: titleHover.hovered && titleLabel.truncated
                    && !root.theme.suppressToolTips
                text: titleLabel.text
                delay: 400
            }
            HoverHandler { id: titleHover }
        }
        Flow {
            width: parent.width
            height: root.expanded ? 55 : 24
            spacing: 4
            clip: true
            visible: (root.infoChips && root.infoChips.length > 0)
                || (root.progressItems && root.progressItems.length > 0)
            Controls.CompletionStrip {
                theme: root.theme
                items: root.progressItems || []
                maximumItems: root.expanded ? 5 : 1
                onCompletionRequested: searchType => {
                    if (root.controller)
                        root.controller.open_completion(root.nodeId, searchType)
                }
            }
            Controls.InfoValueStrip {
                width: parent.width
                height: 16
                theme: root.theme
                items: root.infoChips || []
                selected: root.selected
                maximumItemWidth: root.expanded ? 160 : 120
            }
        }
        Label {
            width: parent.width
            text: root.isSnapshot
                ? [root.version, root.process, root.repository]
                    .filter(function(value) { return Boolean(value) }).join(" · ")
                : root.isProcess
                    ? [root.process || root.title, root.status]
                        .filter(function(value) { return Boolean(value) }).join(" · ")
                    : [root.status, root.author]
                        .filter(function(value) { return Boolean(value) }).join(" · ")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            elide: Text.ElideRight
        }
        Label {
            id: descriptionLabel
            width: Math.max(40, parent.width
                - ((root.tasks > 0 || root.comments > 0) ? 68 : 0))
            leftPadding: 4
            rightPadding: 8
            bottomPadding: 2
            text: root.displayedSubtitle
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
            elide: Text.ElideRight
            MouseArea {
                id: descriptionMouse
                anchors.fill: parent
                z: 7
                acceptedButtons: Qt.NoButton
                hoverEnabled: true
                Controls.ToolTip {
                    theme: root.theme
                    visible: descriptionMouse.containsMouse
                        && descriptionLabel.text.length > 0
                        && !root.theme.suppressToolTips
                    text: root.subtitle || root.timestamp
                    delay: 400
                }
            }
        }
    }

    Loader {
        id: cardControlsLoader
        z: 4
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.top: parent.top
        anchors.topMargin: 8
        active: (root.hovered || root.hasPersistentItemControls)
            && (root.itemControls || []).length > 0
        sourceComponent: Row {
            spacing: 2
            Repeater {
                model: root.itemControls || []
                delegate: Rectangle {
                    required property var modelData
                    visible: modelData.persistent || root.hovered
                    width: visible ? 27 : 0
                    height: 27
                    radius: 14
                    color: modelData.success ? "transparent"
                        : modelData.active
                            ? root.theme.contentSelection
                        : root.theme.panel
                    border.width: modelData.success ? 0 : 1
                    border.color: root.theme.outline
                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: modelData.icon
                        size: 15
                        color: modelData.success ? root.theme.green
                            : modelData.active
                                ? root.theme.contentSelectionText
                            : root.theme.secondaryText
                    }
                    MouseArea {
                        id: cardControlMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (modelData.command === "relations") {
                                root.actionMenuRequested(
                                    root.nodeId,
                                    appController.relation_menu_actions(
                                        root.nodeId),
                                    parent, 0, parent.height, true
                                )
                            } else if (modelData.command === "repo_sync") {
                                root.actionMenuRequested(
                                    root.nodeId,
                                    appController.repo_sync_menu_actions(
                                        root.nodeId),
                                    parent, 0, parent.height, true
                                )
                            } else {
                                appController.invoke_item_action(
                                    modelData.command, root.nodeId
                                )
                            }
                        }
                        Controls.ToolTip {
                            theme: root.theme
                            visible: cardControlMouse.containsMouse
                                && !root.theme.suppressToolTips
                            text: modelData.tip || ""
                        }
                    }
                }
            }
        }
    }

    Loader {
        id: countControls
        objectName: "workspaceCardCountControls"
        z: 4
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 7
        active: root.isSobject || root.isProcess
        visible: active
        opacity: root.tasks > 0 || root.comments > 0
            || root.hovered ? 1 : 0
        Behavior on opacity {
            enabled: !root.transientAnimationsSuppressed
                && !root.theme.suppressTransientMotion
            NumberAnimation { duration: theme.hoverMotionFast }
        }
        sourceComponent: Row {
            spacing: 3

            Controls.ItemCountActionButton {
                id: taskCountButton
                objectName: "workspaceTaskCountButton"
                theme: root.theme
                iconName: "calendar_check"
                count: root.tasks
                activeColor: root.isSobject
                    ? root.theme.secondaryText : root.theme.action
                badgeColor: root.tasksUpdated
                    ? root.theme.error : activeColor
                toolTip: qsTr("Open Tasks (") + root.tasks + ")"
                onClicked: root.processCountMenuRequested(
                    root.nodeId, "tasks", taskCountButton
                )
            }
            Controls.ItemCountActionButton {
                id: noteCountButton
                objectName: "workspaceNoteCountButton"
                theme: root.theme
                iconName: "comment"
                count: root.comments
                activeColor: root.isSobject
                    ? root.theme.secondaryText : root.theme.error
                badgeColor: root.commentsUpdated
                    ? root.theme.error : activeColor
                toolTip: qsTr("Open Notes (") + root.comments + ")"
                onClicked: root.processCountMenuRequested(
                    root.nodeId, "notes", noteCountButton
                )
            }
        }
    }

    MouseArea {
        id: cardMouse
        z: 2
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled
            ? Qt.PointingHandCursor : Qt.ArrowCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onClicked: function(mouse) {
            root.forceActiveFocus()
            appController.select_result_node(
                root.nodeId, root.searchKey, root.nodeType,
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
            root.openCard(mouse.modifiers)
        }
    }

    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter
                || event.key === Qt.Key_Space) {
            root.openCard(event.modifiers)
            event.accepted = true
        } else if (event.key === Qt.Key_Delete) {
            appController.invoke_item_action("delete", root.nodeId)
            event.accepted = true
        } else if (event.key === Qt.Key_T
                && (event.modifiers & Qt.ControlModifier)) {
            appController.invoke_item_action("new_tab", root.nodeId)
            event.accepted = true
        } else if (event.key === Qt.Key_A
                && (event.modifiers & Qt.ControlModifier)) {
            appController.select_all_result_siblings()
            event.accepted = true
        }
    }

    WorkspaceFileDropTarget {
        id: cardFileDropTarget
        anchors.fill: parent
        theme: root.theme
        controller: appController
        nodeId: root.nodeId
        nodeType: root.nodeType
        nodeTitle: root.title
        targetProcess: root.process
        spacious: true
    }

}
