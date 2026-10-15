import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id:root
    objectName:"workspaceStreamEditor"
    required property var controller
    property var original:({})
    property var choices:({types:[],depots:[],parents:[]})
    property string request:""
    property string notice:""
    property string initializedRequest:""
    property bool loading:false
    property bool saving:false
    property bool creating:true
    property string parentCode:""
    readonly property var editorResult:controller.view_data.stream_editor || ({})
    modal:true;draggable:true;parent:Overlay.overlay
    width:Math.min(660,parent ? parent.width-24 : 660)
    height:Math.min(660,parent ? parent.height-24 : 660)
    title:creating ? qsTr("New stream") : qsTr("Edit stream: %1").arg(original.code || "")
    closePolicy:saving ? Popup.NoAutoClose : Popup.CloseOnEscape
    onWidthChanged:if(visible && parent)x=(parent.width-width)/2
    onHeightChanged:if(visible && parent)y=(parent.height-height)/2
    function center() {if(visible && parent){x=(parent.width-width)/2;y=(parent.height-height)/2}}
    onOpened:center()
    Connections {target:root.parent;function onWidthChanged(){root.center()} function onHeightChanged(){root.center()}}
    function openSpec(row,child) {
        original=row || {};creating=child || !original.code;parentCode=child ? original.code : original.parent || ""
        notice="";loading=true;saving=false;request=String(Date.now())+Math.random()
        open()
        controller.action("stream_editor",{request:request,stream:creating ? "" : original.code})
    }
    onEditorResultChanged:{
        if(!visible || editorResult.request!==request)return
        loading=false;saving=false
        if(editorResult.error){notice=editorResult.error;return}
        if(editorResult.saved){close();controller.action("catalog_page",{});return}
        if(initializedRequest===request)return
        initializedRequest=request
        choices=editorResult
        if(!creating){original=editorResult.info;parentCode=original.parent || ""}
        code.text=creating ? "" : original.code
        name.text=creating ? "" : original.title || original.code
        description.text=creating ? "" : original.description || ""
        depot.currentIndex=Math.max(0,choices.depots.findIndex(item=>item.code===original.depot))
        type.currentIndex=Math.max(0,choices.types.indexOf(creating ? (parentCode ? original.stream_type==="release" ? "release" : "development" : "mainline") : original.stream_type))
        parentStream.text=parentCode
        locked.checked=!creating && Boolean(original.locked)
    }
    function save() {
        const values={request:String(Date.now())+Math.random(),title:name.text,description:description.text,
            stream_type:type.currentText,parent:type.currentText==="mainline" ? null : parentStream.text.trim(),locked:locked.checked}
        if(creating){values.code=code.text.trim();values.depot=depot.currentValue}
        else {values.stream=original.code;values.spec_revision=String(original.spec_revision)}
        request=values.request;saving=true;notice="";controller.action("save_stream",values)
    }
    contentItem:Flickable {
        id:scroll;clip:true;contentWidth:width;contentHeight:fields.implicitHeight
        ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:scroll}
        ColumnLayout {
            id:fields;width:Math.max(0,scroll.width-bar.reservedExtent);spacing:8;enabled:!root.loading && !root.saving
            Label {Layout.fillWidth:true;visible:Boolean(root.notice);text:root.notice;color:root.theme.error;wrapMode:Text.Wrap;textFormat:Text.PlainText}
            Label {visible:root.loading;text:qsTr("Loading…");color:root.theme.secondaryText}
            Label {text:qsTr("Stream code");color:root.theme.secondaryText}
            Controls.TextField {id:code;objectName:"streamEditorCode";theme:root.theme;Layout.fillWidth:true;readOnly:!root.creating;Accessible.name:qsTr("Stream code")}
            Label {text:qsTr("Name");color:root.theme.secondaryText}
            Controls.TextField {id:name;objectName:"streamEditorName";theme:root.theme;Layout.fillWidth:true;Accessible.name:qsTr("Name")}
            Label {text:qsTr("Depot");color:root.theme.secondaryText}
            Controls.ComboBox {id:depot;theme:root.theme;Layout.fillWidth:true;model:root.choices.depots || [];textRole:"code";valueRole:"code";translateDisplayText:false;enabled:root.creating;Accessible.name:qsTr("Depot")}
            Label {text:qsTr("Stream type");color:root.theme.secondaryText}
            Controls.ComboBox {id:type;objectName:"streamEditorType";theme:root.theme;Layout.fillWidth:true;model:root.choices.types || [];translateDisplayText:false;enabled:root.creating;Accessible.name:qsTr("Stream type")}
            Label {text:qsTr("Parent stream");color:root.theme.secondaryText}
            RowLayout {
                Layout.fillWidth:true;enabled:type.currentText!=="mainline"
                Controls.TextField {id:parentStream;objectName:"streamEditorParent";theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0;Accessible.name:qsTr("Parent stream")}
                Controls.ComboBox {theme:root.theme;Layout.preferredWidth:150;displayText:qsTr("Choose parent");translateDisplayText:false;model:(root.choices.parents || []).filter(row=>row.code!==code.text && row.depot===depot.currentValue).map(row=>row.code);onActivated:parentStream.text=currentText;Accessible.name:qsTr("Choose parent")}
            }
            Label {Layout.fillWidth:true;visible:root.choices.more || false;text:qsTr("The picker shows the first 1000 records. Enter another parent stream code directly.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
            Label {text:qsTr("Description");color:root.theme.secondaryText}
            Controls.TextArea {id:description;objectName:"streamEditorDescription";theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:100;wrapMode:TextEdit.Wrap;Accessible.name:qsTr("Description")}
            Label {visible:!root.creating;text:qsTr("Owner: %1").arg(root.original.owner || "—");color:root.theme.secondaryText}
            Controls.CheckBox {id:locked;theme:root.theme;text:qsTr("Only the owner and administrators may edit stream settings")}
            Label {Layout.fillWidth:true;text:root.creating && type.currentText!=="mainline" ? qsTr("The new branch starts from the parent's published files without copying file contents.") : !root.creating ? qsTr("Changing Parent changes the hierarchy. Existing files and their branch history stay intact.") : "";visible:text.length>0;color:root.theme.secondaryText;wrapMode:Text.Wrap}
            Label {Layout.fillWidth:true;text:qsTr("Virtual streams, inherited path views and automatic merge/copy policies are not supported yet.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
        }
    }
    footer:Controls.DialogActions {
        theme:root.theme
        Controls.Button {theme:root.theme;text:qsTr("Cancel");icon.name:"close";enabled:!root.saving;onClicked:root.close()}
        Controls.Button {objectName:"streamEditorSave";theme:root.theme;text:root.creating ? qsTr("Create") : qsTr("Save");icon.name:"save";enabled:!root.loading && !root.saving && code.text.trim().length>0 && type.currentIndex>=0 && depot.currentIndex>=0;onClicked:root.save()}
    }
}
