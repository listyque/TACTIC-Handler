pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var columnsController

    signal configureRequested()
    signal closeRequested()

    width: 0
    height: 0

    function actions() {
        const views = columnsController.tableViews || []
        const values = [{"title": "Table views", "header": true}]
        for (let index = 0; index < views.length; ++index) {
            const view = views[index]
            values.push({
                "title": String(view.view || "") === "table"
                    ? qsTr("Default table")
                    : String(view.title || view.view || ""),
                "icon": "table-view",
                "command": "select:" + index,
                "checked": Boolean(view.current),
                "translate": false
            })
        }
        values.push({"separator": true})
        values.push({
            "title": "Configure columns",
            "icon": "view-column",
            "command": "configure",
            "enabled": !columnsController.busy
        })
        values.push({
            "title": "Save current as new view…",
            "icon": "add",
            "command": "save_as",
            "enabled": !columnsController.busy
        })
        return values
    }

    function openBelow(anchor) {
        presetMenu.actions = actions()
        presetMenu.openBelow(anchor)
    }

    ActionMenu {
        id: presetMenu
        objectName: "tableViewPresetsMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 280
        onTriggered: command => {
            if (command === "save_as") {
                viewName.clear()
                saveDialog.open()
                viewName.forceActiveFocus()
            } else if (command === "configure") {
                root.configureRequested()
                root.closeRequested()
            } else if (command.indexOf("select:") === 0) {
                root.columnsController.select_table_view(
                    Number(command.split(":")[1])
                )
                root.closeRequested()
            }
        }
    }

    Controls.Dialog {
        id: saveDialog
        objectName: "saveTableViewDialog"
        parent: Overlay.overlay
        theme: root.theme
        anchors.centerIn: parent
        width: 390
        modal: true
        title: qsTr("Save table view")
        onClosed: root.closeRequested()
        onAccepted:
            root.columnsController.save_table_view_as(viewName.text)
        contentItem: Controls.TextField {
            id: viewName
            width: 342
            theme: root.theme
            placeholderText: qsTr("View name")
            Accessible.name: qsTr("View name")
            Keys.onReturnPressed: {
                if (text.trim().length > 0)
                    saveDialog.accept()
            }
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Save")
                highlighted: true
                enabled: viewName.text.trim().length > 0
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }
}
