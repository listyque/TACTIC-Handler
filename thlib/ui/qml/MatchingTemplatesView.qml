import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "controls" as Controls
Item {
    id: root
    required property var theme
    required property string windowId

    function toolbarActions() {
        return [
            {
                "title": "Duplicate",
                "icon": "content_copy",
                "command": "duplicate",
                "enabled": matchingTemplatesController.selectedRow >= 0
            },
            {
                "title": "Move up",
                "icon": "arrow_upward",
                "command": "move_up",
                "enabled": matchingTemplatesController.selectedRow > 0
            },
            {
                "title": "Move down",
                "icon": "arrow_downward",
                "command": "move_down",
                "enabled": matchingTemplatesController.selectedRow >= 0
                    && matchingTemplatesController.selectedRow
                        < templateList.count - 1
            },
            {
                "title": "Delete",
                "icon": "delete",
                "command": "delete",
                "enabled": matchingTemplatesController.selectedRow >= 0
                    && !matchingTemplatesController.selectedTemplate.locked
            }
        ]
    }

    function runToolbarAction(command) {
        if (command === "duplicate")
            matchingTemplatesController.duplicate_selected()
        else if (command === "move_up")
            matchingTemplatesController.move_selected(-1)
        else if (command === "move_down")
            matchingTemplatesController.move_selected(1)
        else if (command === "delete")
            matchingTemplatesController.delete_selected()
    }

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
            id: templateListPanel
            objectName: "matchingTemplatesListPanel"
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            Layout.preferredWidth: Math.max(300, root.width * 0.48)
            radius: 16
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true
            readonly property bool compactToolbar: width < 400

            ColumnLayout {
                id: templateListLayout
                objectName: "matchingTemplatesListLayout"
                anchors.fill: parent
                anchors.margins: 9
                spacing: 7
                RowLayout {
                    id: templateToolbar
                    objectName: "matchingTemplatesToolbar"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Label {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        text: qsTr("Matching templates")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "add"
                        onClicked: matchingTemplatesController.create_template()
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "content_copy"
                        visible: !templateListPanel.compactToolbar
                        enabled: matchingTemplatesController.selectedRow >= 0
                        onClicked:
                            matchingTemplatesController.duplicate_selected()
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "arrow_upward"
                        visible: !templateListPanel.compactToolbar
                        enabled: matchingTemplatesController.selectedRow > 0
                        onClicked: matchingTemplatesController.move_selected(-1)
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "arrow_downward"
                        visible: !templateListPanel.compactToolbar
                        enabled: matchingTemplatesController.selectedRow >= 0
                            && matchingTemplatesController.selectedRow
                                < templateList.count - 1
                        onClicked: matchingTemplatesController.move_selected(1)
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "delete"
                        visible: !templateListPanel.compactToolbar
                        enabled: matchingTemplatesController.selectedRow >= 0
                            && !matchingTemplatesController.selectedTemplate.locked
                        onClicked:
                            matchingTemplatesController.delete_selected()
                    }
                    Controls.CompactIconButton {
                        id: templateToolbarOverflowButton
                        objectName: "matchingTemplatesOverflowButton"
                        visible: templateListPanel.compactToolbar
                        theme: root.theme
                        iconName: "more_vert"
                        toolTip: qsTr("Template actions")
                        onPressed: templateToolbarMenu.sourceWasOpen
                            = templateToolbarMenu.opened
                        onClicked:
                            templateToolbarMenu.toggleBelow(
                                templateToolbarOverflowButton
                            )
                    }
                }

                ListView {
                    id: templateList
                    objectName: "matchingTemplatesList"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 0
                    clip: true
                    spacing: 5
                    model: matchingTemplatesModel
                    delegate: Rectangle {
                        objectName: "matchingTemplateDelegate"
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
                        width: Math.max(0, templateList.width - 10)
                        height: 64
                        radius: 12
                        color: selected
                            ? root.theme.secondaryContainer
                            : root.theme.surfaceContainerHigh

                        Controls.ActivationHandler {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onActivated:
                                matchingTemplatesController.select_row(index)
                        }
                        RowLayout {
                            z: 1
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8
                            Controls.CheckBox {
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
                                font.pointSize: Controls.Typography.label
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
                                    font.pointSize: Controls.Typography.body
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
                                    font.pointSize: Controls.Typography.label
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: matchingType
                                        + (process ? " • " + process : "")
                                        + (context ? " / " + context : "")
                                    color: root.theme.disabledText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                            Controls.MaterialIcon {
                                name: locked ? "lock" : "drag_handle"
                                size: 16
                                color: root.theme.secondaryText
                            }
                        }
                    }
                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: templateList
                    }
                }
            }
        }

        Rectangle {
            id: editor
            objectName: "matchingTemplatesEditorPanel"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            radius: 16
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant
            property var record:
                matchingTemplatesController.selectedTemplate
            readonly property bool compactFields: width < 360

            ColumnLayout {
                id: editorLayout
                objectName: "matchingTemplatesEditorLayout"
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
                    font.pointSize: Controls.Typography.label
                }
                Controls.TextField {
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
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
                GridLayout {
                    id: mappingGrid
                    objectName: "matchingTemplatesMappingGrid"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Layout.maximumWidth: editorLayout.width
                    columns: editor.compactFields ? 1 : 2
                    rowSpacing: 8
                    columnSpacing: 10
                    Label {
                        text: qsTr("Process mapping")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.ComboBox {
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.maximumWidth: mappingGrid.width
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
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.ComboBox {
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.maximumWidth: mappingGrid.width
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
                    font.pointSize: Controls.Typography.label
                }
                GridLayout {
                    id: patternTestGrid
                    objectName: "matchingTemplatesTestGrid"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Layout.maximumWidth: editorLayout.width
                    columns: editor.compactFields ? 1 : 2
                    columnSpacing: 8
                    rowSpacing: 8
                    Controls.TextField {
                        id: exampleField
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.maximumWidth: patternTestGrid.width
                        placeholderText: qsTr("shot.001.exr")
                        text: matchingTemplatesController.testExample
                        onAccepted:
                            matchingTemplatesController.test_pattern(text)
                    }
                    Controls.Button {
                        theme: root.theme
                        Layout.fillWidth: editor.compactFields
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
                    font.pointSize: Controls.Typography.label
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
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Cancel")
                        onClicked: {
                            matchingTemplatesController.cancel()
                            windowModel.close_window(root.windowId)
                        }
                    }
                    Controls.Button {
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

    ActionMenu {
        id: templateToolbarMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 220
        actions: root.toolbarActions()
        onTriggered: command => root.runToolbarAction(command)
    }
}
