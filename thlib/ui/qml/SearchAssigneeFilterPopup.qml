import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Popup {
    id: root
    required property var controller
    objectName: "searchAssigneeFilterPopup"
    parent: Overlay.overlay
    width: parent
        ? Math.min(400, Math.max(300, parent.width - 16))
        : 400
    height: parent
        ? Math.min(430, Math.max(260, parent.height - 16))
        : 430
    padding: 12
    modal: false
    focus: true
    settledClosePolicy:
        Popup.CloseOnEscape | Popup.CloseOnPressOutside

    function openBelow(sourceItem) {
        assigneeUserPicker.setSelection(
            root.controller.quick_filter_assignee_logins, false
        )
        root.openBelowItem(sourceItem, true, 6)
    }

    contentItem: ColumnLayout {
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Label {
                Layout.fillWidth: true
                text: qsTr("ASSIGNED TO")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
            }
            QuickFilterChip {
                theme: root.theme
                text: qsTr("ALL")
                checked:
                    root.controller.quick_filter_assignee_logins
                        .length === 0
                    && !root.controller.quick_filter_my_tasks
                onClicked: {
                    root.controller.toggle_quick_filter(
                        "assigned", ""
                    )
                    assigneeUserPicker.setSelection([], false)
                }
            }
        }

        QuickFilterChip {
            Layout.alignment: Qt.AlignLeft
            theme: root.theme
            text: qsTr("MY TASKS")
            iconName: "person"
            checked: root.controller.quick_filter_my_tasks
            onClicked: root.controller.toggle_my_tasks_filter()
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.separator
        }

        UserPicker {
            id: assigneeUserPicker
            Layout.fillWidth: true
            Layout.fillHeight: true
            theme: root.theme
            includeCurrent: false
            multiple: true
            onSelectionChanged: function(logins) {
                root.controller.set_quick_filter_assignees(logins)
            }
        }
    }
}
