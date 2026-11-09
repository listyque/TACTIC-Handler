import QtQuick
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/activity/event.ui.mjs" as UI

Item {
    id: root
    objectName: "activityEventCard"

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
    property bool detailsExpanded: false
    readonly property int collapsedTextLimit: 80

    signal activityRequested
    signal targetRequested

    readonly property color accent: processColor.length ? processColor : typeColor.length ? typeColor : kind === "publication" ? theme.green : kind === "work_hour" ? theme.cyan : kind === "task" ? theme.yellow : theme.action
    readonly property bool showsChangeRows: (kind === "create" || kind === "change" || kind === "delete") && !relationAction.length && (changes || []).length > 0
    readonly property bool hasExpandableText: {
        if (textNeedsExpansion(detail) || textNeedsExpansion(eventTitle))
            return true;
        for (let index = 0; index < (changes || []).length; ++index) {
            if (textNeedsExpansion(plainChangeValue(changes[index])))
                return true;
        }
        return false;
    }
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    property var measured: ({})
    readonly property var presentation: UI.card({
        kind,
        relationAction,
        processColor,
        typeColor,
        actor,
        actorLabel,
        actorAvatar,
        actorInitials,
        actorColor,
        serverGenerated,
        time: timestampPretty,
        fullTime: timestampFull,
        changes: showsChangeRows ? (changes || []).map(row => ({
                    field: row.field,
                    label: fieldLabel(row.field)
                })) : [],
        expandable: hasExpandableText,
        expanded: detailsExpanded,
        hovered: hover.hovered
    }, width, measured, language, theme.styleName)
    implicitHeight: presentation.height
    function measure(key, item) {
        Qt.callLater(function () {
            if (item && item.width > 0 && item.contentHeight >= 0 && root.measured[key] !== item.contentHeight)
                root.measured = Object.assign({}, root.measured, {
                    [key]: item.contentHeight
                });
        });
    }

    function activityIcon(value) {
        if (root.relationAction.length)
            return "link";
        switch (String(value || "")) {
        case "publication":
            return "snapshot";
        case "note":
            return "notes";
        case "task":
            return "task";
        case "work_hour":
            return "schedule";
        case "status":
            return "system-activity";
        case "create":
            return "add";
        case "delete":
            return "delete";
        case "change":
            return "edit";
        default:
            return "activity-feed";
        }
    }

    function processLabel() {
        if (root.process.length)
            return root.process;
        return String(root.context || "").split("/")[0];
    }

    function versionValue() {
        const value = String(root.version || "");
        if (/^v/i.test(value) || !/^\d+$/.test(value))
            return value;
        return "v" + value.padStart(3, "0");
    }

    function shortSearchType(value) {
        const parts = String(value || "").split("/");
        return parts.length ? parts[parts.length - 1].replace(/_/g, " ") : "";
    }

    function escapeHtml(value) {
        return String(value || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;");
    }

    function richLink(value, action, enabled) {
        const label = root.escapeHtml(value);
        if (!enabled || !label.length)
            return label;
        return '<a style="color:' + root.theme.action + '" href="' + action + '">' + label + '</a>';
    }

    function safeColor(value) {
        const color = String(value || "");
        return /^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(color) ? color : "";
    }

    function colored(value, color) {
        const label = root.escapeHtml(value);
        const safe = root.safeColor(color);
        return safe.length ? '<span style="color:' + safe + '">' + label + '</span>' : label;
    }

    function semanticLabel(value, color) {
        const safe = root.safeColor(color);
        return safe.length ? root.colored("● " + value, safe) : root.escapeHtml(value);
    }

    function targetReference() {
        const title = root.targetTitle.length ? root.targetTitle : qsTr("the related object");
        const target = root.richLink(title, "target", root.canOpenTarget);
        const searchType = root.targetTypeTitle.length ? root.targetTypeTitle : root.relationAction.length ? "" : root.shortSearchType(root.targetType);
        return searchType.length ? root.semanticLabel(searchType, root.typeColor) + " / " + target : target;
    }

    function itemReference() {
        const title = root.itemTitle.length ? root.itemTitle : qsTr("the related object");
        const item = root.richLink(title, "activity", root.canOpenActivity);
        const searchType = root.itemTypeLabel();
        return searchType.length ? root.semanticLabel(searchType, root.itemTypeColor) + " / " + item : item;
    }

    function itemTypeLabel() {
        if (root.itemTypeTitle.length)
            return root.itemTypeTitle;
        switch (String(root.itemType || "")) {
        case "sthpw/task":
            return qsTr("Task");
        case "sthpw/note":
            return qsTr("Note");
        case "sthpw/snapshot":
            return qsTr("Snapshot");
        default:
            return root.shortSearchType(root.itemType);
        }
    }

    function processPhrase() {
        const value = root.processLabel();
        return value.length ? qsTr(" in process %1").arg("<b>" + root.semanticLabel(value, root.processColor) + "</b>") : "";
    }

    function contextPhrase() {
        const value = String(root.context || "");
        if (!value.length || value === root.processLabel())
            return "";
        return qsTr(", context %1").arg("<b>" + root.escapeHtml(value) + "</b>");
    }

    function detailPhrase() {
        const value = root.detailsExpanded ? root.detail : root.compactText(root.detail);
        if (typeof appController !== "undefined" && appController.rich_text_html)
            return appController.rich_text_html(value);
        return root.escapeHtml(value).replace(/\r?\n/g, "<br>");
    }

    function normalizedText(value) {
        return String(value || "").replace(/\s+/g, " ").trim();
    }

    function compactText(value) {
        const normalized = root.normalizedText(value);
        if (normalized.length <= root.collapsedTextLimit)
            return normalized;
        return normalized.slice(0, root.collapsedTextLimit).replace(/\s+$/, "") + "…";
    }

    function textNeedsExpansion(value) {
        const raw = String(value || "");
        return /[\r\n]/.test(raw) || root.normalizedText(raw).length > root.collapsedTextLimit;
    }

    function richValue(value) {
        if (typeof appController !== "undefined" && appController.rich_text_html)
            return appController.rich_text_html(String(value || ""));
        return root.escapeHtml(value);
    }

    function openRichLink(link) {
        if (link === "target") {
            root.targetRequested();
            return;
        }
        if (link === "activity") {
            root.activityRequested();
            return;
        }
        if (typeof appController !== "undefined" && appController.open_rich_link)
            appController.open_rich_link(link);
    }

    function fieldLabel(value) {
        switch (String(value || "").toLowerCase()) {
        case "name":
            return qsTr("Name");
        case "title":
            return qsTr("Title");
        case "description":
            return qsTr("Description");
        case "assigned":
            return qsTr("Assignee");
        case "status":
            return qsTr("Status");
        case "priority":
            return qsTr("Priority");
        case "bid start date":
            return qsTr("Start date");
        case "bid end date":
            return qsTr("Deadline");
        default:
            return String(value || "");
        }
    }

    function plainChangeValue(change) {
        if (change.valuesKnown === false)
            return qsTr("Changed");
        const before = String(change.before || "");
        const after = String(change.after || "");
        if (root.kind === "create" && after.length)
            return after;
        if (root.kind === "delete" && before.length)
            return qsTr("Previous value: %1").arg(before);
        if (before.length || after.length) {
            return (before.length ? before : qsTr("empty")) + " → " + (after.length ? after : qsTr("empty"));
        }
        return qsTr("Changed");
    }

    function changeValue(change) {
        if (!root.detailsExpanded)
            return root.escapeHtml(root.compactText(root.plainChangeValue(change)));
        if (change.valuesKnown === false)
            return qsTr("Changed");
        const before = root.richValue(change.before || "");
        const after = root.richValue(change.after || "");
        if (root.kind === "create" && after.length)
            return after;
        if (root.kind === "delete" && before.length)
            return qsTr("Previous value: %1").arg(before);
        if (before.length || after.length) {
            return (before.length ? before : qsTr("empty")) + " → " + (after.length ? after : qsTr("empty"));
        }
        return qsTr("Changed");
    }

    function eventSentence() {
        const target = root.targetReference();
        const process = root.processPhrase();
        const context = root.contextPhrase();
        const detail = root.detailPhrase();
        const item = root.richLink(root.itemTitle || root.itemCode || qsTr("snapshot"), "activity", root.canOpenActivity);
        const action = root.richLink(root.kind === "note" ? qsTr("Open note") : root.kind === "task" ? qsTr("Open task") : qsTr("Open details"), "activity", root.canOpenActivity);

        if (root.relationAction === "link")
            return qsTr("Linked %1 to %2.").arg(root.itemReference()).arg(target);
        if (root.relationAction === "unlink")
            return qsTr("Removed the link between %1 and %2.").arg(root.itemReference()).arg(target);

        switch (root.kind) {
        case "work_hour":
            {
                const hoursValue = Number(root.hours || 0);
                const hoursText = qsTr("%1 h").arg(hoursValue.toLocaleString(Qt.locale(), "f", Number.isInteger(hoursValue) ? 0 : 2));
                const workDate = root.workDayPretty.length ? root.workDayPretty : qsTr("No date");
                const category = root.workHourCategory === "overtime" ? qsTr("Overtime") : qsTr("Regular");
                const status = root.workHourStatus.toLowerCase() === "approved" ? qsTr("Approved") : qsTr("Pending");
                const owner = root.workHourOwner.length && root.workHourOwner !== root.actor ? qsTr(" for user %1").arg("<b>" + root.escapeHtml(root.workHourOwner) + "</b>") : "";
                const description = detail.length ? qsTr(" Comment: “%1”").arg(detail) : "";
                const sentence = root.workHourAction === "delete" ? qsTr("Deleted a %1 work-hours entry%2 for %3%4 on %5 (%6).") : root.workHourAction === "change" ? qsTr("Updated work hours to %1%2 for %3%4 on %5 (%6, %7).") : qsTr("Logged %1%2 for %3%4 on %5 (%6, %7).");
                return root.workHourAction === "delete" ? sentence.arg(hoursText).arg(owner).arg(target).arg(process).arg(root.escapeHtml(workDate)).arg(category) + description : sentence.arg(hoursText).arg(owner).arg(target).arg(process).arg(root.escapeHtml(workDate)).arg(category).arg(status) + description;
            }
        case "publication":
            {
                const version = root.version.length ? qsTr(", version %1").arg("<b>" + root.escapeHtml(root.versionValue()) + "</b>") : "";
                const comment = detail.length ? qsTr(" Comment: “%1”").arg(detail) : "";
                return qsTr("Committed snapshot %1 to %2%3%4%5.%6").arg(item).arg(target).arg(process).arg(context).arg(version).arg(comment);
            }
        case "note":
            return qsTr("Added a note to %1%2%3: %4 %5").arg(target).arg(process).arg(context).arg(detail || qsTr("No text")).arg(action);
        case "task":
            return (root.serverGenerated ? qsTr("Created task for %1%2%3: %4") : qsTr("Updated task for %1%2%3: %4")).arg(target).arg(process).arg(context).arg(root.statusAfter.length ? "<b>" + root.colored(root.statusAfter, root.statusAfterColor) + "</b>" : detail || action);
        case "status":
            if (root.statusBefore.length || root.statusAfter.length) {
                return qsTr("Changed status for %1%2%3: %4 → %5.").arg(target).arg(process).arg(context).arg("<b>" + root.colored(root.statusBefore || "—", root.statusBeforeColor) + "</b>").arg("<b>" + root.colored(root.statusAfter || "—", root.statusAfterColor) + "</b>");
            }
            return qsTr("Updated the status of %1%2%3: %4").arg(target).arg(process).arg(context).arg(detail || action);
        case "create":
            if (root.itemType.length)
                return qsTr("Created %1 for %2.").arg(root.itemReference()).arg(target);
            return qsTr("Created object: %1.").arg(target);
        case "delete":
            if (root.itemType.length)
                return qsTr("Deleted %1 from %2.").arg(root.itemReference()).arg(target);
            return qsTr("Deleted object: %1.").arg(target);
        case "change":
            if (root.itemType.length)
                return qsTr("Updated %1 for %2.%3").arg(root.itemReference()).arg(target).arg(root.showsChangeRows || !detail.length ? "" : " " + detail);
            return qsTr("Updated object: %1.%2").arg(target).arg(root.showsChangeRows || !detail.length ? "" : " " + detail);
        default:
            return detail.length ? detail : root.escapeHtml(root.detailsExpanded ? root.eventTitle : root.compactText(root.eventTitle));
        }
    }

    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.presentation
        views: ({
                sentence: sentencePort,
                change: {
                    component: changePort,
                    nodeProps: true
                }
            })
        onEvent: action => {
            if (action.type === "expand")
                root.detailsExpanded = !root.detailsExpanded;
        }
    }
    HoverHandler {
        id: hover
    }
    Component {
        id: sentencePort
        Controls.SelectableText {
            id: activitySentence
            objectName: "activitySentence"
            theme: root.theme
            richText: true
            text: root.eventSentence()
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 13,
                hintingPreference: Font.PreferVerticalHinting
            })
            onWidthChanged: root.measure("sentence", activitySentence)
            onContentHeightChanged: root.measure("sentence", activitySentence)
            Component.onCompleted: root.measure("sentence", activitySentence)
            Controls.ActivationHandler {
                cursorShape: activitySentence.hoveredLink.length ? Qt.PointingHandCursor : Qt.IBeamCursor
                onActivated: function (modifiers, x, y) {
                    const link = activitySentence.linkAt(x, y);
                    if (link.length)
                        root.openRichLink(link);
                }
            }
        }
    }
    Component {
        id: changePort
        Controls.SelectableText {
            id: changeText
            property var frameNode: ({
                    index: 0
                })
            objectName: "activityChangeText_" + frameNode.index
            theme: root.theme
            richText: true
            text: root.changeValue(root.changes[frameNode.index] || {})
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 12,
                hintingPreference: Font.PreferVerticalHinting
            })
            onWidthChanged: root.measure("change_" + frameNode.index, changeText)
            onContentHeightChanged: root.measure("change_" + frameNode.index, changeText)
            Component.onCompleted: root.measure("change_" + frameNode.index, changeText)
            Controls.ActivationHandler {
                cursorShape: changeText.hoveredLink.length ? Qt.PointingHandCursor : Qt.IBeamCursor
                onActivated: function (modifiers, x, y) {
                    const link = changeText.linkAt(x, y);
                    if (link.length)
                        root.openRichLink(link);
                }
            }
        }
    }
}
