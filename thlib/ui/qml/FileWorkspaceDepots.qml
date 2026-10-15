import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id:root
    required property var theme
    required property var controller
    readonly property var state:controller.view_data
    readonly property var draft:state.depot_draft || ({})
    readonly property bool editing:draft.creating!==undefined
    readonly property bool dirty:JSON.stringify(draft)!==JSON.stringify(state.depot_original || {})
    property string notice:""
    function change(key,value) { const next=Object.assign({},draft);next[key]=value;controller.set_value("depot_draft",next) }
    function edit(row) { if(dirty){notice=qsTr("Save or reset the current depot draft first.");return}notice="";controller.action("depot_editor",row ? {depot:row.code} : {}) }
    function reset() {controller.set_value("depot_draft",state.depot_original);notice=""}
    ColumnLayout {
        anchors.fill:parent;anchors.margins:8;spacing:8
        RowLayout {
            Layout.fillWidth:true
            Label {Layout.fillWidth:true; text:qsTr("Depots");font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.title;font.bold:true;color:root.theme.primaryText}
            Controls.Button {theme:root.theme;text:qsTr("Refresh");icon.name:"refresh";enabled:!root.controller.busy;onClicked:root.controller.action("catalog_page",{})}
            Controls.Button {theme:root.theme;text:qsTr("Next page");icon.name:"chevron-right";visible:Boolean(root.state.catalog_after);enabled:!root.controller.busy;onClicked:root.controller.action("catalog_page",{more:true})}
        }
    SplitView {
        id:split
        Layout.fillWidth:true;Layout.fillHeight:true
        orientation:root.width<600 ? Qt.Vertical : Qt.Horizontal
        handle:Controls.SplitterHandle {theme:root.theme;vertical:root.width>=600}
        ListView {
            id:rows;SplitView.fillWidth:true;SplitView.fillHeight:true;clip:true
            model:root.controller.catalog_model
            ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:rows}
            delegate:Controls.EditorListItem {
                required property var node
                theme:root.theme;width:rows.width-bar.reservedExtent;text:node.code
                description:(node.title || node.code)+" · "+((node.storage || {}).repository || qsTr("Project storage"))
                iconName:"database";selected:root.state.catalog_detail.code===node.code
                onClicked:root.controller.set_value("catalog_detail",node)
            }
            Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;anchors.centerIn:parent;visible:rows.count===0;text:qsTr("No permitted records on this page");color:root.theme.secondaryText;width:parent.width;wrapMode:Text.Wrap}
        }
        Flickable {
            id:info;SplitView.preferredWidth:split.width*0.45;SplitView.preferredHeight:split.height*0.6
            SplitView.minimumWidth:0;SplitView.minimumHeight:0;contentWidth:width;contentHeight:fields.implicitHeight;clip:true
            ScrollBar.vertical:Controls.ScrollBar {id:infoBar;theme:root.theme;flickableTarget:info}
            ColumnLayout {
                id:fields;width:Math.max(0,info.width-infoBar.reservedExtent);spacing:8
                Label {font.family:root.theme.fontFamily;Layout.fillWidth:true;text:root.editing ? root.draft.creating ? qsTr("New depot") : qsTr("Edit depot") : root.state.catalog_detail.code || qsTr("Select a depot");color:root.theme.primaryText;font.bold:true;font.pointSize:Controls.Typography.title;wrapMode:Text.Wrap}
                Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:Boolean(root.notice);text:root.notice;color:root.theme.error;wrapMode:Text.Wrap}
                Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;visible:root.editing;text:qsTr("Depot code");color:root.theme.secondaryText}
                Controls.TextField {objectName:"depotEditorCode";theme:root.theme;Layout.fillWidth:true;visible:root.editing;text:root.draft.code || "";readOnly:!root.draft.creating;enabled:!root.controller.busy;Accessible.name:qsTr("Depot code");onTextEdited:root.change("code",text)}
                Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;visible:root.editing;text:qsTr("Name");color:root.theme.secondaryText}
                Controls.TextField {objectName:"depotEditorName";theme:root.theme;Layout.fillWidth:true;visible:root.editing;text:root.draft.title || "";enabled:!root.controller.busy;Accessible.name:qsTr("Name");onTextEdited:root.change("title",text)}
                Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;visible:root.editing;text:qsTr("Repository");color:root.theme.secondaryText}
                Controls.ComboBox {theme:root.theme;Layout.fillWidth:true;visible:root.editing;enabled:!root.controller.busy;textRole:"label";valueRole:"value";translateDisplayText:false;model:[{value:"",label:qsTr("Project storage")}].concat((root.state.catalog_capabilities.repositories || []).map(value=>({value:value,label:value}))).concat(root.draft.repository && !(root.state.catalog_capabilities.repositories || []).includes(root.draft.repository) ? [{value:root.draft.repository,label:root.draft.repository}] : []);currentIndex:Math.max(0,model.findIndex(row=>row.value===root.draft.repository));Accessible.name:qsTr("Repository");onActivated:root.change("repository",currentValue)}
                Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:root.editing;text:qsTr("Repository changes apply to new uploads. Existing file contents stay in their original storage.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
                Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:root.editing;text:qsTr("Depot paths are case-sensitive. Access is configured in Administration → Rules using file_depot.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
                Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:!root.editing && Boolean(root.state.catalog_detail.code);text:(root.state.catalog_detail.title || "")+"\n"+qsTr("Repository")+": "+((root.state.catalog_detail.storage || {}).repository || qsTr("Project storage"))+"\n"+qsTr("Revision")+": "+root.state.catalog_detail.revision+"\n"+qsTr("Case-sensitive depot paths");color:root.theme.secondaryText;wrapMode:Text.Wrap}
                Flow {
                    Layout.fillWidth:true;spacing:8
                    Controls.Button {theme:root.theme;visible:!root.editing && root.state.administrator;text:qsTr("New depot");icon.name:"add";enabled:!root.controller.busy;onClicked:root.edit(null)}
                    Controls.Button {theme:root.theme;visible:!root.editing && root.state.administrator;text:qsTr("Edit depot");icon.name:"edit";enabled:!root.controller.busy && Boolean(root.state.catalog_detail.code);onClicked:root.edit(root.state.catalog_detail)}
                    Controls.Button {theme:root.theme;visible:root.editing;text:qsTr("Reset");icon.name:"undo";enabled:!root.controller.busy;onClicked:root.reset()}
                    Controls.Button {theme:root.theme;visible:root.editing;text:qsTr("Cancel");icon.name:"close";enabled:!root.controller.busy;onClicked:{if(root.dirty){root.notice=qsTr("Save or reset the current depot draft first.");return}root.controller.set_value("depot_draft",{});root.controller.set_value("depot_original",{})}}
                    Controls.Button {theme:root.theme;visible:root.editing;text:root.draft.creating ? qsTr("Create") : qsTr("Save");icon.name:"content-save";enabled:!root.controller.busy && Boolean((root.draft.code || "").trim());onClicked:root.controller.action("save_depot",{})}
                }
            }
        }
    }
    }
}
