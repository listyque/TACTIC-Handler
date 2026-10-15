import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "FileWorkspacePresentation.js" as Presentation

Item {
    id:root
    required property var theme
    required property var row
    property bool selected:false
    property bool focused:false
    onFocusedChanged:if(focused)forceActiveFocus()
    property bool narrow:false
    property string localLabel:""
    property string serverLabel:""
    property string checkoutLabel:""
    property var checkoutHolders:[]
    property string currentUser:""
    property var columns:[]
    property var dragData:({})
    property int leftPadding:0
    signal selectedChangedByUser(bool checked)
    signal selectedByUser(int modifiers)
    signal activated()
    signal menuRequested(var source, real x, real y)
    signal dragRequested()
    readonly property var badges:Presentation.badges(row).concat(checkoutHolders.map(holder=>({label:holder.owner===currentUser ? (holder.mode==="exclusive" ? "Exclusive checkout by you" : "Checked out by you") : (holder.mode==="exclusive" ? "Exclusive checkout by another user" : "Checked out by another user"),icon:holder.mode==="exclusive" ? "lock" : "edit",tone:holder.owner===currentUser ? "action" : "other"})))
    implicitHeight:34
    activeFocusOnTab:true
    Accessible.role:Accessible.ListItem
    Accessible.name:row.path
    Accessible.description:localLabel+"; "+serverLabel+"; "+checkoutLabel
    Accessible.selected:selected
    Accessible.onPressAction:root.selectedByUser(0)
    Drag.active:drag.active
    Drag.dragType:Drag.Automatic
    Drag.supportedActions:Qt.CopyAction | Qt.MoveAction
    Drag.mimeData:root.dragData
    Drag.hotSpot.x:20
    Drag.hotSpot.y:height/2
    Controls.ItemSurface {anchors.fill:parent;theme:root.theme;selected:root.selected;hovered:hover.hovered;pressed:activation.pressed;normalColor:"transparent";selectedColor:root.theme.selected;railVisible:false;separatorVisible:true;borderWidth:root.focused || root.activeFocus ? 1 : 0;borderColor:root.theme.action}
    HoverHandler {id:hover}
    RowLayout {
        anchors.fill:parent;anchors.leftMargin:root.leftPadding+4;anchors.rightMargin:4;spacing:6
        Controls.CheckBox {theme:root.theme;compact:true;Layout.preferredWidth:24;checked:root.selected;Accessible.name:root.row.path;onToggled:root.selectedChangedByUser(checked)}
        Controls.MaterialIcon {name:root.badges[0].icon;size:17;Layout.preferredWidth:17;color:Presentation.color(root.theme,root.badges[0].tone)}
        Repeater {
            model:root.columns.length ? root.columns.filter(column=>column.visible) : [{key:"path",width:300},{key:"local_status",width:120},{key:"server_status",width:120},{key:"number",width:72}]
            delegate:Label {
                required property var modelData
                Layout.preferredWidth:modelData.width;Layout.minimumWidth:modelData.width;Layout.maximumWidth:modelData.width
                text:modelData.key === "checkout" ? root.checkoutLabel : modelData.key === "local_status" ? root.localLabel : modelData.key === "server_status" ? root.serverLabel : Presentation.value(root.row,modelData.key)
                color:root.selected ? root.theme.selectedText : modelData.key === "path" ? root.theme.primaryText : modelData.key === "server_status" ? Presentation.color(root.theme,root.badges[0].tone) : root.theme.secondaryText
                font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.label;elide:Text.ElideMiddle
            }
        }
        Item {Layout.fillWidth:true}
        Controls.MaterialIcon {Layout.preferredWidth:14;visible:root.checkoutLabel.length>0 && root.checkoutLabel!==qsTr("No active checkout");name:"lock";size:14;color:root.checkoutHolders.some(holder=>holder.owner!==root.currentUser) ? root.theme.violet : root.theme.action}
    }
    Controls.ActivationHandler {id:activation;repeatPointerTaps:true;onActivated:(modifiers,x,y)=>{root.forceActiveFocus();root.selectedByUser(modifiers)};onDoubleActivated:root.activated()}
    MouseArea {anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:mouse=>root.menuRequested(root,mouse.x,mouse.y)}
    DragHandler {id:drag;target:null;acceptedButtons:Qt.LeftButton;onActiveChanged:if(active)root.dragRequested()}
    Keys.onPressed:event=>{
        if(event.key===Qt.Key_Escape && drag.active){root.Drag.cancel();event.accepted=true}
        else if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter){root.activated();event.accepted=true}
        else if(event.key===Qt.Key_Space){root.selectedByUser(Qt.ControlModifier);event.accepted=true}
        else if(event.key===Qt.Key_Menu || (event.key===Qt.Key_F10 && (event.modifiers & Qt.ShiftModifier))){root.menuRequested(root,8,height);event.accepted=true}
    }
    Controls.ToolTip {theme:root.theme;visible:hover.hovered && !root.theme.suppressToolTips;delay:500;text:root.row.path+"\n"+root.badges.map(badge=>qsTr(badge.label)).join(" · ")+"\n"+root.checkoutLabel}
}
