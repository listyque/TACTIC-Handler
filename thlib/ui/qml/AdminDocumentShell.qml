import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root
    required property var theme
    required property var controller
    property string title: ""
    property string description: ""
    property string iconName: "edit"
    property string selectionLabel: qsTr("Selected document")
    property bool allowCreate: false
    property bool createRequiresCleanDocument: true
    property string createText: qsTr("Create")
    property string createObjectName: "adminCreateDocument"
    property var createAction: null
    property bool allowReload: true
    property bool allowSave: true
    property string confirmationMessage: qsTr("These changes will be saved on the server and will affect other users of the project.")
    property string confirmationDetails: ""
    property bool showSelector: true
    property bool showDocumentChrome: true
    property alias editorContent: body.data
    spacing: 8

    function requestSave() {
        if (!root.visible || !root.enabled || !root.allowSave || !root.controller.canWrite
                || root.controller.busy || !root.controller.dirty || saveConfirmation.visible) return
        saveConfirmation.open()
    }

    AdminSaveBar {
        objectName: "adminDocumentToolbar"
        visible: root.showDocumentChrome
        Layout.fillWidth: true
        theme: root.theme
        busy: root.controller.busy
        dirty: root.controller.dirty
        canWrite: root.controller.canWrite
        saveEnabled: root.allowSave
        onDiscardRequested: root.controller.discard()
        onSaveRequested: root.requestSave()
        leadingActions: [
            Label {
                visible: root.showSelector
                text: root.selectionLabel
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
            },
            Controls.ComboBox {
                objectName: "adminDocumentSelector"
                Layout.preferredWidth: 220
                Layout.minimumWidth: 80
                theme: root.theme
                visible: root.showSelector
                model: root.controller.catalog
                textRole: "label"
                valueRole: "identity"
                translateDisplayText: false
                currentIndex: root.controller.catalog.findIndex(
                    row => row.identity === root.controller.identity)
                enabled: !root.controller.busy && !root.controller.dirty
                onActivated: root.controller.select(String(currentValue))
            },
            Controls.Button {
                objectName: root.createObjectName
                theme: root.theme
                text: root.createText
                icon.name: "add"
                visible: root.allowCreate
                enabled: (root.controller.canWrite || root.controller.metadata.canCreate === true)
                    && !root.controller.busy
                    && (!root.createRequiresCleanDocument || !root.controller.dirty)
                onClicked: {
                    if (root.createAction) root.createAction()
                    else root.controller.new_document()
                }
            },
            Controls.CompactIconButton {
                objectName: "adminReloadDocument"
                theme: root.theme
                iconName: "refresh"
                toolTip: qsTr("Reload from server")
                visible: root.allowReload
                enabled: !root.controller.busy && !root.controller.dirty
                onClicked: root.controller.reload()
            }
        ]
    }
    Label {
        objectName: "adminDocumentError"
        Layout.fillWidth: true
        text: root.controller.error
        color: root.theme.error
        wrapMode: Text.Wrap
        visible: text.length > 0
    }
    Item {
        id: body
        objectName: "adminDocumentBody"
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: 120
        enabled: !root.controller.busy
    }
    Controls.Dialog {
        id: saveConfirmation
        objectName: "adminSaveConfirmation"
        theme: root.theme
        modal: true
        // Popups render in the window overlay and are not managed by this layout.
        anchors.centerIn: parent // qmllint disable Quick.layout-positioning
        width: Math.min(480, root.width) // qmllint disable Quick.layout-positioning
        height: Math.min(implicitHeight, Math.max(200, root.height - 24)) // qmllint disable Quick.layout-positioning
        title: qsTr("Apply administrative changes?")
        standardButtons: Dialog.NoButton
        focus: true
        onOpened: {
            confirmationViewport.contentY = 0
            cancelSave.forceActiveFocus()
        }
        onAccepted: root.controller.save()
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                id: cancelSave
                objectName: "adminCancelSave"
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: saveConfirmation.reject()
            }
            Controls.Button {
                objectName: "adminConfirmSave"
                theme: root.theme
                text: qsTr("Save")
                icon.name: "save"
                highlighted: true
                onClicked: saveConfirmation.accept()
            }
        }
        contentItem: Flickable {
            id: confirmationViewport
            objectName: "adminConfirmationScroll"
            implicitHeight: confirmationText.implicitHeight
            contentHeight: confirmationText.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            clip: true
            Label {
                id: confirmationText
                objectName: "adminConfirmationText"
                width: Math.max(0, confirmationViewport.width - confirmationBar.reservedExtent - 4)
                text: root.confirmationMessage + (root.confirmationDetails ? "\n\n" + root.confirmationDetails : "")
                textFormat: Text.PlainText
                color: root.theme.primaryText
                wrapMode: Text.Wrap
            }
            ScrollBar.vertical: Controls.ScrollBar {
                id: confirmationBar
                objectName: "adminConfirmationScrollBar"
                theme: root.theme
                flickableTarget: confirmationViewport
            }
        }
    }
}
