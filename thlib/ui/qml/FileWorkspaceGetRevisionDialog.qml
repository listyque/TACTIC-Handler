import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id: root
    objectName: "workspaceGetRevisionDialog"
    required property var controller
    property string scope: "workspace"
    property string target: ""
    property string selector: ""
    property string value: ""
    property bool force: false
    property var request: ({})
    readonly property bool valid: selector === "" || (selector === "at_date" ? value.trim().length > 0 : /^[0-9]+$/.test(value) && Number(value) >= (selector === "revision" ? 0 : 1))
    title: qsTr("Get Revision")
    modal: true
    width: Math.min(480, parent ? parent.width - 24 : 480)
    parent: Overlay.overlay
    anchors.centerIn: parent
    footer: RowLayout {
        spacing: 8
        Item { Layout.fillWidth: true }
        Controls.Button { Layout.bottomMargin: 12; theme: root.theme; text: qsTr("Cancel"); onClicked: root.reject() }
        Controls.Button { Layout.rightMargin: root.rightPadding; Layout.bottomMargin: 12; theme: root.theme; text: qsTr("Get"); icon.name: "cloud-download"; enabled: root.valid; onClicked: root.accept() }
    }
    contentItem: ColumnLayout {
        spacing: 12
        Label { Layout.fillWidth: true; text: root.target; wrapMode: Text.Wrap; color: root.theme.primaryText }
        Controls.ComboBox {
            objectName: "workspaceRevisionSelector"
            theme: root.theme; Layout.fillWidth: true
            Accessible.name: qsTr("Revision selector")
            model: [{text:qsTr("Latest"),key:""}, {text:qsTr("File revision (each file)"),key:"file_revision"}, {text:qsTr("Submitted changelist"),key:"changelist"}, {text:qsTr("As of date / time"),key:"at_date"}, {text:qsTr("Stream revision"),key:"revision"}]
            textRole: "text"; valueRole: "key"; translateDisplayText: false
            currentIndex: model.findIndex(row => row.key === root.selector)
            onActivated: { root.selector = currentValue; root.value = "" }
        }
        Controls.TextField {
            objectName: "workspaceRevisionValue"
            theme: root.theme; Layout.fillWidth: true; visible: root.selector !== ""
            Accessible.name: qsTr("Revision number or date")
            placeholderText: root.selector === "at_date" ? qsTr("YYYY-MM-DD or ISO date / time") : qsTr("Number")
            text: root.value; onTextEdited: root.value = text
        }
        Label {
            Layout.fillWidth: true; wrapMode: Text.Wrap; color: root.theme.secondaryText
            text: root.selector === "at_date" ? qsTr("Without a timezone, UTC is used. A date includes the whole UTC day.") : root.selector === "file_revision" ? qsTr("Files without this revision are left unchanged and reported in the Log.") : qsTr("Changelist and stream revision select the complete submitted state of the selected stream.")
        }
        Controls.CheckBox {
            objectName: "workspaceRevisionForce"
            theme: root.theme; text: qsTr("Force overwrite local files")
            checked: root.force; onToggled: root.force = checked
        }
        Label {
            Layout.fillWidth: true; visible: root.force; wrapMode: Text.Wrap; color: root.theme.error
            text: qsTr("Force replaces modified files and removes files absent from the selected state. Preserve your local changes first.")
        }
    }
    onAccepted: {
        const values = Object.assign({}, request, {scope:scope, force:force})
        if (selector !== "") values[selector] = value.trim()
        controller.action("get_revision", values)
    }
}
