import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property string kind: "activity"
    property string eventTitle: ""
    property string detail: ""
    property string actor: ""
    property string actorLabel: actor
    property string actorAvatar: ""
    property string actorInitials: "?"
    property string actorColor: ""
    property string timestamp: ""
    property string timestampPretty: ""
    property string timestampFull: ""
    property string targetSearchKey: ""
    property string targetTitle: ""
    property string targetType: ""
    property string targetTypeTitle: ""
    property string typeColor: ""
    property string processColor: ""
    property string itemCode: ""
    property string itemTitle: ""
    property string itemType: ""
    property string itemTypeTitle: ""
    property string itemTypeColor: ""
    property string relationAction: ""
    property string process: ""
    property string context: ""
    property string version: ""
    property string statusBefore: ""
    property string statusAfter: ""
    property string statusBeforeColor: ""
    property string statusAfterColor: ""
    property var changes: []
    property string taskCode: ""
    property real hours: 0
    property string workDay: ""
    property string workDayPretty: ""
    property string workHourAction: ""
    property string workHourCategory: ""
    property string workHourStatus: ""
    property string workHourOwner: ""
    property bool serverGenerated: false
    property bool canOpenActivity: false
    property bool canOpenTarget: false

    signal activityRequested()
    signal targetRequested()

    readonly property color accent: processColor.length
        ? processColor : typeColor.length ? typeColor
        : kind === "publication" ? theme.green
        : kind === "work_hour" ? theme.cyan
        : kind === "task" ? theme.yellow : theme.action
    readonly property bool showsChangeRows: (
        kind === "create" || kind === "change" || kind === "delete"
    ) && !relationAction.length && (changes || []).length > 0
    readonly property real avatarExtent: width < 380 ? 34 : 40
    readonly property real bubbleExtent: Math.max(
        0,
        Math.min(
            760,
            width - avatarExtent - theme.communicationAvatarSpacing - 8
        )
    )
    implicitHeight: Math.max(72, eventBubble.implicitHeight + 8)

    function activityIcon(value) {
        if (root.relationAction.length)
            return "link"
        switch (String(value || "")) {
        case "publication": return "snapshot"
        case "note": return "notes"
        case "task": return "task"
        case "work_hour": return "schedule"
        case "status": return "system-activity"
        case "create": return "add"
        case "delete": return "delete"
        case "change": return "edit"
        default: return "activity-feed"
        }
    }

    function processLabel() {
        if (root.process.length)
            return root.process
        return String(root.context || "").split("/")[0]
    }

    function versionValue() {
        const value = String(root.version || "")
        if (/^v/i.test(value) || !/^\d+$/.test(value))
            return value
        return "v" + value.padStart(3, "0")
    }

    function shortSearchType(value) {
        const parts = String(value || "").split("/")
        return parts.length
            ? parts[parts.length - 1].replace(/_/g, " ") : ""
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
    }

    function richLink(value, action, enabled) {
        const label = root.escapeHtml(value)
        if (!enabled || !label.length)
            return label
        return '<a style="color:' + root.theme.action
            + '" href="' + action + '">' + label + '</a>'
    }

    function safeColor(value) {
        const color = String(value || "")
        return /^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(color)
            ? color : ""
    }

    function colored(value, color) {
        const label = root.escapeHtml(value)
        const safe = root.safeColor(color)
        return safe.length
            ? '<span style="color:' + safe + '">' + label + '</span>'
            : label
    }

    function semanticLabel(value, color) {
        const safe = root.safeColor(color)
        return safe.length
            ? root.colored("● " + value, safe)
            : root.escapeHtml(value)
    }

    function targetReference() {
        const title = root.targetTitle.length
            ? root.targetTitle : qsTr("the related object")
        const target = root.richLink(title, "target", root.canOpenTarget)
        const searchType = root.targetTypeTitle.length
            ? root.targetTypeTitle
            : root.relationAction.length
            ? "" : root.shortSearchType(root.targetType)
        return searchType.length
            ? root.semanticLabel(searchType, root.typeColor) + " / " + target
            : target
    }

    function itemReference() {
        const title = root.itemTitle.length
            ? root.itemTitle : qsTr("the related object")
        const item = root.richLink(
            title, "activity", root.canOpenActivity
        )
        const searchType = root.itemTypeLabel()
        return searchType.length
            ? root.semanticLabel(searchType, root.itemTypeColor) + " / " + item
            : item
    }

    function itemTypeLabel() {
        if (root.itemTypeTitle.length)
            return root.itemTypeTitle
        switch (String(root.itemType || "")) {
        case "sthpw/task": return qsTr("Task")
        case "sthpw/note": return qsTr("Note")
        case "sthpw/snapshot": return qsTr("Snapshot")
        default: return root.shortSearchType(root.itemType)
        }
    }

    function processPhrase() {
        const value = root.processLabel()
        return value.length
            ? qsTr(" in process %1").arg(
                "<b>" + root.semanticLabel(value, root.processColor) + "</b>"
            )
            : ""
    }

    function contextPhrase() {
        const value = String(root.context || "")
        if (!value.length || value === root.processLabel())
            return ""
        return qsTr(", context %1").arg("<b>" + root.escapeHtml(value) + "</b>")
    }

    function detailPhrase() {
        if (typeof appController !== "undefined"
                && appController.rich_text_html)
            return appController.rich_text_html(root.detail)
        return root.escapeHtml(root.detail).replace(/\r?\n/g, "<br>")
    }

    function richValue(value) {
        if (typeof appController !== "undefined"
                && appController.rich_text_html)
            return appController.rich_text_html(String(value || ""))
        return root.escapeHtml(value)
    }

    function openRichLink(link) {
        if (link === "target") {
            root.targetRequested()
            return
        }
        if (link === "activity") {
            root.activityRequested()
            return
        }
        if (typeof appController !== "undefined"
                && appController.open_rich_link)
            appController.open_rich_link(link)
    }

    function fieldLabel(value) {
        switch (String(value || "").toLowerCase()) {
        case "name": return qsTr("Name")
        case "title": return qsTr("Title")
        case "description": return qsTr("Description")
        case "assigned": return qsTr("Assignee")
        case "status": return qsTr("Status")
        case "priority": return qsTr("Priority")
        case "bid start date": return qsTr("Start date")
        case "bid end date": return qsTr("Deadline")
        default: return String(value || "")
        }
    }

    function changeValue(change) {
        if (change.valuesKnown === false)
            return qsTr("Changed")
        const before = root.richValue(change.before || "")
        const after = root.richValue(change.after || "")
        if (root.kind === "create" && after.length)
            return after
        if (root.kind === "delete" && before.length)
            return qsTr("Previous value: %1").arg(before)
        if (before.length || after.length) {
            return (before.length ? before : qsTr("empty")) + " → "
                + (after.length ? after : qsTr("empty"))
        }
        return qsTr("Changed")
    }

    function eventSentence() {
        const target = root.targetReference()
        const process = root.processPhrase()
        const context = root.contextPhrase()
        const detail = root.detailPhrase()
        const item = root.richLink(
            root.itemTitle || root.itemCode || qsTr("snapshot"),
            "activity",
            root.canOpenActivity
        )
        const action = root.richLink(
            root.kind === "note" ? qsTr("Open note")
                : root.kind === "task" ? qsTr("Open task")
                : qsTr("Open details"),
            "activity",
            root.canOpenActivity
        )

        if (root.relationAction === "link")
            return qsTr("Linked %1 to %2.")
                .arg(root.itemReference()).arg(target)
        if (root.relationAction === "unlink")
            return qsTr("Removed the link between %1 and %2.")
                .arg(root.itemReference()).arg(target)

        switch (root.kind) {
        case "work_hour": {
            const hoursValue = Number(root.hours || 0)
            const hoursText = qsTr("%1 h").arg(
                hoursValue.toLocaleString(Qt.locale(), "f",
                    Number.isInteger(hoursValue) ? 0 : 2)
            )
            const workDate = root.workDayPretty.length
                ? root.workDayPretty : qsTr("No date")
            const category = root.workHourCategory === "overtime"
                ? qsTr("Overtime") : qsTr("Regular")
            const status = root.workHourStatus.toLowerCase() === "approved"
                ? qsTr("Approved") : qsTr("Pending")
            const owner = root.workHourOwner.length
                    && root.workHourOwner !== root.actor
                ? qsTr(" for user %1").arg(
                    "<b>" + root.escapeHtml(root.workHourOwner) + "</b>"
                ) : ""
            const description = detail.length
                ? qsTr(" Comment: “%1”").arg(detail) : ""
            const sentence = root.workHourAction === "delete"
                ? qsTr("Deleted a %1 work-hours entry%2 for %3%4 on %5 (%6).")
                : root.workHourAction === "change"
                ? qsTr("Updated work hours to %1%2 for %3%4 on %5 (%6, %7).")
                : qsTr("Logged %1%2 for %3%4 on %5 (%6, %7).")
            return root.workHourAction === "delete"
                ? sentence.arg(hoursText).arg(owner).arg(target)
                    .arg(process).arg(root.escapeHtml(workDate)).arg(category)
                    + description
                : sentence.arg(hoursText).arg(owner).arg(target)
                    .arg(process).arg(root.escapeHtml(workDate))
                    .arg(category).arg(status) + description
        }
        case "publication": {
            const version = root.version.length
                ? qsTr(", version %1").arg(
                    "<b>" + root.escapeHtml(root.versionValue()) + "</b>"
                ) : ""
            const comment = detail.length
                ? qsTr(" Comment: “%1”").arg(detail) : ""
            return qsTr("Committed snapshot %1 to %2%3%4%5.%6")
                .arg(item).arg(target).arg(process).arg(context).arg(version)
                .arg(comment)
        }
        case "note":
            return qsTr("Added a note to %1%2%3: %4 %5")
                .arg(target).arg(process).arg(context)
                .arg(detail || qsTr("No text")).arg(action)
        case "task":
            return (root.serverGenerated
                ? qsTr("Created task for %1%2%3: %4")
                : qsTr("Updated task for %1%2%3: %4"))
                .arg(target).arg(process).arg(context)
                .arg(root.statusAfter.length
                    ? "<b>" + root.colored(
                        root.statusAfter, root.statusAfterColor
                    ) + "</b>"
                    : detail || action)
        case "status":
            if (root.statusBefore.length || root.statusAfter.length) {
                return qsTr("Changed status for %1%2%3: %4 → %5.")
                    .arg(target).arg(process).arg(context)
                    .arg("<b>" + root.colored(
                        root.statusBefore || "—", root.statusBeforeColor
                    ) + "</b>")
                    .arg("<b>" + root.colored(
                        root.statusAfter || "—", root.statusAfterColor
                    ) + "</b>")
            }
            return qsTr("Updated the status of %1%2%3: %4")
                .arg(target).arg(process).arg(context).arg(detail || action)
        case "create":
            if (root.itemType.length)
                return qsTr("Created %1 for %2.")
                    .arg(root.itemReference()).arg(target)
            return qsTr("Created object: %1.").arg(target)
        case "delete":
            if (root.itemType.length)
                return qsTr("Deleted %1 from %2.")
                    .arg(root.itemReference()).arg(target)
            return qsTr("Deleted object: %1.").arg(target)
        case "change":
            if (root.itemType.length)
                return qsTr("Updated %1 for %2.%3")
                    .arg(root.itemReference()).arg(target)
                    .arg(root.showsChangeRows || !detail.length
                        ? "" : " " + detail)
            return qsTr("Updated object: %1.%2")
                .arg(target)
                .arg(root.showsChangeRows || !detail.length
                    ? "" : " " + detail)
        default:
            return detail.length ? detail : root.escapeHtml(root.eventTitle)
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 4
        anchors.rightMargin: 4
        anchors.topMargin: 4
        anchors.bottomMargin: 4
        spacing: root.theme.communicationAvatarSpacing

        Controls.ItemPreview {
            objectName: "activityActorPreview"
            Layout.preferredWidth: root.avatarExtent
            Layout.preferredHeight: root.avatarExtent
            Layout.alignment: Qt.AlignTop
            theme: root.theme
            source: root.actorAvatar
            fallbackIcon: root.serverGenerated ? "system-activity" : "person"
            fallbackText: root.serverGenerated ? "" : root.actorInitials
            previewSize: root.avatarExtent
            round: true
            outlined: true
            accent: root.actorColor.length ? root.actorColor : root.theme.action
        }

        Item {
            id: eventBubble
            Layout.preferredWidth: root.bubbleExtent
            Layout.minimumWidth: 0
            implicitHeight: bubbleContent.implicitHeight + 20

            HoverHandler { id: bubbleHover }

            Controls.ItemSurface {
                anchors.fill: parent
                theme: root.theme
                hovered: bubbleHover.hovered
                normalColor: root.theme.surfaceContainerHigh
                cornerRadius: root.theme.communicationBubbleRadius
                borderWidth: 1
                borderColor: root.theme.outlineVariant
                railVisible: false
                separatorVisible: false
            }

            ColumnLayout {
                id: bubbleContent
                anchors.fill: parent
                anchors.margins: 10
                spacing: root.theme.communicationContentSpacing

                GridLayout {
                    Layout.fillWidth: true
                    columns: eventBubble.width >= 520 ? 2 : 1
                    columnSpacing: 8
                    rowSpacing: 2

                    Label {
                        objectName: "activityActorLabel"
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        text: root.serverGenerated
                            ? qsTr("Server trigger")
                            : root.actorLabel.length
                            ? root.actorLabel : qsTr("Unknown user")
                        color: root.theme.action
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: eventBubble.width < 520
                        Layout.minimumWidth: 0
                        Layout.alignment: eventBubble.width >= 520
                            ? Qt.AlignRight : Qt.AlignLeft
                        text: root.timestampPretty
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight

                        HoverHandler { id: timestampHover }
                        Controls.ToolTip {
                            theme: root.theme
                            visible: timestampHover.hovered
                                && root.timestampFull.length > 0
                            text: root.timestampFull
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Controls.MaterialIcon {
                        Layout.alignment: Qt.AlignTop
                        name: root.activityIcon(root.kind)
                        size: 20
                        color: root.accent
                    }
                    Controls.SelectableText {
                        id: activitySentence
                        objectName: "activitySentence"
                        Layout.fillWidth: true
                        Layout.preferredHeight: contentHeight
                        theme: root.theme
                        richText: true
                        text: root.eventSentence()
                        font.pointSize: Controls.Typography.body

                        Controls.ActivationHandler {
                            cursorShape: activitySentence.hoveredLink.length
                                ? Qt.PointingHandCursor : Qt.IBeamCursor
                            onActivated: function(modifiers, x, y) {
                                const link = activitySentence.linkAt(x, y)
                                if (link.length)
                                    root.openRichLink(link)
                            }
                        }
                    }
                }

                ColumnLayout {
                    id: activityChangeList
                    objectName: "activityChangeList"
                    visible: root.showsChangeRows
                    Layout.fillWidth: true
                    spacing: 4

                    Repeater {
                        model: root.showsChangeRows ? root.changes : []

                        delegate: Rectangle {
                            id: changeDelegate
                            required property var modelData

                            Layout.fillWidth: true
                            implicitHeight: changeRow.implicitHeight + 10
                            radius: root.theme.itemRadius
                            color: root.theme.surfaceContainer
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            RowLayout {
                                id: changeRow
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                anchors.topMargin: 5
                                anchors.bottomMargin: 5
                                spacing: 10

                                Label {
                                    Layout.preferredWidth: Math.min(
                                        116, Math.max(72, implicitWidth)
                                    )
                                    Layout.maximumWidth: 116
                                    text: root.fieldLabel(
                                        changeDelegate.modelData.field
                                    )
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                                Controls.SelectableText {
                                    id: changeText
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: contentHeight
                                    theme: root.theme
                                    richText: true
                                    text: root.changeValue(
                                        changeDelegate.modelData
                                    )
                                    font.pointSize: Controls.Typography.label

                                    Controls.ActivationHandler {
                                        cursorShape: changeText.hoveredLink.length
                                            ? Qt.PointingHandCursor
                                            : Qt.IBeamCursor
                                        onActivated: function(modifiers, x, y) {
                                            const link = changeText.linkAt(x, y)
                                            if (link.length)
                                                root.openRichLink(link)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Item {
            visible: root.width > 840
            Layout.fillWidth: true
            Layout.minimumWidth: 0
        }
    }
}
