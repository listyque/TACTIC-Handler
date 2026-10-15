import QtQuick
import "../.."
import "../../../controls" as Controls
import "code.ui.mjs" as UI

Item {
 id:root
 required property var theme
 required property var node
 required property var controller
 signal event(var action)
 property real codeFont:9.25
 property int commandRevision:0
 property bool ready:false
 property string activeBuffer:""
 readonly property var model: {const revision=source.historyRevision;const state=source.currentHistory();return {historyCount:state?state.entries.length+1:1,historyIndex:state?state.index:0,canUndo:source.canUndo,canRedo:source.canRedo,canCopy:source.canCopy,fontSize:codeFont,readOnly:source.readOnly}}
 objectName:node.id
 function synchronize(){
  const key=String(node.bufferKey||node.id),value=String(node.text||"")
  if(activeBuffer!==key){activeBuffer=key;source.loadBuffer(key,value)}
  else if(String(source.text)!==value)source.loadBuffer(key,value)
 }
 // Reducers publish the document after UI state in the same input event.
 onNodeChanged:if(ready)Qt.callLater(root.synchronize)
 Component.onCompleted:{ready=true;synchronize()}
 function dispatch(action){
  commandRevision++
  if(action.type==="font"){codeFont=Number(action.value);return}
  if(action.type==="history"){if(!source.readOnly)source.applyHistoryIndex(Number(action.value));return}
  const command=action.value
  if(command==="undo"&&source.canUndo)source.undoEdit()
  else if(command==="redo"&&source.canRedo)source.redoEdit()
  else if(command==="copy"&&source.canCopy)source.copySelection()
  else if(command==="cut"&&source.canCut)source.cutSelection()
  else if(command==="paste"&&!source.readOnly)source.pasteClipboard()
  else if(command==="find"||command==="replace"&&!source.readOnly)source.showFind(command==="replace")
  else if(command==="help")root.event(root.node.helpAction||{type:"help"})
 }
 FrameView{id:toolbar;width:root.width;height:30;theme:root.theme;scene:UI.toolbar(root.model,width,root.node.language||"en",root.commandRevision);onEvent:action=>root.dispatch(action)}
 Controls.ScriptCodeEditor{id:source;y:36;width:root.width;height:root.height-y;theme:root.theme;controller:root.controller;readOnly:root.node.readOnly||!root.node.enabled;fontPointSize:root.codeFont;onTextEdited:if(root.node.action)root.event(Object.assign({},root.node.action,{value:text}))}
}
