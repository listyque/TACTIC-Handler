import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property string pendingDeleteCode: ""

    function createMilestone() {
        searchField.clear()
        milestoneController.set_filter("")
        milestoneController.create_milestone()
        milestoneList.currentIndex = 0
        milestoneList.positionViewAtBeginning()
        Qt.callLater(function() {
            const item = milestoneList.currentItem
            if (item)
                item.focusNameEditor()
        })
    }

    function dayPart(value) {
        const parts = String(value || "").split("-")
        return parts.length === 3 ? parts[2] : "--"
    }

    function monthPart(value) {
        const names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                       "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        const parts = String(value || "").split("-")
        const index = parts.length === 3 ? Number(parts[1]) - 1 : -1
        return index >= 0 && index < names.length ? names[index] : qsTr("DATE")
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 11

                Rectangle {
                    Layout.preferredWidth: 46
                    Layout.preferredHeight: 46
                    radius: root.theme.itemRadius
                    color: root.theme.secondaryContainer
                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: "milestone"
                        size: 22
                        color: root.theme.action
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        text: qsTr("Project milestones")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Schedule reusable task deadlines for ")
                            + (milestoneController.projectCode || qsTr("current project"))
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        elide: Text.ElideRight
                    }
                }
                Label {
                    text: milestoneController.count + " " + qsTr("milestones")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
                RefreshIconButton {
                    theme: root.theme
                    enabled: !milestoneController.busy
                    toolTip: milestoneController.hasDirtyRows
                        ? qsTr("Refresh and discard unsaved changes")
                        : qsTr("Refresh milestones")
                    onClicked: {
                        if (milestoneController.hasDirtyRows)
                            refreshDialog.open()
                        else
                            milestoneController.refresh()
                    }
                }
                Controls.FilledActionButton {
                    theme: root.theme
                    iconName: "add"
                    text: qsTr("New milestone")
                    enabled: !milestoneController.busy
                    onClicked: root.createMilestone()
                }
            }
        }

        Controls.TextField {
            id: searchField
            Layout.fillWidth: true
            theme: root.theme
            placeholderText: qsTr("Search milestones")
            enabled: !milestoneController.busy
            leftPadding: 39
            onTextEdited: milestoneController.set_filter(text)
            Controls.MaterialIcon {
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                name: "search"
                size: 16
                color: root.theme.secondaryText
            }
        }

        ListView {
            id: milestoneList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 7
            reuseItems: true
            boundsBehavior: Flickable.StopAtBounds
            model: milestoneModel

            delegate: Rectangle {
                id: milestoneRow
                required property string code
                required property string description
                required property string dueDate
                required property bool isNew
                required property bool dirty
                required property bool saving
                required property string error
                required property int completion
                required property int taskCount
                required property int completedCount
                required property int overdueCount
                required property string planStartDate
                required property string processSummary
                required property real plannedHours

                function focusNameEditor() {
                    nameField.forceActiveFocus(Qt.TabFocusReason)
                    nameField.selectAll()
                }

                width: milestoneList.width
                height: error ? 148 : 126
                radius: root.theme.itemRadius
                color: dirty
                    ? root.theme.surfaceContainerHigh
                    : root.theme.surfaceContainerLow
                border.width: dirty ? 1 : 0
                border.color: error ? root.theme.error
                    : dirty ? root.theme.action : root.theme.outlineVariant

                RowLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: planPanel.top
                    anchors.margins: 9
                    spacing: 9

                    Rectangle {
                        Layout.preferredWidth: 50
                        Layout.preferredHeight: 50
                        Layout.alignment: Qt.AlignBottom
                        radius: root.theme.itemRadius
                        color: isNew
                            ? root.theme.secondaryContainer
                            : root.theme.surfaceContainerHighest
                        Column {
                            anchors.centerIn: parent
                            spacing: -2
                            Label {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: root.dayPart(milestoneRow.dueDate)
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                            }
                            Label {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: root.monthPart(milestoneRow.dueDate)
                                color: root.theme.action
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.Bold
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 12
                            Layout.minimumHeight: 12
                            Layout.maximumHeight: 12
                            spacing: 5
                            Label {
                                text: isNew ? qsTr("NEW") : qsTr("MILESTONE")
                                color: isNew ? root.theme.action
                                    : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.Bold
                            }
                            Label {
                                visible: dirty
                                text: milestoneRow.saving
                                    ? qsTr("Saving…")
                                    : qsTr("Unsaved changes")
                                color: milestoneRow.saving
                                    ? root.theme.action : root.theme.yellow
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                            }
                        }
                        Controls.TextField {
                            id: nameField
                            Layout.fillWidth: true
                            theme: root.theme
                            text: milestoneRow.description
                            placeholderText: qsTr("Milestone name")
                            enabled: !milestoneRow.saving
                                && !milestoneController.busy
                            onEditingFinished: milestoneController.stage_value(
                                milestoneRow.code, "description", text)
                        }
                    }

                    ColumnLayout {
                        Layout.preferredWidth: 168
                        spacing: 3
                        Label {
                            Layout.preferredHeight: 12
                            Layout.minimumHeight: 12
                            Layout.maximumHeight: 12
                            text: qsTr("DUE DATE")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            font.weight: Font.Bold
                        }
                        Controls.DateField {
                            id: dueDateField
                            Layout.fillWidth: true
                            theme: root.theme
                            text: milestoneRow.dueDate
                            placeholderText: qsTr("Due date")
                            includeTime: false
                            allowClear: false
                            enabled: !milestoneRow.saving
                                && !milestoneController.busy
                            onAccepted: value => milestoneController.stage_value(
                                milestoneRow.code, "dueDate", value)
                            onEditingFinished: milestoneController.stage_value(
                                milestoneRow.code, "dueDate", text)
                        }
                    }

                    ColumnLayout {
                        Layout.preferredWidth: actionRow.implicitWidth
                        spacing: 3
                        Item {
                            Layout.preferredHeight: 12
                            Layout.minimumHeight: 12
                            Layout.maximumHeight: 12
                        }
                        RowLayout {
                            id: actionRow
                            Layout.preferredHeight: root.theme.controlHeight
                            spacing: 2
                            Controls.CompactIconButton {
                                theme: root.theme
                                iconName: "undo"
                                toolTip: milestoneRow.isNew
                                    ? qsTr("Discard milestone")
                                    : qsTr("Discard changes")
                                visible: milestoneRow.dirty
                                enabled: !milestoneController.busy
                                onClicked: milestoneController.discard(
                                    milestoneRow.code)
                            }
                            Controls.CompactIconButton {
                                theme: root.theme
                                iconName: "save"
                                iconColor: milestoneRow.dirty
                                    ? root.theme.action
                                    : root.theme.disabledText
                                toolTip: qsTr("Save milestone")
                                enabled: milestoneRow.dirty
                                    && !milestoneController.busy
                                onClicked: {
                                    milestoneController.stage_value(
                                        milestoneRow.code, "description",
                                        nameField.text)
                                    milestoneController.stage_value(
                                        milestoneRow.code, "dueDate",
                                        dueDateField.text)
                                    milestoneController.save(milestoneRow.code)
                                }
                            }
                            Controls.CompactIconButton {
                                theme: root.theme
                                iconName: "delete"
                                iconColor: root.theme.error
                                toolTip: qsTr("Delete milestone")
                                enabled: !milestoneController.busy
                                onClicked: {
                                    root.pendingDeleteCode = milestoneRow.code
                                    deleteDialog.open()
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    id: planPanel
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: errorLabel.visible
                        ? errorLabel.top : parent.bottom
                    anchors.leftMargin: 69
                    anchors.rightMargin: 10
                    anchors.bottomMargin: errorLabel.visible ? 2 : 7
                    height: 43
                    radius: root.theme.controlRadius
                    color: root.theme.surfaceContainerHighest

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 9
                        anchors.rightMargin: 9
                        spacing: 9

                        Rectangle {
                            Layout.preferredWidth: 28
                            Layout.preferredHeight: 28
                            radius: root.theme.controlRadius
                            color: root.theme.secondaryContainer
                            Controls.MaterialIcon {
                                anchors.centerIn: parent
                                name: "milestone"
                                size: 15
                                color: root.theme.action
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                text: qsTr("MILESTONE PLAN") + "  ·  "
                                    + (milestoneRow.taskCount > 0
                                        ? milestoneRow.completedCount + " / "
                                            + milestoneRow.taskCount + " "
                                            + qsTr("tasks")
                                        : qsTr("No tasks"))
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.DemiBold
                            }
                            Label {
                                Layout.fillWidth: true
                                text: milestoneRow.taskCount > 0
                                    ? (milestoneRow.planStartDate
                                        || qsTr("Start not set"))
                                        + "  →  " + milestoneRow.dueDate
                                        + (milestoneRow.processSummary
                                            ? "  ·  "
                                                + milestoneRow.processSummary : "")
                                        + (milestoneRow.plannedHours > 0
                                            ? "  ·  "
                                                + milestoneRow.plannedHours
                                                + " h" : "")
                                    : qsTr("Assign tasks to build the milestone plan")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                        ColumnLayout {
                            Layout.preferredWidth: 128
                            spacing: 3
                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: qsTr("COMPLETION")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.micro
                                    font.weight: Font.Bold
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: milestoneRow.taskCount > 0
                                        ? milestoneRow.completion + "%" : "—"
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: Font.DemiBold
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 5
                                radius: 2.5
                                color: root.theme.surfaceContainerLow
                                Rectangle {
                                    width: parent.width * Math.max(0, Math.min(
                                        100, milestoneRow.completion)) / 100
                                    height: parent.height
                                    radius: parent.radius
                                    color: root.theme.action
                                }
                            }
                        }
                        Label {
                            visible: milestoneRow.overdueCount > 0
                            text: milestoneRow.overdueCount + " "
                                + qsTr("overdue")
                            color: root.theme.error
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            font.weight: Font.DemiBold
                        }
                    }
                }

                Label {
                    id: errorLabel
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.leftMargin: 69
                    anchors.rightMargin: 10
                    anchors.bottomMargin: 6
                    visible: milestoneRow.error.length > 0
                    text: qsTr(milestoneRow.error)
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    elide: Text.ElideRight
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: milestoneList
            }
        }

        Item {
            objectName: "milestoneEmptyState"
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !milestoneController.busy
                && milestoneController.visibleCount === 0
            ColumnLayout {
                objectName: "milestoneEmptyStateContent"
                anchors.centerIn: parent
                spacing: 8
                Controls.MaterialIcon {
                    Layout.alignment: Qt.AlignHCenter
                    name: "milestone"
                    size: 36
                    color: root.theme.disabledText
                }
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: searchField.text
                        ? qsTr("No matching milestones")
                        : qsTr("No milestones yet")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: searchField.text
                        ? qsTr("Try another search")
                        : qsTr("Create a reusable deadline for project tasks")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
                Controls.FilledActionButton {
                    visible: !searchField.text
                    Layout.alignment: Qt.AlignHCenter
                    theme: root.theme
                    iconName: "add"
                    text: qsTr("New milestone")
                    onClicked: root.createMilestone()
                }
            }
        }
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        z: 50
        visible: milestoneController.busy
        theme: root.theme
        message: qsTr("Updating milestones…")
    }

    Controls.Dialog {
        id: deleteDialog
        anchors.centerIn: parent
        theme: root.theme
        title: qsTr("Delete milestone?")
        width: Math.min(440, root.width - 32)
        contentItem: Label {
            width: deleteDialog.width - 40
            text: qsTr("The milestone will only be deleted when no tasks use it.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            wrapMode: Text.WordWrap
        }
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: deleteDialog.reject()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                destructive: true
                onClicked: {
                    milestoneController.delete_milestone(root.pendingDeleteCode)
                    root.pendingDeleteCode = ""
                    deleteDialog.accept()
                }
            }
        }
    }

    Controls.Dialog {
        id: refreshDialog
        anchors.centerIn: parent
        theme: root.theme
        title: qsTr("Discard unsaved changes?")
        width: Math.min(440, root.width - 32)
        contentItem: Label {
            width: refreshDialog.width - 40
            text: qsTr("Refreshing will discard every unsaved milestone change.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            wrapMode: Text.WordWrap
        }
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                theme: root.theme
                text: qsTr("Keep editing")
                onClicked: refreshDialog.reject()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Discard and refresh")
                destructive: true
                onClicked: {
                    refreshDialog.accept()
                    milestoneController.discard_all_and_refresh()
                }
            }
        }
    }

    Component.onCompleted: milestoneController.refresh()
}
