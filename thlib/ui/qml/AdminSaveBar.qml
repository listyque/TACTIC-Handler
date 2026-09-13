import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property bool busy: false
    property bool dirty: false
    property bool canWrite: false
    property bool saveEnabled: true
    property string saveObjectName: "adminSaveDocument"
    property alias leadingActions: leadingActionRow.data
    readonly property bool compact: width < 480
    signal saveRequested()
    signal discardRequested()

    implicitHeight: theme.controlHeight

    RowLayout {
        id: layout
        anchors.fill: parent
        spacing: 8
        RowLayout {
            id: leadingActionRow
            spacing: 6
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            visible: root.busy || root.dirty || !root.canWrite
            spacing: 8
            Controls.BusyIndicator {
                uiTheme: root.theme
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                running: root.busy
                visible: running
            }
            Controls.MaterialIcon {
                visible: !root.busy
                name: root.dirty ? "edit" : root.canWrite ? "cloud" : "lock"
                size: 17
                color: root.dirty ? root.theme.action : root.theme.secondaryText
            }
            Label {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                text: root.busy ? qsTr("Working on the server…")
                    : root.dirty ? qsTr("Unsaved changes")
                    : qsTr("Read-only")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                elide: Text.ElideRight
            }
        }
        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8
            Controls.Button {
                objectName: "adminDiscardDocument"
                theme: root.theme
                text: qsTr("Discard")
                compact: root.compact
                enabled: root.dirty && !root.busy
                onClicked: root.discardRequested()
            }
            Controls.Button {
                objectName: root.saveObjectName
                theme: root.theme
                text: qsTr("Save to server")
                icon.name: "save"
                compact: root.compact
                highlighted: true
                enabled: root.canWrite && root.dirty && !root.busy && root.saveEnabled
                onClicked: root.saveRequested()
            }
        }
    }
}
