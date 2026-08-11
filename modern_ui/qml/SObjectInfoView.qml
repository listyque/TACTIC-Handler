import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 7

        GridLayout {
            columns: 2
            Layout.fillWidth: true
            Label {
                text: qsTr("Selected sObject")
                color: root.theme.secondaryText
                font.pixelSize: 10
            }
            Label {
                text: workspaceState.selected_title
                color: root.theme.primaryText
                font.pixelSize: 10
            }
            Label {
                text: qsTr("Description")
                color: root.theme.secondaryText
                font.pixelSize: 10
            }
            Label {
                Layout.fillWidth: true
                text: workspaceState.description || qsTr("No description")
                color: workspaceState.description
                    ? root.theme.primaryText : root.theme.secondaryText
                font.pixelSize: 10
                elide: Text.ElideRight
            }
        }
        TabBar {
            id: infoTabs
            Layout.fillWidth: true
            Md3TabButton { theme: root.theme; text: qsTr("Tasks") }
            Md3TabButton { theme: root.theme; text: qsTr("Notes") }
            Md3TabButton { theme: root.theme; text: qsTr("Edit") }
        }
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: infoTabs.currentIndex
            ListView {
                model: taskModel
                delegate: Label {
                    required property string process
                    width: ListView.view ? ListView.view.width : 0
                    padding: 7
                    text: process
                    color: root.theme.primaryText
                    font.pixelSize: 10
                }
            }
            ListView {
                model: noteModel
                delegate: Label {
                    required property string body
                    width: ListView.view ? ListView.view.width : 0
                    padding: 7
                    text: body
                    color: root.theme.primaryText
                    font.pixelSize: 10
                    wrapMode: Text.WordWrap
                }
            }
            DescriptionEditor {
                theme: root.theme
                value: workspaceState.description
                targetTitle: workspaceState.descriptionTargetTitle
                targetKind: workspaceState.descriptionTargetKind
                editing: workspaceState.descriptionEditing
                pinned: workspaceState.descriptionPinned
                dirty: workspaceState.descriptionDirty
                saving: workspaceState.descriptionSaving
                canSave: workspaceState.descriptionCanSave
                editorEnabled: workspaceState.descriptionTargetTitle.length > 0
                errorText: workspaceState.descriptionError
                onEditRequested: workspaceState.begin_description_edit()
                onValueEdited: value => workspaceState.set_description(value)
                onSaveRequested: workspaceState.commit_description()
                onCancelRequested: workspaceState.cancel_description_edit()
                onPinRequested: workspaceState.freeze_description()
                onUnpinRequested: workspaceState.unfreeze_description()
            }
        }
    }
}
