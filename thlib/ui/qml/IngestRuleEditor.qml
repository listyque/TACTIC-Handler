import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    signal deleteRuleRequested()
    spacing: 8

    Label {
        text: qsTr("File selection")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        font.weight: Font.DemiBold
    }
    RowLayout {
        Layout.fillWidth: true
        Controls.TextField {
            theme: root.theme
            Layout.fillWidth: true
            placeholderText: qsTr("Include: .mov, /regex/")
            text: root.controller.options.filter || ""
            onTextEdited: root.controller.set_option("filter", text)
        }
        Controls.TextField {
            theme: root.theme
            Layout.fillWidth: true
            placeholderText: qsTr("Ignore: .tmp, .db")
            text: root.controller.options.ignore || ""
            onTextEdited: root.controller.set_option("ignore", text)
        }
    }
    Controls.CheckBox {
        theme: root.theme
        text: qsTr("Parse values from a path pattern")
        checked: !!root.controller.options.usePattern
        onToggled: root.controller.set_option("usePattern", checked)
    }
    Controls.TextField {
        theme: root.theme
        Layout.fillWidth: true
        enabled: !!root.controller.options.usePattern
        placeholderText: qsTr("{sobject.name}_{snapshot.context}.mov")
        text: root.controller.options.pattern || ""
        onTextEdited: root.controller.set_option("pattern", text)
    }

    Label {
        text: qsTr("Publish target")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        font.weight: Font.DemiBold
    }
    RowLayout {
        Layout.fillWidth: true
        Controls.TextField {
            theme: root.theme
            Layout.fillWidth: true
            placeholderText: qsTr("Process")
            text: root.controller.options.process || "publish"
            onTextEdited: root.controller.set_option("process", text)
        }
        Controls.TextField {
            theme: root.theme
            Layout.fillWidth: true
            placeholderText: qsTr("Context")
            text: root.controller.options.context || "publish"
            onTextEdited: root.controller.set_option("context", text)
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Controls.CheckBox {
            theme: root.theme
            text: qsTr("Update matching item")
            checked: root.controller.options.updateMode === "update"
            onToggled: root.controller.set_option(
                "updateMode", checked ? "update" : "insert")
        }
        Controls.CheckBox {
            theme: root.theme
            text: qsTr("Create preview when supported")
            checked: !!root.controller.options.createIcon
            onToggled: root.controller.set_option("createIcon", checked)
        }
    }

    Label {
        text: qsTr("Extra Search Object values (JSON)")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        font.weight: Font.DemiBold
    }
    Controls.TextArea {
        theme: root.theme
        Layout.fillWidth: true
        Layout.preferredHeight: 82
        text: root.controller.options.extraDataJson || "{}"
        onTextChanged: if (activeFocus)
            root.controller.set_option("extraDataJson", text)
    }

    Label {
        text: qsTr("TACTIC server scripts")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        font.weight: Font.DemiBold
    }
    Label {
        Layout.fillWidth: true
        text: qsTr("Scripts receive path, sobject, parent and snapshot. Return a truthy value to accept the file.")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.caption
        wrapMode: Text.WordWrap
    }
    RowLayout {
        Layout.fillWidth: true
        Controls.TextField {
            theme: root.theme
            Layout.fillWidth: true
            placeholderText: qsTr("Validation script path")
            text: root.controller.options.validationScript || ""
            onTextEdited: root.controller.set_option("validationScript", text)
        }
        Controls.Button {
            theme: root.theme
            compact: true
            text: qsTr("Open Script Editor")
            icon.name: "script-python"
            onClicked: windowModel.show_window("script_editor")
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Controls.TextField {
            theme: root.theme
            Layout.fillWidth: true
            placeholderText: qsTr("Process script path")
            text: root.controller.options.processScript || ""
            onTextEdited: root.controller.set_option("processScript", text)
        }
        Controls.Button {
            theme: root.theme
            compact: true
            text: qsTr("Open Script Editor")
            icon.name: "script-python"
            onClicked: windowModel.show_window("script_editor")
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: saveRuleRow.implicitHeight + 16
        color: root.theme.surfaceContainerLow
        radius: root.theme.itemRadius
        border.width: 1
        border.color: root.theme.outlineVariant
        RowLayout {
            id: saveRuleRow
            anchors.fill: parent
            anchors.margins: 8
            Controls.TextField {
                theme: root.theme
                Layout.fillWidth: true
                placeholderText: qsTr("Rule title")
                text: root.controller.options.title || ""
                onTextEdited: root.controller.set_option("title", text)
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Save rule")
                icon.name: "save"
                onClicked: root.controller.save_rule(
                    root.controller.options.title || "")
            }
            Controls.Button {
                theme: root.theme
                compact: true
                text: qsTr("Delete rule")
                icon.name: "delete"
                destructive: true
                enabled: root.controller.canDeleteRule
                onClicked: root.deleteRuleRequested()
            }
        }
    }
}
