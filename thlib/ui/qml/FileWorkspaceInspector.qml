import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root
    required property var theme
    required property var info
    required property var preview
    required property string currentTab
    property bool historyMode: false
    property bool busy: false
    property string error: ""
    readonly property var file: info.file || ({})
    readonly property bool hasFile: Boolean(info.path)
    readonly property var tabs: [{id:"details",title:qsTr("Details")},
        historyMode ? {id:"integrations",title:qsTr("Integrations")} : {id:"checkout",title:qsTr("Checked Out By")},
        {id:"preview",title:qsTr("Preview")}]
    readonly property var details: historyMode ? [
        [qsTr("Date submitted"),date(info.submitted_at)], [qsTr("Changelist"),change()],
        [qsTr("Submitted by"),info.author || "—"], [qsTr("Type"),type()],
        [qsTr("Workspace"),info.workspace || "—"], [qsTr("File size"),size()],
        [qsTr("Action"),info.action || "—"]] : [
        [qsTr("Workspace location"),info.workspace_location || info.local_path || "—"],
        [qsTr("Depot location"),"//"+info.stream+"/"+info.path],
        [qsTr("Revision"),"#"+(file.number || "—")+" · Have #"+(info.have?.number || "—")+" · Head #"+(info.head?.number || "—")],
        [qsTr("Local modification date"),info.local_modified_ns ? date(info.local_modified_ns/1000) : "—"],
        [qsTr("Submitted at"),date(info.submitted_at)], [qsTr("File size"),size()],
        [qsTr("Author"),info.author || "—"], [qsTr("Changelist"),change()],
        [qsTr("Type"),type()], ["SHA-256",file.sha256 || "—"],
        [qsTr("Integration source"),info.provenance ? info.provenance.stream+" · "+info.provenance.change+" · "+info.provenance.version : "—"]]
    signal tabSelected(string tab)

    function date(value) {return value ? Qt.formatDateTime(new Date(value/1000),"dd.MM.yyyy HH:mm:ss") : "—"}
    function change() {return info.change_number ? "#"+info.change_number : "—"}
    function type() {const path=info.path || "";return file.file_type || (path.lastIndexOf(".")>path.lastIndexOf("/") ? path.slice(path.lastIndexOf(".")+1).toUpperCase() : "—")}
    function size() {const value=file.size ?? info.local_size ?? 0;return value<1024 ? value+" B" : value<1048576 ? (value/1024).toFixed(1)+" KiB" : (value/1048576).toFixed(1)+" MiB"}

    objectName: historyMode ? "historyRevisionInspector" : "workspaceFileInspector"
    color: theme.panelDeep
    clip: true
    ColumnLayout {
        anchors.fill:parent;anchors.margins:8;spacing:4
        RowLayout {
            Layout.fillWidth:true
            Repeater {
                model:root.tabs
                Controls.TabButton {
                    required property var modelData
                    objectName:(root.historyMode ? "historyTab_" : "fileInspectorTab_")+modelData.id
                    theme:root.theme;text:modelData.title;checked:root.currentTab===modelData.id
                    Layout.fillWidth:root.width<500;Layout.preferredWidth:root.width<500 ? 1 : implicitWidth;Layout.minimumWidth:root.width<500 ? 0 : implicitWidth
                    onClicked:root.tabSelected(modelData.id)
                }
            }
            Item {Layout.fillWidth:true}
            Controls.BusyIndicator {uiTheme:root.theme;running:root.busy;visible:running}
        }
        Label {
            Layout.fillWidth:true;visible:!root.hasFile || Boolean(root.error)
            text:root.error || (root.historyMode ? qsTr("Select a revision") : qsTr("Select a file to inspect"))
            color:root.error ? root.theme.error : root.theme.secondaryText;textFormat:Text.PlainText;wrapMode:Text.Wrap
        }
        Flickable {
            id:scroll;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;contentWidth:width;contentHeight:fields.implicitHeight+8
            ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:scroll}
            ColumnLayout {
                id:fields;width:Math.max(0,scroll.width-bar.reservedExtent);spacing:6;visible:root.hasFile
                ColumnLayout {
                    Layout.fillWidth:true;visible:root.currentTab==="details"
                    Label {Layout.fillWidth:true;visible:root.historyMode;text:root.hasFile ? "//"+root.info.stream+"/"+root.info.path+"#"+root.file.number : "";textFormat:Text.PlainText;elide:Text.ElideMiddle;color:root.theme.primaryText}
                    GridLayout {
                        Layout.fillWidth:true;columns:width<650 ? 1 : 2;columnSpacing:20;rowSpacing:4
                        Repeater {
                            model:root.details
                            RowLayout {
                                required property var modelData
                                Layout.fillWidth:true
                                Label {Layout.preferredWidth:Math.min(145,root.width*0.3);text:modelData[0];elide:Text.ElideRight;color:root.theme.secondaryText}
                                Controls.TextField {
                                    theme:root.theme;tableCell:true;readOnly:true;Accessible.name:modelData[0]
                                    Layout.fillWidth:true;Layout.minimumWidth:0;Layout.preferredHeight:root.theme.compactControlHeight
                                    text:String(modelData[1])
                                    HoverHandler {id:hover}
                                    Controls.ToolTip {theme:root.theme;text:parent.text;visible:hover.hovered && parent.contentWidth>parent.width-parent.leftPadding-parent.rightPadding}
                                }
                            }
                        }
                    }
                    Label {text:qsTr("Description");color:root.theme.secondaryText}
                    Controls.TextArea {objectName:root.historyMode ? "historyRevisionDescription" : "fileInspectorDescription";theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:85;text:root.info.description || "";readOnly:true;wrapMode:TextEdit.Wrap;textFormat:TextEdit.PlainText;Accessible.name:qsTr("Description")}
                }
                ColumnLayout {
                    Layout.fillWidth:true;visible:root.currentTab==="integrations"
                    Label {visible:!root.info.provenance;text:qsTr("No integration source for this revision");color:root.theme.secondaryText}
                    Repeater {
                        model:root.info.provenance ? [[qsTr("Stream"),root.info.provenance.stream],[qsTr("Changelist"),root.info.provenance.change],[qsTr("Revision"),root.info.provenance.version]] : []
                        Label {required property var modelData;Layout.fillWidth:true;text:modelData[0]+": "+modelData[1];textFormat:Text.PlainText;wrapMode:Text.Wrap;color:root.theme.primaryText}
                    }
                }
                ColumnLayout {
                    Layout.fillWidth:true;visible:root.currentTab==="checkout"
                    Label {visible:!(root.info.holders || []).length;text:qsTr("No active checkout");color:root.theme.secondaryText}
                    Repeater {
                        model:root.info.holders || []
                        RowLayout {
                            required property var modelData
                            Layout.fillWidth:true
                            Controls.MaterialIcon {name:modelData.mode==="exclusive" ? "lock" : "lock-open-variant";color:root.theme.action;size:18}
                            Label {Layout.fillWidth:true;text:modelData.owner+" · "+modelData.workspace+" · #"+(modelData.number || modelData.change)+" · "+(modelData.mode==="exclusive" ? qsTr("Exclusive checkout") : qsTr("Ordinary checkout"));color:root.theme.primaryText;wrapMode:Text.Wrap;textFormat:Text.PlainText}
                        }
                    }
                }
                ColumnLayout {
                    Layout.fillWidth:true;visible:root.currentTab==="preview"
                    Label {Layout.fillWidth:true;visible:!root.preview.kind || Boolean(root.preview.error);text:root.preview.error || (root.busy ? qsTr("Loading preview…") : qsTr("No content available for this file"));color:root.preview.error ? root.theme.error : root.theme.secondaryText;wrapMode:Text.Wrap}
                    Label {visible:root.preview.kind==="binary" || Boolean(root.preview.truncated);text:(root.preview.kind==="binary" ? qsTr("Binary file") : "")+(root.preview.truncated ? " · "+qsTr("Preview shows the first 256 KiB") : "");color:root.theme.secondaryText}
                    Controls.TextArea {objectName:root.historyMode ? "historyRevisionPreview" : "fileInspectorPreview";theme:root.theme;Layout.fillWidth:true;Layout.preferredHeight:Math.max(120,scroll.height-36);visible:["text","binary"].indexOf(root.preview.kind)>=0;text:root.preview.text || "";readOnly:true;textFormat:TextEdit.PlainText;Accessible.name:qsTr("File preview")}
                    Image {visible:root.preview.kind==="image";Layout.fillWidth:true;Layout.preferredHeight:Math.max(120,scroll.height-36);source:visible ? root.preview.image || "" : "";fillMode:Image.PreserveAspectFit;sourceSize.width:1024;sourceSize.height:1024}
                }
            }
        }
    }
}
