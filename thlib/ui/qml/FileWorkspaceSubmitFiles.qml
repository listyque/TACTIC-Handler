import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id:root
    required property var theme
    property var rows:[]
    property bool selectable:true
    property bool selectionAll:true
    property var exceptions:[]
    signal toggled(string path, bool selected)
    signal selectAll(bool selected)
    function actionLabel(row) {
        return row.action==="delete" || row.action==="move/delete" ? qsTr("Delete") : row.action==="move/add" ? qsTr("Rename") : row.base ? qsTr("Edit") : qsTr("Add")
    }
    color:theme.panelDeep
    border.color:theme.outlineVariant
    radius:theme.surfaceRadius
    implicitHeight:150
    ColumnLayout {
        anchors.fill:parent;anchors.margins:6;spacing:2
        RowLayout {
            Layout.fillWidth:true
            Controls.CheckBox {objectName:"submitSelectAll";theme:root.theme;visible:root.selectable;checked:root.selectionAll && !root.exceptions.length;Accessible.name:qsTr("Select all files");onToggled:root.selectAll(checked)}
            Label {Layout.fillWidth:true;text:qsTr("File / folder");color:root.theme.secondaryText}
            Label {Layout.preferredWidth:100;text:qsTr("Action");color:root.theme.secondaryText}
        }
        ListView {
            id:list;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:root.rows
            ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:list}
            delegate:RowLayout {
                required property var modelData
                width:list.width-bar.reservedExtent;height:34;spacing:6
                Controls.CheckBox {objectName:"submitFileSelect:"+modelData.path;theme:root.theme;visible:root.selectable;checked:root.selectionAll ? root.exceptions.indexOf(modelData.path)<0 : root.exceptions.indexOf(modelData.path)>=0;Accessible.name:modelData.path;onToggled:root.toggled(modelData.path,checked)}
                Controls.MaterialIcon {name:modelData.action==="delete" || modelData.action==="move/delete" ? "delete" : modelData.base ? "edit" : "add";size:16;color:root.theme.secondaryText}
                Label {Layout.fillWidth:true;Layout.minimumWidth:0;text:modelData.path;textFormat:Text.PlainText;elide:Text.ElideMiddle;color:root.theme.primaryText;ToolTip.visible:hover.hovered;ToolTip.text:text;HoverHandler{id:hover}}
                Label {Layout.preferredWidth:100;text:root.actionLabel(modelData);color:root.theme.secondaryText;elide:Text.ElideRight}
            }
            Label {anchors.centerIn:parent;visible:!list.count;text:qsTr("No files");color:root.theme.secondaryText}
        }
    }
}
