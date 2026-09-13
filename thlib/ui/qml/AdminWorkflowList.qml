import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    property var collapsed: ({})
    readonly property bool creatingPipeline: !controller.identity
        && controller.document.xml !== undefined
    readonly property var groups: groupPipelines(
        controller.processCatalog.pipelines || [],
        controller.processCatalog.searchTypes || [],
        creatingPipeline ? controller.document : null)

    function groupPipelines(pipelines, types, draft) {
        const groupsByType = {}
        for (const pipeline of pipelines) {
            const type = pipeline.searchType || ""
            if (!groupsByType[type]) groupsByType[type] = []
            groupsByType[type].push(pipeline)
        }
        if (draft && draft.searchType) {
            if (!groupsByType[draft.searchType]) groupsByType[draft.searchType] = []
            groupsByType[draft.searchType].push({
                identity: "",
                label: String(draft.name || "").trim() || qsTr("New pipeline"),
                searchType: draft.searchType,
                color: draft.color || "",
                draft: true
            })
        }
        // Status workflows are a distinct native catalog, even before the first
        // project-owned status workflow is created.
        if (!groupsByType["sthpw/task"]) groupsByType["sthpw/task"] = []
        const result = Object.keys(groupsByType).map(type => ({
            identity: type,
            label: type === "sthpw/task" ? qsTr("Task status workflows")
                : (types.find(row => row.identity === type) || {}).label || type || qsTr("No Search Type"),
            pipelines: groupsByType[type],
            forceExpanded: groupsByType[type].some(row => row.draft === true),
            canCreate: types.some(row => row.identity === type) || type === "sthpw/task"
        }))
        return result.sort((a, b) => a.identity === "sthpw/task" ? 1 : b.identity === "sthpw/task" ? -1 : a.label.localeCompare(b.label))
    }

    function visibleRows() {
        const rows = []
        for (const group of groups) {
            rows.push({header: true, identity: group.identity, label: group.label,
                count: group.pipelines.filter(row => row.draft !== true).length,
                canCreate: group.canCreate, forceExpanded: group.forceExpanded})
            if (group.forceExpanded || !collapsed[group.identity])
                for (const pipeline of group.pipelines) rows.push(Object.assign({header: false}, pipeline))
        }
        return rows
    }

    spacing: 6

    Controls.SectionLabel {
        Layout.fillWidth: true
        theme: root.theme
        text: qsTr("Workflows")
    }
    ListView {
        id: workflowList
        objectName: "adminWorkflowList"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 4
        model: root.visibleRows()
        boundsBehavior: Flickable.StopAtBounds
        delegate: Item {
            id: row
            required property var modelData
            width: Math.max(0, workflowList.width - workflowBar.reservedExtent - 4)
            height: entry.implicitHeight

            Controls.EditorListItem {
                id: entry
                objectName: row.modelData.draft ? "adminWorkflowDraft"
                    : (row.modelData.header ? "adminWorkflowGroup_" : "adminWorkflow_") + row.modelData.identity
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.rightMargin: createWorkflow.visible ? createWorkflow.width : 0
                theme: root.theme
                text: row.modelData.label
                wrapTitle: row.modelData.header
                badgeText: row.modelData.header ? String(row.modelData.count) : ""
                description: row.modelData.draft ? qsTr("Draft · not saved yet")
                    : row.modelData.shared ? qsTr("Shared · read-only") : ""
                iconName: row.modelData.header
                    ? (root.collapsed[row.modelData.identity] && !row.modelData.forceExpanded
                        ? "chevron-right" : "expand-more")
                    : row.modelData.draft ? "add" : "workflow"
                accent: row.modelData.color || root.theme.action
                selected: row.modelData.draft === true
                    || (!row.modelData.header && root.controller.identity === row.modelData.identity)
                enabled: row.modelData.header || row.modelData.draft === true
                    || (!root.controller.busy && !root.controller.dirty)
                padding: 8
                onClicked: {
                    root.forceActiveFocus()
                    if (row.modelData.header) {
                        const collapsed = Object.assign({}, root.collapsed)
                        collapsed[row.modelData.identity] = !collapsed[row.modelData.identity]
                        root.collapsed = collapsed
                    } else if (!row.modelData.draft) root.controller.select(row.modelData.identity)
                }
                Controls.ToolTip {
                    theme: root.theme
                    visible: entry.hovered
                    text: row.modelData.label + (row.modelData.identity ? "\n" + row.modelData.identity : "")
                }
            }
            Controls.CompactIconButton {
                id: createWorkflow
                objectName: "adminCreateWorkflow_" + row.modelData.identity
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                theme: root.theme
                visible: row.modelData.header && row.modelData.canCreate === true
                enabled: root.controller.processCatalog.canCreate === true && !root.controller.busy && !root.controller.dirty
                iconName: "add"
                toolTip: qsTr("Create workflow for %1").arg(row.modelData.label)
                onClicked: {
                    root.forceActiveFocus()
                    root.controller.new_document(row.modelData.identity, row.modelData.label)
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: workflowBar
            theme: root.theme
            flickableTarget: workflowList
        }
    }
}
