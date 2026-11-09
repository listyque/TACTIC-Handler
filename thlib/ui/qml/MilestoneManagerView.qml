import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/milestones.ui.mjs" as UI

Item {
    id: root

    required property var theme
    property string pendingDeleteCode: ""
    property string query: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language

    readonly property var geometry: UI.layout(width, height, theme.controlHeight)

    function createMilestone() {
        query = "";
        milestoneController.set_filter("");
        milestoneController.create_milestone();
        milestoneList.currentIndex = 0;
        milestoneList.positionViewAtBeginning();
        Qt.callLater(function () {
            const item = milestoneList.currentItem;
            if (item)
                item.focusNameEditor();
        });
    }

    function dayPart(value) {
        const parts = String(value || "").split("-");
        return parts.length === 3 ? parts[2] : "--";
    }

    function monthPart(value) {
        const names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
        const parts = String(value || "").split("-");
        const index = parts.length === 3 ? Number(parts[1]) - 1 : -1;
        return index >= 0 && index < names.length ? names[index] : qsTr("DATE");
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    Item {
        anchors.fill: parent

        Frame.FrameView {
            theme: root.theme
            x: root.geometry.margin
            y: root.geometry.margin
            width: root.geometry.inner
            height: 76
            scene: UI.header({
                project: milestoneController.projectCode,
                count: milestoneController.count,
                radius: root.theme.itemRadius,
                busy: milestoneController.busy,
                canCreate: !!milestoneController.projectCode
            }, width, root.language)
            onEvent: action => {
                if (action.type === "create")
                    root.createMilestone();
                else if (milestoneController.hasDirtyRows)
                    refreshDialog.open();
                else
                    milestoneController.refresh();
            }
        }
        Frame.FrameView {
            theme: root.theme
            x: root.geometry.margin
            y: root.geometry.searchY
            width: root.geometry.inner
            height: root.theme.controlHeight
            scene: UI.search({
                query: root.query,
                controlHeight: root.theme.controlHeight,
                busy: milestoneController.busy
            }, width, root.language)
            onEvent: action => {
                root.query = action.value;
                milestoneController.set_filter(action.value);
            }
        }

        ListView {
            id: milestoneList
            x: root.geometry.margin
            y: root.geometry.listY
            width: root.geometry.inner
            height: root.geometry.listHeight
            clip: true
            spacing: 7
            reuseItems: true
            boundsBehavior: Flickable.StopAtBounds
            model: milestoneModel

            delegate: Frame.FrameView {
                id: milestoneRow
                Accessible.role: Accessible.Grouping
                Accessible.name: milestoneRow.description || qsTr("New milestone")
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
                    focusControl("milestoneName");
                }
                theme: root.theme
                width: milestoneList.width - 14
                height: scene.height
                scene: UI.row({
                    code,
                    description,
                    dueDate,
                    isNew,
                    dirty,
                    saving,
                    error,
                    completion,
                    taskCount,
                    completedCount,
                    overdueCount,
                    planStartDate,
                    processSummary,
                    plannedHours,
                    busy: milestoneController.busy,
                    radius: root.theme.itemRadius,
                    controlHeight: root.theme.controlHeight
                }, width, root.language)
                onEvent: action => {
                    if (action.type === "change")
                        milestoneController.stage_value(code, action.field, action.value);
                    else if (action.type === "discard")
                        milestoneController.discard(code);
                    else if (action.type === "save")
                        milestoneController.save(code);
                    else if (action.type === "delete") {
                        root.pendingDeleteCode = code;
                        deleteDialog.open();
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: milestoneList
            }
        }

        Item {
            objectName: "milestoneEmptyState"
            x: root.geometry.margin
            y: root.geometry.listY
            width: root.geometry.inner
            height: root.geometry.listHeight
            visible: !milestoneController.busy && milestoneController.visibleCount === 0
            Frame.FrameView {
                objectName: "milestoneEmptyStateContent"
                theme: root.theme
                anchors.centerIn: parent
                width: Math.min(360, parent.width)
                height: scene.height
                scene: UI.empty({
                    query: root.query,
                    busy: milestoneController.busy,
                    canCreate: !!milestoneController.projectCode
                }, width, root.language)
                onEvent: action => root.createMilestone()
            }
        }
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
                    milestoneController.delete_milestone(root.pendingDeleteCode);
                    root.pendingDeleteCode = "";
                    deleteDialog.accept();
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
                    refreshDialog.accept();
                    milestoneController.discard_all_and_refresh();
                }
            }
        }
    }

    Component.onCompleted: milestoneController.refresh()
}
