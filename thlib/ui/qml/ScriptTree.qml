pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property var treeModel
    property string selectedToken: ""
    signal scriptRequested(string token)
    signal menuRequested(string token, var anchor, real x, real y)

    function scriptIcon(language) {
        if (language === "local_python" || language === "dcc_python"
                || language === "python")
            return "script-python"
        if (language === "javascript" || language === "server_js")
            return "script-javascript"
        if (language === "expression")
            return "script-expression"
        if (language === "xml")
            return "script-xml"
        return "code"
    }

    function scriptIconColor(language) {
        if (language === "local_python")
            return root.theme.red
        if (language === "dcc_python")
            return root.theme.cyan
        if (language === "python" || language === "server_js")
            return root.theme.action
        if (language === "javascript")
            return root.theme.yellow
        if (language === "expression")
            return root.theme.violet
        if (language === "xml")
            return root.theme.cyan
        return root.theme.secondaryText
    }

    Component.onCompleted: root.controller.set_tree_filter("")

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        Controls.SearchField {
            id: treeSearch
            objectName: "scriptEditorTreeSearch"
            theme: root.theme
            Layout.fillWidth: true
            Layout.leftMargin: 3
            Layout.rightMargin: 3
            placeholderText: qsTr("Search scripts")
            onSearchEdited: query => root.controller.set_tree_filter(query)
        }

        ListView {
            id: scripts
            objectName: "scriptEditorTreeList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.treeModel
            visible: count > 0
            clip: true
            spacing: 1
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                id: treeRow

                required property string token
                required property string nodeType
                required property string path
                required property string folder
                required property string title
                required property string language
                required property int depth
                required property bool expanded
                required property bool hasChildren
                width: scripts.width - (treeScrollBar.visible
                    ? treeScrollBar.width + 4 : 0)
                height: 32
                radius: root.theme.itemRadius
                color: root.selectedToken === token
                    ? root.theme.secondaryContainer
                    : treeMouse.containsMouse ? root.theme.rowHover : "transparent"

                Behavior on color {
                    ColorAnimation { duration: root.theme.hoverMotionFast }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6 + treeRow.depth * 14
                    anchors.rightMargin: 5
                    spacing: 5

                    Controls.MaterialIcon {
                        visible: treeRow.nodeType === "folder"
                        name: treeRow.expanded ? "expand_more" : "chevron_right"
                        size: 16
                        color: root.theme.secondaryText
                    }

                    Controls.MaterialIcon {
                        name: treeRow.nodeType === "folder"
                            ? treeRow.expanded ? "folder_open" : "folder"
                            : root.scriptIcon(treeRow.language)
                        size: 16
                        color: treeRow.nodeType === "folder"
                            ? root.theme.action
                            : root.scriptIconColor(treeRow.language)
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0

                        Label {
                            Layout.fillWidth: true
                            text: treeRow.title
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: treeRow.nodeType === "folder"
                                ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                        }

                        Label {
                            visible: treeRow.nodeType === "script"
                            Layout.fillWidth: true
                            text: treeRow.language.replace("_", " ")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            elide: Text.ElideRight
                        }
                    }
                }

                MouseArea {
                    id: treeMouse
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: mouse => {
                        if (mouse.button === Qt.RightButton) {
                            if (treeRow.nodeType === "script")
                                root.menuRequested(
                                    treeRow.token, treeRow, mouse.x, mouse.y)
                            return
                        }
                        if (treeRow.nodeType === "folder")
                            root.controller.toggle_folder(treeRow.path)
                        else
                            root.scriptRequested(treeRow.token)
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                id: treeScrollBar
                objectName: "scriptEditorTreeVerticalScrollBar"
                theme: root.theme
                flickableTarget: scripts
            }
        }

        Label {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 8
            visible: treeSearch.text.length > 0 && scripts.count === 0
            text: qsTr("No scripts found")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.WordWrap
        }
    }
}
