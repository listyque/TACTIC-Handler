import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property bool compact: width < 760
    signal deleteRequested()

    function choiceIndex(values, selected) {
        const source = values || []
        for (let index = 0; index < source.length; ++index) {
            if (String(source[index].value || "") === String(selected || ""))
                return index
        }
        return -1
    }

    function openMoreFields(sourceItem) {
        moreFieldsPopup.toggleBelowItem(sourceItem, true, 6)
    }

    implicitHeight: visible ? 48 : 0
    visible: tasksController.advancedCheckedCount > 0

    Rectangle {
        anchors.fill: parent
        color: root.theme.secondaryContainer
        radius: root.theme.itemRadius

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 9
            anchors.rightMargin: 7
            spacing: 6

            Controls.MaterialIcon {
                name: "edit_note"
                size: 17
                color: root.theme.action
            }
            Label {
                Layout.preferredWidth: root.compact ? 86 : 112
                text: tasksController.advancedCheckedCount
                    + (tasksController.advancedCheckedCount === 1
                        ? qsTr(" task selected") : qsTr(" tasks selected"))
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            RowLayout {
                visible: !root.compact
                spacing: 2
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    leftPadding: 5
                    checked: !!tasksController.bulkEditor.statusEnabled
                    enabled: !tasksController.bulkBusy
                        && tasksController.advancedDirtyCount === 0
                    onClicked: tasksController.set_bulk_enabled(
                        "status", checked
                    )
                }
                Controls.ComboBox {
                    id: statusCombo
                    theme: root.theme
                    Layout.preferredWidth: 132
                    model: tasksController.bulkStatusOptions
                    textRole: "label"
                    valueRole: "value"
                    colorRole: "color"
                    enabled: !!tasksController.bulkEditor.statusEnabled
                        && !tasksController.bulkBusy
                    currentIndex: root.choiceIndex(
                        tasksController.bulkStatusOptions,
                        tasksController.bulkEditor.status || ""
                    )
                    displayText: tasksController.bulkEditor.statusMixed
                            && !tasksController.bulkEditor.statusSet
                        ? qsTr("Mixed status")
                        : currentIndex >= 0 ? currentText : qsTr("Select status")
                    onActivated: tasksController.set_bulk_value(
                        "status", currentValue
                    )
                }
            }

            RowLayout {
                visible: !root.compact
                spacing: 2
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    leftPadding: 5
                    checked: !!tasksController.bulkEditor.assignedEnabled
                    enabled: !tasksController.bulkBusy
                        && tasksController.advancedDirtyCount === 0
                    onClicked: tasksController.set_bulk_enabled(
                        "assigned", checked
                    )
                }
                UserComboBox {
                    id: assigneeCombo
                    theme: root.theme
                    Layout.preferredWidth: 150
                    userModel: userListModel
                    model: tasksController.bulkUserOptions
                    textRole: "label"
                    valueRole: "value"
                    enabled: !!tasksController.bulkEditor.assignedEnabled
                        && !tasksController.bulkBusy
                    currentIndex: tasksController.bulkEditor.assignedMixed
                            && !tasksController.bulkEditor.assignedSet
                        ? -1 : root.choiceIndex(
                            tasksController.bulkUserOptions,
                            tasksController.bulkEditor.assigned || ""
                        )
                    displayText: tasksController.bulkEditor.assignedMixed
                            && !tasksController.bulkEditor.assignedSet
                        ? qsTr("Mixed assignee")
                        : currentIndex >= 0 ? currentText : qsTr("Select assignee")
                    onActivated: tasksController.set_bulk_value(
                        "assigned", currentValue
                    )
                }
            }

            Controls.CompactIconButton {
                id: moreFieldsButton
                theme: root.theme
                iconName: "tune"
                toolTip: qsTr("Bulk edit dates, progress and description")
                enabled: !tasksController.bulkBusy
                    && tasksController.advancedDirtyCount === 0
                elevated: true
                onPressed: moreFieldsPopup.rememberSourceOpen()
                onClicked: root.openMoreFields(moreFieldsButton)
            }

            Label {
                Layout.fillWidth: true
                text: tasksController.advancedDirtyCount > 0
                    ? qsTr("Save or discard row changes first")
                    : tasksController.bulkPreview.fields === 0
                        ? qsTr("Choose fields to change")
                        : tasksController.bulkPreview.eligible + qsTr(" ready")
                            + (tasksController.bulkPreview.unchanged > 0
                                ? " | " + tasksController.bulkPreview.unchanged
                                    + " unchanged" : "")
                            + (tasksController.bulkPreview.invalid > 0
                                ? " | " + tasksController.bulkPreview.invalid
                                    + " invalid" : "")
                color: tasksController.bulkPreview.invalid > 0
                    ? root.theme.error : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                horizontalAlignment: Text.AlignRight
                elide: Text.ElideRight
            }

            Controls.Button {
                theme: root.theme
                text: tasksController.bulkBusy
                    ? qsTr("APPLYING") : qsTr("APPLY")
                icon.name: "done_all"
                highlighted: true
                enabled: tasksController.bulkCanApply
                onClicked: tasksController.apply_bulk()
            }
            Controls.CompactIconButton {
                objectName: "taskBulkDeleteButton"
                theme: root.theme
                iconName: "delete"
                iconColor: root.theme.error
                backgroundColor: root.theme.errorContainer
                toolTip: qsTr("Delete selected tasks")
                enabled: !tasksController.bulkBusy
                    && !tasksController.advancedDeleting
                    && tasksController.advancedDirtyCount === 0
                onClicked: root.deleteRequested()
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "close"
                toolTip: qsTr("Cancel bulk edit and clear selection")
                enabled: !tasksController.bulkBusy
                onClicked: tasksController.cancel_bulk()
            }
        }
    }

    Controls.Popup {
        id: moreFieldsPopup
        parent: Overlay.overlay
        theme: root.theme
        readonly property bool compactLayout: width < 420
        width: Math.min(
            540, parent ? Math.max(0, parent.width - 16) : root.width
        )
        implicitHeight: moreFieldsContent.implicitHeight + 20
        height: Math.min(
            implicitHeight,
            parent ? Math.max(0, parent.height - 16) : implicitHeight
        )
        padding: 10

        contentItem: Flickable {
            id: moreFieldsFlickable
            clip: true
            contentWidth: width
            contentHeight: moreFieldsContent.implicitHeight
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: moreFieldsContent
                width: moreFieldsFlickable.width
                spacing: 8

            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: qsTr("MORE BULK FIELDS")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
                Label {
                    visible: !moreFieldsPopup.compactLayout
                    text: qsTr("Each checked field replaces its current value")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: moreFieldsPopup.compactLayout ? 2 : 4
                columnSpacing: 7
                rowSpacing: 7
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    text: qsTr("Start")
                    checked: !!tasksController.bulkEditor.startEnabled
                    onClicked: tasksController.set_bulk_enabled("start", checked)
                }
                Controls.DateField {
                    theme: root.theme
                    Layout.fillWidth: true
                    includeTime: true
                    enabled: !!tasksController.bulkEditor.startEnabled
                    placeholderText: tasksController.bulkEditor.startMixed
                        ? qsTr("Mixed start dates")
                        : qsTr("Start date and time")
                    text: tasksController.bulkEditor.startMixed
                        && !tasksController.bulkEditor.startSet ? ""
                        : String(tasksController.bulkEditor.start || "")
                    onAccepted: value => tasksController.set_bulk_value(
                        "start", value
                    )
                    onEditingFinished: tasksController.set_bulk_value(
                        "start", text
                    )
                }
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    text: qsTr("Deadline")
                    checked: !!tasksController.bulkEditor.endEnabled
                    onClicked: tasksController.set_bulk_enabled("end", checked)
                }
                Controls.DateField {
                    theme: root.theme
                    Layout.fillWidth: true
                    includeTime: true
                    enabled: !!tasksController.bulkEditor.endEnabled
                    placeholderText: tasksController.bulkEditor.endMixed
                        ? qsTr("Mixed end dates")
                        : qsTr("End date and time")
                    text: tasksController.bulkEditor.endMixed
                        && !tasksController.bulkEditor.endSet ? ""
                        : String(tasksController.bulkEditor.end || "")
                    onAccepted: value => tasksController.set_bulk_value(
                        "end", value
                    )
                    onEditingFinished: tasksController.set_bulk_value(
                        "end", text
                    )
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: moreFieldsPopup.compactLayout ? 2 : 6
                columnSpacing: 7
                rowSpacing: 7
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    text: qsTr("Priority")
                    checked: !!tasksController.bulkEditor.priorityEnabled
                    onClicked: tasksController.set_bulk_enabled(
                        "priority", checked
                    )
                }
                Controls.ComboBox {
                    theme: root.theme
                    Layout.fillWidth: true
                    enabled: !!tasksController.bulkEditor.priorityEnabled
                    model: tasksController.bulkPriorityOptions
                    textRole: "label"
                    valueRole: "value"
                    currentIndex: root.choiceIndex(
                        tasksController.bulkPriorityOptions,
                        tasksController.bulkEditor.priority || ""
                    )
                    displayText: tasksController.bulkEditor.priorityMixed
                            && !tasksController.bulkEditor.prioritySet
                        ? qsTr("Mixed priorities")
                        : currentIndex >= 0 ? currentText : qsTr("Select priority")
                    onActivated: tasksController.set_bulk_value(
                        "priority", currentValue
                    )
                }
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    text: qsTr("Milestone")
                    checked: !!tasksController.bulkEditor.milestoneCodeEnabled
                    onClicked: tasksController.set_bulk_enabled(
                        "milestoneCode", checked
                    )
                }
                Controls.ComboBox {
                    theme: root.theme
                    Layout.fillWidth: true
                    enabled: !!tasksController.bulkEditor.milestoneCodeEnabled
                    model: tasksController.bulkMilestoneOptions
                    textRole: "label"
                    valueRole: "value"
                    currentIndex: root.choiceIndex(
                        tasksController.bulkMilestoneOptions,
                        tasksController.bulkEditor.milestoneCode || ""
                    )
                    displayText: tasksController.bulkEditor.milestoneCodeMixed
                            && !tasksController.bulkEditor.milestoneCodeSet
                        ? qsTr("Mixed milestones")
                        : currentIndex >= 0 ? currentText : qsTr("Select milestone")
                    onActivated: tasksController.set_bulk_value(
                        "milestoneCode", currentValue
                    )
                }
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    text: qsTr("Supervisor")
                    checked: !!tasksController.bulkEditor.supervisorEnabled
                    onClicked: tasksController.set_bulk_enabled(
                        "supervisor", checked
                    )
                }
                Controls.ComboBox {
                    theme: root.theme
                    Layout.fillWidth: true
                    enabled: !!tasksController.bulkEditor.supervisorEnabled
                    model: tasksController.bulkSupervisorOptions
                    textRole: "label"
                    valueRole: "value"
                    currentIndex: root.choiceIndex(
                        tasksController.bulkSupervisorOptions,
                        tasksController.bulkEditor.supervisor || ""
                    )
                    displayText: tasksController.bulkEditor.supervisorMixed
                            && !tasksController.bulkEditor.supervisorSet
                        ? qsTr("Mixed supervisors")
                        : currentIndex >= 0 ? currentText : qsTr("Select supervisor")
                    onActivated: tasksController.set_bulk_value(
                        "supervisor", currentValue
                    )
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: moreFieldsPopup.compactLayout ? 3 : 5
                columnSpacing: 7
                rowSpacing: 7
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    text: qsTr("Progress")
                    checked: !!tasksController.bulkEditor.progressEnabled
                    enabled: tasksController.progressSupported
                    onClicked: tasksController.set_bulk_enabled(
                        "progress", checked
                    )
                }
                Controls.TextField {
                    theme: root.theme
                    Layout.preferredWidth: 108
                    enabled: !!tasksController.bulkEditor.progressEnabled
                    placeholderText: tasksController.bulkEditor.progressMixed
                            && !tasksController.bulkEditor.progressSet
                        ? qsTr("Mixed") : "0-100"
                    text: tasksController.bulkEditor.progressMixed
                            && !tasksController.bulkEditor.progressSet
                        ? "" : String(tasksController.bulkEditor.progress || 0)
                    validator: IntValidator { bottom: 0; top: 100 }
                    onEditingFinished: tasksController.set_bulk_value(
                        "progress", text
                    )
                }
                Label {
                    text: qsTr("%")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.CheckBox {
                    theme: root.theme
                    prominent: true
                    text: qsTr("Description")
                    checked: !!tasksController.bulkEditor.descriptionEnabled
                    onClicked: tasksController.set_bulk_enabled(
                        "description", checked
                    )
                }
                Controls.TextField {
                    theme: root.theme
                    Layout.fillWidth: true
                    enabled: !!tasksController.bulkEditor.descriptionEnabled
                    placeholderText: tasksController.bulkEditor.descriptionMixed
                        ? qsTr("Mixed descriptions") : qsTr("Description")
                    text: tasksController.bulkEditor.descriptionMixed
                        && !tasksController.bulkEditor.descriptionSet ? ""
                        : String(tasksController.bulkEditor.description || "")
                    onEditingFinished: tasksController.set_bulk_value(
                        "description", text
                    )
                }
            }

            Item { Layout.fillHeight: true }
            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: tasksController.bulkPreview.targets + qsTr(" selected | ")
                        + tasksController.bulkPreview.eligible + qsTr(" eligible | ")
                        + tasksController.bulkPreview.unchanged + qsTr(" unchanged | ")
                        + tasksController.bulkPreview.invalid + qsTr(" invalid | ")
                        + tasksController.bulkPreview.skipped + qsTr(" skipped")
                    color: tasksController.bulkPreview.invalid > 0
                        ? root.theme.error : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    elide: Text.ElideRight
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("DONE")
                    tonal: true
                    onClicked: moreFieldsPopup.close()
                }
            }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: moreFieldsFlickable
            }
        }
    }
}
