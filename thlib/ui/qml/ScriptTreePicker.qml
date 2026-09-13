pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Popup {
    id: root

    required property var treeModel
    required property var treeController
    property var scriptOptions: []
    property string currentScript: ""
    signal scriptSelected(string script)

    width: Math.min(420, maximumAvailableWidth)
    height: Math.min(480, maximumAvailableHeight)

    function scriptPath(folder, title) {
        return (String(folder || "") + "/" + String(title || ""))
            .replace(/^\/+|\/+$/g, "")
    }

    function isRunnable(script) {
        for (let index = 0; index < scriptOptions.length; ++index) {
            if (String(scriptOptions[index].value || "") === script)
                return true
        }
        return false
    }

    function iconFor(language) {
        if (language === "local_python" || language === "dcc_python"
                || language === "python")
            return "script-python"
        if (language === "javascript" || language === "server_js")
            return "script-javascript"
        if (language === "expression")
            return "script-expression"
        return "code"
    }

    function iconColor(language) {
        if (language === "local_python")
            return theme.red
        if (language === "dcc_python")
            return theme.cyan
        if (language === "python" || language === "server_js")
            return theme.action
        if (language === "expression")
            return theme.violet
        return theme.secondaryText
    }

    function openFor(sourceItem, script) {
        treeSearch.text = ""
        treeController.set_tree_filter("")
        currentScript = String(script || "")
        openBelowItem(sourceItem, false, 4, 0)
    }

    onAboutToHide: {
        treeSearch.text = ""
        treeController.set_tree_filter("")
    }

    contentItem: ColumnLayout {
        spacing: 4

        Label {
            Layout.fillWidth: true
            Layout.leftMargin: 7
            Layout.rightMargin: 7
            Layout.preferredHeight: 28
            text: qsTr("Choose script")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
            verticalAlignment: Text.AlignVCenter
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.outlineVariant
        }

        Controls.SearchField {
            id: treeSearch
            objectName: "shelfScriptTreeSearch"
            theme: root.theme
            Layout.fillWidth: true
            Layout.leftMargin: 7
            Layout.rightMargin: 7
            placeholderText: qsTr("Search scripts")
            onSearchEdited: query => root.treeController.set_tree_filter(query)
        }

        ListView {
            id: scriptTree
            objectName: "shelfScriptTree"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.rightMargin: treeScrollBar.reservedExtent + 3
            clip: true
            spacing: 1
            boundsBehavior: Flickable.StopAtBounds
            model: root.treeModel
            visible: count > 0

            delegate: Rectangle {
                id: treeRow

                required property string nodeType
                required property string path
                required property string folder
                required property string title
                required property string language
                required property int depth
                required property bool expanded
                required property bool hasChildren

                readonly property string script:
                    root.scriptPath(folder, title)
                readonly property bool selectable:
                    nodeType === "folder" || root.isRunnable(script)

                objectName: "shelfScriptTreeRow_" + nodeType + "_" + title
                width: scriptTree.width
                height: nodeType === "folder" ? 34 : 40
                radius: root.theme.itemRadius
                color: nodeType === "script"
                        && script === root.currentScript
                    ? root.theme.secondaryContainer
                    : treeMouse.containsMouse && selectable
                        ? root.theme.rowHover : "transparent"
                opacity: selectable ? 1 : 0.45

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 7 + treeRow.depth * 14
                    anchors.rightMargin: 7
                    spacing: 6

                    Controls.MaterialIcon {
                        visible: treeRow.nodeType === "folder"
                        name: treeRow.expanded
                            ? "expand-more" : "chevron-right"
                        size: 15
                        color: root.theme.secondaryText
                    }

                    Controls.MaterialIcon {
                        name: treeRow.nodeType === "folder"
                            ? treeRow.expanded ? "folder-open" : "folder"
                            : root.iconFor(treeRow.language)
                        size: 16
                        color: treeRow.nodeType === "folder"
                            ? root.theme.action
                            : root.iconColor(treeRow.language)
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
                            Layout.fillWidth: true
                            visible: treeRow.nodeType === "script"
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
                    enabled: treeRow.selectable
                    hoverEnabled: true
                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: {
                        if (treeRow.nodeType === "folder") {
                            root.treeController.toggle_folder(treeRow.path)
                            return
                        }
                        root.scriptSelected(treeRow.script)
                        root.close()
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                id: treeScrollBar
                objectName: "shelfScriptTreeScrollBar"
                theme: root.theme
                flickableTarget: scriptTree
            }
        }

        Label {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 8
            visible: treeSearch.text.length > 0 && scriptTree.count === 0
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
