import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property var controller: administrationController.workflowEditor.rulesEditor
    property string page: "triggers"
    readonly property var rules: controller.document.rules || []
    readonly property var rule: controller.selectedRule
    readonly property bool rulePage: page === "triggers" || page === "notifications"

    function selectVisibleRule() {
        if (!rulePage) return
        const kind = page === "notifications" ? "notification" : "trigger"
        if (rule.kind !== kind)
            controller.select_rule(rules.findIndex(row => row.kind === kind))
    }
    onPageChanged: selectVisibleRule()
    onRulesChanged: selectVisibleRule()

    AdminDocumentShell {
        anchors.fill: parent
        anchors.margins: 14
        theme: root.theme
        controller: root.controller
        title: qsTr("Process dependencies") + (root.controller.metadata.process ? " · " + root.controller.metadata.process : "")
        description: (root.controller.metadata.searchType || "") + " / " + (root.controller.metadata.pipeline || "")
        iconName: "schema"
        showSelector: false
        confirmationMessage: qsTr("Save process rules on the server? Global rules also affect same-name processes in other pipelines. Removed rules will be deleted; their scripts are kept. Actions and notifications are not executed by Save.")
        editorContent: ColumnLayout {
            // The alias reparents this item into AdminDocumentShell's plain Item.
            anchors.fill: parent // qmllint disable Quick.layout-positioning
            spacing: 12
            Controls.SegmentedButton {
                objectName: "adminDependencyPages"
                Layout.fillWidth: true
                theme: root.theme
                currentValue: root.page
                model: [
                    {value: "triggers", label: qsTr("Triggers") + " · " + root.rules.filter(row => row.kind === "trigger").length, translate: false, icon: "process"},
                    {value: "notifications", label: qsTr("Notifications") + " · " + root.rules.filter(row => row.kind === "notification").length, translate: false, icon: "notifications"},
                    {value: "naming", label: qsTr("Naming") + " · " + (root.controller.metadata.naming || []).length, translate: false, icon: "naming-editor"},
                    {value: "objects", label: qsTr("Search Objects") + " · " + (root.controller.metadata.itemCount || 0), translate: false, icon: "sobject"}
                ]
                onActivated: value => {
                    root.forceActiveFocus()
                    root.page = value
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.rulePage
                spacing: 12
                Controls.EditorPanel {
                    Layout.preferredWidth: Math.min(270, root.width * 0.3)
                    Layout.fillHeight: true
                    theme: root.theme
                    title: root.page === "notifications" ? qsTr("Notifications") : qsTr("Triggers")
                    iconName: root.page === "notifications" ? "notifications" : "process"
                    actions: [Controls.CompactIconButton {
                        objectName: "adminAddProcessRule"
                        theme: root.theme
                        iconName: "add"
                        toolTip: qsTr("Create")
                        enabled: root.controller.canWrite
                        onClicked: root.controller.add_rule(root.page === "notifications" ? "notification" : "trigger")
                    }]
                    ListView {
                        id: ruleList
                        objectName: "adminProcessRulesList"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 6
                        model: root.rules.map((row, index) => ({rule: row, rowIndex: index})).filter(
                            row => row.rule.kind === (root.page === "notifications" ? "notification" : "trigger"))
                        delegate: Controls.EditorListItem {
                            required property var modelData
                            objectName: "adminProcessRule_" + modelData.rowIndex
                            width: Math.max(0, ruleList.width - ruleBar.reservedExtent - 4)
                            theme: root.theme
                            text: modelData.rule.title || (modelData.rule.key ? modelData.rule.event : qsTr("New rule"))
                            description: modelData.rule.managed ? qsTr("Managed by node parameters")
                                : modelData.rule.scope === "global" ? qsTr("All matching processes") : qsTr("This pipeline")
                            iconName: modelData.rule.managed ? "lock" : "edit"
                            selected: root.controller.selectedIndex === modelData.rowIndex
                            onClicked: {
                                root.forceActiveFocus()
                                root.controller.select_rule(modelData.rowIndex)
                                ruleViewport.contentY = 0
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            id: ruleBar
                            theme: root.theme
                            flickableTarget: ruleList
                        }
                    }
                }
                Controls.EditorPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    title: root.rule.title || (root.rule.kind ? qsTr("New rule") : qsTr("Select a rule"))
                    iconName: "edit"
                    actions: [Controls.CompactIconButton {
                        objectName: "adminRemoveProcessRule"
                        theme: root.theme
                        iconName: "delete"
                        iconColor: root.theme.error
                        toolTip: qsTr("Remove")
                        enabled: root.controller.canWrite && !!root.rule.kind && !root.rule.managed
                        onClicked: removeConfirmation.open()
                    }]
                    Flickable {
                        id: ruleViewport
                        objectName: "adminRuleViewport"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: width
                        contentHeight: ruleContent.implicitHeight + 4
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        ColumnLayout {
                            id: ruleContent
                            width: Math.max(0, ruleViewport.width - detailBar.reservedExtent - 4)
                            Controls.EmptyState {
                                Layout.fillWidth: true
                                visible: !root.rule.kind
                                theme: root.theme
                                iconName: "process"
                                title: qsTr("No rule selected")
                                message: qsTr("Create a trigger or notification using the plus button.")
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: root.rule.managed === true
                                text: qsTr("This trigger is generated by the workflow engine. Edit its action or progress listener in the node parameters, not in a second copy here.")
                                color: root.theme.secondaryText
                                wrapMode: Text.Wrap
                            }
                            Loader {
                                Layout.fillWidth: true
                                active: !!root.rule.kind
                                sourceComponent: AdminProcessRuleForm {
                                    theme: root.theme
                                    controller: root.controller
                                }
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            id: detailBar
                            theme: root.theme
                            flickableTarget: ruleViewport
                        }
                    }
                }
            }
            Controls.EditorPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: !root.rulePage
                theme: root.theme
                title: root.page === "naming" ? qsTr("Naming conventions") : qsTr("Objects using this pipeline")
                description: root.page === "naming"
                    ? qsTr("Rules whose context starts with this process. Edit naming in the Search Type's existing Naming Editor.")
                    : qsTr("This count is for the pipeline, not the number of tasks in this process.")
                ListView {
                    id: dependencyList
                    objectName: "adminRelatedObjects"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 6
                    model: root.page === "naming" ? root.controller.metadata.naming || [] : root.controller.metadata.items || []
                    delegate: Controls.EditorListItem {
                        required property var modelData
                        width: Math.max(0, dependencyList.width - dependencyBar.reservedExtent - 4)
                        theme: root.theme
                        text: root.page === "naming" ? modelData.context || "" : modelData.label || ""
                        description: root.page === "naming" ? (modelData.directory || "") + " / " + (modelData.file || "") : ""
                        iconName: root.page === "naming" ? "naming-editor" : "sobject"
                        onClicked: if (root.page === "objects") root.controller.open_object(modelData.key)
                    }
                    ScrollBar.vertical: Controls.ScrollBar {
                        id: dependencyBar
                        theme: root.theme
                        flickableTarget: dependencyList
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    visible: root.page === "objects"
                    Controls.Button {
                        objectName: "adminObjectsPrevious"
                        theme: root.theme
                        text: qsTr("Previous")
                        enabled: !root.controller.dirty && (root.controller.metadata.itemOffset || 0) > 0
                        onClicked: root.controller.show_item_page(root.controller.metadata.itemOffset - 50)
                    }
                    Label {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        text: (root.controller.metadata.itemOffset || 0) + (dependencyList.count ? 1 : 0)
                            + "–" + ((root.controller.metadata.itemOffset || 0) + dependencyList.count)
                            + " / " + (root.controller.metadata.itemCount || 0)
                        color: root.theme.secondaryText
                    }
                    Controls.Button {
                        objectName: "adminObjectsNext"
                        theme: root.theme
                        text: qsTr("Next")
                        enabled: !root.controller.dirty && (root.controller.metadata.itemOffset || 0) + dependencyList.count < (root.controller.metadata.itemCount || 0)
                        onClicked: root.controller.show_item_page((root.controller.metadata.itemOffset || 0) + 50)
                    }
                }
            }
        }
    }
    Controls.Dialog {
        id: removeConfirmation
        objectName: "adminRemoveRuleConfirmation"
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(440, root.width - 32)
        title: qsTr("Remove this rule?")
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: root.controller.remove_rule()
        contentItem: Label {
            text: qsTr("The rule will be removed from the server when you save. The script itself is not deleted.")
            wrapMode: Text.Wrap
            color: root.theme.primaryText
        }
    }
}
