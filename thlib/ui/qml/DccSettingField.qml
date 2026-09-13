pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "controls" as Controls

Controls.SettingsRow {
    id: root

    required property var field
    property var value
    objectName: "dccSetting_" + String(field.key || "")

    signal valueEdited(var value)

    title: qsTr(String(field.title || field.key || ""))
    description: qsTr(String(field.description || ""))

    Loader {
        sourceComponent: root.field.type === "boolean" ? booleanEditor
            : root.field.type === "choice" ? choiceEditor
            : root.field.type === "integer" ? integerEditor
            : textEditor
    }

    Component {
        id: booleanEditor

        Controls.Switch {
            objectName: "dccSettingControl_" + String(root.field.key || "")
            theme: root.theme
            text: ""
            checked: Boolean(root.value)
            onToggled: root.valueEdited(checked)
        }
    }

    Component {
        id: choiceEditor

        Controls.ComboBox {
            objectName: "dccSettingControl_" + String(root.field.key || "")
            theme: root.theme
            Layout.preferredWidth: 220
            model: root.field.choices || []
            textRole: "label"
            currentIndex: {
                const choices = root.field.choices || []
                for (let index = 0; index < choices.length; ++index) {
                    if (choices[index].value === root.value)
                        return index
                }
                return 0
            }
            onActivated: {
                const choice = (root.field.choices || [])[currentIndex]
                if (choice)
                    root.valueEdited(choice.value)
            }
        }
    }

    Component {
        id: integerEditor

        Controls.SpinBox {
            objectName: "dccSettingControl_" + String(root.field.key || "")
            theme: root.theme
            from: Number(root.field.minimum ?? 0)
            to: Number(root.field.maximum ?? 999999)
            value: Number(root.value ?? root.field.default ?? 0)
            onValueModified: root.valueEdited(value)
        }
    }

    Component {
        id: textEditor

        Controls.TextField {
            objectName: "dccSettingControl_" + String(root.field.key || "")
            theme: root.theme
            Layout.preferredWidth: 320
            Layout.preferredHeight: 40
            text: String(root.value ?? "")
            readOnly: Boolean(root.field.read_only)
            selectByMouse: true
            onEditingFinished: root.valueEdited(text)
        }
    }
}
