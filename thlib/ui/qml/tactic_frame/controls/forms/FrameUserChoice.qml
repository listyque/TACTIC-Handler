import QtQuick
import "../../.." as TH

TH.UserComboBox {
    id: control
    required property var node
    signal event(var action)
    readonly property var choices: {
        const rows = node.options || [];
        return rows.some(row => row.value === "") ? rows : [
            {
                value: "",
                label: qsTr("Not assigned")
            },
            ...rows];
    }
    objectName: node.id
    model: choices
    userModel: profiles
    textRole: "label"
    valueRole: "value"
    currentIndex: choices.findIndex(row => row.value === node.value)
    actionField: !!node.actionField
    Accessible.name: node.label || ""
    onActivated: if (node.action)
        control.event(Object.assign({}, node.action, {
            value: currentValue
        }))
    QtObject {
        id: profiles
        signal contentReplaced
        function lookup(role, value) {
            return control.choices.find(row => (row[role] === undefined && role === "login" ? row.value : row[role]) === value) || ({});
        }
    }
    onChoicesChanged: if (profiles)
        profiles.contentReplaced()
}
