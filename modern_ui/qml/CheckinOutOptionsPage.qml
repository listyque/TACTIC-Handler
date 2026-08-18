import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property bool managed: true
    property bool loadingValues: true
    property var state: ({"globalTabs": [], "projects": []})
    property int currentProjectIndex: state.projects.length ? 0 : -1

    function currentProject() {
        return currentProjectIndex >= 0
            && currentProjectIndex < state.projects.length
            ? state.projects[currentProjectIndex] : null
    }

    function currentTabs() {
        const project = currentProject()
        return globalMode.checked || !project
            ? state.globalTabs : project.tabs
    }

    function selectProject(index) {
        currentProjectIndex = index
        const project = currentProject()
        if (project && project.searchTypes.length === 0)
            configurationController.load_checkinout_project(project.code)
    }

    function formValues() {
        return {
            "processFilterEnabled": processFilterEnabled.checked,
            "controlsFilterEnabled": controlsFilterEnabled.checked,
            "globalMode": globalMode.checked,
            "perProjectMode": perProjectMode.checked,
            "lastViewForAllTabs": lastViewForAllTabs.checked,
            "globalTabs": state.globalTabs,
            "projects": state.projects
        }
    }

    function loadValues(values) {
        loadingValues = true
        state = JSON.parse(JSON.stringify(values || {}))
        if (!state.globalTabs)
            state.globalTabs = []
        if (!state.projects)
            state.projects = []
        currentProjectIndex = state.projects.length ? 0 : -1
        processFilterEnabled.checked = Boolean(values.processFilterEnabled)
        controlsFilterEnabled.checked = Boolean(values.controlsFilterEnabled)
        globalMode.checked = values.globalMode !== false
        perProjectMode.checked = !globalMode.checked
        lastViewForAllTabs.checked = Boolean(values.lastViewForAllTabs)
        loadingValues = false
        if (currentProjectIndex >= 0)
            selectProject(currentProjectIndex)
    }

    function syncValues() {
        loadValues(configurationController.page_values(
            "checkinout_preferences"
        ))
    }

    function updateValues(rebuild) {
        if (rebuild)
            state = JSON.parse(JSON.stringify(state))
        if (managed && !loadingValues)
            configurationController.update_page(
                "checkinout_preferences", formValues()
            )
    }

    function moveTab(index, direction) {
        const tabs = currentTabs()
        const target = index + direction
        if (target < 0 || target >= tabs.length)
            return
        const item = tabs[index]
        tabs.splice(index, 1)
        tabs.splice(target, 0, item)
        updateValues(true)
    }

    function copyCurrentTabsToAll() {
        const source = JSON.parse(JSON.stringify(currentTabs()))
        for (let index = 0; index < state.projects.length; ++index)
            state.projects[index].tabs = JSON.parse(JSON.stringify(source))
        updateValues(true)
    }

    Component.onCompleted: syncValues()

    Connections {
        target: configurationController
        function onSessionStarted() { root.syncValues() }
        function onPageReset(pageId) {
            if (pageId === "checkinout_preferences")
                root.syncValues()
        }
        function onCheckinOutProjectLoaded(projectCode, records) {
            for (let index = 0; index < root.state.projects.length; ++index) {
                if (root.state.projects[index].code === projectCode) {
                    root.state.projects[index].searchTypes = records
                    root.state = JSON.parse(JSON.stringify(root.state))
                    break
                }
            }
        }
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: optionsRow.height + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            flickableTarget: scroll
        }

        RowLayout {
            id: optionsRow
            x: 22
            y: 20
            width: Math.max(0, scroll.availableWidth - 44)
            height: Math.max(620, root.height - 40)
            spacing: 14

            ConfigurationSection {
                Layout.preferredWidth: Math.min(230, parent.width * 0.30)
                Layout.fillHeight: true
                theme: root.theme
                title: qsTr("Projects")
                description: qsTr("Select a project to edit its search types.")
                iconName: "folder-open"

                ListView {
                    id: projectsList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 3
                    model: root.state.projects
                    ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

                    delegate: Rectangle {
                        id: projectRow
                        required property int index
                        required property var modelData
                        width: projectsList.width
                        height: 48
                        radius: 11
                        color: root.currentProjectIndex === index
                            ? root.theme.secondaryContainer
                            : projectMouse.containsMouse
                                ? root.theme.rowHover
                                : root.theme.surfaceContainerHigh

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 10
                            spacing: 1
                            Label {
                                Layout.fillWidth: true
                                text: projectRow.modelData.title
                                color: root.theme.primaryText
                                font.pointSize: Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: projectRow.modelData.code
                                color: root.theme.secondaryText
                                font.pointSize: Typography.label
                                elide: Text.ElideRight
                            }
                        }
                        MouseArea {
                            id: projectMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.selectProject(projectRow.index)
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 14

                ConfigurationSection {
                    Layout.fillWidth: true
                    theme: root.theme
                    title: qsTr("Control tabs")
                    description: qsTr("Visibility, labels and order of workspace tabs.")
                    iconName: "view-kanban"

                    RowLayout {
                        Layout.fillWidth: true
                        Md3CheckBox {
                            id: controlsFilterEnabled
                            theme: root.theme
                            text: qsTr("Filter control tabs")
                            onToggled: root.updateValues(false)
                        }
                        Item { Layout.fillWidth: true }
                        Md3CheckBox {
                            id: globalMode
                            theme: root.theme
                            text: qsTr("Globally")
                            onToggled: {
                                if (checked)
                                    perProjectMode.checked = false
                                else if (!perProjectMode.checked)
                                    perProjectMode.checked = true
                                root.updateValues(true)
                            }
                        }
                        Md3CheckBox {
                            id: perProjectMode
                            theme: root.theme
                            text: qsTr("Per project")
                            onToggled: {
                                if (checked)
                                    globalMode.checked = false
                                else if (!globalMode.checked)
                                    globalMode.checked = true
                                root.updateValues(true)
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        enabled: controlsFilterEnabled.checked
                        spacing: 4

                        Repeater {
                            model: root.currentTabs()
                            delegate: Rectangle {
                                id: tabRow
                                required property int index
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                radius: 11
                                color: root.theme.surfaceContainerHigh

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 7
                                    anchors.rightMargin: 7
                                    spacing: 5
                                    Md3CheckBox {
                                        theme: root.theme
                                        checked: tabRow.modelData.enabled
                                        onToggled: {
                                            tabRow.modelData.enabled = checked
                                            root.updateValues(false)
                                        }
                                    }
                                    Label {
                                        Layout.preferredWidth: 120
                                        text: tabRow.modelData.name
                                        color: root.theme.secondaryText
                                        font.pointSize: Typography.label
                                        elide: Text.ElideRight
                                    }
                                    Md3TextField {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 34
                                        theme: root.theme
                                        text: tabRow.modelData.label
                                        onTextEdited: {
                                            tabRow.modelData.label = text
                                            root.updateValues(false)
                                        }
                                    }
                                    CompactIconButton {
                                        theme: root.theme
                                        iconName: "arrow-up"
                                        enabled: tabRow.index > 0
                                        toolTip: qsTr("Move up")
                                        onClicked: root.moveTab(tabRow.index, -1)
                                    }
                                    CompactIconButton {
                                        theme: root.theme
                                        iconName: "arrow-down"
                                        enabled: tabRow.index
                                            < root.currentTabs().length - 1
                                        toolTip: qsTr("Move down")
                                        onClicked: root.moveTab(tabRow.index, 1)
                                    }
                                }
                            }
                        }

                        Md3Button {
                            theme: root.theme
                            visible: perProjectMode.checked
                            text: qsTr("Apply current to all projects")
                            icon.name: "content-copy"
                            onClicked: root.copyCurrentTabsToAll()
                        }
                    }
                }

                ConfigurationSection {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    title: qsTr("Process tabs")
                    description: root.currentProject()
                        ? "Search types visible for " + root.currentProject().title
                        : qsTr("No project is available.")
                    iconName: "account-tree"

                    Md3CheckBox {
                        id: processFilterEnabled
                        Layout.fillWidth: true
                        theme: root.theme
                        text: qsTr("Filter process tabs for this project")
                        onToggled: root.updateValues(false)
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 6
                        enabled: processFilterEnabled.checked

                        Repeater {
                            model: root.currentProject()
                                ? root.currentProject().searchTypes : []
                            delegate: Md3CheckBox {
                                required property var modelData
                                theme: root.theme
                                text: modelData.title
                                checked: modelData.enabled
                                onToggled: {
                                    modelData.enabled = checked
                                    root.updateValues(false)
                                }
                            }
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: root.currentProject()
                            && root.currentProject().searchTypes.length === 0
                        text: qsTr("Search types have not been loaded for this project yet.")
                        color: root.theme.secondaryText
                        font.pointSize: Typography.label
                        wrapMode: Text.WordWrap
                    }
                }

                ConfigurationSection {
                    Layout.fillWidth: true
                    theme: root.theme
                    title: qsTr("SObject tabs")
                    description: qsTr("Shared layout behaviour for opened tabs.")
                    iconName: "tab"

                    Md3CheckBox {
                        id: lastViewForAllTabs
                        Layout.fillWidth: true
                        theme: root.theme
                        text: qsTr("Apply last opened tab layout to all tabs")
                        onToggled: root.updateValues(false)
                    }
                }
            }
        }
    }
}
