import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id:root
    objectName:"workspaceComparisonDialog"
    required property var controller
    readonly property var comparison:controller.view_data.comparison || ({})
    title:qsTr("File comparison")
    modal:false
    width:Math.max(260,Math.min(900,parent ? parent.width-24 : 900))
    height:Math.max(180,Math.min(600,parent ? parent.height-24 : 600))
    x:parent ? (parent.width-width)/2 : 0;y:parent ? (parent.height-height)/2 : 0
    signal externalRequested()
    contentItem:ColumnLayout {
        Repeater {
            model:[root.comparison.left || ({}),root.comparison.right || ({})]
            delegate:Label {
                required property var modelData
                Layout.fillWidth:true;text:(modelData.path || "")+" · "+(modelData.size || 0)+" "+qsTr("bytes")+(modelData.sha256 ? " · SHA-256 "+modelData.sha256 : "")
                color:root.theme.secondaryText;wrapMode:Text.Wrap;textFormat:Text.PlainText
            }
        }
        Label {Layout.fillWidth:true;visible:root.comparison.kind!=="text";text:qsTr("Binary or large file. Use an external comparison application.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
        ScrollView {
            id:scroll;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;contentWidth:availableWidth
            ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme}
            Controls.TextArea {theme:root.theme;width:scroll.availableWidth-bar.reservedExtent;text:root.comparison.text || (root.comparison.identical===true ? qsTr("No differences.") : "");readOnly:true;font.family:"Consolas";Accessible.name:qsTr("Comparison result")}
        }
    }
    footer:RowLayout {
        Controls.Button {theme:root.theme;icon.name:"compare";text:qsTr("Compare with application…");enabled:!root.controller.busy;onClicked:root.externalRequested()}
        Item {Layout.fillWidth:true}
        Controls.Button {theme:root.theme;icon.name:"close";text:qsTr("Close");onClicked:root.close()}
    }
}
