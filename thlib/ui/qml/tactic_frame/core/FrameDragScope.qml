import QtQuick

Item {
 id:root
 required property var value
 signal started()
 readonly property var frameDragValue:value
 function cancel(){proxy.Drag.cancel();proxy.dragging=false}
 onVisibleChanged:if(!visible)cancel()
 HoverHandler{cursorShape:Qt.OpenHandCursor}
 DragHandler{
  id:gesture;target:null;acceptedButtons:Qt.LeftButton;cursorShape:Qt.ClosedHandCursor
  onActiveChanged:{if(active){proxy.dragging=true;root.started()}else if(proxy.dragging){proxy.Drag.drop();proxy.dragging=false}}
  onCanceled:root.cancel()
 }
 Item{id:proxy;x:gesture.centroid.position.x;y:gesture.centroid.position.y;width:1;height:1
  property bool dragging:false
  Drag.active:dragging;Drag.source:root;Drag.keys:["application/x-tactic-frame"];Drag.supportedActions:Qt.MoveAction;Drag.dragType:Drag.Internal
 }
 Connections{target:root.Window.window;function onActiveChanged(){if(root.Window.window&&!root.Window.window.active)root.cancel()}}
}
