import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property string windowId: ""
    property int selectedRow: 0
    property int modelRevision: 0

    Component.onCompleted: repositoryEditorController.begin_edit()
    Connections {
        target: repositoryEditorModel
        function onDataChanged() { root.modelRevision += 1 }
        function onContentReplaced() { root.modelRevision += 1 }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Rectangle {
            Layout.preferredWidth: Math.min(220, root.width * 0.34)
            Layout.fillHeight: true
            radius: 12
            color: root.theme.panelRaised
            border.color: root.theme.border

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("REPOSITORIES")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                        leftPadding: 8
                        topPadding: 6
                        bottomPadding: 4
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "add"
                        round: false
                        toolTip: qsTr("Add custom repository")
                        onClicked: {
                            repositoryEditorController.add_custom_repository()
                            root.selectedRow = repositoryEditorModel.count() - 1
                        }
                    }
                }
                ListView {
                    id: repositoryList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: repositoryEditorModel
                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: repositoryList
                    }
                    delegate: Rectangle {
                        required property int index
                        required property string title
                        required property string code
                        required property bool active
                        width: repositoryList.width
                        height: 54
                        radius: 10
                        color: root.selectedRow === index
                            ? root.theme.selected : mouse.containsMouse
                                ? root.theme.rowHover : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 9
                            Rectangle {
                            implicitWidth: 8
                            implicitHeight: 8
                                radius: 4
                                color: active ? root.theme.accent
                                    : root.theme.secondaryText
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    Layout.fillWidth: true
                                    text: title
                                    elide: Text.ElideRight
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.bodyLarge
                                    font.weight: Font.DemiBold
                                }
                                Label {
                                    text: code
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                }
                            }
                        }
                        MouseArea {
                            id: mouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.selectedRow = index
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 12
            color: root.theme.workspace
            border.color: root.theme.border

            Loader {
                anchors.fill: parent
                anchors.margins: 16
                sourceComponent: editorComponent
            }
        }
    }

    Component {
        id: editorComponent
        Item {
            property var record: {
                root.modelRevision
                return repositoryEditorModel.get(root.selectedRow)
            }

            ColumnLayout {
                anchors.fill: parent
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label {
                            text: record.title || qsTr("Repository")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 17
                            font.weight: Font.DemiBold
                        }
                        Label {
                            text: qsTr("Paths are stored in the active server preset")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                        }
                    }
                    Controls.CheckBox {
                        theme: root.theme
                        text: qsTr("Enabled")
                        checked: Boolean(record.active)
                        onToggled: repositoryEditorModel.set_value(
                            root.selectedRow, "active", checked
                        )
                    }
                    Controls.CheckBox {
                        theme: root.theme
                        text: qsTr("Default")
                        enabled: Boolean(record.active)
                            && Boolean(record.defaultEligible)
                        checked: Boolean(record.isDefault)
                        onToggled: repositoryEditorModel.set_value(
                            root.selectedRow, "isDefault", checked
                        )
                    }
                    Controls.CompactIconButton {
                        visible: Boolean(record.custom)
                        theme: root.theme
                        iconName: "delete"
                        round: false
                        toolTip: qsTr("Remove custom repository")
                        onClicked: {
                            repositoryEditorController.remove_custom_repository(
                                root.selectedRow
                            )
                            root.selectedRow = Math.max(
                                0,
                                Math.min(
                                    root.selectedRow,
                                    repositoryEditorModel.count() - 1
                                )
                            )
                        }
                    }
                }

                Controls.TextField {
                    theme: root.theme
                    Layout.fillWidth: true
                    placeholderText: qsTr("Display name")
                    text: record.title || ""
                    onTextEdited: repositoryEditorModel.set_value(
                        root.selectedRow, "title", text
                    )
                }
                Controls.TextField {
                    theme: root.theme
                    Layout.fillWidth: true
                    placeholderText: qsTr("Windows path")
                    text: record.windowsPath || ""
                    onTextEdited: repositoryEditorModel.set_value(
                        root.selectedRow, "windowsPath", text
                    )
                }
                Controls.TextField {
                    theme: root.theme
                    Layout.fillWidth: true
                    placeholderText: qsTr("Linux path")
                    text: record.linuxPath || ""
                    onTextEdited: repositoryEditorModel.set_value(
                        root.selectedRow, "linuxPath", text
                    )
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: mappingColumn.implicitHeight + 24
                    radius: 10
                    color: root.theme.panelRaised
                    border.color: root.theme.border
                    ColumnLayout {
                        id: mappingColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.margins: 12
                        spacing: 4
                        Label {
                            text: qsTr("PROJECT MAPPING")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                        }
                        Label {
                            Layout.fillWidth: true
                            text: record.projectMapping || qsTr("No mappings")
                            wrapMode: Text.WordWrap
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Controls.MaterialIcon {
                        name: record.status === "available"
                            ? "check_circle" : record.status === "unavailable"
                                ? "error" : "info"
                        size: 17
                        color: record.status === "available"
                            ? root.theme.green : record.status === "unavailable"
                                ? root.theme.red : root.theme.secondaryText
                    }
                    Label {
                        Layout.fillWidth: true
                        text: record.statusText || qsTr("Not checked")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                    }
                    Controls.Button {
                        theme: root.theme
                        text: repositoryEditorController.busy
                            ? qsTr("CHECKING…") : qsTr("CHECK PATHS")
                        enabled: !repositoryEditorController.busy
                        onClicked: repositoryEditorController.check_paths()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: repositoryEditorController.message
                    color: text.indexOf("saved") >= 0
                        ? root.theme.green : root.theme.red
                    wrapMode: Text.WordWrap
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
                Item { Layout.fillHeight: true }
                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    spacing: 8
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("CANCEL")
                        enabled: repositoryEditorController.dirty
                        onClicked: repositoryEditorController.cancel()
                    }
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("SAVE")
                        highlighted: true
                        enabled: repositoryEditorController.dirty
                            && !repositoryEditorController.busy
                        onClicked: repositoryEditorController.save()
                    }
                }
            }
        }
    }
}
