import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Popup {
    id: root

    property var dayCounts: ({})
    property bool busy: false
    property string selectedDay: ""
    property string localeName: "en_US"
    property date visibleMonth: new Date()
    readonly property var calendarLocale: Qt.locale(localeName)

    signal accepted(string dateKey)

    objectName: "activityCalendarPopup"
    parent: Overlay.overlay
    width: 364
    height: calendarLayout.implicitHeight + topPadding + bottomPadding
    padding: 10
    modal: true
    dim: true
    focus: true
    settledClosePolicy: Controls.Popup.CloseOnEscape
        | Controls.Popup.CloseOnPressOutside

    Overlay.modal: Rectangle {
        objectName: "activityCalendarScrim"
        color: root.theme.scrim
    }

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

    function countFor(value) {
        if (!root.dayCounts)
            return 0
        return Number(root.dayCounts[String(value)] || 0)
    }

    function newestActivityDay() {
        let newest = ""
        const counts = root.dayCounts || ({})
        for (const key in counts) {
            if (Number(counts[key] || 0) > 0 && key > newest)
                newest = key
        }
        return newest
    }

    function showBelow(anchorItem) {
        const initialDay = dateFromKey(selectedDay || newestActivityDay())
        visibleMonth = initialDay || new Date()
        toggleBelowItem(anchorItem, true, 6)
    }

    function acceptDay(value) {
        root.accepted(String(value || ""))
        root.close()
    }

    function firstDayOffset() {
        const firstDay = new Date(
            visibleMonth.getFullYear(), visibleMonth.getMonth(), 1, 12
        ).getDay()
        const localeFirstDay = Number(calendarLocale.firstDayOfWeek) % 7
        return (firstDay - localeFirstDay + 7) % 7
    }

    function cellDate(index) {
        return new Date(
            visibleMonth.getFullYear(), visibleMonth.getMonth(),
            index - firstDayOffset() + 1, 12
        )
    }

    contentItem: ColumnLayout {
        id: calendarLayout
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Controls.CompactIconButton {
                objectName: "activityCalendarPreviousMonth"
                theme: root.theme
                iconName: "chevron_left"
                toolTip: qsTr("Previous month")
                onClicked: root.visibleMonth = new Date(
                    root.visibleMonth.getFullYear(),
                    root.visibleMonth.getMonth() - 1, 1, 12
                )
            }
            Label {
                objectName: "activityCalendarMonthLabel"
                Layout.fillWidth: true
                text: root.calendarLocale.monthName(
                    root.visibleMonth.getMonth(), Locale.LongFormat
                ) + " " + root.visibleMonth.getFullYear()
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
            }
            Controls.CompactIconButton {
                objectName: "activityCalendarNextMonth"
                theme: root.theme
                iconName: "chevron_right"
                toolTip: qsTr("Next month")
                onClicked: root.visibleMonth = new Date(
                    root.visibleMonth.getFullYear(),
                    root.visibleMonth.getMonth() + 1, 1, 12
                )
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 7
            columnSpacing: 3
            rowSpacing: 3

            Repeater {
                objectName: "activityCalendarWeekdayRepeater"
                model: 7
                delegate: Label {
                    required property int index
                    readonly property int dayOfWeek:
                        (Number(root.calendarLocale.firstDayOfWeek)
                            + index - 1) % 7 + 1
                    Layout.fillWidth: true
                    Layout.preferredHeight: 22
                    text: root.calendarLocale.dayName(
                        dayOfWeek, Locale.NarrowFormat
                    )
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Repeater {
                objectName: "activityCalendarDayRepeater"
                model: 42
                delegate: Controls.PopupAction {
                    id: dayCell
                    objectName: "activityCalendarDay_" + key
                    required property int index
                    readonly property date value: root.cellDate(index)
                    readonly property string key: root.dateKey(value)
                    readonly property int eventCount: root.countFor(key)
                    readonly property bool inMonth:
                        value.getMonth() === root.visibleMonth.getMonth()
                    readonly property bool selected: key === root.selectedDay
                    readonly property bool today:
                        key === root.dateKey(new Date())

                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    hoverEnabled: true
                    enabled: eventCount > 0
                    Accessible.name: key
                    background: Rectangle {
                        anchors.margins: 1
                        radius: root.theme.itemRadius
                        color: dayCell.selected
                            ? root.theme.selected
                            : dayCell.down
                                ? root.theme.surfaceContainerHighest
                                : dayCell.hovered
                                    ? root.theme.rowHover : "transparent"
                        border.width:
                            dayCell.today && !dayCell.selected ? 1 : 0
                        border.color: root.theme.action
                    }
                    contentItem: Item {
                        Label {
                            anchors.centerIn: parent
                            text: dayCell.value.getDate()
                            color: dayCell.selected
                                ? root.theme.selectedText
                                : dayCell.eventCount <= 0
                                    ? root.theme.disabledText
                                    : dayCell.inMonth
                                        ? root.theme.primaryText
                                        : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: dayCell.selected
                                ? Font.DemiBold : Font.Normal
                        }
                        Rectangle {
                            visible: dayCell.eventCount > 0
                            anchors.top: parent.top
                            anchors.right: parent.right
                            width: Math.max(16, countLabel.implicitWidth + 6)
                            height: 16
                            radius: 8
                            color: dayCell.selected
                                ? root.theme.selectedText : root.theme.action

                            Label {
                                id: countLabel
                                anchors.centerIn: parent
                                text: dayCell.eventCount > 99
                                    ? "99+" : String(dayCell.eventCount)
                                color: dayCell.selected
                                    ? root.theme.selected
                                    : root.theme.selectedText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.micro
                                font.weight: Font.Bold
                            }
                        }
                    }
                    onClicked: root.acceptDay(dayCell.key)

                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.separator
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Controls.Button {
                theme: root.theme
                text: qsTr("All history")
                onClicked: {
                    root.accepted("")
                    root.close()
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Controls.BusyIndicator {
                    objectName: "activityCalendarLoading"
                    anchors.centerIn: parent
                    uiTheme: root.theme
                    width: 18
                    height: 18
                    running: root.visible && root.busy
                    Accessible.name: qsTr("Updating calendar history...")
                }
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Close")
                onClicked: root.close()
            }
        }
    }
}
