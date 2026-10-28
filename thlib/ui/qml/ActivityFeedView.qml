import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/activity/feed.ui.mjs" as UI

Item {
    id: root

    required property var theme
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language

    readonly property bool narrowToolbar: width < 760
    readonly property bool compactFilterSegments: width < 1000
    readonly property bool compactCalendarButton: width < 1120
    readonly property bool showUserFilterLabel: width >= 1320
    readonly property string interfaceLocaleName: {
        if (typeof localizationController === "undefined")
            return Qt.locale().name;
        return String(localizationController.current_language) === "ru" ? "ru_RU" : "en_US";
    }
    readonly property var interfaceLocale: Qt.locale(interfaceLocaleName)
    property var pendingUserLogins: []
    readonly property var feedFilters: [
        {
            "value": "all",
            "label": "All",
            "icon": "select-all"
        },
        {
            "value": "my_tasks",
            "label": "My tasks",
            "icon": "task"
        },
        {
            "value": "my_objects",
            "label": "My objects",
            "icon": "inventory-2"
        },
        {
            "value": "notes",
            "label": "Notes",
            "icon": "notes"
        },
        {
            "value": "publications",
            "label": "Publications",
            "icon": "snapshot"
        }
    ]

    function dateKey(value) {
        const year = value.getFullYear();
        const month = String(value.getMonth() + 1).padStart(2, "0");
        const day = String(value.getDate()).padStart(2, "0");
        return year + "-" + month + "-" + day;
    }

    function dateFromKey(value) {
        const parts = String(value || "").split("-");
        if (parts.length !== 3)
            return null;
        const result = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]), 12);
        return Number.isNaN(result.getTime()) ? null : result;
    }

    function selectedDayLabel() {
        const value = dateFromKey(activityFeedController.selectedDay);
        return value ? Qt.formatDate(value, interfaceLocale, "d MMM yyyy") : qsTr("All history");
    }

    function dayHeaderLabel(value) {
        const date = dateFromKey(value);
        if (!date)
            return qsTr("No date");
        const today = new Date(activityFeedController.currentTime);
        const yesterday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1, 12);
        const suffix = Qt.formatDate(date, interfaceLocale, date.getFullYear() === today.getFullYear() ? "d MMMM" : "d MMMM yyyy");
        if (dateKey(date) === dateKey(today))
            return qsTr("Today") + "  ·  " + suffix;
        if (dateKey(date) === dateKey(yesterday))
            return qsTr("Yesterday") + "  ·  " + suffix;
        return suffix;
    }

    function userFilterTitle() {
        const logins = activityFeedController.selectedUsers || [];
        if (!logins.length)
            return qsTr("All users");
        if (logins.length > 1)
            return qsTr("%1 users").arg(logins.length);
        const login = String(logins[0] || "");
        for (let index = 0; index < userListModel.count(); ++index) {
            const user = userListModel.get(index);
            if (String(user.login || "") === login)
                return String(user.displayName || login);
        }
        return login;
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    Rectangle {
        id: feedPanel
        objectName: "activityFeedPanel"
        anchors.fill: parent
        anchors.margins: 12
        radius: root.theme.surfaceRadius
        color: root.theme.panel
        border.width: 1
        border.color: root.theme.outlineVariant
        clip: true

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            Frame.FrameView {
                id: feedToolbar
                objectName: "activityFeedToolbar"
                Layout.fillWidth: true
                Layout.preferredHeight: scene.height
                theme: root.theme
                scene: UI.toolbar({
                    notifications: activityFeedController.notificationsEnabled,
                    excludeOwn: activityFeedController.excludeOwnActivity,
                    search: activityFeedController.searchText,
                    filter: activityFeedController.currentFilter,
                    userTitle: root.userFilterTitle(),
                    userCount: activityFeedController.selectedUsers.length,
                    day: activityFeedController.selectedDay,
                    dayLabel: root.selectedDayLabel(),
                    busy: activityFeedController.busy
                }, width, root.language)
                onEvent: (action, source) => {
                    if (action.type === "notifications")
                        activityFeedController.set_notifications_enabled(action.value);
                    else if (action.type === "exclude")
                        activityFeedController.set_exclude_own_activity(action.value);
                    else if (action.type === "search")
                        activityFeedController.set_search_text(action.value);
                    else if (action.type === "filter")
                        activityFeedController.set_filter(action.value);
                    else if (action.type === "refresh")
                        activityFeedController.refresh();
                    else if (action.type === "users-press")
                        userFilterPopup.rememberSourceOpen();
                    else if (action.type === "users")
                        userFilterPopup.toggleBelowItem(source, true, 6);
                    else if (action.type === "calendar-press")
                        activityCalendar.rememberSourceOpen();
                    else if (action.type === "calendar")
                        activityCalendar.showBelow(source);
                }
            }

            Label {
                visible: activityFeedController.error.length > 0
                Layout.fillWidth: true
                text: activityFeedController.error
                color: root.theme.error
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
            }

            Controls.SmoothListView {
                id: feed
                theme: root.theme
                objectName: "activityFeedList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.rightMargin: 8
                clip: true
                spacing: 6
                model: activityFeedModel
                section.property: "dayKey"
                section.criteria: ViewSection.FullString
                section.labelPositioning: ViewSection.InlineLabels | ViewSection.CurrentLabelAtStart
                section.delegate: Frame.FrameView {
                    required property string section
                    width: Math.max(0, feed.width - 12)
                    height: 34
                    z: 2
                    theme: root.theme
                    scene: UI.day(root.dayHeaderLabel(section), width)
                }

                ScrollBar.vertical: Controls.ScrollBar {
                    id: activityFeedScrollBar
                    objectName: "activityFeedScrollBar"
                    theme: root.theme
                    flickableTarget: feed
                }

                property real lastWheelDelta: 0
                property bool paginationCheckQueued: false
                function requestMoreIfNeeded() {
                    if (paginationCheckQueued)
                        return;
                    paginationCheckQueued = true;
                    // Let the result owner finish reconciliation before inspecting the new page.
                    Qt.callLater(function () {
                        feed.paginationCheckQueued = false;
                        if (!feed.visible || activityFeedController.busy || activityFeedController.error || !activityFeedController.hasMore)
                            return;
                        // Model notifications precede ListView polish. Do not mistake
                        // the old (or zero) extent for an underfilled new page.
                        feed.forceLayout();
                        const underfilled = contentHeight <= height + 1;
                        if (!underfilled && feed.lastWheelDelta > 0)
                            return;
                        if ((!underfilled && !atYEnd && maximumContentY - contentY > feed.wheelStep) || !activityFeedScrollBar.takePaginationPermit(underfilled))
                            return;
                        activityFeedController.load_more();
                    });
                }

                onDraggingChanged: if (dragging)
                    lastWheelDelta = 0
                onFlickStarted: lastWheelDelta = 0
                onMovementEnded: feed.requestMoreIfNeeded()
                onWheelScrollRequested: delta => {
                    lastWheelDelta = delta;
                    if (delta < 0)
                        feed.requestMoreIfNeeded();
                }
                onInteractionMovingChanged: {
                    if (!interactionMoving)
                        feed.requestMoreIfNeeded();
                }
                onAtYEndChanged: feed.requestMoreIfNeeded()
                onCountChanged: feed.requestMoreIfNeeded()
                onVisibleChanged: feed.requestMoreIfNeeded()

                Connections {
                    target: activityFeedController
                    function onStateChanged() {
                        if (!activityFeedController.busy)
                            feed.requestMoreIfNeeded();
                    }
                }

                footer: Item {
                    width: feed.width
                    height: activityFeedController.busy && feed.count > 0 ? 44 : 0

                    Controls.BusyIndicator {
                        anchors.centerIn: parent
                        width: 24
                        height: 24
                        uiTheme: root.theme
                        running: parent.height > 0
                    }
                }

                delegate: Item {
                    id: eventRow
                    required property int index
                    required property string kind
                    required property string title
                    required property string detail
                    required property string actor
                    required property string actorLabel
                    required property string actorAvatar
                    required property string actorInitials
                    required property string actorColor
                    required property string timestamp
                    required property string timestampPretty
                    required property string timestampFull
                    required property string searchKey
                    required property string targetSearchKey
                    required property string targetTitle
                    required property string targetType
                    required property string targetTypeTitle
                    required property string typeColor
                    required property string processColor
                    required property string itemCode
                    required property string itemTitle
                    required property string itemType
                    required property string itemTypeTitle
                    required property string itemTypeColor
                    required property string relationAction
                    required property string project
                    required property string process
                    required property string context
                    required property string version
                    required property string statusBefore
                    required property string statusAfter
                    required property string statusBeforeColor
                    required property string statusAfterColor
                    required property var changes
                    required property string taskCode
                    required property real hours
                    required property string workDay
                    required property string workDayPretty
                    required property string workHourAction
                    required property string workHourCategory
                    required property string workHourStatus
                    required property string workHourOwner
                    required property bool serverGenerated
                    required property bool canOpen
                    width: Math.max(0, feed.width - 12)
                    height: eventCard.implicitHeight

                    ActivityEventCard {
                        id: eventCard
                        anchors.fill: parent
                        theme: root.theme
                        kind: eventRow.kind
                        eventTitle: eventRow.title
                        detail: eventRow.detail
                        actor: eventRow.actor
                        actorLabel: eventRow.actorLabel
                        actorAvatar: eventRow.actorAvatar
                        actorInitials: eventRow.actorInitials
                        actorColor: eventRow.actorColor
                        timestamp: eventRow.timestamp
                        timestampPretty: eventRow.timestampPretty
                        timestampFull: eventRow.timestampFull
                        targetSearchKey: eventRow.targetSearchKey
                        targetTitle: eventRow.targetTitle
                        targetType: eventRow.targetType
                        targetTypeTitle: eventRow.targetTypeTitle
                        typeColor: eventRow.typeColor
                        processColor: eventRow.processColor
                        itemCode: eventRow.itemCode
                        itemTitle: eventRow.itemTitle
                        itemType: eventRow.itemType
                        itemTypeTitle: eventRow.itemTypeTitle
                        itemTypeColor: eventRow.itemTypeColor
                        relationAction: eventRow.relationAction
                        process: eventRow.process
                        context: eventRow.context
                        version: eventRow.version
                        statusBefore: eventRow.statusBefore
                        statusAfter: eventRow.statusAfter
                        statusBeforeColor: eventRow.statusBeforeColor
                        statusAfterColor: eventRow.statusAfterColor
                        changes: eventRow.changes
                        taskCode: eventRow.taskCode
                        hours: eventRow.hours
                        workDay: eventRow.workDay
                        workDayPretty: eventRow.workDayPretty
                        workHourAction: eventRow.workHourAction
                        workHourCategory: eventRow.workHourCategory
                        workHourStatus: eventRow.workHourStatus
                        workHourOwner: eventRow.workHourOwner
                        serverGenerated: eventRow.serverGenerated
                        canOpenActivity: eventRow.canOpen && eventRow.searchKey.length > 0
                        canOpenTarget: eventRow.targetSearchKey.length > 0
                        onActivityRequested: activityFeedController.open_item(eventRow.index)
                        onTargetRequested: activityFeedController.open_target(eventRow.index)
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: feed.count === 0 && !activityFeedController.busy
                    text: activityFeedController.searchText.length ? qsTr("No matching activity") : activityFeedController.selectedDay.length ? qsTr("No activity for this day") : qsTr("No activity for this filter")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                }
            }
        }
    }

    Connections {
        target: activityFeedController
        function onStateChanged() {
            Qt.callLater(feed.requestMoreIfNeeded);
        }
    }

    Controls.Popup {
        id: userFilterPopup
        objectName: "activityFeedUserFilterPopup"
        parent: Overlay.overlay
        theme: root.theme
        width: UI.peoplePopup(parent ? parent.width : 420, parent ? parent.height : 540).width + effectiveShadowMargin * 2
        implicitHeight: UI.peoplePopup(parent ? parent.width : 420, parent ? parent.height : 540).height + effectiveShadowMargin * 2
        padding: 14
        modal: false
        focus: true

        onAboutToShow: {
            root.pendingUserLogins = Array.from(activityFeedController.selectedUsers || []);
            userFilterFrame.picker?.setSelection(root.pendingUserLogins, false);
        }

        contentItem: Frame.FrameView {
            id: userFilterFrame
            property var picker: null
            theme: root.theme
            scene: UI.people({
                count: root.pendingUserLogins.length
            }, width, height, root.language)
            views: ({
                    people: peoplePort
                })
            onEvent: action => {
                if (action.type === "clear") {
                    root.pendingUserLogins = [];
                    picker?.setSelection([], false);
                } else if (action.type === "cancel")
                    userFilterPopup.close();
                else if (action.type === "apply") {
                    activityFeedController.set_users(root.pendingUserLogins);
                    userFilterPopup.close();
                }
            }
            Component {
                id: peoplePort
                UserPicker {
                    id: picker
                    objectName: "activityFeedUserPicker"
                    theme: root.theme
                    includeCurrent: true
                    multiple: true
                    selectedLogins: root.pendingUserLogins
                    onSelectionChanged: logins => root.pendingUserLogins = Array.from(logins || [])
                    Component.onCompleted: userFilterFrame.picker = picker
                    Component.onDestruction: if (userFilterFrame.picker === picker)
                        userFilterFrame.picker = null
                }
            }
        }
    }

    ActivityCalendarPopup {
        id: activityCalendar
        theme: root.theme
        currentTime: activityFeedController.currentTime
        dayCounts: activityFeedController.calendarCounts
        busy: activityFeedController.calendarBusy
        selectedDay: activityFeedController.selectedDay
        localeName: root.interfaceLocaleName
        onAboutToShow: activityFeedController.ensure_calendar_counts()
        onOpened: activityFeedController.ensure_calendar_counts()
        onAccepted: dateKey => activityFeedController.select_day(dateKey)
    }

    Connections {
        target: activityFeedController
        function onCalendarInvalidated() {
            if (activityCalendar.opened)
                activityFeedController.ensure_calendar_counts();
        }
    }

    ContentLoadingOverlay {
        anchors.fill: feedPanel
        anchors.margins: 10
        z: 20
        theme: root.theme
        visible: activityFeedController.busy && feed.count === 0
        message: qsTr("Loading activity...")
    }
}
