import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "controls" as Controls
Item {
    id: root
    required property var theme
    property bool embedded: false
    property bool advancedExpanded: false
    property int pendingRow: -1
    property string pendingAction: ""
    readonly property bool compactEditor: editor.width < 650
    readonly property bool stacked: embedded && width < 800

    component FieldLabel: Label {
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
    }

    function chooseRule(row) {
        if (namingEditorController.dirty) {
            pendingRow = row
            pendingAction = "select"
            discardDialog.open()
        } else {
            namingEditorController.select_rule(row)
        }
    }

    function createRule() {
        if (namingEditorController.dirty) {
            pendingAction = "create"
            discardDialog.open()
        } else {
            namingEditorController.create_rule()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.embedded ? 0 : 12
        spacing: 9

        NamingEditorHeader {
            Layout.fillWidth: true
            theme: root.theme
            controller: namingEditorController
            onReloadRequested: {
                if (namingEditorController.dirty) {
                    root.pendingAction = "reload"
                    discardDialog.open()
                } else {
                    namingEditorController.reload()
                }
            }
        }

        SplitView {
            id: editorSplit
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: root.stacked ? Qt.Vertical : Qt.Horizontal
            handle: Rectangle {
                implicitWidth: 9
                implicitHeight: 9
                color: "transparent"
                Rectangle {
                    anchors.centerIn: parent
                    width: root.stacked ? Math.max(0, parent.width - 18) : 1
                    height: root.stacked ? 1 : Math.max(0, parent.height - 18)
                    color: root.theme.outlineVariant
                }
            }

            Rectangle {
                SplitView.preferredWidth: 310
                SplitView.minimumWidth: root.stacked ? 0 : 250
                SplitView.maximumWidth: root.stacked ? root.width : 430
                SplitView.preferredHeight: 140
                SplitView.minimumHeight: root.stacked ? 110 : 0
                color: root.theme.surfaceContainerLow
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 9
                    spacing: 7

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Naming rules")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }
                        Controls.CompactIconButton {
                            objectName: "namingCreate"
                            theme: root.theme
                            iconName: "add"
                            toolTip: qsTr("Create naming rule")
                            enabled: !namingEditorController.busy
                                && Boolean(namingEditorController.currentObject.searchType)
                            onClicked: root.createRule()
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "content_copy"
                            toolTip: qsTr("Duplicate selected rule")
                            enabled: namingEditorController.selectedRow >= 0
                                && !namingEditorController.busy
                            onClicked: {
                                if (namingEditorController.dirty) {
                                    root.pendingAction = "duplicate"
                                    discardDialog.open()
                                } else {
                                    namingEditorController.duplicate_rule()
                                }
                            }
                        }
                    }

                    Controls.SmoothListView {
                        theme: root.theme
                        id: rulesList
                        objectName: "namingRulesList"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 5
                        model: namingEditorModel

                        delegate: Rectangle {
                            id: ruleRow
                            required property int index
                            required property string code
                            required property string title
                            required property string summary
                            required property string searchType
                            required property string context
                            required property string fileNaming
                            required property string dirNaming
                            required property string checkinType
                            required property bool scripted
                            required property bool versionless
                            required property bool selected
                            objectName: "namingRule_" + code
                            width: rulesList.width - rulesBar.reservedExtent - 4
                            height: 76
                            radius: root.theme.itemRadius
                            color: selected
                                ? root.theme.secondaryContainer
                                : ruleMouse.containsMouse
                                    ? root.theme.rowHover
                                    : root.theme.surfaceContainerHigh

                            Behavior on color {
                                ColorAnimation { duration: root.theme.hoverMotionFast }
                            }

                            MouseArea {
                                id: ruleMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.chooseRule(ruleRow.index)
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 8
                                Rectangle {
                                    Layout.preferredWidth: 34
                                    Layout.preferredHeight: 34
                                    radius: 11
                                    color: root.theme.surfaceContainerHighest
                                    Controls.MaterialIcon {
                                        anchors.centerIn: parent
                                        name: ruleRow.scripted ? "code" : "route"
                                        size: 17
                                        color: root.theme.action
                                    }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 1
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
                                        elide: Text.ElideMiddle
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: ruleRow.code + "  /  "
                                            + (ruleRow.checkinType || "auto")
                                            + (ruleRow.versionless ? "  /  versionless" : "")
                                        color: root.theme.disabledText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                        }

                        ScrollBar.vertical: Controls.ScrollBar {
                            id: rulesBar
                            objectName: "namingRulesBar"
                            theme: root.theme
                            flickableTarget: rulesList
                        }

                        Label {
                            anchors.centerIn: parent
                            width: parent.width - rulesBar.reservedExtent - 20
                            visible: rulesList.count === 0
                                && !namingEditorController.busy
                            text: namingEditorController.currentObject.searchType
                                ? qsTr("No rules for this search type")
                                : qsTr("Select an sObject")
                            wrapMode: Text.Wrap
                            horizontalAlignment: Text.AlignHCenter
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                        }
                    }
                }
            }

            Rectangle {
                id: editor
                SplitView.fillWidth: !root.stacked
                SplitView.fillHeight: root.stacked
                SplitView.minimumWidth: root.stacked ? 0 : 520
                SplitView.minimumHeight: root.stacked ? 220 : 0
                color: root.theme.surfaceContainerLow
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                property var record: namingEditorController.selectedRule

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    Flickable {
                        id: fieldsScroll
                        objectName: "namingFieldsScroll"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: width
                        contentHeight: fields.implicitHeight + 24
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds

                        ColumnLayout {
                            id: fields
                            width: fieldsScroll.width - fieldsBar.reservedExtent - 4
                            spacing: 9

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.leftMargin: 12
                                Layout.rightMargin: 12
                                Layout.topMargin: 12
                                Layout.preferredHeight: previewContent.implicitHeight + 22
                                radius: root.theme.surfaceRadius
                                color: root.theme.secondaryContainer

                                ColumnLayout {
                                    id: previewContent
                                    anchors.fill: parent
                                    anchors.margins: 11
                                    spacing: 7

                                    RowLayout {
                                        Layout.fillWidth: true
                                        Controls.MaterialIcon {
                                            name: "route"
                                            size: 18
                                            color: root.theme.action
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: qsTr("Naming preview")
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pixelSize: 12
                                            font.weight: Font.DemiBold
                                        }
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: namingEditorController.typeMode
                                            ? qsTr("Example values; no Search Object is selected")
                                                + " · " + namingEditorController.previewStatus
                                            : namingEditorController.previewStatus
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        wrapMode: Text.Wrap
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: namingEditorController.previewPath
                                            || qsTr("No preview available")
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.bodyLarge
                                        font.weight: Font.DemiBold
                                        wrapMode: Text.WrapAnywhere
                                    }
                                    GridLayout {
                                        Layout.fillWidth: true
                                        columns: root.compactEditor ? 2 : 6
                                        columnSpacing: 7
                                        rowSpacing: 5
                                        FieldLabel { text: qsTr("Example file") }
                                        Controls.TextField {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            text: namingEditorController.sampleFile
                                            onEditingFinished:
                                                namingEditorController.set_sample_file(text)
                                        }
                                        FieldLabel { text: qsTr("Version") }
                                        Controls.SpinBox {
                                            theme: root.theme
                                            Layout.preferredWidth: 120
                                            from: 1
                                            to: 9999
                                            value: namingEditorController.sampleVersion
                                            onValueModified:
                                                namingEditorController.set_sample_version(value)
                                        }
                                        FieldLabel { text: qsTr("File type") }
                                        Controls.ComboBox {
                                            theme: root.theme
                                            Layout.preferredWidth: 140
                                            model: ["main", "playblast", "web", "icon", "attachment"]
                                            currentIndex: Math.max(
                                                0, model.indexOf(namingEditorController.sampleFileType)
                                            )
                                            onActivated:
                                                namingEditorController.set_sample_file_type(currentText)
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.leftMargin: 12
                                Layout.rightMargin: 12
                                Layout.preferredHeight: mainFields.implicitHeight + 22
                                radius: root.theme.surfaceRadius
                                color: root.theme.surfaceContainerHigh

                                ColumnLayout {
                                    id: mainFields
                                    anchors.fill: parent
                                    anchors.margins: 11
                                    spacing: 7
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label {
                                            Layout.fillWidth: true
                                            text: namingEditorController.isNew
                                                ? qsTr("New naming rule")
                                                : (editor.record.code
                                                    || qsTr("Naming rule"))
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pixelSize: 13
                                            font.weight: Font.DemiBold
                                        }
                                        Label {
                                            visible: namingEditorController.dirty
                                            text: qsTr("Unsaved changes")
                                            color: root.theme.tertiary
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.label
                                            font.weight: Font.DemiBold
                                        }
                                    }
                                    FieldLabel { text: qsTr("Search Type") }
                                    Controls.TextField {
                                        objectName: "namingSearchType"
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        readOnly: true
                                        text: editor.record.search_type || ""
                                    }
                                    GridLayout {
                                        Layout.fillWidth: true
                                        columns: root.compactEditor ? 1 : 2
                                        rowSpacing: 7
                                        columnSpacing: 9
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 3
                                            FieldLabel { text: qsTr("Rule context (empty means any)") }
                                            Controls.TextField {
                                                theme: root.theme
                                                Layout.fillWidth: true
                                                text: editor.record.context || ""
                                                placeholderText: qsTr("Any context")
                                                onEditingFinished:
                                                    namingEditorController.set_field("context", text)
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 3
                                            FieldLabel { text: qsTr("Check-in type") }
                                            Controls.ComboBox {
                                                theme: root.theme
                                                Layout.fillWidth: true
                                                readonly property var values: ["auto", "strict", ""]
                                                model: ["Auto", "Strict", "Unspecified"]
                                                currentIndex: Math.max(
                                                    0, values.indexOf(editor.record.checkin_type || "")
                                                )
                                                onActivated:
                                                    namingEditorController.set_field(
                                                        "checkin_type", values[currentIndex]
                                                    )
                                            }
                                        }
                                    }
                                    FieldLabel { text: qsTr("Directory naming") }
                                    Controls.TextArea {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 74
                                        text: editor.record.dir_naming || ""
                                        placeholderText: qsTr("{project.code}/{search_type.table_name}/{sobject.code}/versions")
                                        onActiveFocusChanged: {
                                            if (!activeFocus)
                                                namingEditorController.set_field("dir_naming", text)
                                        }
                                    }
                                    FieldLabel { text: qsTr("File naming") }
                                    Controls.TextArea {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 66
                                        text: editor.record.file_naming || ""
                                        placeholderText: qsTr("{sobject.name}_v{version}.{ext}")
                                        onActiveFocusChanged: {
                                            if (!activeFocus)
                                                namingEditorController.set_field("file_naming", text)
                                        }
                                    }
                                    GridLayout {
                                        Layout.fillWidth: true
                                        columns: root.compactEditor ? 1 : 3
                                        Controls.CheckBox {
                                            theme: root.theme
                                            text: qsTr("Latest versionless")
                                            checked: Boolean(editor.record.latest_versionless)
                                            onClicked: namingEditorController.set_field(
                                                "latest_versionless", checked
                                            )
                                        }
                                        Controls.CheckBox {
                                            theme: root.theme
                                            text: qsTr("Current versionless")
                                            checked: Boolean(editor.record.current_versionless)
                                            onClicked: namingEditorController.set_field(
                                                "current_versionless", checked
                                            )
                                        }
                                        Controls.CheckBox {
                                            theme: root.theme
                                            text: qsTr("Manual version")
                                            checked: Boolean(editor.record.manual_version)
                                            onClicked: namingEditorController.set_field(
                                                "manual_version", checked
                                            )
                                        }
                                    }
                                }
                            }

                            Controls.Button {
                                theme: root.theme
                                Layout.leftMargin: 12
                                text: root.advancedExpanded
                                    ? qsTr("Hide advanced fields")
                                    : qsTr("Advanced fields")
                                icon.name: root.advancedExpanded
                                    ? "expand_less" : "expand_more"
                                flat: true
                                onClicked: root.advancedExpanded = !root.advancedExpanded
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.leftMargin: 12
                                Layout.rightMargin: 12
                                Layout.bottomMargin: 12
                                Layout.preferredHeight: advancedFields.implicitHeight + 22
                                visible: root.advancedExpanded
                                radius: root.theme.surfaceRadius
                                color: root.theme.surfaceContainerHigh

                                GridLayout {
                                    id: advancedFields
                                    anchors.fill: parent
                                    anchors.margins: 11
                                    columns: root.compactEditor ? 1 : 2
                                    rowSpacing: 7
                                    columnSpacing: 9

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        FieldLabel { text: qsTr("Snapshot type") }
                                        Controls.TextField {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            text: editor.record.snapshot_type || ""
                                            onEditingFinished:
                                                namingEditorController.set_field("snapshot_type", text)
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        FieldLabel { text: qsTr("Base directory alias") }
                                        Controls.TextField {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            text: editor.record.base_dir_alias || ""
                                            onEditingFinished:
                                                namingEditorController.set_field("base_dir_alias", text)
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.columnSpan: advancedFields.columns
                                        spacing: 3
                                        FieldLabel { text: qsTr("Sandbox directory naming") }
                                        Controls.TextArea {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 60
                                            text: editor.record.sandbox_dir_naming || ""
                                            onActiveFocusChanged: {
                                                if (!activeFocus)
                                                    namingEditorController.set_field("sandbox_dir_naming", text)
                                            }
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        FieldLabel { text: qsTr("Sandbox directory alias") }
                                        Controls.TextField {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            text: editor.record.sandbox_dir_alias || ""
                                            onEditingFinished:
                                                namingEditorController.set_field("sandbox_dir_alias", text)
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        FieldLabel { text: qsTr("Ingest rule code") }
                                        Controls.TextField {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            text: editor.record.ingest_rule_code || ""
                                            onEditingFinished:
                                                namingEditorController.set_field("ingest_rule_code", text)
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.columnSpan: advancedFields.columns
                                        spacing: 3
                                        FieldLabel { text: qsTr("Condition") }
                                        Controls.TextArea {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 60
                                            text: editor.record.condition || ""
                                            placeholderText: qsTr("@GET(snapshot.context) == publish")
                                            onActiveFocusChanged: {
                                                if (!activeFocus)
                                                    namingEditorController.set_field("condition", text)
                                            }
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        FieldLabel { text: qsTr("Script path") }
                                        Controls.TextField {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            text: editor.record.script_path || ""
                                            onEditingFinished:
                                                namingEditorController.set_field("script_path", text)
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        FieldLabel { text: qsTr("Class name") }
                                        Controls.TextField {
                                            theme: root.theme
                                            Layout.fillWidth: true
                                            text: editor.record.class_name || ""
                                            onEditingFinished:
                                                namingEditorController.set_field("class_name", text)
                                        }
                                    }
                                }
                            }
                        }

                        ScrollBar.vertical: Controls.ScrollBar {
                            id: fieldsBar
                            objectName: "namingFieldsBar"
                            theme: root.theme
                            flickableTarget: fieldsScroll
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 56
                        color: root.theme.surfaceContainerHigh

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 7
                            Controls.MaterialIcon {
                                visible: namingEditorController.busy
                                    || namingEditorController.error.length > 0
                                name: namingEditorController.error.length > 0
                                    ? "error" : "sync"
                                size: 16
                                color: namingEditorController.error.length > 0
                                    ? root.theme.error : root.theme.action
                            }
                            Label {
                                Layout.fillWidth: true
                                text: namingEditorController.error
                                    || namingEditorController.message
                                    || (namingEditorController.busy ? qsTr("Working") : "")
                                color: namingEditorController.error.length > 0
                                    ? root.theme.error : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                elide: Text.ElideRight
                            }
                            Controls.Button {
                                objectName: "namingReset"
                                theme: root.theme
                                text: qsTr("Reset")
                                icon.name: "undo"
                                enabled: namingEditorController.dirty
                                    && !namingEditorController.busy
                                onClicked: namingEditorController.reset()
                            }
                            Controls.Button {
                                objectName: "namingSave"
                                theme: root.theme
                                text: qsTr("Save rule")
                                icon.name: "save"
                                highlighted: enabled
                                enabled: namingEditorController.dirty
                                    && !namingEditorController.busy
                                onClicked: {
                                    if (namingEditorController.isNew)
                                        namingEditorController.save()
                                    else
                                        saveConfirmation.open()
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Controls.Dialog {
        id: discardDialog
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(430, root.width - 32)
        title: qsTr("Discard unsaved naming changes?")
        contentItem: Label {
            width: discardDialog.width - 40
            text: qsTr("The current naming rule has unsaved changes.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Discard")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Keep editing")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onAccepted: {
            if (root.pendingAction === "select")
                namingEditorController.select_rule(root.pendingRow)
            else if (root.pendingAction === "duplicate")
                namingEditorController.duplicate_rule()
            else if (root.pendingAction === "reload")
                namingEditorController.reload()
            else
                namingEditorController.create_rule()
            root.pendingAction = ""
            root.pendingRow = -1
        }
    }

    Controls.Dialog {
        id: saveConfirmation
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(450, root.width - 32)
        title: qsTr("Update project naming rule?")
        contentItem: Label {
            width: saveConfirmation.width - 40
            text: qsTr("This changes a config/naming record used by future check-ins in the current project.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Update rule")
                icon.name: "save"
                highlighted: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onAccepted: namingEditorController.save()
    }
}
