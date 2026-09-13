import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root
    required property var theme
    required property var preview
    property bool animatePreview: true
    signal activated()
    signal retryRequested()
    signal contextRequested(real localX, real localY)
    signal nestedActivated(string searchKey)
    signal nestedRetryRequested(string searchKey)

    readonly property string loadState:
        String(root.preview.status || "loading")
    readonly property bool failed: root.loadState === "error"
    readonly property string kind: String(root.preview.kind || "sobject")
    readonly property bool resolvedNote:
        root.kind === "note" && root.loadState === "ready"
    readonly property bool resolvedMessage:
        root.kind === "message" && root.loadState === "ready"
    readonly property bool knowledgePreview: root.kind === "knowledge"
    readonly property bool canOpenMessage:
        root.resolvedMessage && root.preview.canOpen === true

    implicitHeight: root.resolvedNote
        ? noteDetails.implicitHeight + 20
        : root.resolvedMessage
        ? messageDetails.implicitHeight + 20
        : root.knowledgePreview
        ? knowledgeDetails.implicitHeight + 20
        : root.kind === "snapshot"
        ? 88
        : 72
    radius: 14
    color: cardHover.hovered
            && (!root.resolvedMessage || root.canOpenMessage)
        ? root.theme.surfaceContainerHighest
        : root.resolvedMessage
            ? root.theme.surfaceContainerHigh : root.theme.surfaceContainer
    border.width: 1
    border.color: failed ? root.theme.error : root.theme.outlineVariant

    function fallbackIcon() {
        const icons = {
            "sobject": "inventory_2", "task": "task_alt",
            "snapshot": "photo_library", "file": "description",
            "note": "sticky_note_2", "message": "chat",
            "user": "person", "project": "folder_special",
            "knowledge": "article"
        }
        return icons[root.kind] || "link"
    }

    function accentColor() {
        const colors = {
            "task": root.theme.green,
            "snapshot": root.theme.violet,
            "file": root.theme.cyan,
            "note": root.theme.yellow,
            "message": root.theme.action,
            "user": root.theme.tertiary,
            "project": root.theme.cyan,
            "knowledge": root.theme.tertiary
        }
        return colors[root.kind] || root.theme.action
    }

    Behavior on color {
        ColorAnimation {
            duration: root.theme.hoverMotionFast
            easing.type: Easing.OutCubic
        }
    }

    HoverHandler {
        id: cardHover
        cursorShape: root.resolvedMessage && !root.canOpenMessage
            ? Qt.ArrowCursor : Qt.PointingHandCursor
    }

    Controls.ActivationHandler {
        enabled: root.canOpenMessage
        onActivated: root.activated()
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: root.resolvedMessage
            ? Qt.RightButton : Qt.LeftButton | Qt.RightButton
        cursorShape: root.resolvedMessage && !root.canOpenMessage
            ? Qt.ArrowCursor : Qt.PointingHandCursor
        onClicked: mouse => {
            if (mouse.button === Qt.RightButton)
                root.contextRequested(mouse.x, mouse.y)
            else if (root.failed)
                root.retryRequested()
            else if (!root.resolvedMessage || root.canOpenMessage)
                root.activated()
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        width: 3
        radius: width / 2
        visible: root.kind === "snapshot" || root.knowledgePreview
        color: root.accentColor()
    }

    RowLayout {
        id: headerRow
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 72
        anchors.leftMargin: 10
        anchors.rightMargin: 7
        spacing: 10
        visible: root.kind !== "snapshot"
            && !root.resolvedNote && !root.resolvedMessage
            && !root.knowledgePreview

        Controls.ItemPreview {
            Layout.preferredWidth: 48
            Layout.preferredHeight: 48
            theme: root.theme
            source: String(root.preview.previewUrl || "")
            fallbackIcon: root.fallbackIcon()
            fallbackText: ""
            previewSize: 48
            round: false
            outlined: true
            accent: root.accentColor()
            animateAppearance: root.animatePreview
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                Label {
                    text: root.kind.replace("_", " ").toUpperCase()
                    color: root.accentColor()
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.Bold
                }
                Label {
                    Layout.fillWidth: true
                    text: String(root.preview.title || qsTr("TACTIC item"))
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
            }

            Label {
                Layout.fillWidth: true
                text: String(root.preview.subtitle || "")
                visible: text.length > 0
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                elide: Text.ElideRight
            }

            Label {
                Layout.fillWidth: true
                text: root.failed
                    ? String(root.preview.error
                        || qsTr("Link preview is unavailable"))
                    : String(root.preview.detail || "")
                visible: text.length > 0
                color: root.failed ? root.theme.error : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                elide: Text.ElideRight
            }
        }

        Item {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28
            Controls.BusyIndicator {
                uiTheme: root.theme
                anchors.fill: parent
                visible: root.loadState === "loading"
                running: visible
            }
            Controls.CompactIconButton {
                anchors.fill: parent
                visible: root.loadState !== "loading"
                theme: root.theme
                iconName: root.failed ? "refresh" : "open_in_new"
                iconColor: root.failed ? root.theme.error : root.theme.action
                toolTip: root.failed
                    ? qsTr("Retry preview") : qsTr("Open linked item")
                onClicked: root.failed ? root.retryRequested() : root.activated()
            }
        }
    }

    RowLayout {
        id: knowledgeDetails
        objectName: "knowledgeSkeyPreview"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        visible: root.knowledgePreview
        spacing: 11

        Rectangle {
            Layout.preferredWidth: 46
            Layout.preferredHeight: 46
            Layout.alignment: Qt.AlignTop
            radius: root.theme.itemRadius
            color: root.theme.blend(
                root.theme.tertiary,
                root.theme.surfaceContainer,
                0.15)
            Controls.MaterialIcon {
                anchors.centerIn: parent
                name: String(root.preview.articleKind || "article")
                    === "section" ? "folder-open" : "book-open"
                size: 19
                color: root.theme.tertiary
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                Label {
                    text: qsTr("Knowledge Base")
                    color: root.theme.tertiary
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.Bold
                }
                Rectangle {
                    implicitWidth: knowledgeKind.implicitWidth + 10
                    implicitHeight: 20
                    radius: height / 2
                    color: root.theme.surfaceContainerHigh
                    Label {
                        id: knowledgeKind
                        anchors.centerIn: parent
                        text: String(root.preview.articleKind || "article")
                            === "section" ? qsTr("Section") : qsTr("Article")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                }
            }

            Label {
                objectName: "knowledgeSkeyPreviewTitle"
                Layout.fillWidth: true
                text: root.loadState === "loading"
                    ? qsTr("Loading article")
                    : String(root.preview.title || qsTr("Knowledge Base article"))
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            Label {
                objectName: "knowledgeSkeyPreviewDescription"
                Layout.fillWidth: true
                text: root.failed
                    ? String(root.preview.error
                        || qsTr("Link preview is unavailable"))
                    : root.loadState === "loading"
                        ? qsTr("Resolving Knowledge Base link")
                        : String(
                            root.preview.description
                                || root.preview.excerpt || "")
                visible: text.length > 0
                color: root.failed
                    ? root.theme.error : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                elide: Text.ElideRight
            }
        }

        Item {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28
            Layout.alignment: Qt.AlignVCenter
            Controls.BusyIndicator {
                uiTheme: root.theme
                anchors.fill: parent
                visible: root.loadState === "loading"
                running: visible
            }
            Controls.CompactIconButton {
                anchors.fill: parent
                visible: root.loadState !== "loading"
                theme: root.theme
                iconName: root.failed ? "refresh" : "arrow-forward"
                iconColor: root.failed
                    ? root.theme.error : root.theme.tertiary
                toolTip: root.failed
                    ? qsTr("Retry preview") : qsTr("Open article")
                onClicked: root.failed
                    ? root.retryRequested() : root.activated()
            }
        }
    }

    RowLayout {
        id: snapshotRow
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10
        visible: root.kind === "snapshot"

        Controls.ItemPreview {
            Layout.preferredWidth: 58
            Layout.preferredHeight: 58
            Layout.alignment: Qt.AlignVCenter
            theme: root.theme
            source: String(root.preview.previewUrl || "")
            fallbackIcon: "file"
            fallbackText: ""
            previewSize: 58
            round: false
            cornerRadius: 9
            accent: root.accentColor()
            animateAppearance: root.animatePreview
        }

        SnapshotSummary {
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight
            Layout.alignment: Qt.AlignVCenter
            theme: root.theme
            title: String(root.preview.title || "Snapshot")
            description: String(root.preview.description || "")
            version: String(root.preview.version || "")
            revision: String(root.preview.revision || "")
            repository: String(root.preview.repository || "")
            repositoryColor: String(root.preview.repositoryColor || "")
            fileSize: String(root.preview.fileSize || "")
            author: String(root.preview.author || "")
            timestamp: String(root.preview.timestamp || "")
            fileExists: root.preview.fileExists !== false
            isLatest: Boolean(root.preview.isLatest)
            infoChips: root.preview.infoChips || []
        }

        Item {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28

            Controls.BusyIndicator {
                uiTheme: root.theme
                anchors.fill: parent
                visible: root.loadState === "loading"
                running: visible
            }

            Controls.CompactIconButton {
                anchors.fill: parent
                visible: root.loadState !== "loading"
                theme: root.theme
                iconName: root.failed ? "refresh" : "open_in_new"
                iconColor: root.failed ? root.theme.error : root.theme.action
                toolTip: root.failed
                    ? qsTr("Retry preview") : qsTr("Open snapshot")
                onClicked: root.failed
                    ? root.retryRequested() : root.activated()
            }
        }
    }

    RowLayout {
        id: messageDetails
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 12
        visible: root.resolvedMessage
        spacing: 10

        Controls.ItemPreview {
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
            Layout.alignment: Qt.AlignTop
            theme: root.theme
            source: String(root.preview.avatarUrl || "")
            fallbackIcon: "person"
            fallbackText: String(root.preview.initials || "?")
            previewSize: 32
            round: true
            outlined: true
            accent: root.preview.authorColor || root.theme.action
            animateAppearance: root.animatePreview
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 7

            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Label {
                    id: messageAuthor
                    Layout.fillWidth: true
                    text: String(
                        root.preview.authorDisplay
                            || root.preview.author || "Removed user"
                    )
                    color: String(
                        root.preview.authorColor || root.theme.action
                    )
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                    font.underline: messageAuthorMouse.containsMouse
                    elide: Text.ElideRight

                    MouseArea {
                        id: messageAuthorMouse
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: Math.min(parent.width, messageAuthor.implicitWidth)
                        hoverEnabled: true
                        enabled: String(root.preview.author || "").length > 0
                        cursorShape: enabled
                            ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onClicked: root.nestedActivated(
                            "skey://sthpw/login?code="
                                + String(root.preview.author || ""))
                    }
                }

                Label {
                    id: messageTime
                    text: messageTimeMouse.containsMouse
                        ? String(
                            root.preview.timeSimple
                                || root.preview.detail || "")
                        : String(
                            root.preview.timePretty
                                || root.preview.detail || "")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption

                    MouseArea {
                        id: messageTimeMouse
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                }
            }

            TextEdit {
                Layout.fillWidth: true
                Layout.preferredHeight: contentHeight
                text: String(root.preview.body || "")
                visible: text.length > 0
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 14
                wrapMode: TextEdit.Wrap
                readOnly: true
                selectByMouse: true
                activeFocusOnTab: true
            }
        }
    }

    ColumnLayout {
        id: noteDetails
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.topMargin: 10
        visible: root.resolvedNote
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Controls.ItemPreview {
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                theme: root.theme
                source: String(root.preview.avatarUrl || "")
                fallbackIcon: "person"
                fallbackText: String(root.preview.initials || "?")
                previewSize: 32
                round: true
                outlined: true
                accent: root.preview.authorColor || root.theme.action
                animateAppearance: root.animatePreview
            }

            Label {
                id: noteAuthor
                Layout.fillWidth: true
                text: String(
                    root.preview.authorDisplay
                        || root.preview.author || "Removed user"
                )
                color: String(root.preview.authorColor || root.theme.action)
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
                font.underline: noteAuthorMouse.containsMouse
                elide: Text.ElideRight

                MouseArea {
                    id: noteAuthorMouse
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: Math.min(parent.width, noteAuthor.implicitWidth)
                    hoverEnabled: true
                    enabled: String(root.preview.author || "").length > 0
                    cursorShape: enabled
                        ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: root.nestedActivated(
                        "skey://sthpw/login?code="
                            + String(root.preview.author || ""))
                }
            }

            Label {
                id: noteTime
                text: noteTimeMouse.containsMouse
                    ? String(root.preview.timeSimple || root.preview.detail || "")
                    : String(root.preview.timePretty || root.preview.detail || "")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption

                MouseArea {
                    id: noteTimeMouse
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }

            Controls.CompactIconButton {
                id: noteActions
                theme: root.theme
                iconName: "more_vert"
                toolTip: qsTr("Note link actions")
                onClicked: {
                    const point = noteActions.mapToItem(
                        root, 0, noteActions.height)
                    root.contextRequested(point.x, point.y)
                }
            }
        }

        TextEdit {
            Layout.fillWidth: true
            text: String(root.preview.body || "")
            visible: text.length > 0
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 14
            wrapMode: TextEdit.Wrap
            readOnly: true
            selectByMouse: true
            activeFocusOnTab: true
        }

        Repeater {
            model: root.preview.nestedPreviews || []
            delegate: Item {
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                Controls.ItemSurface {
                    anchors.fill: parent
                    theme: root.theme
                    hovered: nestedHover.containsMouse
                    pressed: nestedHover.pressed
                    cornerRadius: 10
                    inset: 1
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 9
                    anchors.rightMargin: 9
                    spacing: 8
                    Controls.MaterialIcon {
                        name: String(modelData.icon || "link")
                        size: 17
                        color: modelData.status === "error"
                            ? root.theme.error : root.theme.action
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Label {
                            Layout.fillWidth: true
                            text: String(modelData.title || qsTr("Linked item"))
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: modelData.status === "error"
                                ? String(modelData.error
                                    || qsTr("Preview unavailable"))
                                : String(modelData.detail || modelData.subtitle || "")
                            color: modelData.status === "error"
                                ? root.theme.error : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            elide: Text.ElideRight
                        }
                    }
                }
                MouseArea {
                    id: nestedHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        const searchKey = String(modelData.searchKey || "")
                        if (modelData.status === "error")
                            root.nestedRetryRequested(searchKey)
                        else
                            root.nestedActivated(searchKey)
                    }
                }
            }
        }

        Label {
            Layout.fillWidth: true
            readonly property int hiddenCount: Math.max(
                0, Number(root.preview.nestedPreviewCount || 0)
                    - (root.preview.nestedPreviews || []).length)
            visible: hiddenCount > 0
            text: qsTr("+") + hiddenCount
                + (hiddenCount === 1
                    ? qsTr(" more linked item")
                    : qsTr(" more linked items"))
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
        }

        Controls.ResponsiveFlow {
            id: noteAttachmentFlow
            Layout.fillWidth: true
            visible: (root.preview.attachments || []).length > 0
            minimumCellWidth: 210
            preferredCellWidth: 240
            maximumColumns: 2
            spacing: 6

            Repeater {
                model: root.preview.attachments || []

                delegate: AttachmentCard {
                    id: linkedAttachment
                    required property var modelData
                    width: imageAttachment
                        ? noteAttachmentFlow.width
                        : noteAttachmentFlow.cellWidth()
                    theme: root.theme
                    title: String(modelData.title || qsTr("Attachment"))
                    extension: String(modelData.extension || "")
                    previewUrl: String(modelData.previewUrl || "")
                    sizeText: String(modelData.size || "")
                    local: true
                    onActivated: root.nestedActivated(
                        String(modelData.searchKey || ""))
                    onContextRequested: (localX, localY) => {
                        const point = linkedAttachment.mapToItem(
                            root, localX, localY)
                        root.contextRequested(point.x, point.y)
                    }
                }
            }
        }

        Label {
            Layout.fillWidth: true
            readonly property int hiddenCount: Math.max(
                0, Number(root.preview.attachmentCount || 0)
                    - (root.preview.attachments || []).length)
            visible: hiddenCount > 0
            text: qsTr("+") + hiddenCount
                + (hiddenCount === 1
                    ? qsTr(" more attachment")
                    : qsTr(" more attachments"))
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
        }
    }

}
