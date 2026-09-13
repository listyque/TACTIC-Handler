import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Item {
    id: root

    required property var theme
    property alias text: dateTextField.text
    property alias placeholderText: dateTextField.placeholderText
    property alias readOnly: dateTextField.readOnly
    property alias errorState: dateTextField.errorState
    property bool includeTime: false
    property bool allowClear: true
    readonly property string datePresentationText:
        presentationDate(dateTextField.text)
    readonly property string fullPresentationText:
        presentationDateTime(dateTextField.text)
    readonly property real availablePresentationWidth: Math.max(
        0, width - dateTextField.leftPadding - dateTextField.rightPadding
    )
    readonly property bool showTimeInPresentation: includeTime
        && fullPresentationText !== datePresentationText
        && presentationMetrics.advanceWidth(fullPresentationText)
            <= availablePresentationWidth
    readonly property string presentationText: showTimeInPresentation
        ? fullPresentationText : datePresentationText
    signal textEdited(string text)
    signal editingFinished()
    signal accepted(string value)

    implicitWidth: 180
    implicitHeight: theme.controlHeight

    function pad(value) {
        return value < 10 ? "0" + value : String(value)
    }

    function parseValue(value) {
        const match = String(value || "").match(
            /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/
        )
        if (!match)
            return null
        const result = new Date(
            Number(match[1]), Number(match[2]) - 1, Number(match[3]),
            Number(match[4] || 0), Number(match[5] || 0),
            Number(match[6] || 0)
        )
        return isNaN(result.getTime()) ? null : result
    }

    function formattedValue(value) {
        let result = value.getFullYear() + "-" + pad(value.getMonth() + 1)
            + "-" + pad(value.getDate())
        if (includeTime)
            result += " " + pad(hourPicker.value) + ":"
                + pad(minutePicker.value) + ":00"
        return result
    }

    function presentationDate(value) {
        const parsed = parseValue(value)
        return parsed
            ? Qt.locale().toString(parsed, "d MMMM yyyy")
            : String(value || "")
    }

    function presentationDateTime(value) {
        const parsed = parseValue(value)
        if (!parsed || !includeTime || !/[ T]\d{2}:\d{2}/.test(value))
            return presentationDate(value)
        return presentationDate(value) + " · "
            + pad(parsed.getHours()) + ":" + pad(parsed.getMinutes())
    }

    function showCalendar() {
        const sourceText = String(dateTextField.text || "")
        const parsed = parseValue(sourceText) || new Date()
        const hasExplicitTime = /[ T]\d{2}:\d{2}/.test(sourceText)
        const now = new Date()
        calendarPopup.pendingDate = new Date(
            parsed.getFullYear(), parsed.getMonth(), parsed.getDate()
        )
        calendarPopup.visibleMonth = new Date(
            parsed.getFullYear(), parsed.getMonth(), 1
        )
        hourPicker.value = hasExplicitTime
            ? parsed.getHours() : now.getHours()
        minutePicker.value = hasExplicitTime ? parsed.getMinutes() : 0
        calendarPopup.toggleBelowItem(root, false, 6)
    }

    Controls.TextField {
        id: dateTextField
        objectName: "dateFieldTextInput"
        anchors.fill: parent
        theme: root.theme
        rightPadding: calendarButton.width + 9
        color: !activeFocus && text.length > 0
            ? "transparent"
            : enabled ? root.theme.primaryText : root.theme.disabledText
        onTextEdited: root.textEdited(text)
        onEditingFinished: root.editingFinished()
    }

    FontMetrics {
        id: presentationMetrics
        font: dateTextField.font
    }

    Label {
        objectName: "dateFieldPresentationLabel"
        visible: !dateTextField.activeFocus && dateTextField.text.length > 0
        anchors.left: parent.left
        anchors.leftMargin: dateTextField.leftPadding
        anchors.right: calendarButton.left
        anchors.rightMargin: 5
        anchors.verticalCenter: parent.verticalCenter
        text: root.presentationText
        color: root.enabled
            ? root.theme.primaryText : root.theme.disabledText
        font: dateTextField.font
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }

    Controls.CompactIconButton {
        id: calendarButton
        objectName: "dateFieldCalendarButton"
        anchors.right: parent.right
        anchors.rightMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        width: 28
        height: 28
        theme: root.theme
        iconName: "calendar_month"
        iconSize: 16
        iconColor: root.enabled && !root.readOnly
            ? root.theme.secondaryText : root.theme.disabledText
        toolTip: root.includeTime
            ? qsTr("Choose date and time") : qsTr("Choose date")
        onPressed: calendarPopup.rememberSourceOpen()
        onClicked: if (root.enabled && !root.readOnly) root.showCalendar()
    }

    Controls.Popup {
        id: calendarPopup
        objectName: "dateFieldCalendarPopup"
        parent: Overlay.overlay
        theme: root.theme
        property date visibleMonth: new Date()
        property date pendingDate: new Date()

        width: 304
        height: calendarLayout.implicitHeight + topPadding + bottomPadding
        padding: 10
        modal: false
        focus: true
        settledClosePolicy: Controls.Popup.CloseOnEscape
            | Controls.Popup.CloseOnPressOutside

        function daysInMonth() {
            return new Date(
                visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 0
            ).getDate()
        }

        function firstDayOffset() {
            return (new Date(
                visibleMonth.getFullYear(), visibleMonth.getMonth(), 1
            ).getDay() + 6) % 7
        }

        function acceptDate(value) {
            pendingDate = value
            const formatted = root.formattedValue(pendingDate)
            dateTextField.text = formatted
            root.accepted(formatted)
            close()
        }

        contentItem: ColumnLayout {
            id: calendarLayout
            spacing: 7

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 42
                radius: root.theme.itemRadius
                color: root.theme.surfaceContainerHigh
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 4
                    anchors.rightMargin: 4
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "chevron-left"
                        toolTip: qsTr("Previous month")
                        onClicked: calendarPopup.visibleMonth = new Date(
                            calendarPopup.visibleMonth.getFullYear(),
                            calendarPopup.visibleMonth.getMonth() - 1, 1
                        )
                    }
                    Label {
                        objectName: "calendarMonthLabel"
                        Layout.fillWidth: true
                        text: Qt.locale().monthName(
                            calendarPopup.visibleMonth.getMonth(),
                            Locale.LongFormat
                        ) + " " + calendarPopup.visibleMonth.getFullYear()
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.bodyLarge
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "chevron-right"
                        toolTip: qsTr("Next month")
                        onClicked: calendarPopup.visibleMonth = new Date(
                            calendarPopup.visibleMonth.getFullYear(),
                            calendarPopup.visibleMonth.getMonth() + 1, 1
                        )
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: 7
                columnSpacing: 2
                rowSpacing: 2

                Repeater {
                    model: [1, 2, 3, 4, 5, 6, 7]
                    delegate: Label {
                        required property int modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 20
                        text: Qt.locale().dayName(
                            modelData, Locale.NarrowFormat
                        )
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.caption
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Repeater {
                    model: 42
                    delegate: Controls.PopupAction {
                        id: dayCell
                        required property int index
                        readonly property int dayNumber:
                            index - calendarPopup.firstDayOffset() + 1
                        readonly property bool valid:
                            dayNumber > 0
                            && dayNumber <= calendarPopup.daysInMonth()
                        readonly property bool selected: valid
                            && calendarPopup.pendingDate.getFullYear()
                                === calendarPopup.visibleMonth.getFullYear()
                            && calendarPopup.pendingDate.getMonth()
                                === calendarPopup.visibleMonth.getMonth()
                            && calendarPopup.pendingDate.getDate() === dayNumber
                        readonly property bool today: valid
                            && new Date().getFullYear()
                                === calendarPopup.visibleMonth.getFullYear()
                            && new Date().getMonth()
                                === calendarPopup.visibleMonth.getMonth()
                            && new Date().getDate() === dayNumber

                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        enabled: valid
                        hoverEnabled: true
                        Accessible.name: valid ? String(dayNumber) : ""
                        background: Item {
                            Rectangle {
                                width: 28
                                height: 28
                                radius: height / 2
                                anchors.centerIn: parent
                                color: dayCell.selected
                                    ? root.theme.selected
                                    : dayCell.down
                                        ? root.theme.surfaceContainerHighest
                                        : dayCell.hovered
                                            ? root.theme.rowHover
                                            : "transparent"
                                border.width:
                                    dayCell.today && !dayCell.selected ? 1 : 0
                                border.color: root.theme.action
                            }
                        }
                        contentItem: Label {
                            text: dayCell.valid ? dayCell.dayNumber : ""
                            color: dayCell.selected
                                ? root.theme.selectedText
                                : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.label
                            font.weight: dayCell.selected
                                ? Font.DemiBold : Font.Normal
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: calendarPopup.acceptDate(new Date(
                            calendarPopup.visibleMonth.getFullYear(),
                            calendarPopup.visibleMonth.getMonth(),
                            dayCell.dayNumber
                        ))

                    }
                }
            }

            RowLayout {
                visible: root.includeTime
                Layout.fillWidth: true
                spacing: 7
                Label {
                    text: qsTr("Time")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                }
                Item { Layout.fillWidth: true }
                Controls.SpinBox {
                    id: hourPicker
                    theme: root.theme
                    from: 0
                    to: 23
                    Layout.preferredWidth: 92
                    textFromValue: function(value, locale) {
                        return root.pad(value)
                    }
                    valueFromText: function(text, locale) {
                        return Math.max(0, Math.min(23, parseInt(text) || 0))
                    }
                }
                Label {
                    text: qsTr(":")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                }
                Controls.SpinBox {
                    id: minutePicker
                    theme: root.theme
                    from: 0
                    to: 59
                    stepSize: 5
                    Layout.preferredWidth: 92
                    textFromValue: function(value, locale) {
                        return root.pad(value)
                    }
                    valueFromText: function(text, locale) {
                        return Math.max(0, Math.min(59, parseInt(text) || 0))
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: root.theme.outlineVariant
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 7
                Controls.Button {
                    visible: root.allowClear
                    theme: root.theme
                    text: qsTr("Clear")
                    flat: true
                    onClicked: {
                        dateTextField.text = ""
                        root.accepted("")
                        calendarPopup.close()
                    }
                }
                Item { Layout.fillWidth: true }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Today")
                    flat: true
                    onClicked: {
                        const today = new Date()
                        calendarPopup.acceptDate(new Date(
                            today.getFullYear(), today.getMonth(), today.getDate()
                        ))
                    }
                }
            }
        }
    }
}
