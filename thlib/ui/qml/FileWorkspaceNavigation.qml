import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id:root
    required property var theme
    required property var controller
    readonly property var state:controller.view_data
    readonly property bool compact:width<240
    signal menuRequested(string kind,var anchor)
    spacing:4

    RowLayout {
        Layout.fillWidth:true;spacing:4
        Controls.Button {id:actions;theme:root.theme;compact:root.compact;toolTip:text;Accessible.name:text;text:qsTr("Actions");icon.name:"play-arrow";onClicked:root.menuRequested("actions",actions)}
        Controls.Button {id:tools;theme:root.theme;compact:root.compact;toolTip:text;Accessible.name:text;text:qsTr("Tools");icon.name:"settings";onClicked:root.menuRequested("tools",tools)}
        Item {Layout.fillWidth:true}
    }
    Controls.ComboBox {
        objectName:"fileWorkspaceSelector";theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0
        model:root.state.workspaces;textRole:"code";valueRole:"code";translateDisplayText:false
        currentIndex:root.state.workspaces.findIndex(row=>row.code===root.state.workspace)
        enabled:!root.controller.busy;Accessible.name:qsTr("Workspace")
        onActivated:root.controller.action("preview_workspace_switch",{workspace:currentValue})
    }
    RowLayout {
        Layout.fillWidth:true;spacing:2
        Controls.CompactIconButton {theme:root.theme;iconName:"chevron-left";toolTip:qsTr("Back");enabled:root.state.navigation_index>0;onClicked:root.controller.set_navigation(-1)}
        Controls.CompactIconButton {theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Forward");enabled:root.state.navigation_index+1<root.state.navigation.length;onClicked:root.controller.set_navigation(1)}
        Controls.CompactIconButton {theme:root.theme;iconName:"folder-open";toolTip:qsTr("Parent folder");onClicked:root.controller.action("navigate",{path:"//"+root.state.stream+"/"+root.state.prefix.replace(/\/?[^/]+\/?$/,"")})}
        Controls.TextField {theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0;Accessible.name:qsTr("Workspace or depot path");text:"//"+root.state.stream+"/"+root.state.prefix;onAccepted:root.controller.action("navigate",{path:text})}
    }
    Controls.CompactIconButton {objectName:"workspaceResumeOperation";theme:root.theme;iconName:"restore";toolTip:qsTr("Resume interrupted operation");Accessible.name:toolTip;visible:Boolean(root.state.recovery.available || root.state.recovery.action);enabled:!root.controller.busy;onClicked:root.controller.action("resume_operation",{})}
    Label {visible:root.state.connection_state==="offline" || root.state.connection_state==="recovery_available";Layout.fillWidth:true;wrapMode:Text.Wrap;text:root.state.connection_state==="offline" ? qsTr("Connection lost; work retained") : qsTr("Interrupted operation available to resume");color:root.theme.yellow}
}
