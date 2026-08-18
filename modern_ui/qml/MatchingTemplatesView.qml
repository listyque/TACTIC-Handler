import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "controls"

Item {
    id: root
    required property var theme
    required property string windowId

    Component.onCompleted: matchingTemplatesController.begin_edit()
    Component.onDestruction: {
        if (matchingTemplatesController)
            matchingTemplatesController.cancel()
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: Math.max(300, root.width * 0.48)
            radius: 16
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 9
                spacing: 7
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("Matching templates")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "add"
                        onClicked: matchingTemplatesController.create_template()
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "content_copy"
                        enabled: matchingTemplatesController.selectedRow >= 0
                        onClicked:
                            matchingTemplatesController.duplicate_selected()
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "arrow_upward"
                        enabled: matchingTemplatesController.selectedRow > 0
                        onClicked: matchingTemplatesController.move_selected(-1)
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "arrow_downward"
                        enabled: matchingTemplatesController.selectedRow >= 0
                            && matchingTemplatesController.selectedRow
                                < templateList.count - 1
                        onClicked: matchingTemplatesController.move_selected(1)
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "delete"
                        enabled: matchingTemplatesController.selectedRow >= 0
                            && !matchingTemplatesController.selectedTemplate.locked
                        onClicked:
                            matchingTemplatesController.delete_selected()
                    }
                }

                ListView {
                    id: templateList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 5
                    model: matchingTemplatesModel
                    delegate: Rectangle {
                        required property int index
                        required property bool templateEnabled
                        required property string pattern
                        required property string preview
                        required property string matchingType
                        required property string process
                        required property string context
                        required property bool locked
                        required property bool selected
                        required property int priority
                        required property string validationError
                        width: templateList.width
                        height: 64
                        radius: 12
                        color: selected
                            ? root.theme.secondaryContainer
                            : root.theme.surfaceContainerHigh

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked:
                                matchingTemplatesController.select_row(index)
                        }
                        RowLayout {
                            z: 1
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8
                            Md3CheckBox {
                                theme: root.theme
                                checked: parent.parent.templateEnabled
                                enabled: !parent.parent.locked
                                onClicked: {
                                    matchingTemplatesController.select_row(
                                        parent.parent.index
                                    )
                                    matchingTemplatesController.update_selected(
                                        "enabled", checked
                                    )
                                }
                            }
                            Label {
                                text: String(priority + 1)
                                color: root.theme.disabledText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    Layout.fillWidth: true
                                    text: pattern
                                    color: validationError
                                        ? root.theme.error
                                        : root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.body
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideMiddle
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: validationError || preview
                                    color: validationError
                                        ? root.theme.error
                                        : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.label
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: matchingType
                                        + (process ? " • " + process : "")
                                        + (context ? " / " + context : "")
                                    color: root.theme.disabledText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                            MaterialIcon {
                                name: locked ? "lock" : "drag_handle"
                                size: 16
                                color: root.theme.secondaryText
                            }
                        }
                    }
                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: templateList
                    }
                }
            }
        }

        Rectangle {
            id: editor
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 16
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant
            property var record:
                matchingTemplatesController.selectedTemplate

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 10
                Label {
                    text: qsTr("Template properties")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
                Label {
                    text: qsTr("Pattern")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                }
                Md3TextField {
                    theme: root.theme
                    Layout.fillWidth: true
                    enabled: matchingTemplatesController.selectedRow >= 0
                        && !editor.record.locked
                    text: editor.record.pattern || ""
                    onEditingFinished:
                        matchingTemplatesController.update_selected(
                            "pattern", text
                        )
                }
                Label {
                    Layout.fillWidth: true
                    text: editor.record.validationError
                        || (qsTr("Preview: ") + (editor.record.preview || "—")
                            + qsTr("   Type: ")
                            + (editor.record.matchingType || "—"))
                    color: editor.record.validationError
                        ? root.theme.error : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                    wrapMode: Text.WordWrap
                }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    rowSpacing: 8
                    columnSpacing: 10
                    Label {
                        text: qsTr("Process mapping")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.label
                    }
                    Md3ComboBox {
                        theme: root.theme
                        Layout.fillWidth: true
                        enabled: matchingTemplatesController.selectedRow >= 0
                            && !editor.record.locked
                        editable: true
                        model: [""].concat(
                            checkinOutController
                                ? checkinOutController.processes : []
                        )
                        editText: editor.record.process || ""
                        displayText: editText || "All processes"
                        onActivated:
                            matchingTemplatesController.update_selected(
                                "process", currentText
                            )
                        onAccepted:
                            matchingTemplatesController.update_selected(
                                "process", editText
                            )
                    }
                    Label {
                        text: qsTr("Context mapping")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.label
                    }
                    Md3ComboBox {
                        theme: root.theme
                        Layout.fillWidth: true
                        enabled: matchingTemplatesController.selectedRow >= 0
                            && !editor.record.locked
                        editable: true
                        model: [""].concat(
                            checkinOutController
                                ? checkinOutController.contexts : []
                        )
                        editText: editor.record.context || ""
                        displayText: editText || "All contexts"
                        onActivated:
                            matchingTemplatesController.update_selected(
                                "context", currentText
                            )
                        onAccepted:
                            matchingTemplatesController.update_selected(
                                "context", editText
                            )
                    }
                }
                Label {
                    text: qsTr("Test on filename")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                }
                RowLayout {
                    Layout.fillWidth: true
                    Md3TextField {
                        id: exampleField
                        theme: root.theme
                        Layout.fillWidth: true
                        placeholderText: qsTr("shot.001.exr")
                        text: matchingTemplatesController.testExample
                        onAccepted:
                            matchingTemplatesController.test_pattern(text)
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Test")
                        icon.name: "science"
                        enabled: matchingTemplatesController.selectedRow >= 0
                        onClicked:
                            matchingTemplatesController.test_pattern(
                                exampleField.text
                            )
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: matchingTemplatesController.testResult
                    visible: text.length > 0
                    color: text === "No match"
                        ? root.theme.error : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                    wrapMode: Text.WordWrap
                }
                Item { Layout.fillHeight: true }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        Layout.fillWidth: true
                        text: matchingTemplatesController.dirty
                            ? qsTr("Unsaved changes") : ""
                        color: root.theme.yellow
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.label
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Cancel")
                        onClicked: {
                            matchingTemplatesController.cancel()
                            windowModel.close_window(root.windowId)
                        }
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Save")
                        icon.name: "save"
                        highlighted: enabled
                        enabled: matchingTemplatesController.dirty
                        onClicked: {
                            if (matchingTemplatesController.save())
                                windowModel.close_window(root.windowId)
                        }
                    }
                }
            }
        }
    }
}
