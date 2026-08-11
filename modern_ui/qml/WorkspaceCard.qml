import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

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
    required property string previewUrl
    required property bool previewRevealed
    required property bool previewRequested
    required property var progressItems
    required property var infoChips
    required property var itemControls
    required property bool nodeLoading
    required property var theme
    property bool selected: false
    property bool externalMenuVisible: false
    property bool transientAnimationsSuppressed: true
    readonly property bool expanded: false
    signal actionMenuRequested(
        string nodeId,
        var actions,
        var anchorItem,
        real localX,
        real localY,
        bool below
    )

    readonly property bool isProcess: nodeType === "process"
    readonly property bool isSnapshot: nodeType === "snapshot"
    readonly property bool isSobject: nodeType === "sobject"
    readonly property bool isRelation: nodeType === "relation"
    readonly property bool hasLargePreview: isSobject || isSnapshot
        || nodeType === "file"
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

    scale: root.interactiveHovered ? 1.018 : 1
    Behavior on scale {
        NumberAnimation { duration: 170; easing.type: Easing.OutCubic }
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
        if (root.hasLargePreview && !root.previewRequested)
            appController.request_item_preview(nodeId)
        transientAnimationArm.restart()
    }
    GridView.onPooled: {
        transientAnimationArm.stop()
        root.transientAnimationsSuppressed = true
        cardFileDrop.activeZone = -1
    }
    GridView.onReused: {
        root.transientAnimationsSuppressed = true
        cardFileDrop.activeZone = -1
        if (root.hasLargePreview && !root.previewRequested)
            appController.request_item_preview(root.nodeId)
        transientAnimationArm.restart()
    }

    Timer {
        id: transientAnimationArm
        interval: 0
        onTriggered: {
            if (!cardHover.hovered)
                root.transientAnimationsSuppressed = false
        }
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
            color: root.theme.dark ? "#36000000" : "#26000000"
            transparentBorder: true
        }
    }
    Rectangle {
        id: cardBackground
        anchors.fill: parent
        radius: 12
        color: root.selected
            ? root.theme.surfaceContainerHighest : root.theme.panelRaised
        border.width: root.selected ? 2 : 0
        border.color: root.selected ? root.theme.action : "transparent"
        Behavior on color {
            ColorAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }
        Behavior on border.color {
            ColorAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }
    }
    Rectangle {
        anchors.fill: cardBackground
        radius: cardBackground.radius
        color: root.theme.action
        opacity: root.selected ? 0.08 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
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
                MaterialIcon {
                    anchors.centerIn: parent
                            name: "chevron_right"
                    size: 12
                    color: "#ffffff"
                    forceSolid: true
                }
                MouseArea {
                    id: openTypeMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.openCard(Qt.NoModifier)
                    Md3ToolTip {
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
                    MaterialIcon {
                        name: root.typeIcon
                        size: 12
                        color: "#ffffff"
                        forceSolid: true
                    }
                    Label {
                        text: root.typeLabel
                        color: "#ffffff"
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
                        font.weight: Font.Bold
                    }
                }
            }
            Md3BusyIndicator {
                uiTheme: root.theme
                anchors.centerIn: parent
                width: 28
                height: 28
                visible: root.nodeLoading
                running: visible
            }
        }

        Component {
            id: imagePreviewComponent
            Item {
                ItemPreview {
                    width: 154
                    height: 154
                    anchors.centerIn: parent
                    theme: root.theme
                    source: root.previewUrl
                    accent: root.accent
                    round: root.isSobject
                    cornerRadius: root.isSobject ? 77 : 11
                    previewSize: 154
                    selected: root.selected
                    fallbackIcon: root.typeIcon
                    fallbackText: ""
                    animateAppearance:
                        !root.previewRevealed && root.hoverAllowed
                    onAppearanceCompleted: {
                        if (!root.previewRevealed)
                            appController.mark_item_preview_revealed(root.nodeId)
                    }
                }
            }
        }
        Component {
            id: snapshotPreviewComponent
            Rectangle {
                width: 154
                height: 154
                anchors.centerIn: parent
                radius: 11
                color: root.theme.panel
                border.width: 1
                border.color: root.typeColor
                Label {
                    anchors.centerIn: parent
                    text: root.snapshotExtension
                    color: root.typeColor
                    font.family: root.theme.fontFamily
                    font.pixelSize: 30
                    font.weight: Font.Bold
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
                        color: "#ffffff"
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
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
                    font.pixelSize: 9
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
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                }
            }
        }

        Label {
            id: titleLabel
            width: parent.width
            text: String(root.title || root.searchKey || qsTr("Untitled"))
                .replace(/[\r\n\t]+/g, " ")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 14
            font.weight: Font.Bold
            elide: Text.ElideRight
            Md3ToolTip {
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
            height: root.expanded ? 55 : 17
            spacing: 4
            clip: true
            visible: (root.infoChips && root.infoChips.length > 0)
                || (root.progressItems && root.progressItems.length > 0)
            Repeater {
                model: (root.progressItems || []).slice(
                    0, root.expanded ? 5 : 1)
                delegate: Row {
                    required property var modelData
                    spacing: 3
                    MaterialIcon {
                        name: "donut_small"
                        size: 12
                        color: modelData.color
                    }
                    Label {
                        text: modelData.label
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
                    }
                }
            }
            Repeater {
                model: (root.infoChips || []).slice(
                    0, root.expanded ? 6 : 1)
                delegate: Rectangle {
                    required property var modelData
                    height: 16
                    width: Math.min(
                        root.expanded ? 104 : 86,
                        chipLabel.implicitWidth + 10
                    )
                    radius: 8
                    color: "transparent"
                    border.width: 1
                    border.color: root.theme.outline
                    Label {
                        id: chipLabel
                        anchors.centerIn: parent
                        width: parent.width - 8
                        text: modelData.label + ": " + modelData.value
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
                        elide: Text.ElideRight
                    }
                }
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
            font.pixelSize: 9
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
            font.pixelSize: 8
            elide: Text.ElideRight
            MouseArea {
                id: descriptionMouse
                anchors.fill: parent
                z: 7
                acceptedButtons: Qt.NoButton
                hoverEnabled: true
                Md3ToolTip {
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
        active: root.hovered && (root.itemControls || []).length > 0
        sourceComponent: Row {
            spacing: 2
            Repeater {
                model: root.itemControls || []
                delegate: Rectangle {
                    required property var modelData
                    width: 27
                    height: 27
                    radius: 14
                    color: modelData.active
                        ? root.theme.selected : root.theme.panel
                    border.width: 1
                    border.color: root.theme.outline
                    MaterialIcon {
                        anchors.centerIn: parent
                        name: modelData.icon
                        size: 15
                        color: modelData.active
                            ? root.theme.action : root.theme.secondaryText
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
                        Md3ToolTip {
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

    Row {
        id: countControls
        z: 4
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 7
        spacing: 3
        visible: root.isSobject || root.isProcess
        opacity: root.tasks > 0 || root.comments > 0
            || root.hovered ? 1 : 0
        Behavior on opacity {
            enabled: !root.transientAnimationsSuppressed
            NumberAnimation { duration: 120 }
        }
        ItemCountActionButton {
            theme: root.theme
            iconName: "calendar_check"
            count: root.tasks
            toolTip: qsTr("Open Tasks (") + root.tasks + ")"
            onClicked: appController.invoke_item_action("tasks", root.nodeId)
        }
        ItemCountActionButton {
            theme: root.theme
            iconName: "comment_alt"
            count: root.comments
            toolTip: qsTr("Open Notes (") + root.comments + ")"
            onClicked: appController.invoke_item_action("notes", root.nodeId)
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

    DropArea {
        id: cardFileDrop
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

    Loader {
        anchors.fill: parent
        anchors.margins: 3
        z: 13
        active: cardFileDrop.containsDrag
        sourceComponent: Rectangle {
            radius: 12
            color: root.theme.panelRaised
            opacity: 0.98
            Row {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 5
                Repeater {
                    model: root.nodeType === "process"
                        ? [{
                            "title": "Drop File to "
                                + (root.process || root.title),
                            "icon": "publish"
                        }]
                        : [
                            {"title": "Add Icon", "icon": "image"},
                            {"title": "Publish File", "icon": "publish"},
                            {"title": "Attach File", "icon": "attachment"}
                        ]
                    delegate: Rectangle {
                        required property int index
                        required property var modelData
                        readonly property bool active:
                            index === cardFileDrop.activeZone
                        width: (
                            parent.width
                            - parent.spacing * (
                                root.nodeType === "process" ? 0 : 2)
                        ) / (root.nodeType === "process" ? 1 : 3)
                        height: parent.height
                        radius: 10
                        color: active ? root.theme.selected : "transparent"
                        border.width: active ? 1 : 0
                        border.color: root.theme.action
                        scale: active ? 1 : 0.96
                        opacity: active ? 1 : 0.56
                        Behavior on color {
                            ColorAnimation { duration: 110 }
                        }
                        Behavior on scale {
                            NumberAnimation {
                                duration: 130
                                easing.type: Easing.OutCubic
                            }
                        }
                        Behavior on opacity {
                            NumberAnimation { duration: 110 }
                        }
                        Column {
                            anchors.centerIn: parent
                            spacing: 5
                            MaterialIcon {
                                anchors.horizontalCenter: parent.horizontalCenter
                                name: modelData.icon
                                size: active ? 26 : 21
                                color: active
                                    ? root.theme.action
                                    : root.theme.secondaryText
                                Behavior on size {
                                    NumberAnimation { duration: 120 }
                                }
                            }
                            Label {
                                width: parent.parent.width - 8
                                text: modelData.title
                                color: active
                                    ? root.theme.selectedText
                                    : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 9
                                font.weight: active
                                    ? Font.Bold : Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }
        }
    }

}
