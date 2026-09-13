import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    required property var securityModel
    readonly property var entry: controller.selectedEntry
    readonly property bool isLink: entry.entryType === "link"
    readonly property bool isSection: entry.entryType === "section"
    property string page: "item"

    function optionIndex(options, value) {
        for (let index = 0; index < options.length; ++index) {
            if (String(options[index].value || "") === String(value || ""))
                return index
        }
        return 0
    }

    spacing: 12

    RowLayout {
        Layout.fillWidth: true
        Label {
            Layout.fillWidth: true
            text: String(root.entry.title || qsTr("Select a sidebar item"))
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Controls.CompactIconButton {
            theme: root.theme
            iconName: "arrow_upward"
            toolTip: qsTr("Move up")
            enabled: root.controller.selectedRow >= 0 && Boolean(root.entry.included)
            onClicked: root.controller.move_selected(-1)
        }
        Controls.CompactIconButton {
            theme: root.theme
            iconName: "arrow_downward"
            toolTip: qsTr("Move down")
            enabled: root.controller.selectedRow >= 0 && Boolean(root.entry.included)
            onClicked: root.controller.move_selected(1)
        }
        Controls.CompactIconButton {
            theme: root.theme
            iconName: "delete"
            toolTip: qsTr("Delete item")
            enabled: root.controller.selectedRow >= 0
            onClicked: root.controller.delete_selected()
        }
    }

    Controls.SegmentedButton {
        Layout.fillWidth: true
        theme: root.theme
        visible: root.controller.selectedRow >= 0
        currentValue: root.page
        model: [
            {value: "item", label: "Item", icon: "edit"},
            {value: "access", label: "Access", icon: "groups"},
            {value: "technical", label: "Technical", icon: "code"}
        ]
        onActivated: value => {
            root.forceActiveFocus()
            root.page = value
        }
    }

    Controls.EmptyState {
        Layout.fillWidth: true
        theme: root.theme
        visible: root.controller.selectedRow < 0
        iconName: "sidebar-link"
        title: qsTr("Select an item in the preview to edit it, or add a new link or section.")
    }

    Flickable {
        id: viewport
        objectName: "sidebarSettingsViewport"
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: root.controller.selectedRow >= 0
        clip: true
        contentWidth: width
        contentHeight: sections.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        Connections {
            target: root
            function onPageChanged() { viewport.contentY = 0 }
        }

        ColumnLayout {
            id: sections
            width: Math.max(0, viewport.width - settingsScrollBar.reservedExtent - 4)
            spacing: 16

            ConfigurationSection {
                Layout.fillWidth: true
                visible: root.page === "item"
                theme: root.theme
                title: qsTr("Appearance")
                description: qsTr("How this item appears in project navigation. Its color comes from the Search Type; selection follows your theme.")

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Title")
                    description: qsTr("A short, recognizable name in the sidebar.")
                    Controls.TextField {
                        objectName: "sidebarTitleField"
                        Layout.preferredWidth: 230
                        theme: root.theme
                        text: String(root.entry.title || "")
                        onTextEdited: root.controller.update_selected("title", text)
                    }
                }
                Controls.SettingsRow {
                    visible: root.entry.entryType !== "separator"
                    theme: root.theme
                    title: qsTr("Icon")
                    description: qsTr("Click the icon to choose from the searchable library.")
                    IconPickerButton {
                        theme: root.theme
                        iconName: String(root.entry.glyph || "")
                        tacticCompatibleOnly: true
                        onIconSelected: name => root.controller.update_selected("icon", name)
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Visible in navigation")
                    description: qsTr("Hide this item without deleting its settings.")
                    showDivider: false
                    Controls.CheckBox {
                        theme: root.theme
                        checked: Boolean(root.entry.isVisible)
                        Accessible.name: qsTr("Visible in navigation")
                        onToggled: root.controller.update_selected("isVisible", checked)
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                visible: root.page === "item" && root.isLink
                theme: root.theme
                title: qsTr("Search and quick filters")
                description: qsTr("The saved search defines the starting query. Quick filters refine it in the same search tab and use this item's own defaults.")

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Search Type")
                    description: qsTr("Which project objects this item opens.")
                    Controls.ComboBox {
                        Layout.preferredWidth: 230
                        theme: root.theme
                        textRole: "label"; valueRole: "value"
                        translateDisplayText: false
                        model: root.controller.searchTypes
                        currentIndex: root.optionIndex(model, root.entry.searchType)
                        onActivated: root.controller.update_selected("searchType", currentValue)
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Predefined search")
                    description: qsTr("Choose a saved query or leave the list unfiltered. Configure search opens the Search Type's shared library and results.")
                    Controls.ComboBox {
                        objectName: "sidebarSearchPreset"
                        Layout.preferredWidth: 230
                        theme: root.theme
                        textRole: "label"; valueRole: "value"
                        translateDisplayText: false
                        model: root.controller.searchPresetOptions
                        enabled: !root.controller.searchPresetsBusy && Boolean(root.entry.searchType)
                        currentIndex: root.optionIndex(model, root.entry.searchView)
                        onActivated: root.controller.update_selected("searchView", currentValue)
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Default item view")
                    description: qsTr("The initial presentation when this search tab is opened.")
                    Controls.ComboBox {
                        Layout.preferredWidth: 230
                        theme: root.theme
                        textRole: "label"; valueRole: "value"; iconRole: "icon"
                        model: root.controller.resultViewOptions
                        currentIndex: root.optionIndex(model, root.entry.resultViewMode)
                        onActivated: root.controller.update_selected("resultViewMode", currentValue)
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Workspace layout")
                    description: qsTr("Apply a saved dock arrangement when this sidebar item opens.")
                    Controls.ComboBox {
                        objectName: "sidebarLayoutPreset"
                        Layout.preferredWidth: 230
                        theme: root.theme
                        textRole: "label"
                        valueRole: "value"
                        translateDisplayText: false
                        model: root.controller.layoutPresets
                            ? root.controller.layoutPresets.options : []
                        enabled: root.controller.layoutPresets
                            && !root.controller.layoutPresets.busy
                        currentIndex: root.optionIndex(
                            model, root.entry.layoutPreset
                        )
                        onActivated: root.controller.update_selected(
                            "layoutPreset", currentValue
                        )
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Script shelf")
                    description: qsTr("Show this shared shelf when the sidebar tab is active.")
                    showDivider: false
                    Controls.ComboBox {
                        objectName: "sidebarScriptShelf"
                        Layout.preferredWidth: 230
                        theme: root.theme
                        textRole: "label"
                        valueRole: "value"
                        translateDisplayText: false
                        model: root.controller.scriptShelf
                            ? root.controller.scriptShelf.assignmentOptions : []
                        enabled: root.controller.scriptShelf
                            && !root.controller.scriptShelf.busy
                        currentIndex: root.optionIndex(
                            model, root.entry.scriptShelf
                        )
                        onActivated: root.controller.update_selected(
                            "scriptShelf", currentValue
                        )
                    }
                }
                Controls.Button {
                    objectName: "sidebarSearchSetupButton"
                    theme: root.theme
                    text: qsTr("Configure search")
                    icon.name: "edit"
                    enabled: root.controller.canOpenSearch
                    onClicked: root.controller.open_search()
                }
                Label {
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    text: root.controller.dirty
                        ? qsTr("Save sidebar changes before opening this search and its quick filters.")
                        : qsTr("Opens a modal search preview with saved searches, results and quick filters. Save keeps your tab's setup; Save as defaults on server publishes its quick filters for everyone.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                visible: root.page === "access"
                Layout.preferredHeight: viewport.height
                fillContentHeight: true
                theme: root.theme
                title: qsTr("Who can see this item")
                description: qsTr("Only the selected login groups can see this navigation item. Changes are saved with the sidebar.")
                Controls.Button {
                    objectName: "manageSidebarGroups"
                    visible: root.controller.canManageGroups
                    Layout.bottomMargin: 8
                    theme: root.theme
                    text: qsTr("Manage groups and members")
                    icon.name: "groups"
                    onClicked: root.controller.open_group_manager()
                }
                Label {
                    visible: root.controller.securityGroupCount === 0
                    Layout.fillWidth: true
                    text: qsTr("No login groups available")
                    color: root.theme.secondaryText
                    wrapMode: Text.WordWrap
                }
                ListView {
                    id: groups
                    objectName: "sidebarAccessGroups"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 120
                    clip: true
                    model: root.securityModel
                    boundsBehavior: Flickable.StopAtBounds
                    delegate: Controls.CheckBox {
                        required property string code
                        required property string label
                        required property bool allowed
                        width: Math.max(0, groups.width - groupScrollBar.reservedExtent - 4)
                        theme: root.theme
                        text: label
                        checked: allowed
                        onToggled: root.controller.set_group_allowed(code, checked)
                    }
                    ScrollBar.vertical: Controls.ScrollBar {
                        id: groupScrollBar
                        theme: root.theme
                        flickableTarget: groups
                    }
                }
            }

            SidebarTechnicalSettings {
                Layout.fillWidth: true
                visible: root.page === "technical"
                theme: root.theme
                controller: root.controller
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: settingsScrollBar
            theme: root.theme
            flickableTarget: viewport
        }
    }
}
