import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id:root
    objectName:"workspaceReviewDialog"
    required property var controller
    property string operation:"shelve"
    property var paths:[]
    property var request:({})
    readonly property var review:controller.view_data.review || ({})
    title:operation==="compare_shelf" ? qsTr("Compare pending with shelf") : ["merge_begin","rebase_begin","unshelve_begin"].indexOf(operation)>=0 ? qsTr("Review integration") : qsTr("Review shelving")
    modal:true
    width:Math.max(240,Math.min(700,parent ? parent.width-24 : 700))
    height:Math.max(180,Math.min(560,parent ? parent.height-24 : 560))
    x:(parent.width-width)/2;y:(parent.height-height)/2
    contentItem:ColumnLayout {
        spacing:6
        Label {Layout.fillWidth:true;text:root.review.number ? qsTr("Changelist #%1").arg(root.review.number)+" · "+(root.review.files_unknown ? (root.review.items || []).length : root.review.files || 0)+" "+(root.review.files_unknown ? qsTr("files on this page") : qsTr("files")) : qsTr("Loading");color:root.theme.primaryText;wrapMode:Text.Wrap}
        Label {Layout.fillWidth:true;visible:Boolean(root.review.source);text:(root.review.source || "")+" → "+(root.review.target || "");color:root.theme.primaryText;wrapMode:Text.Wrap}
        Controls.TextArea {theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:70;text:root.controller.view_data.description;readOnly:true;Accessible.name:qsTr("Changelist description")}
        Label {Layout.fillWidth:true;visible:Boolean(root.review.active_transfer || root.review.integration || root.review.rebase_required);text:root.review.active_transfer ? qsTr("Finish or cancel the upload before submit") : root.review.integration ? qsTr("Resolve all conflicts before submit") : qsTr("Stream head changed; rebase before submit");color:root.theme.error;wrapMode:Text.Wrap}
        Label {Layout.fillWidth:true;visible:root.operation==="shelve_revert";text:qsTr("The shelf is saved before reverting. Local files are kept.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
        ListView {
            id:files;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:root.review.items || []
            ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:files}
            delegate:Controls.EditorListItem {
                required property var modelData
                theme:root.theme;width:files.width-bar.reservedExtent;implicitHeight:32
                text:modelData.path+" · "+(modelData.excluded ? qsTr("Excluded by workspace mapping") : modelData.conflict ? qsTr("Conflict") : modelData.action || "")+(modelData.shelf_status ? " · "+modelData.shelf_status : "")
            }
        }
        RowLayout {
            Layout.fillWidth:true
            Label {Layout.fillWidth:true;text:root.review.after ? qsTr("More files are available on the next page") : "";color:root.theme.secondaryText;wrapMode:Text.Wrap}
            Controls.Button {theme:root.theme;icon.name:"chevron-right";text:qsTr("Next page");enabled:!root.controller.busy && Boolean(root.review.after);onClicked:root.controller.action("review_more",{})}
        }
    }
    footer:RowLayout {
        spacing:6
        Controls.Button {theme:root.theme;icon.name:"close";text:qsTr("Cancel");onClicked:root.close()}
        Item {Layout.fillWidth:true}
        Controls.Button {
            theme:root.theme;icon.name:root.review.kind ? "source-branch" : "archive";text:root.operation==="merge_begin" ? qsTr("Merge stream") : root.operation==="unshelve_begin" ? qsTr("Unshelve") : root.operation==="rebase_begin" ? qsTr("Rebase / resolve") : root.operation==="update_shelf" ? qsTr("Replace shelf files") : qsTr("Shelve")
            visible:root.operation!=="compare_shelf"
            enabled:!root.controller.busy && Boolean(root.review.number) && root.review.editable && !root.review.active_transfer && !root.review.integration && (["merge_begin","unshelve_begin"].indexOf(root.operation)<0 || !root.review.rebase_required)
            onClicked:{root.controller.action(root.operation,Object.assign({},root.request,{review_revision:String(root.review.edit_revision)},root.paths.length ? {paths:root.paths} : {},root.review.preview_head_revision!==undefined ? {preview_head_revision:String(root.review.preview_head_revision),preview_source_root:root.review.preview_source_root} : {}));root.close()}
        }
    }
}
