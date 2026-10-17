pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame/features/table/menus.ui.mjs" as TableMenus

Item {
    id: root

    required property var theme
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    required property var columnsController

    signal configureRequested
    signal closeRequested

    width: 0
    height: 0

    function actions() {
        return TableMenus.viewActions(columnsController.tableViews || [], !columnsController.busy, root.language);
    }

    function openBelow(anchor) {
        presetMenu.actions = actions();
        presetMenu.openBelow(anchor);
    }

    ActionMenu {
        id: presetMenu
        objectName: "tableViewPresetsMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 280
        onTriggered: command => {
            if (command === "save_as") {
                viewName.clear();
                saveDialog.open();
                viewName.forceActiveFocus();
            } else if (command === "configure") {
                root.configureRequested();
                root.closeRequested();
            } else if (command.indexOf("select:") === 0) {
                root.columnsController.select_table_view(Number(command.split(":")[1]));
                root.closeRequested();
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
        onAccepted: root.columnsController.save_table_view_as(viewName.text)
        contentItem: Controls.TextField {
            id: viewName
            width: 342
            theme: root.theme
            placeholderText: qsTr("View name")
            Accessible.name: qsTr("View name")
            Keys.onReturnPressed: {
                if (text.trim().length > 0)
                    saveDialog.accept();
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
