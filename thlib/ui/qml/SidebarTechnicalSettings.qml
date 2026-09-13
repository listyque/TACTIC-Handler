import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ConfigurationSection {
    id: root

    required property var controller
    readonly property var entry: controller.selectedEntry

    function optionIndex(options, value) {
        for (let index = 0; index < options.length; ++index) {
            if (String(options[index].value || "") === String(value || ""))
                return index
        }
        return 0
    }

    title: qsTr("Technical settings")
    description: qsTr("TACTIC identifiers and widget options. For normal setup, use Item; change these only when the server configuration requires it.")

    Controls.SettingsRow {
        theme: root.theme
        title: qsTr("Item type")
        description: qsTr("A link opens a search, a section groups links, and a separator divides the list.")
        Controls.ComboBox {
            objectName: "sidebarItemType"
            Layout.preferredWidth: 230
            theme: root.theme
            textRole: "label"; valueRole: "value"; iconRole: "icon"
            model: [
                {value: "link", label: qsTr("Link"), icon: "sidebar-link"},
                {value: "section", label: qsTr("Section"), icon: "sidebar-section"},
                {value: "separator", label: qsTr("Separator"), icon: "sidebar-separator"}
            ]
            currentIndex: root.optionIndex(model, root.entry.entryType)
            onActivated: root.controller.update_selected("entryType", currentValue)
        }
    }
    Controls.SettingsRow {
        theme: root.theme
        title: qsTr("Internal name")
        description: qsTr("The stable identifier for this sidebar item and its quick-filter defaults. Change the title instead if you only want a different label.")
        Controls.TextField {
            objectName: "sidebarNameField"
            Layout.preferredWidth: 230
            theme: root.theme
            text: String(root.entry.name || "")
            onEditingFinished: root.controller.update_selected("name", text)
        }
    }
    Controls.SettingsRow {
        visible: root.entry.entryType === "section"
        theme: root.theme
        title: qsTr("Child view")
        description: qsTr("The SideBarWdg view containing this section's links.")
        Controls.TextField {
            Layout.preferredWidth: 230
            theme: root.theme
            text: String(root.entry.targetView || "")
            onEditingFinished: root.controller.update_selected("targetView", text)
        }
    }
    Controls.SettingsRow {
        visible: root.entry.entryType !== "separator"
        theme: root.theme
        title: qsTr("Icon name")
        description: qsTr("The server icon identifier. You can also choose an icon on the Item page.")
        Controls.TextField {
            Layout.preferredWidth: 230
            theme: root.theme
            text: String(root.entry.icon || "")
            onEditingFinished: root.controller.update_selected("icon", text)
        }
    }
    Controls.SettingsRow {
        visible: root.entry.entryType === "link"
        theme: root.theme
        title: qsTr("Widget Type")
        description: qsTr("The TACTIC web widget used by this link. Handler result presentation is set on the Item page.")
        Controls.ComboBox {
            Layout.preferredWidth: 230
            theme: root.theme
            textRole: "label"; valueRole: "value"; iconRole: "icon"
            model: root.controller.widgetTypeOptions
            currentIndex: root.optionIndex(model, root.entry.widgetType)
            onActivated: root.controller.update_selected("widgetType", currentValue)
        }
    }
    Controls.SettingsRow {
        visible: root.entry.entryType === "link" && root.entry.widgetType === "__class__"
        theme: root.theme
        title: qsTr("Class Path")
        description: qsTr("The Python class registered for this TACTIC widget.")
        Controls.TextField {
            Layout.preferredWidth: 230
            theme: root.theme
            text: String(root.entry.displayClassName || "")
            onEditingFinished: root.controller.update_selected("displayClassName", text)
        }
    }
    Controls.SettingsRow {
        visible: root.entry.entryType === "link" && [
            "custom_layout", "edit_layout", "tile_layout", "fast_layout"
        ].indexOf(String(root.entry.widgetType)) >= 0
        theme: root.theme
        title: qsTr("View")
        description: qsTr("The server view used to render the selected TACTIC widget.")
        showDivider: false
        Controls.TextField {
            Layout.preferredWidth: 230
            theme: root.theme
            text: String(root.entry.displayView || "")
            onEditingFinished: root.controller.update_selected("displayView", text)
        }
    }
}
