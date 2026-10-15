import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id:root
    required property var theme
    required property var row
    required property string caption
    property string subtitle:""
    property bool selected:false
    readonly property bool branch:["depot","stream","workspace","directory","change"].indexOf(row.kind)>=0
    property bool focused:false
    onFocusedChanged:if(focused)forceActiveFocus()
    property var dragData:({})
    signal selectedByUser(int modifiers)
    signal menuRequested(var source, real x, real y)
    signal dragRequested()
    signal dropped(var payload, var urls)
    property bool acceptsDrop:false
    property var dropReason:null
    property var dropCaption:null
    property string dragCaption:""
    property string dragFeedback:""
    Drag.active:rowDrag.active
    Drag.dragType:Drag.Automatic
    Drag.supportedActions:Qt.CopyAction | Qt.MoveAction
    Drag.mimeData:dragData
    signal disclosure()
    signal activated()
    signal doubleActivated()
    implicitHeight:subtitle.length ? 42 : 30
    objectName:"workspaceTreeRow:"+row.id
    activeFocusOnTab:true
    Accessible.role:Accessible.Button
    Accessible.name:caption
    Accessible.description:subtitle || row.path || ""
    Controls.ToolTip {theme:root.theme;visible:hover.hovered && !root.theme.suppressToolTips;delay:500;text:root.caption+"\n"+root.subtitle}
    Accessible.onPressAction:if(enabled){if(row.kind==="change")doubleActivated();else activated()}
    Keys.onRightPressed:if(branch && !row.expanded)disclosure()
    Keys.onLeftPressed:if(branch && row.expanded)disclosure()
    Keys.onReturnPressed:if(row.kind==="change")doubleActivated();else activated()
    Keys.onSpacePressed:activated()
    HoverHandler {id:hover;cursorShape:root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor}
    Controls.ItemSurface {anchors.fill:parent;theme:root.theme;normalColor:"transparent";selected:root.selected;hovered:hover.hovered;pressed:activation.pressed;selectedColor:root.theme.selected;railVisible:false;borderWidth:root.activeFocus || root.focused ? 1 : 0;borderColor:root.theme.action}
    RowLayout {
        anchors.fill:parent;anchors.leftMargin:Math.min(root.row.depth,8)*16+2;anchors.rightMargin:2;spacing:4
        Controls.CompactIconButton {
            theme:root.theme;iconSize:14;implicitWidth:22;implicitHeight:24
            visible:root.branch;iconName:root.row.expanded ? "expand-more" : "chevron-right"
            toolTip:(root.row.expanded ? qsTr("Collapse %1") : qsTr("Expand %1")).arg(root.caption)
            Accessible.name:toolTip;objectName:"workspaceDisclosure:"+root.row.id
            onClicked:root.disclosure()
        }
        Item {implicitWidth:22;visible:!root.branch}
        Item {
            Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumWidth:0
            RowLayout {
                anchors.fill:parent;spacing:4
                Controls.MaterialIcon {name:root.row.kind === "workspace" ? "desktop" : root.row.kind === "depot" ? "database" : root.row.kind === "stream" ? "workflow" : root.row.kind === "directory" ? (root.row.expanded ? "folder-open" : "folder") : root.row.kind === "change" ? "archive" : root.row.kind === "more" ? "add" : "file";size:17;color:root.row.kind === "change" ? (root.row.state === "submitted" ? root.theme.green : root.row.state === "shelved" ? root.theme.violet : root.theme.yellow) : root.theme.secondaryText}
                ColumnLayout {
                    Layout.fillWidth:true;Layout.minimumWidth:0;spacing:1
                    Label {Layout.fillWidth:true;Layout.minimumWidth:0;text:root.caption;textFormat:Text.PlainText;font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.label;color:root.theme.primaryText;elide:Text.ElideMiddle}
                    Label {Layout.fillWidth:true;Layout.minimumWidth:0;visible:root.subtitle.length>0;text:root.subtitle;textFormat:Text.PlainText;font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.caption;color:root.theme.secondaryText;elide:Text.ElideRight}
                }
                Controls.MaterialIcon {visible:root.row.kind === "change";name:root.row.state === "submitted" ? "check-circle" : root.row.state === "shelved" ? "archive" : root.row.state === "reverted" ? "undo" : "schedule";size:14;color:root.theme.secondaryText}
            }
            Controls.ActivationHandler {id:activation;repeatPointerTaps:true;enabled:root.enabled;onActivated:(modifiers,x,y)=>{root.forceActiveFocus();root.selectedByUser(modifiers);if(!(modifiers & (Qt.ControlModifier | Qt.ShiftModifier)))root.activated()};onDoubleActivated:{if(root.row.kind==="change")root.doubleActivated();else if(root.branch)root.disclosure()}}
        }
    }
    MouseArea {anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:mouse=>root.menuRequested(root,mouse.x,mouse.y)}
    DragHandler {id:rowDrag;target:null;acceptedButtons:Qt.LeftButton;onActiveChanged:if(active)root.dragRequested()}
    DropArea {
        id:dropTarget;anchors.fill:parent;enabled:root.acceptsDrop
        keys:["application/x-tactic-file-workspace","text/uri-list"]
        onEntered:drag=>{
            root.dragCaption=root.dropCaption ? root.dropCaption(drag.getDataAsString("application/x-tactic-file-workspace"),drag.urls) : ""
            root.dragFeedback=root.dropReason ? root.dropReason(drag.getDataAsString("application/x-tactic-file-workspace"),drag.urls) : ""
            pointerY=scrollView ? root.mapToItem(scrollView,drag.x,drag.y).y : 0
            drag.accepted=true
        }
        onExited:root.dragFeedback=""
        onDropped:drop=>{
            const payload=drop.getDataAsString("application/x-tactic-file-workspace")
            const reason=root.dropReason ? root.dropReason(payload,drop.urls) : ""
            if(reason){root.dragFeedback="";drop.accepted=false;return}
            root.dropped(payload,drop.urls);drop.acceptProposedAction();root.dragFeedback=""
        }
        readonly property var scrollView:root.ListView.view || (root.parent ? root.parent.ListView.view : null)
        property real pointerY:0
        onPositionChanged:drag=>{if(scrollView)pointerY=root.mapToItem(scrollView,drag.x,drag.y).y}
        Timer {interval:400;running:dropTarget.containsDrag && !root.dragFeedback && root.branch && !root.row.expanded;onTriggered:root.disclosure()}
        Timer {interval:30;repeat:true;running:dropTarget.containsDrag && Boolean(dropTarget.scrollView)
            onTriggered:{const view=dropTarget.scrollView;const direction=dropTarget.pointerY<24 ? -1 : dropTarget.pointerY>view.height-24 ? 1 : 0;view.contentY=Math.max(0,Math.min(view.contentHeight-view.height,view.contentY+direction*12))}
        }
        Rectangle {anchors.fill:parent;visible:dropTarget.containsDrag;color:"transparent";border.width:2;border.color:root.dragFeedback ? root.theme.red : root.theme.action;radius:root.theme.surfaceRadius}
    }
    Controls.ToolTip {theme:root.theme;visible:dropTarget.containsDrag;delay:0;text:root.dragFeedback || root.dragCaption || qsTr("Add to changelist #%1").arg(root.row.number || root.row.code)}
    Keys.onPressed:event=>{if(event.key===Qt.Key_Escape && rowDrag.active){root.Drag.cancel();event.accepted=true}else if(event.key===Qt.Key_Menu || (event.key===Qt.Key_F10 && (event.modifiers & Qt.ShiftModifier))){root.menuRequested(root,8,height);event.accepted=true}}
    Controls.ToolTip {theme:root.theme;visible:hover.hovered && !root.theme.suppressToolTips;delay:500;text:(root.row.path || root.caption)+(root.subtitle ? "\n"+root.subtitle : "")}
}
