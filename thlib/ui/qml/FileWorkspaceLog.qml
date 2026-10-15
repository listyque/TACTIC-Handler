import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root
    objectName: "fileWorkspaceLog"
    required property var theme
    required property var controller
    color: theme.panelDeep
    border.color: theme.outlineVariant
    radius: theme.surfaceRadius

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 4
        spacing: 2
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            Controls.MaterialIcon { name:"terminal";size:16;color:root.theme.secondaryText }
            Label { text:qsTr("Log");Layout.fillWidth:true;color:root.theme.primaryText;font.family:root.theme.fontFamily }
            Controls.CompactIconButton {theme:root.theme;iconName:"copy";toolTip:qsTr("Copy log");onClicked:root.controller.copy_log()}
            Controls.CompactIconButton {objectName:"fileWorkspaceClearLog";theme:root.theme;iconName:"delete";toolTip:qsTr("Clear log");onClicked:root.controller.clear_log()}
            Controls.CompactIconButton {theme:root.theme;iconName:"bug-report";toolTip:qsTr("Debug Log");onClicked:root.controller.open_debug_log()}
            Controls.CompactIconButton {objectName:"fileWorkspaceHideLog";theme:root.theme;iconName:"close";toolTip:qsTr("Hide log");Accessible.name:toolTip;onClicked:root.controller.set_value("log_visible",false)}
        }
        ListView {
            id: entries
            objectName: "fileWorkspaceLogEntries"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.controller.log_model
            Accessible.role: Accessible.List
            Accessible.name: qsTr("Operation log")
            ScrollBar.vertical: Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:entries}
            onCountChanged: if(count)Qt.callLater(entries.positionViewAtEnd)
            delegate: RowLayout {
                required property string time
                required property string level
                required property string operation
                required property string message
                required property string path
                width:entries.width-bar.reservedExtent
                spacing:6
                Controls.MaterialIcon {name:level==="ERROR" ? "error" : level==="WARNING" ? "warning" : "info";size:16;color:level==="ERROR" ? root.theme.error : level==="WARNING" ? root.theme.yellow : root.theme.secondaryText}
                Controls.TextArea {
                    theme:root.theme
                    implicitHeight:contentHeight
                    leftPadding:0;rightPadding:0;topPadding:0;bottomPadding:0
                    background:Item {}
                    objectName: "fileWorkspaceLogMessage"
                    Layout.fillWidth:true
                    readOnly:true;selectByMouse:true;wrapMode:TextEdit.Wrap
                    textFormat:TextEdit.PlainText
                    text:parent.time+" · "+parent.operation+" · "+parent.message+(parent.path ? "\n"+parent.path : "")
                    color:parent.level==="ERROR" ? root.theme.error : root.theme.primaryText
                    font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.label
                    Accessible.name:text
                }
            }
        }
    }
}
