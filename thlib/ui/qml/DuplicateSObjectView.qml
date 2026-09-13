import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    objectName: "duplicateSObjectView"
    required property var theme
    readonly property bool compactLayout: width < 700
    readonly property bool compactFooter: width < 1000
    readonly property real minimumFieldCardWidth: 430
    readonly property int maximumFieldColumns: 3

    Controls.ImageFileDialog {
        id: previewFileDialog
        onImageSelected: (row, image) => {
            if (row >= 0)
                sobjectDuplicateFieldModel.setValue(row, image)
        }
    }

    readonly property var stepModel: [
        { "value": "0", "label": qsTr("Fields"), "icon": "edit" },
        { "value": "1", "label": qsTr("Relations"), "icon": "account-tree" },
        { "value": "2", "label": qsTr("Snapshots"), "icon": "inventory-2" },
        { "value": "3", "label": qsTr("Tasks and messages"), "icon": "task" },
        { "value": "4", "label": qsTr("Review"), "icon": "fact-check" }
    ]
    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        Rectangle {
            id: header
            objectName: "duplicateSObjectHeader"
            Layout.fillWidth: true
            Layout.preferredHeight: 68
            radius: root.theme.sectionRadius
            color: root.theme.surfaceContainer

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 11

                Rectangle {
                    Layout.preferredWidth: 42
                    Layout.preferredHeight: 42
                    radius: root.theme.itemRadius
                    color: root.theme.surfaceContainerHigh
                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: "control-point-duplicate"
                        size: 21
                        color: root.theme.action
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 1
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Duplicate %1").arg(
                            sobjectDuplicateController.title || qsTr("sObject"))
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: sobjectDuplicateController.searchType
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideMiddle
                    }
                }
                Controls.StatusChip {
                    theme: root.theme
                    text: qsTr("Step %1 of 5").arg(
                        sobjectDuplicateController.step + 1)
                    iconName: root.stepModel[
                        sobjectDuplicateController.step].icon
                    accentColor: root.theme.action
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "help"
                    toolTip: qsTr("Duplication help")
                    onClicked: windowModel.open_help("duplicating_objects")
                }
            }
        }

        Controls.SegmentedButton {
            id: steps
            objectName: "duplicateSObjectSteps"
            Layout.fillWidth: true
            theme: root.theme
            model: root.stepModel
            currentValue: String(sobjectDuplicateController.step)
            minimumSegmentWidth: 76
            segmentWidth: Math.max(76, width / 5 - 2)
            onActivated: value => sobjectDuplicateController.set_step(
                Number(value))
        }

        Loader {
            id: pageLoader
            objectName: "duplicateSObjectPageLoader"
            Layout.fillWidth: true
            Layout.fillHeight: true
            active: sobjectDuplicateController.ready
                && !sobjectDuplicateController.busy
            sourceComponent: {
                if (sobjectDuplicateController.step === 0)
                    return fieldsPage
                if (sobjectDuplicateController.step === 1)
                    return relationsPage
                if (sobjectDuplicateController.step === 2
                        || sobjectDuplicateController.step === 3)
                    return processContentPage
                return reviewPage
            }
        }

        Rectangle {
            objectName: "duplicateSObjectErrorBanner"
            Layout.fillWidth: true
            Layout.preferredHeight: duplicateError.implicitHeight + 18
            visible: sobjectDuplicateController.error.length > 0
            radius: root.theme.itemRadius
            color: root.theme.errorContainer
            border.width: 1
            border.color: root.theme.error

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 11
                anchors.rightMargin: 11
                spacing: 8
                Controls.MaterialIcon {
                    name: "warning"
                    size: 17
                    color: root.theme.error
                }
                Label {
                    id: duplicateError
                    Layout.fillWidth: true
                    text: sobjectDuplicateController.error
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
                Controls.Button {
                    visible: !sobjectDuplicateController.ready
                    theme: root.theme
                    text: qsTr("Retry")
                    icon.name: "refresh"
                    onClicked: sobjectDuplicateController.retry()
                }
            }
        }

        Controls.DockWorkspaceFooter {
            id: footer
            objectName: "duplicateSObjectFooter"
            theme: root.theme
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            roundTopLeft: true
            roundTopRight: true
            topDividerVisible: false

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 13
                anchors.rightMargin: 10
                spacing: root.compactFooter ? 5 : 8

                Controls.CheckBox {
                    objectName: "duplicateRememberSettings"
                    theme: root.theme
                    compact: root.compactFooter
                    visible: sobjectDuplicateController.ready
                    checked: sobjectDuplicateController.rememberSettings
                    text: root.compactFooter ? qsTr("Remember")
                        : qsTr("Remember for this Search Type")
                    onToggled: sobjectDuplicateController.rememberSettings = checked
                }
                Item { Layout.fillWidth: true }
                Controls.Button {
                    objectName: "duplicateCancelButton"
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: sobjectDuplicateController.cancel()
                }
                Controls.Button {
                    objectName: "duplicatePreviousButton"
                    visible: sobjectDuplicateController.ready
                        && sobjectDuplicateController.step > 0
                    theme: root.theme
                    compact: root.compactFooter
                    text: qsTr("Back")
                    icon.name: "arrow-back"
                    onClicked: sobjectDuplicateController.previous_step()
                }
                Controls.Button {
                    objectName: "duplicateNextButton"
                    visible: sobjectDuplicateController.ready
                        && sobjectDuplicateController.step < 4
                    theme: root.theme
                    compact: root.compactFooter
                    text: qsTr("Next")
                    icon.name: "arrow-forward"
                    onClicked: sobjectDuplicateController.next_step()
                }
                Controls.Button {
                    objectName: "duplicateConfirmButton"
                    enabled: sobjectDuplicateController.ready
                        && !sobjectDuplicateController.duplicating
                    theme: root.theme
                    text: qsTr("Duplicate")
                    icon.name: "control-point-duplicate"
                    highlighted: true
                    onClicked: sobjectDuplicateController.duplicate()
                }
            }
        }
    }
    Component {
        id: fieldsPage
        ScrollView {
            id: fieldsScroll
            objectName: "duplicateFieldsPage"
            clip: true
            contentWidth: availableWidth
            leftPadding: 6
            rightPadding: 10
            topPadding: 6
            bottomPadding: 10
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
            ColumnLayout {
                width: fieldsScroll.availableWidth
                spacing: 10

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: fieldIntro.implicitHeight + 24
                    radius: root.theme.sectionRadius
                    color: root.theme.surfaceContainerLow
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 10
                        Controls.MaterialIcon {
                            name: "edit"
                            size: 18
                            color: root.theme.action
                        }
                        Label {
                            id: fieldIntro
                            Layout.fillWidth: true
                            text: qsTr("Edit the values of the new object. Identity, project and relationship columns are generated or managed automatically.")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                SObjectFieldGrid {
                    id: fieldFlow
                    objectName: "duplicateFieldFlow"
                    Layout.fillWidth: true
                    theme: root.theme
                    fieldModel: sobjectDuplicateFieldModel
                    itemPrefix: "duplicateFieldItem_"
                    repeaterObjectName: "duplicateFieldRepeater"
                    editorBusy: sobjectDuplicateController.duplicating
                    minimumCellWidth: root.minimumFieldCardWidth
                    maximumColumns: root.maximumFieldColumns
                    onPreviewRequested: row => previewFileDialog.openForRow(row)
                }
            }
        }
    }
    Component {
        id: relationsPage
        ScrollView {
            id: relationsScroll
            objectName: "duplicateRelationsPage"
            clip: true
            contentWidth: availableWidth
            leftPadding: 6
            rightPadding: 10
            topPadding: 6
            bottomPadding: 10
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

            ColumnLayout {
                width: relationsScroll.availableWidth
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    text: qsTr("Choose what happens to each relationship already attached to the source object.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                }

                Repeater {
                    objectName: "duplicateRelationRepeater"
                    model: sobjectDuplicateRelationModel
                    delegate: Rectangle {
                        id: relationCard
                        required property int index
                        required property string kind
                        required property string relationship
                        required property string searchType
                        required property string title
                        required property int count
                        required property string mode
                        required property var options
                        required property var items
                        Layout.fillWidth: true
                        implicitHeight: relationColumn.implicitHeight + 22
                        radius: root.theme.sectionRadius
                        color: root.theme.surfaceContainer

                        ColumnLayout {
                            id: relationColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 11
                            spacing: 7
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 9
                                Rectangle {
                                    Layout.preferredWidth: 34
                                    Layout.preferredHeight: 34
                                    radius: root.theme.itemRadius
                                    color: root.theme.surfaceContainerHigh
                                    Controls.MaterialIcon {
                                        anchors.centerIn: parent
                                        name: relationCard.kind === "instance"
                                            ? "hub" : relationCard.kind === "parent"
                                                ? "arrow-upward" : "arrow-downward"
                                        size: 17
                                        color: root.theme.action
                                    }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    spacing: 0
                                    Label {
                                        Layout.fillWidth: true
                                        text: relationCard.title
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.body
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: relationCard.kind === "instance"
                                            ? qsTr("Instance links · %1 objects").arg(relationCard.count)
                                            : relationCard.kind === "parent"
                                                ? qsTr("Parent relation · %1 object(s)").arg(relationCard.count)
                                                : qsTr("Child relation · %1 object(s)").arg(relationCard.count)
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                            Controls.SegmentedButton {
                                objectName: "duplicateRelationMode_" + relationCard.index
                                Layout.fillWidth: true
                                theme: root.theme
                                model: relationCard.options
                                currentValue: relationCard.mode
                                minimumSegmentWidth: 104
                                segmentWidth: Math.max(104,
                                    (relationColumn.width - 6) / Math.max(
                                        1, relationCard.options.length))
                                onActivated: value => sobjectDuplicateController.set_relation_mode(
                                    relationCard.index, value)
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: relationCard.items && relationCard.items.length > 0
                                text: relationCard.items
                                    ? relationCard.items.map(item => item.title).join("  ·  ")
                                    : ""
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                    }
                }

                Controls.EmptyState {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 190
                    visible: sobjectDuplicateRelationModel.count() === 0
                    theme: root.theme
                    iconName: "link-off"
                    title: qsTr("No linked objects")
                    message: qsTr("The duplicate can be created without relationship decisions.")
                }
            }
        }
    }

    Component {
        id: processContentPage
        ScrollView {
            id: contentScroll
            readonly property bool snapshotsPage:
                sobjectDuplicateController.step === 2
            objectName: snapshotsPage
                ? "duplicateSnapshotsPage" : "duplicateTasksMessagesPage"
            clip: true
            contentWidth: availableWidth
            leftPadding: 6
            rightPadding: 10
            topPadding: 6
            bottomPadding: 10
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

            ColumnLayout {
                width: contentScroll.availableWidth
                spacing: 8
                Label {
                    Layout.fillWidth: true
                    text: contentScroll.snapshotsPage
                        ? qsTr("Choose current snapshots and files to duplicate for each process. Message attachments are handled with their messages on the next step.")
                        : qsTr("Choose tasks, process messages, task messages, and their attached files. Copying task messages also copies their parent tasks.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                }

                Repeater {
                    objectName: "duplicateProcessRepeater"
                    model: sobjectDuplicateProcessModel
                    delegate: Rectangle {
                        id: processCard
                        required property int index
                        required property string name
                        required property int snapshotCount
                        required property int fileCount
                        required property int taskCount
                        required property int processMessageCount
                        required property int taskMessageCount
                        required property int processAttachmentCount
                        required property int taskAttachmentCount
                        required property bool copySnapshots
                        required property bool copyTasks
                        required property bool copyProcessMessages
                        required property bool copyTaskMessages
                        required property bool copyProcessAttachments
                        required property bool copyTaskAttachments
                        Layout.fillWidth: true
                        visible: contentScroll.snapshotsPage
                            ? snapshotCount > 0
                            : taskCount + processMessageCount
                                + taskMessageCount > 0
                        Layout.preferredHeight: visible ? implicitHeight : 0
                        implicitHeight: processColumn.implicitHeight + 22
                        radius: root.theme.sectionRadius
                        color: root.theme.surfaceContainer

                        ColumnLayout {
                            id: processColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 11
                            spacing: 5
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Controls.MaterialIcon {
                                    name: "account-tree"
                                    size: 18
                                    color: root.theme.action
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: processCard.name
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Controls.StatusChip {
                                    theme: root.theme
                                    text: qsTr("%1 items").arg(
                                        contentScroll.snapshotsPage
                                        ? processCard.snapshotCount
                                        : processCard.taskCount
                                            + processCard.processMessageCount
                                            + processCard.taskMessageCount)
                                    iconName: "inventory-2"
                                    accentColor: root.theme.secondaryText
                                }
                            }
                            Flow {
                                Layout.fillWidth: true
                                spacing: 5
                                Controls.CheckBox {
                                    objectName: "duplicateSnapshots_" + processCard.index
                                    theme: root.theme
                                    visible: contentScroll.snapshotsPage
                                        && processCard.snapshotCount > 0
                                    checked: processCard.copySnapshots
                                    text: qsTr("Snapshots %1 · files %2")
                                        .arg(processCard.snapshotCount)
                                        .arg(processCard.fileCount)
                                    onToggled: sobjectDuplicateController.set_process_choice(
                                        processCard.index, "copySnapshots", checked)
                                }
                                Controls.CheckBox {
                                    objectName: "duplicateTasks_" + processCard.index
                                    theme: root.theme
                                    visible: !contentScroll.snapshotsPage
                                        && processCard.taskCount > 0
                                    checked: processCard.copyTasks
                                    text: qsTr("Tasks %1").arg(processCard.taskCount)
                                    onToggled: sobjectDuplicateController.set_process_choice(
                                        processCard.index, "copyTasks", checked)
                                }
                                Controls.CheckBox {
                                    objectName: "duplicateProcessMessages_" + processCard.index
                                    theme: root.theme
                                    visible: !contentScroll.snapshotsPage
                                        && processCard.processMessageCount > 0
                                    checked: processCard.copyProcessMessages
                                    text: qsTr("Process messages %1").arg(
                                        processCard.processMessageCount)
                                    onToggled: sobjectDuplicateController.set_process_choice(
                                        processCard.index, "copyProcessMessages", checked)
                                }
                                Controls.CheckBox {
                                    theme: root.theme
                                    visible: !contentScroll.snapshotsPage
                                        && processCard.processAttachmentCount > 0
                                    checked: processCard.copyProcessAttachments
                                    text: qsTr("Process attachments, files %1").arg(
                                        processCard.processAttachmentCount)
                                    onToggled: sobjectDuplicateController.set_process_choice(
                                        processCard.index, "copyProcessAttachments", checked)
                                }
                                Controls.CheckBox {
                                    objectName: "duplicateTaskMessages_" + processCard.index
                                    theme: root.theme
                                    visible: !contentScroll.snapshotsPage
                                        && processCard.taskMessageCount > 0
                                    checked: processCard.copyTaskMessages
                                    text: qsTr("Task messages %1").arg(
                                        processCard.taskMessageCount)
                                    onToggled: sobjectDuplicateController.set_process_choice(
                                        processCard.index, "copyTaskMessages", checked)
                                }
                                Controls.CheckBox {
                                    theme: root.theme
                                    visible: !contentScroll.snapshotsPage
                                        && processCard.taskAttachmentCount > 0
                                    checked: processCard.copyTaskAttachments
                                    text: qsTr("Task attachments, files %1").arg(
                                        processCard.taskAttachmentCount)
                                    onToggled: sobjectDuplicateController.set_process_choice(
                                        processCard.index, "copyTaskAttachments", checked)
                                }
                            }
                        }
                    }
                }

                Controls.EmptyState {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 190
                    visible: contentScroll.snapshotsPage
                        ? sobjectDuplicateController.availableSnapshotCount === 0
                        : sobjectDuplicateController.availableTaskMessageCount === 0
                    theme: root.theme
                    iconName: "inventory-2"
                    title: contentScroll.snapshotsPage
                        ? qsTr("No snapshots") : qsTr("No tasks or messages")
                    message: contentScroll.snapshotsPage
                        ? qsTr("No current snapshots are attached to this object.")
                        : qsTr("No tasks, process messages, or task messages are attached to this object.")
                }
            }
        }
    }

    Component {
        id: reviewPage
        ScrollView {
            id: reviewScroll
            objectName: "duplicateReviewPage"
            clip: true
            contentWidth: availableWidth
            leftPadding: 6
            rightPadding: 10
            topPadding: 6
            bottomPadding: 10
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

            ColumnLayout {
                width: reviewScroll.availableWidth
                spacing: 10
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: reviewColumn.implicitHeight + 28
                    radius: root.theme.sectionRadius
                    color: root.theme.surfaceContainer
                    ColumnLayout {
                        id: reviewColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 10
                        Controls.MaterialIcon {
                            Layout.alignment: Qt.AlignHCenter
                            name: "control-point-duplicate"
                            size: 34
                            color: root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Ready to create the duplicate")
                            horizontalAlignment: Text.AlignHCenter
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("The new object receives the edited fields. Selected links are recreated; original instance targets are never duplicated.")
                            horizontalAlignment: Text.AlignHCenter
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.alignment: Qt.AlignHCenter
                            spacing: 7
                            Controls.SummaryChip {
                                theme: root.theme
                                label: qsTr("Related")
                                count: sobjectDuplicateController.selectedRelationCount
                                accent: root.theme.action
                            }
                            Controls.SummaryChip {
                                theme: root.theme
                                label: qsTr("Snapshots")
                                count: sobjectDuplicateController.selectedSnapshotCount
                                accent: root.theme.action
                            }
                            Controls.SummaryChip {
                                theme: root.theme
                                label: qsTr("Tasks")
                                count: sobjectDuplicateController.selectedTaskCount
                                accent: root.theme.action
                            }
                            Controls.SummaryChip {
                                theme: root.theme
                                label: qsTr("Messages and files")
                                count: sobjectDuplicateController.selectedMessageCount + sobjectDuplicateController.selectedAttachmentCount
                                accent: root.theme.action
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: rememberedRow.implicitHeight + 22
                    radius: root.theme.itemRadius
                    color: root.theme.surfaceContainerLow
                    RowLayout {
                        id: rememberedRow
                        anchors.fill: parent
                        anchors.margins: 11
                        spacing: 9
                        Controls.MaterialIcon {
                            name: "bolt"
                            size: 18
                            color: root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: sobjectDuplicateController.rememberSettings
                                ? qsTr("These choices will enable Quick duplicate for this Search Type.")
                                : qsTr("These choices will be used only once.")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
    }

    ContentLoadingOverlay {
        objectName: "duplicateLoadingOverlay"
        anchors.fill: parent
        anchors.margins: 10
        anchors.topMargin: header.height + steps.height + 30
        anchors.bottomMargin: footer.height + 22
        visible: sobjectDuplicateController.busy
            || sobjectDuplicateController.duplicating
        theme: root.theme
        message: sobjectDuplicateController.duplicating
            ? qsTr("Creating duplicate on the server… You can continue working.")
            : qsTr("Analyzing fields, relations and process content…")
        // Analysis can be cancelled before mutation starts. TACTIC executes
        // the creation as one server transaction, so pretending to cancel a
        // running request would only hide a duplicate that may still commit.
        cancellable: !sobjectDuplicateController.duplicating
        onCancelRequested: sobjectDuplicateController.cancel()
    }
}
