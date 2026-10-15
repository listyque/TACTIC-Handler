import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id:root
    required property var theme
    property string value:""
    property string primaryStream:""
    property bool enabledEditing:true
    property string written:""
    property string parseError:""
    property bool technical:false
    signal edited(string value)
    ListModel {id:rules}
    function load(){
        if(value===written)return
        try{
            const data=value ? JSON.parse(value) : []
            if(!Array.isArray(data))throw new Error(qsTr("Mappings must be an array"))
            rules.clear()
            for(const row of data)rules.append({stream:row.stream || "",source:row.source || "",target:row.target || "...",exclude:Boolean(row.exclude),writable:Boolean(row.writable)})
            parseError=""
        }catch(error){parseError=String(error.message)}
    }
    function publish(){
        const rows=[]
        for(let i=0;i<rules.count;i++){const row=rules.get(i);const data={stream:row.stream,source:row.source,exclude:row.exclude,writable:row.writable};if(!row.exclude)data.target=row.target;rows.push(data)}
        written=JSON.stringify(rows);edited(written)
    }
    function update(index,name,value){rules.setProperty(index,name,value);publish()}
    onValueChanged:load()
    Component.onCompleted:load()
    RowLayout {
        Layout.fillWidth:true
        Label {Layout.fillWidth:true;text:qsTr("Mappings and exclusions");color:root.theme.primaryText}
        Controls.CompactIconButton {theme:root.theme;iconName:"add";toolTip:qsTr("Add mapping");enabled:root.enabledEditing && rules.count<256;onClicked:{rules.append({stream:root.primaryStream,source:"...",target:"...",exclude:false,writable:true});root.publish()}}
        Controls.CompactIconButton {theme:root.theme;iconName:"code";toolTip:qsTr("Technical JSON");onClicked:root.technical=!root.technical}
    }
    Label {Layout.fillWidth:true;visible:Boolean(root.parseError);text:root.parseError;color:root.theme.error;wrapMode:Text.Wrap}
    Repeater {
        model:rules
        delegate:ColumnLayout {
            required property int index
            required property string stream
            required property string source
            required property string target
            required property bool exclude
            required property bool writable
            Layout.fillWidth:true;visible:!root.technical;spacing:4
            RowLayout {
                Layout.fillWidth:true
                Controls.TextField {theme:root.theme;Layout.fillWidth:true;placeholderText:qsTr("Stream");Accessible.name:qsTr("Mapping stream");text:stream;enabled:root.enabledEditing;onTextEdited:root.update(index,"stream",text)}
                Controls.CompactIconButton {theme:root.theme;iconName:"delete";toolTip:qsTr("Remove mapping");enabled:root.enabledEditing;onClicked:{rules.remove(index);root.publish()}}
            }
            Controls.TextField {theme:root.theme;Layout.fillWidth:true;placeholderText:qsTr("Depot pattern, e.g. assets/...");objectName:"workspaceMappingSource:"+index;Accessible.name:qsTr("Depot pattern");text:source;enabled:root.enabledEditing;onTextEdited:root.update(index,"source",text)}
            Controls.TextField {theme:root.theme;Layout.fillWidth:true;visible:!exclude;placeholderText:qsTr("Local pattern, e.g. art/...");Accessible.name:qsTr("Local pattern");text:target;enabled:root.enabledEditing;onTextEdited:root.update(index,"target",text)}
            RowLayout {
                Controls.CheckBox {theme:root.theme;text:qsTr("Exclude");checked:exclude;enabled:root.enabledEditing;onToggled:root.update(index,"exclude",checked)}
                Controls.CheckBox {theme:root.theme;text:qsTr("Writable");checked:writable;enabled:root.enabledEditing && !exclude;onToggled:root.update(index,"writable",checked)}
            }
            Rectangle {Layout.fillWidth:true;implicitHeight:1;color:root.theme.outlineVariant}
        }
    }
    Controls.TextArea {theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:180;visible:root.technical;text:root.value;readOnly:!root.enabledEditing;Accessible.name:qsTr("Workspace mappings (JSON)");onTextChanged:if(activeFocus)root.edited(text)}
}
