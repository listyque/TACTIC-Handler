import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id:root
    required property var theme
    required property var controller
    signal editStream(var row,bool child)
    readonly property var state:controller.view_data
    readonly property real zoom:state.graph_zoom || 1
    readonly property var nodes:state.graph_nodes || []
    readonly property var positions:layout()
    color:theme.panelDeep;radius:theme.surfaceRadius;border.color:theme.outlineVariant
    function layout() {
        const levels={},slots={},result={}
        let pending=nodes.slice()
        for(let pass=0;pending.length && pass<=nodes.length;pass++){
            const next=[]
            for(const row of pending){
                if(row.parent && nodes.some(node=>node.code===row.parent) && levels[row.parent]===undefined){next.push(row);continue}
                levels[row.code]=levels[row.parent]===undefined ? 0 : levels[row.parent]+1
            }
            if(next.length===pending.length){for(const row of next)levels[row.code]=0;break}
            pending=next
        }
        for(const row of nodes){const level=levels[row.code] || 0;const slot=slots[level] || 0;slots[level]=slot+1;result[row.code]={x:24+level*204,y:24+slot*88}}
        return result
    }
    function menu(row,item,x,y) {
        if(row)controller.set_value("catalog_detail",row)
        context.actions=[{title:qsTr("New stream"),translate:false,icon:"add",command:"new"}]
        if(row)context.actions=context.actions.concat([{title:qsTr("New child stream"),translate:false,icon:"source-branch",command:"child",enabled:Boolean(row.writable)},
            {title:qsTr("Edit stream"),translate:false,icon:"edit",command:"edit",enabled:Boolean(row.writable)}])
        context.openAt(item,x,y)
    }
    ActionMenu {id:context;theme:root.theme;onTriggered:command=>root.editStream(command==="new" ? ({}) : root.state.catalog_detail,command==="child")}
    ColumnLayout {
        anchors.fill:parent;anchors.margins:8;spacing:4
        RowLayout {
            Layout.fillWidth:true
            Controls.CompactIconButton {theme:root.theme;iconName:"add";toolTip:qsTr("New stream");onClicked:root.editStream({},false)}
            Label {Layout.fillWidth:true;text:qsTr("Stream Graph");color:root.theme.primaryText;font.family:root.theme.fontFamily}
            Controls.CompactIconButton {theme:root.theme;iconName:"minus";toolTip:qsTr("Zoom out");onClicked:root.controller.set_value("graph_zoom",Math.max(0.25,root.zoom-0.1))}
            Label {text:Math.round(root.zoom*100)+"%";color:root.theme.secondaryText}
            Controls.CompactIconButton {theme:root.theme;iconName:"plus";toolTip:qsTr("Zoom in");onClicked:root.controller.set_value("graph_zoom",Math.min(2,root.zoom+0.1))}
            Controls.CompactIconButton {theme:root.theme;iconName:"refresh";toolTip:qsTr("Refresh");enabled:!root.controller.busy;onClicked:root.controller.action("catalog_page",{})}
            Controls.Button {theme:root.theme;icon.name:"chevron-right";text:qsTr("Next page");visible:Boolean(root.state.catalog_after);onClicked:root.controller.action("catalog_page",{more:true})}
        }
        Label {Layout.fillWidth:true;text:qsTr("Parent links and submitted integrations. Double-click a stream to edit its settings.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
        Flickable {
            id:view;Layout.fillWidth:true;Layout.fillHeight:true;clip:true
            contentWidth:Math.max(width-vertical.reservedExtent,...root.nodes.map(row=>(root.positions[row.code].x+180)*root.zoom))
            contentHeight:Math.max(height-horizontal.reservedExtent,...root.nodes.map(row=>(root.positions[row.code].y+84)*root.zoom))
            ScrollBar.vertical:Controls.ScrollBar {id:vertical;theme:root.theme;flickableTarget:view}
            ScrollBar.horizontal:Controls.ScrollBar {id:horizontal;theme:root.theme;flickableTarget:view}
            Item {
                id:plane;width:view.contentWidth/root.zoom;height:view.contentHeight/root.zoom;scale:root.zoom;transformOrigin:Item.TopLeft
                MouseArea {anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:event=>root.menu(null,plane,event.x,event.y)}
                Canvas {
                    id:links;anchors.fill:parent
                    Connections {target:root.controller;function onStateChanged(){links.requestPaint()}}
                    onPaint:{
                        const painter=getContext("2d");painter.reset()
                        for(const edge of root.state.graph_edges || []){
                            const a=root.positions[edge.source],b=root.positions[edge.target];if(!a || !b)continue
                            painter.strokeStyle=edge.kind==="merge" ? root.theme.green : root.theme.action;painter.lineWidth=1.5
                            const x=a.x+172,y=a.y+32,targetX=b.x,targetY=b.y+32
                            painter.beginPath();painter.moveTo(x,y);painter.bezierCurveTo(x+40,y,targetX-40,targetY,targetX,targetY);painter.stroke()
                            painter.beginPath();painter.moveTo(targetX-7,targetY-4);painter.lineTo(targetX,targetY);painter.lineTo(targetX-7,targetY+4);painter.stroke()
                        }
                    }
                }
                Repeater {
                    model:root.nodes
                    delegate:Controls.PopupAction {
                        id:streamNode
                        required property var modelData
                        property var theme:root.theme
                        objectName:"streamGraphNode_"+modelData.code
                        x:root.positions[modelData.code].x;y:root.positions[modelData.code].y;width:172;height:64
                        hoverEnabled:true;Accessible.name:modelData.code;Accessible.description:qsTr("Revision %1").arg(modelData.revision)
                        background:Controls.ItemSurface {theme:root.theme;normalColor:root.theme.panel;selected:root.state.catalog_detail?.code===parent.modelData.code;hovered:parent.hovered;railVisible:false}
                        contentItem:ColumnLayout {
                            Label {Layout.fillWidth:true;text:streamNode.modelData.title || streamNode.modelData.code;color:root.theme.primaryText;elide:Text.ElideMiddle;font.family:root.theme.fontFamily}
                            Label {Layout.fillWidth:true;text:streamNode.modelData.stream_type+" · #"+streamNode.modelData.revision+" · "+streamNode.modelData.depot;color:root.theme.secondaryText;elide:Text.ElideRight;font.family:root.theme.fontFamily}
                        }
                        onClicked:root.controller.set_value("catalog_detail",modelData)
                        onDoubleClicked:root.editStream(modelData,false)
                        MouseArea {anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:event=>root.menu(streamNode.modelData,streamNode,event.x,event.y)}
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth:true
            Label {Layout.fillWidth:true;text:root.state.catalog_detail?.code ? root.state.catalog_detail.code+" · #"+root.state.catalog_detail.revision : qsTr("Select a stream");color:root.theme.secondaryText;wrapMode:Text.Wrap}
            Controls.Button {theme:root.theme;icon.name:"chevron-right";text:qsTr("Next connections");visible:Boolean(root.state.graph_after);onClicked:root.controller.action("catalog_page",{edges:true})}
        }
    }
}
