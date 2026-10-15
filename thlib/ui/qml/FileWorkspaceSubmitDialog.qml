import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id:root
    objectName:"workspaceSubmitDialog"
    required property var controller
    readonly property var state:controller.view_data
    readonly property var review:state.review || ({})
    readonly property var context:state.submit_review || ({})
    property string draft:""
    property bool selectionAll:true
    property var exceptions:[]
    property var selectedTasks:[]
    property string taskStatus:""
    property bool tasksInitialized:false
    property bool closeAfterSave:false
    property string savedToken:""
    property string notice:""
    readonly property bool ready:!controller.busy && Boolean(review.number) && review.editable && !review.active_transfer && !review.integration && !review.rebase_required && review.waiting_uploads!==null
    readonly property var taskChoices: [{value:"",label:qsTr("Keep current status")}].concat(selectedTasks.length ? (selectedTasks[0].statuses || []).filter(choice=>selectedTasks.every(task=>(task.statuses || []).some(item=>item.value===choice.value))) : [])
    readonly property var taskRows:selectedTasks.concat((context.tasks?.items || []).filter(task=>!selectedTasks.some(item=>item.code===task.code)))
    function initializeTasks() {
        if(tasksInitialized || !visible || controller.busy || context.change!==state.change.code)return
        tasksInitialized=true
        selectedTasks=context.tasks?.linked || []
        const updates=state.change.task_status_updates || []
        taskStatus=updates.length && updates.every(item=>item.status===updates[0].status) ? updates[0].status : ""
    }
    onReadyChanged:initializeTasks()
    function settings() {
        return {description:draft,restricted:restricted.checked,task_codes:selectedTasks.map(task=>task.code),
            task_status_updates:taskStatus ? selectedTasks.map(task=>({code:task.code,status:taskStatus,revision:task.revision})) : []}
    }
    function selectFile(path,checked) {
        const values=exceptions.filter(item=>item!==path)
        if(checked!==selectionAll)values.push(path)
        if(values.length>1000){notice=qsTr("Select at most 1000 exceptions, or switch Select all.");return}
        exceptions=values
    }
    function save(close) {
        closeAfterSave=close;savedToken=context.saved || ""
        controller.action("submit_save",Object.assign(settings(),{review_revision:String(review.edit_revision)}))
    }
    parent:Overlay.overlay
    modal:true;draggable:true;closePolicy:Popup.CloseOnEscape
    width:Math.min(960,parent ? parent.width-24 : 960)
    height:Math.min(1000,parent ? parent.height-24 : 1000)
    title:qsTr("Submit changelist #%1").arg(state.change.number || "")
    onAboutToShow: {
        x=Qt.binding(()=>Math.max(0,(parent.width-width)/2));y=Qt.binding(()=>Math.max(0,(parent.height-height)/2))
        draft=state.description;tasksInitialized=false;selectionAll=true;exceptions=[];selectedTasks=[];taskStatus="";notice="";closeAfterSave=false
        restricted.checked=Boolean(state.change.restricted);reopen.checked=false;guard.checked=false;unchanged.currentIndex=1
        Qt.callLater(initializeTasks)
    }
    onContextChanged: {
        if(closeAfterSave && context.saved && context.saved!==savedToken){closeAfterSave=false;root.close()}
        initializeTasks()
    }
    contentItem:Flickable {
        id:body;objectName:"submitBody";clip:true;contentHeight:contents.implicitHeight;boundsBehavior:Flickable.StopAtBounds
        ScrollBar.vertical:Controls.ScrollBar {id:bodyBar;theme:root.theme;flickableTarget:body}
        ColumnLayout {
            id:contents;width:body.width-bodyBar.reservedExtent;spacing:8
            Label {text:qsTr("Changelist description");color:root.theme.primaryText}
            Controls.TextArea {objectName:"submitDescription";theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:80;wrapMode:TextEdit.Wrap;text:root.draft;Accessible.name:qsTr("Changelist description");onTextChanged:if(activeFocus)root.draft=text}
            Label {Layout.fillWidth:true;visible:Boolean(root.state.error || root.notice);text:root.notice || root.state.error;wrapMode:Text.Wrap;color:root.theme.error}
            Label {Layout.fillWidth:true;visible:Boolean(root.review.active_transfer || root.review.integration || root.review.rebase_required);text:root.review.active_transfer ? qsTr("Finish or cancel the upload before submit") : root.review.integration ? qsTr("Resolve all conflicts before submit") : qsTr("Stream head changed; rebase before submit");color:root.theme.error;wrapMode:Text.Wrap}
            Label {Layout.fillWidth:true;text:root.controller.busy ? qsTr("Preparing submit…") : qsTr("Choose files to submit (%1)").arg(root.review.files || 0);color:root.theme.primaryText}
            FileWorkspaceSubmitFiles {objectName:"submitPendingFiles";theme:root.theme;Layout.fillWidth:true;rows:root.review.items || [];selectionAll:root.selectionAll;exceptions:root.exceptions;onToggled:(path,selected)=>root.selectFile(path,selected);onSelectAll:selected=>{root.selectionAll=selected;root.exceptions=[]}}
            RowLayout {Layout.fillWidth:true
                Label {Layout.fillWidth:true;text:qsTr("Unchecked files remain pending. Local files are kept.");wrapMode:Text.Wrap;color:root.theme.secondaryText}
                Controls.CompactIconButton {theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Next page");enabled:!root.controller.busy && Boolean(root.review.after);onClicked:root.controller.action("review_more",{})}
            }
            RowLayout {Layout.fillWidth:true
                Label {text:qsTr("Shelved files");color:root.theme.primaryText}
                Controls.ComboBox {id:shelf;theme:root.theme;Layout.fillWidth:true;model:(root.context.shelves?.items || []).map(item=>Object.assign({},item,{label:"#"+item.number}));textRole:"label";translateDisplayText:false;currentIndex:model.length ? Math.max(0,model.findIndex(item=>item.code===root.context.shelf_files?.change)) : -1;Accessible.name:qsTr("Shelf changelist");onActivated:root.controller.action("submit_shelf_files",{shelf:model[currentIndex].code})}
                Controls.CompactIconButton {theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Next shelves");enabled:!root.controller.busy && Boolean(root.context.shelves?.after);onClicked:root.controller.action("submit_shelves",{after:root.context.shelves.after})}
            }
            FileWorkspaceSubmitFiles {objectName:"submitShelvedFiles";theme:root.theme;Layout.fillWidth:true;implicitHeight:120;selectable:false;rows:root.context.shelf_files?.items || []}
            RowLayout {Layout.fillWidth:true
                Label {Layout.fillWidth:true;text:qsTr("Shelves are separate snapshots and are kept after submit.");wrapMode:Text.Wrap;color:root.theme.secondaryText}
                Controls.CompactIconButton {theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Next page");enabled:!root.controller.busy && Boolean(root.context.shelf_files?.after);onClicked:root.controller.action("submit_shelf_files",{shelf:root.context.shelf_files.change,after:root.context.shelf_files.after})}
            }
            Label {text:qsTr("Additional options");color:root.theme.primaryText}
            Controls.CheckBox {id:guard;objectName:"submitGuardResolved";theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0;compact:true;wrapText:true;text:qsTr("Do not submit if resolved files have been modified")}
            Controls.CheckBox {id:reopen;objectName:"submitReopen";theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0;compact:true;wrapText:true;text:qsTr("Check out submitted files after submit")}
            Controls.CheckBox {id:restricted;objectName:"submitRestricted";theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0;compact:true;wrapText:true;text:qsTr("Restrict access to changelist")}
            Label {Layout.fillWidth:true;visible:restricted.checked;text:qsTr("Only the owner and administrators can view changelist details. Depot file permissions do not change.");wrapMode:Text.Wrap;color:root.theme.secondaryText}
            RowLayout {Layout.fillWidth:true
                Label {text:qsTr("On submit");color:root.theme.secondaryText}
                Controls.ComboBox {id:unchanged;objectName:"submitUnchangedPolicy";theme:root.theme;Layout.fillWidth:true;model:[qsTr("Submit all selected files"),qsTr("Revert unchanged files"),qsTr("Leave unchanged files pending")]}
            }
            Label {text:qsTr("Link tasks to changelist (optional)");color:root.theme.primaryText}
            RowLayout {Layout.fillWidth:true
                Controls.TextField {id:query;objectName:"submitTaskSearch";theme:root.theme;Layout.fillWidth:true;placeholderText:qsTr("Find tasks by code or description");onAccepted:root.controller.action("submit_tasks",{query:text})}
                Controls.CompactIconButton {theme:root.theme;iconName:"search";toolTip:qsTr("Search tasks");enabled:!root.controller.busy;onClicked:root.controller.action("submit_tasks",{query:query.text})}
                Controls.CompactIconButton {theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Next tasks");enabled:!root.controller.busy && Boolean(root.context.tasks?.after);onClicked:root.controller.action("submit_tasks",{query:query.text,after:root.context.tasks.after})}
            }
            ListView {
                id:tasks;objectName:"submitTaskList";Layout.fillWidth:true;Layout.preferredHeight:110;clip:true;model:root.taskRows
                ScrollBar.vertical:Controls.ScrollBar {id:taskBar;theme:root.theme;flickableTarget:tasks}
                delegate:RowLayout {
                    required property var modelData
                    width:tasks.width-taskBar.reservedExtent;height:36
                    Controls.CheckBox {objectName:"submitTaskSelect:"+modelData.code;theme:root.theme;checked:root.selectedTasks.some(task=>task.code===modelData.code);Accessible.name:modelData.code;onToggled:{if(checked && root.selectedTasks.length>=100){root.notice=qsTr("Choose at most 100 linked tasks");checked=false;return}root.selectedTasks=checked ? root.selectedTasks.concat([modelData]) : root.selectedTasks.filter(task=>task.code!==modelData.code);root.taskStatus=""}}
                    Label {Layout.fillWidth:true;Layout.minimumWidth:0;text:modelData.code+" · "+modelData.description;textFormat:Text.PlainText;elide:Text.ElideRight;color:root.theme.primaryText}
                    Label {text:modelData.status;color:root.theme.secondaryText}
                }
                Label {anchors.centerIn:parent;visible:!tasks.count;text:qsTr("No tasks. Create tasks in Task Manager.");color:root.theme.secondaryText;wrapMode:Text.Wrap;width:parent.width}
            }
            Label {Layout.fillWidth:true;text:qsTr("Selected tasks: %1").arg(root.selectedTasks.length);color:root.theme.secondaryText}
            RowLayout {Layout.fillWidth:true
                Label {text:qsTr("Status after submit");color:root.theme.secondaryText}
                Controls.ComboBox {objectName:"submitTaskStatus";theme:root.theme;Layout.fillWidth:true;model:root.taskChoices;textRole:"label";translateDisplayText:false;valueRole:"value";currentIndex:Math.max(0,root.taskChoices.findIndex(item=>item.value===root.taskStatus));enabled:root.selectedTasks.length>0;onActivated:root.taskStatus=currentValue}
            }
        }
    }
    footer:Controls.DialogActions {
        theme:root.theme
        GridLayout {columns:root.width<550 ? 2 : 4
            Controls.Button {objectName:"submitCancel";theme:root.theme;text:qsTr("Cancel");icon.name:"close";onClicked:root.reject()}
            Controls.Button {objectName:"submitSave";theme:root.theme;text:qsTr("Save");icon.name:"content-save";enabled:root.ready;onClicked:root.save(true)}
            Controls.Button {objectName:"submitApply";theme:root.theme;text:qsTr("Apply");enabled:root.ready;onClicked:root.save(false)}
            Controls.Button {objectName:"submitAccept";theme:root.theme;text:qsTr("Submit");icon.name:"publish";highlighted:true;enabled:root.ready && (root.selectionAll || root.exceptions.length>0)
                onClicked:{root.controller.action("submit",Object.assign(root.settings(),{review_revision:String(root.review.edit_revision),submit_options:{selection_all:root.selectionAll,selection_paths:root.exceptions,guard_resolved:guard.checked,reopen:reopen.checked,unchanged:["submit","revert","leave"][unchanged.currentIndex]}}));root.close()}
            }
        }
    }
}
