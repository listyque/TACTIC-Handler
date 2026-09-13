import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme

    readonly property bool narrowToolbar: width < 760
    readonly property bool compactFilterSegments: width < 1000
    readonly property bool compactCalendarButton: width < 1120
    readonly property bool showUserFilterLabel: width >= 1320
    readonly property string interfaceLocaleName: {
        if (typeof localizationController === "undefined")
            return Qt.locale().name
        return String(localizationController.current_language) === "ru"
            ? "ru_RU" : "en_US"
    }
    readonly property var interfaceLocale: Qt.locale(interfaceLocaleName)
    property var pendingUserLogins: []
    readonly property var feedFilters: [
        {"value": "all", "label": "All", "icon": "select-all"},
        {"value": "my_tasks", "label": "My tasks", "icon": "task"},
        {"value": "my_objects", "label": "My objects", "icon": "inventory-2"},
        {"value": "notes", "label": "Notes", "icon": "notes"},
        {"value": "publications", "label": "Publications", "icon": "snapshot"}
    ]

    function dateKey(value) {
        const year = value.getFullYear()
        const month = String(value.getMonth() + 1).padStart(2, "0")
        const day = String(value.getDate()).padStart(2, "0")
        return year + "-" + month + "-" + day
    }

    function dateFromKey(value) {
        const parts = String(value || "").split("-")
        if (parts.length !== 3)
            return null
        const result = new Date(
            Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]), 12
        )
        return Number.isNaN(result.getTime()) ? null : result
    }

    function selectedDayLabel() {
        const value = dateFromKey(activityFeedController.selectedDay)
        return value
            ? Qt.formatDate(value, interfaceLocale, "d MMM yyyy")
            : qsTr("All history")
    }

    function dayHeaderLabel(value) {
        const date = dateFromKey(value)
        if (!date)
            return qsTr("No date")
        const today = new Date()
        const yesterday = new Date(
            today.getFullYear(), today.getMonth(), today.getDate() - 1, 12
        )
        const suffix = Qt.formatDate(
            date, interfaceLocale,
            date.getFullYear() === today.getFullYear()
                ? "d MMMM" : "d MMMM yyyy"
        )
        if (dateKey(date) === dateKey(today))
            return qsTr("Today") + "  ·  " + suffix
        if (dateKey(date) === dateKey(yesterday))
            return qsTr("Yesterday") + "  ·  " + suffix
        return suffix
    }

    function userFilterTitle() {
        const logins = activityFeedController.selectedUsers || []
        if (!logins.length)
            return qsTr("All users")
        if (logins.length > 1)
            return qsTr("%1 users").arg(logins.length)
        const login = String(logins[0] || "")
        for (let index = 0; index < userListModel.count(); ++index) {
            const user = userListModel.get(index)
            if (String(user.login || "") === login)
                return String(user.displayName || login)
        }
        return login
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

        Rectangle {
            id: feedToolbar
            objectName: "activityFeedToolbar"
            Layout.fillWidth: true
            Layout.preferredHeight: feedToolbarLayout.implicitHeight + 20
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerHigh

            ColumnLayout {
                id: feedToolbarLayout
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

            GridLayout {
                Layout.fillWidth: true
                columns: root.narrowToolbar ? 1 : 3
                columnSpacing: 12
                rowSpacing: 4

                Controls.SectionLabel {
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("ACTIVITY FEED")
                }

                Controls.CheckBox {
                    id: activityNotifications
                    objectName: "activityFeedNotificationsEnabled"
                    Layout.fillWidth: root.narrowToolbar
                    Layout.maximumWidth: root.narrowToolbar ? 100000 : 220
                    Layout.alignment: root.narrowToolbar
                        ? Qt.AlignLeft : Qt.AlignRight
                    theme: root.theme
                    compact: true
                    checked: activityFeedController.notificationsEnabled
                    text: qsTr("Activity notifications")
                    Accessible.description: qsTr(
                        "Show a bottom-right notification for new activity from other users"
                    )
                    onToggled:
                        activityFeedController.set_notifications_enabled(checked)
                    Controls.ToolTip {
                        theme: root.theme
                        visible: activityNotifications.hovered
                        text: activityNotifications.Accessible.description
                    }
                }

                Controls.CheckBox {
                    id: excludeOwnActivity
                    objectName: "activityFeedExcludeOwnActivity"
                    Layout.fillWidth: root.narrowToolbar
                    Layout.maximumWidth: root.narrowToolbar ? 100000 : 230
                    Layout.alignment: root.narrowToolbar
                        ? Qt.AlignLeft : Qt.AlignRight
                    theme: root.theme
                    compact: true
                    checked: activityFeedController.excludeOwnActivity
                    text: qsTr("Exclude my activity")
                    Accessible.description: qsTr(
                        "Hide actions performed by the current login from this feed"
                    )
                    onToggled:
                        activityFeedController.set_exclude_own_activity(checked)
                    Controls.ToolTip {
                        theme: root.theme
                        visible: excludeOwnActivity.hovered
                        text: excludeOwnActivity.Accessible.description
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: root.narrowToolbar ? 1 : 2
                columnSpacing: 10
                rowSpacing: 8

            Item {
                id: searchBox
                objectName: "activityFeedSearchBox"
                Layout.fillWidth: root.narrowToolbar
                Layout.minimumWidth: root.narrowToolbar ? 0 : 200
                Layout.preferredWidth: root.narrowToolbar ? 0 : 220
                Layout.maximumWidth: root.narrowToolbar ? 100000 : 250
                Layout.preferredHeight: root.theme.controlHeight

                Controls.TextField {
                    id: searchField
                    objectName: "activityFeedSearchField"
                    anchors.fill: parent
                    theme: root.theme
                    leftPadding: 38
                    rightPadding: clearSearchButton.visible ? 36 : 12
                    placeholderText: qsTr("Search activity")
                    text: activityFeedController.searchText
                    onTextEdited:
                        activityFeedController.set_search_text(text)
                }
                Controls.MaterialIcon {
                    anchors.left: parent.left
                    anchors.leftMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    name: "search"
                    size: 18
                    color: root.theme.secondaryText
                }
                Controls.CompactIconButton {
                    id: clearSearchButton
                    visible: searchField.text.length > 0
                    anchors.right: parent.right
                    anchors.rightMargin: 4
                    anchors.verticalCenter: parent.verticalCenter
                    width: 28
                    height: 28
                    theme: root.theme
                    iconName: "close"
                    iconSize: 15
                    toolTip: qsTr("Clear search")
                    onClicked: {
                        searchField.clear()
                        activityFeedController.set_search_text("")
                        searchField.forceActiveFocus()
                    }
                }
            }

            GridLayout {
                id: feedFilterActions
                objectName: "activityFeedFilterActions"
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignRight
                columns: root.narrowToolbar ? 1 : 2
                columnSpacing: 8
                rowSpacing: 8

                Controls.SegmentedButton {
                    objectName: "activityFeedFilterSegments"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    theme: root.theme
                    model: root.feedFilters
                    currentValue: activityFeedController.currentFilter
                    iconOnly: root.compactFilterSegments
                    segmentWidth: root.compactFilterSegments ? 46 : 68
                    minimumSegmentWidth: root.compactFilterSegments ? 38 : 56
                    onActivated: value =>
                        activityFeedController.set_filter(value)
                }

                RowLayout {
                    id: feedSecondaryActions
                    objectName: "activityFeedSecondaryActions"
                    Layout.fillWidth: root.narrowToolbar
                    Layout.alignment: Qt.AlignRight
                    spacing: 8

                    Item {
                        Layout.fillWidth: root.narrowToolbar
                        visible: root.narrowToolbar
                    }

                    Controls.Button {
                        id: userFilterButton
                        objectName: "activityFeedUserFilterButton"
                        visible: root.showUserFilterLabel
                        Layout.preferredWidth: implicitWidth
                        Layout.maximumWidth: 220
                        theme: root.theme
                        text: root.userFilterTitle()
                        icon.name: "groups"
                        highlighted:
                            activityFeedController.selectedUsers.length > 0
                        onPressed: userFilterPopup.rememberSourceOpen()
                        onClicked: userFilterPopup.toggleBelowItem(
                            userFilterButton, true, 6
                        )
                    }

                    Controls.CompactIconButton {
                        id: compactUserFilterButton
                        objectName: "activityFeedCompactUserFilterButton"
                        visible: !root.showUserFilterLabel
                        theme: root.theme
                        iconName: "groups"
                        badgeCount: activityFeedController.selectedUsers.length
                        toolTip: root.userFilterTitle()
                        onPressed: userFilterPopup.rememberSourceOpen()
                        onClicked: userFilterPopup.toggleBelowItem(
                            compactUserFilterButton, true, 6
                        )
                    }

                    Controls.Button {
                        id: calendarButton
                        objectName: "activityFeedCalendarButton"
                        Layout.preferredWidth: root.compactCalendarButton
                            ? root.theme.controlHeight
                            : Math.min(230, implicitWidth)
                        Layout.minimumWidth: Layout.preferredWidth
                        theme: root.theme
                        compact: root.compactCalendarButton
                        clip: true
                        text: root.selectedDayLabel()
                        toolTip: root.selectedDayLabel()
                        icon.name: "calendar-month"
                        highlighted:
                            activityFeedController.selectedDay.length > 0
                        onPressed: activityCalendar.rememberSourceOpen()
                        onClicked: {
                            activityCalendar.showBelow(calendarButton)
                        }
                    }

                    RefreshIconButton {
                        objectName: "activityFeedRefreshButton"
                        theme: root.theme
                        enabled: !activityFeedController.busy
                        toolTip: qsTr("Refresh activity")
                        onClicked: activityFeedController.refresh()
                    }
                }
            }
        }
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
            theme: root.theme
            id: feed
            objectName: "activityFeedList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.rightMargin: 8
            clip: true
            spacing: 6
            model: activityFeedModel
            section.property: "dayKey"
            section.criteria: ViewSection.FullString
            section.labelPositioning: ViewSection.InlineLabels
                | ViewSection.CurrentLabelAtStart
            section.delegate: Item {
                id: daySection
                required property string section
                width: Math.max(0, feed.width - 12)
                height: 34
                z: 2

                Rectangle {
                    anchors.fill: parent
                    color: root.theme.panel
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 4
                    anchors.rightMargin: 6
                    spacing: 10

                    Label {
                        text: root.dayHeaderLabel(daySection.section)
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: root.theme.separator
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                id: activityFeedScrollBar
                objectName: "activityFeedScrollBar"
                theme: root.theme
                flickableTarget: feed
            }

            function requestMoreIfNeeded() {
                if (!feed.visible || activityFeedController.busy
                        || activityFeedController.error
                        || !activityFeedController.hasMore)
                    return
                // Model notifications precede ListView polish. Do not mistake
                // the old (or zero) extent for an underfilled new page.
                feed.forceLayout()
                const underfilled = contentHeight <= height + 1
                if ((!underfilled && !atYEnd)
                        || !activityFeedScrollBar.takePaginationPermit(
                            underfilled))
                    return
                activityFeedController.load_more()
            }

            onMovementEnded: feed.requestMoreIfNeeded()
            onWheelScrollRequested: delta => {
                if (delta < 0)
                    feed.requestMoreIfNeeded()
            }
            onInteractionMovingChanged: {
                if (!interactionMoving)
                    feed.requestMoreIfNeeded()
            }
            onAtYEndChanged: feed.requestMoreIfNeeded()
            onCountChanged: feed.requestMoreIfNeeded()
            onVisibleChanged: feed.requestMoreIfNeeded()

            Connections {
                target: activityFeedController
                function onStateChanged() {
                    if (!activityFeedController.busy)
                        feed.requestMoreIfNeeded()
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
                    canOpenActivity: eventRow.canOpen
                        && eventRow.searchKey.length > 0
                    canOpenTarget: eventRow.targetSearchKey.length > 0
                    onActivityRequested:
                        activityFeedController.open_item(eventRow.index)
                    onTargetRequested:
                        activityFeedController.open_target(eventRow.index)
                }
            }

            Label {
                anchors.centerIn: parent
                visible: feed.count === 0 && !activityFeedController.busy
                text: activityFeedController.searchText.length
                    ? qsTr("No matching activity")
                    : activityFeedController.selectedDay.length
                        ? qsTr("No activity for this day")
                        : qsTr("No activity for this filter")
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
            Qt.callLater(feed.requestMoreIfNeeded)
        }
    }

    Controls.Popup {
        id: userFilterPopup
        objectName: "activityFeedUserFilterPopup"
        parent: Overlay.overlay
        theme: root.theme
        width: parent
            ? Math.min(420, Math.max(320, parent.width - 24))
            : 420
        implicitHeight: parent
            ? Math.min(540, Math.max(360, parent.height - 24))
            : 540
        padding: 14
        modal: false
        focus: true

        onOpened: {
            root.pendingUserLogins = Array.from(
                activityFeedController.selectedUsers || []
            )
            activityUserPicker.setSelection(root.pendingUserLogins, false)
        }

        contentItem: ColumnLayout {
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Controls.MaterialIcon {
                    name: "groups"
                    size: 22
                    color: root.theme.action
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Filter by users")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Show activity created by selected users")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        wrapMode: Text.WordWrap
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: root.theme.separator
            }

            UserPicker {
                id: activityUserPicker
                objectName: "activityFeedUserPicker"
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                includeCurrent: true
                multiple: true
                onSelectionChanged: function(logins) {
                    root.pendingUserLogins = Array.from(logins || [])
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    text: root.pendingUserLogins.length
                        ? qsTr("%1 users").arg(root.pendingUserLogins.length)
                        : qsTr("All users")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Clear")
                    enabled: root.pendingUserLogins.length > 0
                    onClicked: {
                        root.pendingUserLogins = []
                        activityUserPicker.setSelection([], false)
                    }
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: userFilterPopup.close()
                }
                Controls.Button {
                    objectName: "activityFeedApplyUserFilterButton"
                    theme: root.theme
                    text: qsTr("Apply")
                    highlighted: true
                    onClicked: {
                        activityFeedController.set_users(
                            root.pendingUserLogins
                        )
                        userFilterPopup.close()
                    }
                }
            }
        }
    }

    ActivityCalendarPopup {
        id: activityCalendar
        theme: root.theme
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
                activityFeedController.ensure_calendar_counts()
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
