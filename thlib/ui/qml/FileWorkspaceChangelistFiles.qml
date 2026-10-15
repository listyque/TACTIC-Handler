import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "FileWorkspacePresentation.js" as Presentation

Rectangle {
    id:root
    required property var theme
    property var rows:[]
    property bool tasks:false
    property string emptyText:qsTr("No files")
    readonly property var widths:tasks ? [180,140,Math.max(420,width-344)] : [200,Math.max(250,width-624),130,120,150]
    readonly property var headings:tasks ? [qsTr("Task"),qsTr("Status"),qsTr("Description")] : [qsTr("File"),qsTr("In folder"),qsTr("Resolve status"),qsTr("Type"),qsTr("Action")]
    readonly property real tableWidth:widths.reduce((total,value)=>total+value,0)
    color:theme.panelDeep;border.color:theme.outlineVariant;radius:theme.itemRadius
    implicitHeight:190
    function cells(row) {
        if(tasks)return [row.code,row.status,row.description]
        const parts=row.path.split("/"),name=parts.pop()
        const action=row.action || ""
        return [name,parts.join("/") || "/",row.conflict ? qsTr("Conflict") : row.resolved_sha256!==undefined ? qsTr("Resolved") : "—",
            name.lastIndexOf(".")>0 ? name.slice(name.lastIndexOf(".")+1).toUpperCase() : "—",
            action==="delete" || action==="move/delete" ? qsTr("Delete") : action==="move/add" ? qsTr("Rename") : action==="baseline" ? qsTr("Published") : row.base ? qsTr("Edit") : qsTr("Add")]
    }
    ColumnLayout {
        anchors.fill:parent;anchors.margins:6;spacing:2
        Item {Layout.fillWidth:true;Layout.preferredHeight:28;clip:true
            Row {x:-list.contentX
                Repeater {model:root.headings
                    Label {required property int index;required property string modelData;width:root.widths[index];leftPadding:6;text:modelData;color:root.theme.secondaryText;font.family:root.theme.fontFamily;elide:Text.ElideRight}
                }
            }
        }
        ListView {
            id:list;objectName:"changelistContentsList";Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:root.rows
            contentWidth:root.tableWidth;flickableDirection:Flickable.HorizontalAndVerticalFlick;bottomMargin:horizontal.reservedExtent
            ScrollBar.vertical:Controls.ScrollBar {id:vertical;theme:root.theme;flickableTarget:list}
            ScrollBar.horizontal:Controls.ScrollBar {id:horizontal;theme:root.theme;flickableTarget:list}
            delegate:Row {
                id:fileRow
                required property var modelData
                readonly property var values:root.cells(modelData)
                readonly property var badge:root.tasks ? {icon:"task",tone:"action"} : Presentation.badges(modelData)[0]
                width:root.tableWidth;height:32
                Repeater {model:parent.values
                    Label {required property int index;required property string modelData;width:root.widths[index];height:32;leftPadding:index===0 ? 28 : 6;rightPadding:8;text:modelData;textFormat:Text.PlainText;elide:Text.ElideMiddle;verticalAlignment:Text.AlignVCenter;color:root.theme.primaryText;font.family:root.theme.fontFamily
                        HoverHandler {id:cellHover}
                        Controls.ToolTip {theme:root.theme;text:modelData;visible:cellHover.hovered && parent.truncated}
                        Controls.MaterialIcon {visible:index===0;x:5;anchors.verticalCenter:parent.verticalCenter;size:16;name:fileRow.badge.icon;color:Presentation.color(root.theme,fileRow.badge.tone)}
                    }
                }
            }
            Label {anchors.centerIn:parent;visible:!list.count;width:parent.width-vertical.reservedExtent;text:root.emptyText;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.Wrap;color:root.theme.secondaryText}
        }
    }
}
