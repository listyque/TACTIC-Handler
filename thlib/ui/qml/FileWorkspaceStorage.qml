import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Flickable {
    id:root
    required property var theme
    required property var controller
    readonly property var state:controller.view_data
    readonly property var status:state.storage_info || ({})
    readonly property var draft:state.storage_draft || ({})
    readonly property var gcTask:status.gc || ({})
    readonly property bool gcActive:["queued","running"].includes(gcTask.state)
    readonly property var fields:[
        ["bytes_limit",qsTr("Byte quota"),qsTr("Zero means unlimited.")],
        ["files_limit",qsTr("File quota"),qsTr("Zero means unlimited.")],
        ["max_parallel",qsTr("Parallel transfers"),qsTr("From 1 to 16.")],
        ["upload_retention_seconds",qsTr("Unfinished uploads (seconds)"),qsTr("Zero disables expiration.")],
        ["reverted_retention_seconds",qsTr("Reverted changelists (seconds)"),qsTr("Zero disables expiration.")],
        ["task_retention_seconds",qsTr("Completed tasks (seconds)"),qsTr("Zero disables expiration.")],
        ["shelf_retention_seconds",qsTr("Shelved changelists (seconds)"),qsTr("Zero disables expiration.")],
        ["gc_grace_seconds",qsTr("Quarantine before deletion (seconds)"),qsTr("Unreferenced contents stay in quarantine before physical deletion.")],
        ["gc_interval_seconds",qsTr("Automatic GC interval (seconds)"),qsTr("Zero disables automatic cleanup.")]
    ]
    property string notice:""
    property bool indexing:false
    property bool resetting:false
    function size(value) {for(const unit of ["B","KB","MB","GB","TB"]){if(value<1024 || unit==="TB")return value.toFixed(unit==="B" ? 0 : 1)+" "+unit;value/=1024}}
    function reset() {
        if(resetting || !status.policy_values)return
        if(draft.revision===status.policy_revision && JSON.stringify(draft.policy)===JSON.stringify(status.policy_values) && JSON.stringify(state.storage_original)===JSON.stringify(status.policy_values)){notice="";return}
        resetting=true
        controller.set_value("storage_original",status.policy_values)
        controller.set_value("storage_draft",{revision:status.policy_revision,policy:status.policy_values})
        notice="";resetting=false
    }
    function change(key,value) {const policy=Object.assign({},draft.policy);policy[key]=value;controller.set_value("storage_draft",{revision:draft.revision,policy:policy})}
    function act(operation,dry) {notice="";indexing=operation==="storage_index";controller.action("storage_admin",{operation:operation,dry_run:dry===undefined ? true : dry})}
    function save() {
        for(const field of fields){const value=draft.policy[field[0]];if(!/^[0-9]{1,19}$/.test(value) || (value.length===19 && value>"9223372036854775807") || (field[0]==="max_parallel" && (Number(value)<1 || Number(value)>16))){notice=qsTr("Enter non-negative whole numbers; parallel transfers must be from 1 to 16.");return}}
        act("storage_policy")
    }
    function syncDraft(){if(!draft.policy || JSON.stringify(draft.policy)===JSON.stringify(state.storage_original || {}))reset()}
    Component.onCompleted:Qt.callLater(syncDraft)
    contentWidth:width;contentHeight:layout.implicitHeight+16;clip:true
    ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:root}
    Timer {interval:2000;repeat:true;running:root.visible && root.gcActive && !root.controller.busy;onTriggered:root.act("storage_status")}
    Connections {target:root.controller;function onStateChanged(){if(!root.controller.busy)root.indexing=false;Qt.callLater(root.syncDraft)}}
    ColumnLayout {
        id:layout;x:8;y:8;width:Math.min(660,Math.max(0,root.width-bar.reservedExtent-16));spacing:8
        Label {font.family:root.theme.fontFamily;Layout.fillWidth:true;text:qsTr("Storage administration");color:root.theme.primaryText;font.bold:true;font.pointSize:Controls.Typography.title}
        Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;text:root.size(root.status.allocated_bytes || 0)+" · "+(root.status.allocated_files || 0)+" "+qsTr("files")+" · "+(root.status.indexed ? qsTr("Storage index complete") : qsTr("Storage index incomplete"));color:root.theme.secondaryText;wrapMode:Text.Wrap}
        Flow {
            Layout.fillWidth:true;spacing:8
            Controls.Button {theme:root.theme;text:qsTr("Refresh");icon.name:"refresh";enabled:!root.controller.busy;onClicked:root.act("storage_status")}
            Controls.Button {theme:root.theme;visible:!root.status.initialized;text:qsTr("Initialize storage");enabled:!root.controller.busy;onClicked:root.act("storage_upgrade")}
            Controls.Button {theme:root.theme;visible:Boolean(root.status.initialized) && !root.status.indexed;text:qsTr("Continue storage index");enabled:!root.controller.busy;onClicked:root.act("storage_index")}
            Controls.Button {theme:root.theme;visible:root.indexing && root.controller.busy;text:qsTr("Stop waiting");icon.name:"close";onClicked:root.controller.stop()}
        }
        Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:!root.status.indexed;text:qsTr("Finish indexing before editing the policy or running GC. Indexing can be stopped and continued.")+(root.status.index_table===undefined ? "" : "\n"+qsTr("Table")+": "+root.status.index_table+" · "+(root.status.index_after || ""));color:root.theme.secondaryText;wrapMode:Text.Wrap}
        Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:Boolean(root.notice);text:root.notice;color:root.theme.error;wrapMode:Text.Wrap}
        Repeater {
            model:root.draft.policy ? root.fields : []
            ColumnLayout {
                required property var modelData
                required property int index
                Layout.fillWidth:true;spacing:8
                Label {font.family:root.theme.fontFamily;visible:index===0 || index===3;text:index===0 ? qsTr("Quotas") : qsTr("Retention and cleanup");color:root.theme.primaryText;font.bold:true;font.pointSize:Controls.Typography.title}
                Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;text:modelData[1];color:root.theme.secondaryText}
                Controls.TextField {objectName:"storagePolicy_"+modelData[0];theme:root.theme;Layout.fillWidth:true;text:root.draft.policy[modelData[0]];enabled:!root.controller.busy && Boolean(root.status.indexed);inputMethodHints:Qt.ImhDigitsOnly;Accessible.name:modelData[1];onTextEdited:root.change(modelData[0],text)}
                Label {font.family:root.theme.fontFamily;Layout.fillWidth:true;text:modelData[2];font.pointSize:Controls.Typography.caption;color:root.theme.secondaryText;wrapMode:Text.Wrap}
            }
        }
        Flow {Layout.fillWidth:true;spacing:8;visible:Boolean(root.draft.policy)
            Controls.Button {theme:root.theme;text:qsTr("Reset");icon.name:"undo";enabled:!root.controller.busy;onClicked:root.reset()}
            Controls.Button {theme:root.theme;text:qsTr("Save storage policy");icon.name:"content-save";enabled:!root.controller.busy && Boolean(root.status.indexed);onClicked:root.save()}
        }
        Label {font.family:root.theme.fontFamily;text:qsTr("Garbage collection");color:root.theme.primaryText;font.bold:true;font.pointSize:Controls.Typography.title}
        Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;text:qsTr("Dry run counts unused objects without deleting them. Safe GC expires retained records and quarantines unused contents according to the saved policy.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
        Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:!root.state.catalog_capabilities.files_service_configured;text:qsTr("Enable the files service on the server to process GC tasks.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
        Flow {Layout.fillWidth:true;spacing:8
            Controls.Button {theme:root.theme;text:qsTr("GC dry run");enabled:!root.controller.busy && Boolean(root.status.indexed) && Boolean(root.state.catalog_capabilities.files_service_configured) && !root.gcActive;onClicked:root.act("gc_begin",true)}
            Controls.Button {theme:root.theme;text:qsTr("Run safe GC");enabled:!root.controller.busy && Boolean(root.status.indexed) && Boolean(root.state.catalog_capabilities.files_service_configured) && !root.gcActive;onClicked:confirmGc.open()}
            Controls.Button {theme:root.theme;visible:root.gcActive;text:qsTr("Cancel GC");icon.name:"close";enabled:!root.controller.busy;onClicked:root.act("gc_cancel")}
        }
        Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:Boolean(root.gcTask.code);text:(root.gcTask.code || "")+" · "+qsTr(root.gcTask.state || "")+" · "+(root.gcTask.phase || "")+" · "+(root.gcTask.dry_run ? qsTr("GC dry run") : qsTr("Run safe GC"))+"\n"+qsTr("Objects scanned")+": "+(root.gcTask.objects_done || 0)+" · "+qsTr("Candidates")+": "+(root.gcTask.candidates || 0)+" · "+root.size(root.gcTask.candidate_bytes || 0)+"\n"+qsTr("Expired records")+": "+(root.gcTask.expired || 0)+" · "+qsTr("Quarantined")+": "+(root.gcTask.quarantined || 0)+" · "+qsTr("Purged")+": "+(root.gcTask.purged || 0);color:root.theme.secondaryText;wrapMode:Text.Wrap}
        Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:Boolean(root.gcTask.error);text:root.gcTask.error || "";color:root.theme.error;wrapMode:Text.Wrap}
        Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;Layout.fillWidth:true;visible:root.gcTask.state==="error";text:qsTr("GC stopped. After fixing the cause, start a new dry run or safe GC.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
    }
    Controls.Dialog {
        id:confirmGc;theme:root.theme;parent:Overlay.overlay;modal:true;anchors.centerIn:parent;width:Math.min(480,parent ? parent.width-24 : 480);title:qsTr("Run safe GC")
        contentItem:Label {font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.body;text:qsTr("Run safe GC using the configured retention policy?");color:root.theme.primaryText;wrapMode:Text.Wrap}
        footer:Controls.DialogActions {
            theme:root.theme
            Controls.Button {theme:root.theme;text:qsTr("Cancel");onClicked:confirmGc.close()}
            Controls.Button {theme:root.theme;text:qsTr("Run safe GC");onClicked:{confirmGc.close();root.act("gc_begin",false)}}
        }
    }
}
