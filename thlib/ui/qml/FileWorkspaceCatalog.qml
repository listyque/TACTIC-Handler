import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id:root
    required property var theme
    required property var controller
    readonly property var state:controller.view_data
    property var detail:state.catalog_detail || ({})
    color:theme.panelDeep;radius:theme.surfaceRadius;border.color:theme.outlineVariant
    function choose(row) { detail=row;controller.set_value("catalog_detail",row) }
    FileWorkspaceDepots {anchors.fill:parent;theme:root.theme;controller:root.controller;visible:root.state.catalog_source==="depots"}
    FileWorkspaceStorage {anchors.fill:parent;theme:root.theme;controller:root.controller;visible:root.state.catalog_source==="storage"}
    ColumnLayout {
        visible:!["depots","storage"].includes(root.state.catalog_source)
        anchors.fill:parent;anchors.margins:8;spacing:6
        RowLayout {
            Layout.fillWidth:true
            Label {Layout.fillWidth:true;text:qsTr("Server metadata");color:root.theme.primaryText;font.family:root.theme.fontFamily}
            Controls.CompactIconButton {theme:root.theme;iconName:"refresh";toolTip:qsTr("Refresh");enabled:!root.controller.busy;onClicked:root.controller.action("catalog_page",{})}
            Controls.Button {theme:root.theme;icon.name:"chevron-right";text:qsTr("Next page");enabled:!root.controller.busy;visible:Boolean(root.state.catalog_after);onClicked:root.controller.action("catalog_page",{more:true})}
        }
        SplitView {
            Layout.fillWidth:true;Layout.fillHeight:true
            orientation:root.width<600 ? Qt.Vertical : Qt.Horizontal
            handle:Controls.SplitterHandle {theme:root.theme;vertical:root.width>=600}
            ListView {
                id:rows;SplitView.fillWidth:true;SplitView.fillHeight:true;SplitView.minimumWidth:Math.min(180,root.width*0.4);clip:true
                model:root.controller.catalog_model
                ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:rows}
                delegate:Controls.EditorListItem {
                    required property var node
                    theme:root.theme;width:rows.width-bar.reservedExtent
                    text:node.code
                    description:[node.depot,node.stream,node.owner,node.local_root,node.parent ? qsTr("Parent: %1").arg(node.parent) : ""].filter(value=>value).join(" · ")
                    iconName:root.state.catalog_source==="workspaces" ? "desktop" : root.state.catalog_source==="depots" ? "database" : "source-branch"
                    selected:root.detail.code===node.code
                    onClicked:root.choose(node)
                }
                Label {anchors.centerIn:parent;visible:rows.count===0 && root.state.catalog_source!=="storage";text:qsTr("No permitted records on this page");color:root.theme.secondaryText;wrapMode:Text.Wrap;width:parent.width;horizontalAlignment:Text.AlignHCenter}
            }
            Flickable {
                id:info;SplitView.preferredWidth:root.width*0.45;SplitView.preferredHeight:root.height*0.4
                SplitView.minimumWidth:0;SplitView.minimumHeight:Math.min(80,root.height*0.2)
                contentWidth:width;contentHeight:recordText.implicitHeight;clip:true
                ScrollBar.vertical:Controls.ScrollBar {id:infoBar;theme:root.theme;flickableTarget:info}
                Controls.TextArea {id:recordText;theme:root.theme;width:Math.max(0,info.width-infoBar.reservedExtent);text:JSON.stringify(root.detail,null,2);readOnly:true;Accessible.name:qsTr("Selected server record")}
            }
        }
        RowLayout {
            Layout.fillWidth:true
            Controls.Button {theme:root.theme;text:qsTr("Switch workspace");icon.name:"desktop";visible:root.state.catalog_source==="workspaces";enabled:Boolean(root.detail.code) && !root.controller.busy;onClicked:root.controller.action("preview_workspace_switch",{workspace:root.detail.code})}
            Controls.Button {theme:root.theme;text:qsTr("Edit workspace");icon.name:"edit";visible:root.state.catalog_source==="workspaces";enabled:root.detail.code===root.state.workspace && !root.controller.busy;onClicked:root.controller.action("edit_workspace",{})}
            Controls.Button {theme:root.theme;text:qsTr("Workspace setup");icon.name:"add";visible:root.state.catalog_source==="workspaces";enabled:!root.controller.busy;onClicked:root.controller.set_value("setup",true)}
        }
    }
}
