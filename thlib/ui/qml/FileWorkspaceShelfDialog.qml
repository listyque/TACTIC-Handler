import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id:root
    objectName:"workspaceShelfDialog"
    required property var controller
    property string operation:"compare_shelf"
    property var shelf:({})
    title:operation==="update_shelf" ? qsTr("Replace selected files in shelf") : qsTr("Compare pending with shelf")
    parent: Overlay.overlay
    modal: true
    draggable: true
    closePolicy: Popup.CloseOnEscape
    width: Math.min(560,parent ? parent.width-24 : 560)
    onAboutToShow: { x=Qt.binding(()=>Math.max(0,(parent.width-width)/2)); y=Qt.binding(()=>Math.max(0,(parent.height-height)/2)) }
    footer: Controls.DialogActions {
        theme:root.theme
        Controls.Button {theme:root.theme;text:qsTr("Cancel");onClicked:root.reject()}
        Controls.Button {
            objectName:"workspaceTargetAccept"
            theme:root.theme
            text:qsTr("Continue")
            icon.name:"check"
            highlighted:true
            enabled:!root.controller.busy && Boolean(root.shelf.code)
            onClicked:root.accept()
        }
    }
    signal chosen(var values)
    contentItem:ColumnLayout {
        Controls.ComboBox {
            theme:root.theme;Layout.fillWidth:true;Accessible.name:qsTr("Shelved changelist")
            model:(root.controller.view_data.shelves || []).filter(row=>root.operation!=="update_shelf" || row.owner===root.controller.current_user)
            textRole:"label";valueRole:"code";translateDisplayText:false
            currentIndex:model.findIndex(row=>row.code===root.shelf.code)
            onActivated:root.shelf=model[currentIndex]
        }
        Label {Layout.fillWidth:true;text:qsTr("Select a permitted shelf in the same stream. Replacing it preserves its previous contents.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
        Controls.Button {theme:root.theme;icon.name:"chevron-right";text:qsTr("Next shelves");visible:Boolean(root.controller.view_data.shelves_after);enabled:!root.controller.busy;onClicked:root.controller.action("shelf_targets_more",{})}
    }
    onAccepted:if(shelf.code)chosen({shelf:shelf.code,shelf_revision:String(shelf.edit_revision)})
}
