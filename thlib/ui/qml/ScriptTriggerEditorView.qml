pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property var selected: scriptTriggerController.selectedRule

    function optionIndex(options, value) {
        for (let index = 0; index < options.length; ++index) {
            if (String(options[index].value || "") === String(value || ""))
                return index
        }
        return -1
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                Layout.fillWidth: true
                text: qsTr("Script triggers")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.title
                font.weight: Font.DemiBold
            }

            Controls.BusyIndicator {
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                uiTheme: root.theme
                running: scriptTriggerController.busy
                visible: running
            }

            Controls.CompactIconButton {
                objectName: "scriptTriggerHelpButton"
                theme: root.theme
                iconName: "help"
                round: true
                toolTip: qsTr("Help")
                Accessible.name: toolTip
                onClicked: windowModel.open_help("script_triggers")
            }

            Controls.Button {
                theme: root.theme
                text: qsTr("Reload")
                icon.name: "sync"
                enabled: !scriptTriggerController.busy
                    && !scriptTriggerController.dirty
                onClicked: scriptTriggerController.refresh()
            }
        }

        Label {
            Layout.fillWidth: true
            visible: scriptTriggerController.error.length > 0
            text: scriptTriggerController.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            handle: Rectangle {
                implicitWidth: 6
                color: "transparent"
                Rectangle {
                    anchors.centerIn: parent
                    width: 1
                    height: Math.max(0, parent.height - 16)
                    color: root.theme.outlineVariant
                }
            }

            Rectangle {
                SplitView.preferredWidth: 330
                SplitView.minimumWidth: 260
                color: root.theme.panel
                border.width: 1
                border.color: root.theme.outlineVariant
                radius: root.theme.surfaceRadius
                clip: true

                ListView {
                    id: ruleList
                    objectName: "scriptTriggerRuleList"
                    anchors.fill: parent
                    anchors.margins: 7
                    rightMargin: ruleScroll.reservedExtent + 4
                    model: scriptTriggerModel
                    spacing: 5
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Rectangle {
                        id: ruleRow
                        required property int index
                        required property string title
                        required property string summary
                        required property bool ruleEnabled
                        required property bool valid

                        width: ruleList.width - ruleList.rightMargin
                        height: 66
                        radius: root.theme.itemRadius
                        color: ruleRow.index === scriptTriggerController.selectedRow
                            ? root.theme.secondaryContainer
                            : rowHover.hovered ? root.theme.rowHover : root.theme.row
                        border.width: 1
                        border.color: !ruleRow.valid
                            ? root.theme.error
                            : ruleRow.index === scriptTriggerController.selectedRow
                                ? root.theme.action : root.theme.outlineVariant
                        opacity: ruleRow.ruleEnabled ? 1 : 0.62

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8

                            Controls.MaterialIcon {
                                name: ruleRow.valid ? "bolt" : "warning"
                                size: 18
                                color: ruleRow.valid
                                    ? root.theme.action : root.theme.error
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Label {
                                    Layout.fillWidth: true
                                    text: ruleRow.title
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }

                                Label {
                                    Layout.fillWidth: true
                                    text: ruleRow.summary
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                        }

                        HoverHandler { id: rowHover }
                        Controls.ActivationHandler {
                            anchors.fill: parent
                            onActivated: scriptTriggerController.select(ruleRow.index)
                        }
                    }

                    ScrollBar.vertical: Controls.ScrollBar {
                        id: ruleScroll
                        theme: root.theme
                        flickableTarget: ruleList
                    }
                }

                Label {
                    anchors.centerIn: parent
                    width: Math.max(0, parent.width - 32)
                    visible: ruleList.count === 0
                    text: qsTr("No triggers yet")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    horizontalAlignment: Text.AlignHCenter
                }
            }

            Rectangle {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 440
                color: root.theme.panel
                border.width: 1
                border.color: root.theme.outlineVariant
                radius: root.theme.surfaceRadius
                clip: true

                Flickable {
                    id: formScroll
                    anchors.fill: parent
                    anchors.margins: 10
                    rightMargin: formBar.reservedExtent + 5
                    contentWidth: width
                    contentHeight: form.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: form
                        width: formScroll.width
                        spacing: 8
                        enabled: Boolean(root.selected.ruleId)

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Controls.TextField {
                                Layout.fillWidth: true
                                theme: root.theme
                                placeholderText: qsTr("Trigger name")
                                text: String(root.selected.title || "")
                                readOnly: !scriptTriggerController.canManage
                                onTextEdited: scriptTriggerController.update("title", text)
                            }

                            Controls.CheckBox {
                                theme: root.theme
                                text: qsTr("Enabled")
                                compact: true
                                enabled: scriptTriggerController.canManage
                                checked: Boolean(root.selected.enabled)
                                onToggled: scriptTriggerController.update("enabled", checked)
                            }
                        }

                        Controls.TextArea {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 68
                            theme: root.theme
                            placeholderText: qsTr("What this trigger does")
                            text: String(root.selected.description || "")
                            readOnly: !scriptTriggerController.canManage
                            onTextChanged: if (activeFocus)
                                scriptTriggerController.update("description", text)
                        }

                        Label {
                            text: qsTr("Run")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Controls.ComboBox {
                                id: actionBox
                                Layout.fillWidth: true
                                theme: root.theme
                                model: scriptTriggerController.actionOptions
                                textRole: "label"
                                valueRole: "value"
                                translateDisplayText: false
                                enabled: scriptTriggerController.canManage
                                currentIndex: root.optionIndex(
                                    model, root.selected.action
                                )
                                onActivated: scriptTriggerController.update(
                                    "action", currentValue
                                )
                            }

                            Controls.SegmentedButton {
                                Layout.preferredWidth: 220
                                theme: root.theme
                                model: scriptTriggerController.phaseOptions
                                currentValue: String(root.selected.phase || "after")
                                enabled: scriptTriggerController.canManage
                                onActivated: value => scriptTriggerController.update(
                                    "phase", value
                                )
                            }
                        }

                        Label {
                            text: qsTr("For objects")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }

                        Controls.ComboBox {
                            Layout.fillWidth: true
                            theme: root.theme
                            model: scriptTriggerController.searchTypeOptions
                            textRole: "label"
                            valueRole: "value"
                            translateDisplayText: false
                            enabled: scriptTriggerController.canManage
                            currentIndex: root.optionIndex(
                                model, root.selected.searchType
                            )
                            onActivated: scriptTriggerController.update(
                                "searchType", currentValue
                            )
                        }

                        Controls.TextArea {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 76
                            theme: root.theme
                            placeholderText: qsTr("Exact search keys, one per line (optional)")
                            text: String(root.selected.searchKeysText || "")
                            readOnly: !scriptTriggerController.canManage
                            onTextChanged: if (activeFocus)
                                scriptTriggerController.update("searchKeysText", text)
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Controls.TextField {
                                Layout.fillWidth: true
                                theme: root.theme
                                placeholderText: qsTr("Process (optional)")
                                text: String(root.selected.process || "")
                                readOnly: !scriptTriggerController.canManage
                                onTextEdited: scriptTriggerController.update("process", text)
                            }

                            Controls.TextField {
                                Layout.fillWidth: true
                                theme: root.theme
                                placeholderText: qsTr("Context (optional)")
                                text: String(root.selected.context || "")
                                readOnly: !scriptTriggerController.canManage
                                onTextEdited: scriptTriggerController.update("context", text)
                            }
                        }

                        Label {
                            text: String(root.selected.action || "").startsWith("dcc.")
                                ? qsTr("DCC Python script") : qsTr("Saved script")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }

                        Controls.Button {
                            id: scriptButton
                            Layout.fillWidth: true
                            theme: root.theme
                            text: String(root.selected.script || "").length > 0
                                ? String(root.selected.script) : qsTr("Choose script")
                            toolTip: text
                            enabled: scriptTriggerController.canManage
                            onClicked: scriptPicker.openFor(
                                scriptButton, String(root.selected.script || "")
                            )

                            contentItem: RowLayout {
                                spacing: 7
                                Controls.MaterialIcon {
                                    name: "account-tree"
                                    size: 16
                                    color: root.theme.action
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: scriptButton.text
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    elide: Text.ElideMiddle
                                }
                                Controls.MaterialIcon {
                                    name: "chevron-down"
                                    size: 14
                                    color: root.theme.secondaryText
                                }
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            visible: !Boolean(root.selected.valid)
                            text: String(root.selected.error || "")
                            color: root.theme.error
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            wrapMode: Text.WordWrap
                        }

                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Matching triggers run from top to bottom. A failed ‘before’ script stops the action; a failed ‘after’ script is logged and the remaining scripts continue.")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            wrapMode: Text.WordWrap
                        }
                    }

                    ScrollBar.vertical: Controls.ScrollBar {
                        id: formBar
                        theme: root.theme
                        flickableTarget: formScroll
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Controls.Button {
                theme: root.theme
                text: qsTr("Add trigger")
                icon.name: "add"
                enabled: scriptTriggerController.canManage
                    && !scriptTriggerController.busy
                onClicked: scriptTriggerController.add()
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "arrow_upward"
                toolTip: qsTr("Move up")
                enabled: scriptTriggerController.canManage
                    && scriptTriggerController.selectedRow > 0
                onClicked: scriptTriggerController.move(-1)
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "arrow_downward"
                toolTip: qsTr("Move down")
                enabled: scriptTriggerController.canManage
                    && scriptTriggerController.selectedRow >= 0
                    && scriptTriggerController.selectedRow < ruleList.count - 1
                onClicked: scriptTriggerController.move(1)
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                icon.name: "delete"
                destructive: true
                enabled: scriptTriggerController.canManage
                    && scriptTriggerController.selectedRow >= 0
                    && !scriptTriggerController.busy
                onClicked: scriptTriggerController.remove()
            }

            Item { Layout.fillWidth: true }

            Controls.Button {
                theme: root.theme
                text: qsTr("Discard")
                enabled: scriptTriggerController.dirty
                    && !scriptTriggerController.busy
                onClicked: scriptTriggerController.discard()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Save")
                icon.name: "save"
                highlighted: true
                enabled: scriptTriggerController.canManage
                    && scriptTriggerController.dirty
                    && !scriptTriggerController.busy
                onClicked: scriptTriggerController.save()
            }
        }
    }

    ScriptTreePicker {
        id: scriptPicker
        theme: root.theme
        treeModel: scriptEditorModel
        treeController: scriptEditorController
        scriptOptions: scriptTriggerController.compatibleScriptOptions
        onScriptSelected: script => scriptTriggerController.update("script", script)
    }
}
