import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "controls"

Item {
    id: root

    required property var theme
    property string value: ""
    property string targetTitle: ""
    property string targetKind: ""
    property string errorText: ""
    property bool managed: true
    property bool editing: false
    property bool pinned: false
    property bool dirty: false
    property bool saving: false
    property bool canSave: true
    property bool editorEnabled: true
    property bool compact: false
    property bool showTargetHeader: true
    property bool internalTextChange: false

    signal editRequested()
    signal valueEdited(string value)
    signal saveRequested()
    signal cancelRequested()
    signal pinRequested()
    signal unpinRequested()
    signal editingFinished(string value)

    function syncText() {
        if (editor.text === root.value)
            return
        root.internalTextChange = true
        editor.text = root.value
        root.internalTextChange = false
    }

    onValueChanged: syncText()
    Component.onCompleted: syncText()

    Keys.onEscapePressed: event => {
        if (root.managed && root.editing && !root.saving) {
            root.cancelRequested()
            event.accepted = true
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: root.theme.surfaceRadius
        color: root.theme.surfaceContainerLow
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.compact ? 6 : 8
        spacing: root.compact ? 4 : 6

        RowLayout {
            Layout.fillWidth: true
            visible: root.managed && root.showTargetHeader
            spacing: 6

            MaterialIcon {
                name: root.pinned ? "push-pin"
                    : root.targetKind === "snapshot" ? "snapshot"
                    : root.targetKind === "process" ? "settings_suggest"
                    : "description"
                size: 15
                color: root.pinned ? root.theme.tertiary
                    : root.editing ? root.theme.action
                    : root.theme.secondaryText
            }
            Label {
                Layout.fillWidth: true
                text: root.targetTitle.length
                    ? root.targetTitle : qsTr("No sObject selected")
                color: root.editorEnabled
                    ? root.theme.primaryText : root.theme.disabledText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.label
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                visible: root.pinned || root.editing || root.saving
                text: root.saving ? qsTr("Saving…")
                    : root.pinned ? qsTr("Used for check-in")
                    : root.dirty ? qsTr("Unsaved") : qsTr("Editing")
                color: root.pinned ? root.theme.tertiary
                    : root.saving ? root.theme.secondaryText
                    : root.theme.action
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
                font.weight: Font.DemiBold
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Md3TextArea {
                id: editor
                theme: root.theme
                anchors.fill: parent
                enabled: root.editorEnabled || root.pinned
                readOnly: root.managed && !root.editing && !root.pinned
                placeholderText: root.editorEnabled
                    ? qsTr("Description")
                    : qsTr("Select an sObject, process or snapshot")
                errorState: root.errorText.length > 0
                emphasizedOutline: root.managed && (root.editing || root.pinned)
                activeOutlineColor: root.pinned
                    ? root.theme.tertiary : root.theme.action
                bottomPadding: root.managed ? 38 : (root.compact ? 8 : 10)
                font.pixelSize: root.compact ? 10 : 11
                onTextChanged: {
                    if (!root.internalTextChange && activeFocus)
                        root.valueEdited(text)
                }
                onActiveFocusChanged: {
                    if (!activeFocus && !root.managed)
                        root.editingFinished(text)
                }
            }

            Label {
                anchors.left: parent.left
                anchors.right: editorActions.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: 12
                anchors.rightMargin: 6
                anchors.bottomMargin: 9
                visible: root.managed && root.errorText.length > 0
                text: root.errorText
                color: root.theme.error
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
                elide: Text.ElideRight
                z: 2
            }

            Row {
                id: editorActions
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.rightMargin: 7
                anchors.bottomMargin: 5
                visible: root.managed
                spacing: 2
                z: 3

                CompactIconButton {
                    theme: root.theme
                    visible: !root.editing && !root.pinned
                    enabled: root.editorEnabled && !root.saving
                    iconName: "edit"
                    iconColor: root.theme.primaryText
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Edit description")
                    round: true
                    onClicked: {
                        root.editRequested()
                        editor.forceActiveFocus()
                    }
                }
                CompactIconButton {
                    theme: root.theme
                    visible: root.editing
                    enabled: !root.saving
                    iconName: "close"
                    iconColor: root.theme.secondaryText
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Discard changes")
                    round: true
                    onClicked: root.cancelRequested()
                }
                CompactIconButton {
                    theme: root.theme
                    visible: root.editing
                    enabled: root.canSave && root.dirty && !root.saving
                    iconName: "save"
                    iconColor: root.theme.green
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: root.canSave
                        ? qsTr("Save description")
                        : qsTr("This item has no description field")
                    round: true
                    onClicked: root.saveRequested()
                }
                CompactIconButton {
                    theme: root.theme
                    visible: root.editing
                    enabled: !root.saving
                    iconName: "push-pin"
                    iconColor: root.theme.tertiary
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Use this text for check-in")
                    round: true
                    onClicked: root.pinRequested()
                }
                CompactIconButton {
                    theme: root.theme
                    visible: root.pinned
                    enabled: !root.saving
                    iconName: "unlock-alt"
                    iconColor: root.theme.tertiary
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Stop using this text for check-in")
                    round: true
                    onClicked: root.unpinRequested()
                }
            }
        }
    }
}
