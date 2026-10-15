import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id:root
    objectName:"fileWorkspaceChangelistDetails"
    required property var theme
    required property string windowId
    property var controller:fileWorkspaceController
    readonly property var state:controller.view_data
    property var openedChange:({})
    property string changeCode:""
    readonly property var change:state.change.code===changeCode || !changeCode ? Object.assign({},details.info || {},state.change) : openedChange
    readonly property var details:state.change_details?.change===changeCode ? state.change_details : ({})
    readonly property string windowTitle:qsTr("Changelist #%1").arg(change.number || changeCode)
    property string requestId:""
    property int requestNumber:0
    readonly property bool loading:details.request!==requestId
    property string draft:""
    property bool editing:false
    property bool showFiles:true
    property bool showShelves:true
    property bool showTasks:true
    readonly property bool sameChange:state.change.code===changeCode
    readonly property bool editable:sameChange && change.state==="pending" && change.owner===controller.current_user && change.workspace===state.workspace && change.depot_writable!==false && change.editable!==false && !change.active_transfer && !change.active_bulk && !change.integration && !controller.busy
    readonly property bool dirty:draft!==String(change.description || "")
    Component.onCompleted:{openedChange=change;changeCode=String(change.code || "");draft=String(change.description || "");load()}
    onDetailsChanged:if(details.request===requestId && details.info){openedChange=details.info;if(!editing)draft=String(details.info.description || "")}
    onChangeChanged:if(!editing || draft===String(change.description || "")){draft=String(change.description || "");editing=false}
    function close() {windowModel.close_window(root.windowId)}
    function command(name) {root.close();root.controller.details_command(name)}
    function load(section,after,shelf,shelfRevision) {
        requestId=String(Date.now())+":"+String(++requestNumber)
        let values={change:changeCode,request:requestId}
        if(section){values.section=section;values.edit_revision=String(change.edit_revision);values.after=after || ""}
        if(shelf)values.shelf=shelf
        if(shelfRevision!==undefined)values.shelf_revision=String(shelfRevision)
        controller.action("changelist_details",values)
    }
    Rectangle {anchors.fill:parent;color:root.theme.panelDeep}
    ColumnLayout {
        anchors.fill:parent;spacing:0
        Flickable {
            id:content;objectName:"changelistDetailsScroll";Layout.fillWidth:true;Layout.fillHeight:true;clip:true;contentWidth:width;contentHeight:fields.implicitHeight+24
            ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:content}
            ColumnLayout {
                id:fields;x:12;y:12;width:Math.max(0,content.width-24-bar.reservedExtent);spacing:8
                RowLayout {Layout.fillWidth:true
                    Controls.MaterialIcon {name:"archive";size:22;color:root.theme.action}
                    Label {objectName:"fileWorkspaceChangelistNumber";Layout.fillWidth:true;text:qsTr("Changelist #%1").arg(root.change.number || root.changeCode);color:root.theme.primaryText;font.family:root.theme.fontFamily;font.weight:Font.DemiBold}
                    Controls.CompactIconButton {objectName:"changelistDetailsRefresh";theme:root.theme;iconName:"refresh";toolTip:qsTr("Refresh");enabled:!root.loading && !root.dirty;onClicked:root.load()}
                }
                GridLayout {Layout.fillWidth:true;columns:width<600 ? 1 : 2;columnSpacing:20;rowSpacing:4
                    Repeater {model:[
                        [qsTr("State"),root.change.state==="pending" ? qsTr("Pending") : root.change.state==="submitted" ? qsTr("Submitted") : root.change.state==="shelved" ? qsTr("Shelved") : qsTr("Reverted")],
                        [qsTr("Workspace"),root.change.workspace || "—"],
                        [qsTr("Date"),root.change.created_at ? new Date(root.change.created_at*1000).toLocaleString() : root.change.date || "—"],
                        [qsTr("User"),root.change.owner || "—"],
                        [qsTr("Access type"),root.change.restricted ? qsTr("Restricted") : qsTr("Public")],
                        [qsTr("Stream"),root.change.stream || "—"]]
                        delegate:RowLayout {required property var modelData;Layout.fillWidth:true
                            Label {Layout.preferredWidth:96;text:modelData[0];color:root.theme.secondaryText;font.family:root.theme.fontFamily;elide:Text.ElideRight}
                            Label {Layout.fillWidth:true;Layout.minimumWidth:0;text:String(modelData[1]);textFormat:Text.PlainText;color:root.theme.primaryText;font.family:root.theme.fontFamily;elide:Text.ElideMiddle}
                        }
                    }
                }
                Label {text:qsTr("Description");color:root.theme.secondaryText;font.family:root.theme.fontFamily}
                Controls.TextArea {objectName:"fileWorkspaceChangelistDescription";theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:120;wrapMode:TextEdit.Wrap;textFormat:TextEdit.PlainText;readOnly:!root.editable || !root.editing;selectByMouse:true;text:root.draft;Accessible.name:qsTr("Changelist description");onTextChanged:if(activeFocus)root.draft=text}
                Label {Layout.fillWidth:true;visible:root.loading || Boolean(root.details.error || root.sameChange && root.state.error);text:root.loading ? qsTr("Loading changelist contents…") : root.details.error || root.state.error;color:root.details.error || root.state.error ? root.theme.error : root.theme.secondaryText;wrapMode:Text.Wrap;textFormat:Text.PlainText}
                RowLayout {Layout.fillWidth:true
                    Controls.CompactIconButton {theme:root.theme;iconName:root.showFiles ? "chevron-down" : "chevron-right";toolTip:qsTr("Files");onClicked:root.showFiles=!root.showFiles}
                    Label {Layout.fillWidth:true;text:qsTr("Files (%1)").arg(root.details.files?.files ?? root.change.opened_files ?? "—");color:root.theme.primaryText}
                    Controls.CompactIconButton {objectName:"changelistFilesNext";theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Next page");enabled:!root.loading && Boolean(root.details.files?.after);onClicked:root.load("files",root.details.files.after)}
                }
                FileWorkspaceChangelistFiles {objectName:"changelistFiles";theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:210;visible:root.showFiles;rows:root.details.files?.items || []}
                RowLayout {Layout.fillWidth:true
                    Controls.CompactIconButton {theme:root.theme;iconName:root.showShelves ? "chevron-down" : "chevron-right";toolTip:qsTr("Shelved files");onClicked:root.showShelves=!root.showShelves}
                    Label {text:qsTr("Shelved files (%1)").arg(root.details.shelf_files?.files ?? 0);color:root.theme.primaryText}
                    Controls.ComboBox {objectName:"changelistShelfChoice";theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0;translateDisplayText:false;model:(root.details.shelves?.items || []).map(row=>({code:row.code,label:"#"+row.number}));textRole:"label";currentIndex:model.length ? Math.max(0,model.findIndex(row=>row.code===root.details.shelf_files?.change)) : -1;enabled:!root.loading && model.length>0;onActivated:root.load("shelf_files","",model[currentIndex].code)}
                    Controls.CompactIconButton {theme:root.theme;iconName:"more_horiz";toolTip:qsTr("Next shelves");enabled:!root.loading && Boolean(root.details.shelves?.after);onClicked:root.load("shelves",root.details.shelves.after)}
                    Controls.CompactIconButton {theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Next page");enabled:!root.loading && Boolean(root.details.shelf_files?.after);onClicked:root.load("shelf_files",root.details.shelf_files.after,root.details.shelf_files.change,root.details.shelf_files.edit_revision)}
                }
                FileWorkspaceChangelistFiles {objectName:"changelistShelvedFiles";theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:140;visible:root.showShelves;rows:root.details.shelf_files?.items || []}
                RowLayout {Layout.fillWidth:true
                    Controls.CompactIconButton {theme:root.theme;iconName:root.showTasks ? "chevron-down" : "chevron-right";toolTip:qsTr("Tasks");onClicked:root.showTasks=!root.showTasks}
                    Label {Layout.fillWidth:true;text:qsTr("Tasks (%1)").arg(root.details.tasks?.items?.length || 0);color:root.theme.primaryText}
                }
                FileWorkspaceChangelistFiles {objectName:"changelistLinkedTasks";theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:125;visible:root.showTasks;tasks:true;rows:root.details.tasks?.items || [];emptyText:root.details.tasks?.unavailable ? qsTr("Task access is restricted") : qsTr("No linked tasks")}
                Label {Layout.fillWidth:true;visible:!root.sameChange;text:qsTr("The selected changelist has changed. Reopen its details.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
            }
        }
        Controls.DockWorkspaceFooter {theme:root.theme;Layout.fillWidth:true
            RowLayout {anchors.fill:parent;anchors.leftMargin:12;anchors.rightMargin:12;spacing:6
                Controls.CompactIconButton {id:actions;objectName:"fileWorkspaceDetailsActions";theme:root.theme;iconName:"more_vert";toolTip:qsTr("Changelist actions");enabled:root.editable && !root.dirty;onClicked:menu.toggleBelowItem(actions)}
                Controls.Button {objectName:"fileWorkspaceDetailsEdit";theme:root.theme;text:qsTr("Edit");icon.name:"edit";visible:!root.editing;enabled:root.editable && !root.loading;onClicked:root.editing=true}
                Controls.Button {objectName:"fileWorkspaceDetailsSave";theme:root.theme;text:qsTr("Save");icon.name:"content-save";highlighted:true;visible:root.editing;enabled:root.editable && root.dirty;onClicked:{root.controller.set_value("description",root.draft);root.controller.action("update_change",{})}}
                Item {Layout.fillWidth:true}
                Controls.Button {objectName:"fileWorkspaceDetailsClose";theme:root.theme;text:qsTr("Close");icon.name:"close";onClicked:root.close()}
            }
        }
    }
    ActionMenu {
        id:menu;objectName:"fileWorkspaceDetailsMenu";theme:root.theme
        actions:[{title:qsTr("Submit"),command:"submit",icon:"publish",enabled:root.editable && !root.dirty},
            {title:qsTr("Shelve"),command:"shelve",icon:"archive",enabled:root.editable && !root.dirty},
            {title:qsTr("Revert changelist"),command:"revert",icon:"undo",enabled:root.editable && !root.dirty}]
        onTriggered:name=>root.command(name)
    }
}
