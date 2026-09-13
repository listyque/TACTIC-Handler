import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property string editorWindowId
    readonly property bool compact: width < 660
    readonly property real minimumFieldCardWidth: 430
    readonly property int maximumFieldColumns: 3

    function insertBatchToken(token) {
        const window = root.Window.window
        const editor = window ? window.activeFocusItem : null
        if (editor && editor.insertBatchToken)
            editor.insertBatchToken(token)
    }

    Connections {
        target: sobjectEditorController
        function onSaved(searchKey) {
            windowModel.close_window(root.editorWindowId)
        }
    }

    Controls.ImageFileDialog {
        id: previewFileDialog
        allowMultiple: true
        onImagesSelected: (row, images) => {
            if (row >= 0)
                sobjectFieldModel.add_preview_files(row, images)
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            objectName: "sobjectEditorHeader"
            Layout.fillWidth: true
            Layout.preferredHeight: root.compact ? 90 : 98
            color: root.theme.surfaceContainerLow

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: root.compact ? 16 : 22
                anchors.rightMargin: root.compact ? 16 : 22
                spacing: 13

                Rectangle {
                    Layout.preferredWidth: 44
                    Layout.preferredHeight: 44
                    radius: root.theme.itemRadius
                    color: root.theme.secondaryContainer

                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: "sobject"
                        size: 22
                        color: root.theme.action
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            Layout.fillWidth: true
                            text: sobjectEditorController.title
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }

                        Rectangle {
                            visible: sobjectEditorController.mode === "edit"
                            implicitWidth: modeLabel.implicitWidth + 18
                            implicitHeight: 25
                            radius: height / 2
                            color: root.theme.secondaryContainer

                            Label {
                                id: modeLabel

                                anchors.centerIn: parent
                                text: sobjectEditorController.mode === "edit"
                                    ? qsTr("Edit") : qsTr("New")
                                color: root.theme.action
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.DemiBold
                            }
                        }

                        Controls.SegmentedButton {
                            objectName: "sobjectCreateMode"
                            visible: sobjectEditorController.mode === "insert"
                            theme: root.theme
                            model: [
                                { label: qsTr("One"), value: "single", icon: "sobject" },
                                { label: qsTr("Multiple"), value: "batch", icon: "control-point-duplicate" }
                            ]
                            currentValue: sobjectEditorController.batchEnabled
                                ? "batch" : "single"
                            segmentWidth: 116
                            minimumSegmentWidth: 92
                            iconOnly: root.compact
                            onActivated: value => sobjectEditorController.set_batch_enabled(
                                value === "batch")
                        }

                        RefreshIconButton {
                            objectName: "sobjectEditorRefresh"
                            theme: root.theme
                            toolTip: qsTr("Reload schema")
                            enabled: !sobjectEditorController.busy
                            onClicked: sobjectEditorController.begin_session()
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: sobjectEditorController.searchType
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        elide: Text.ElideMiddle
                    }

                    Label {
                        Layout.fillWidth: true
                        visible: sobjectEditorController.parentTitle.length > 0
                        text: qsTr("Parent") + ": "
                            + sobjectEditorController.parentTitle
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }

            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: root.theme.outlineVariant
            }
        }

        ScrollView {
            id: formScroll
            objectName: "sobjectEditorFormScroll"

            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            contentHeight: formColumn.implicitHeight
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                objectName: "sobjectEditorFormVerticalScrollBar"
                theme: root.theme
                flickableTarget: formScroll.contentItem
            }

            Column {
                id: formColumn
                width: formScroll.availableWidth
                topPadding: 18
                bottomPadding: 20
                spacing: 10

                Rectangle {
                    objectName: "sobjectBatchSetup"
                    visible: sobjectEditorController.batchEnabled
                        && !sobjectEditorController.batchPreview
                    width: Math.max(0, parent.width - 40)
                    height: visible ? batchSetupColumn.implicitHeight + 28 : 0
                    x: 20
                    radius: root.theme.sectionRadius
                    color: root.theme.surfaceContainerLow
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    ColumnLayout {
                        id: batchSetupColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                visible: !root.compact
                                Layout.minimumWidth: visible ? implicitWidth : 0
                                Layout.preferredWidth: visible ? implicitWidth : 0
                                Layout.maximumWidth: visible ? implicitWidth : 0
                                text: qsTr("Number of objects")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                            }

                            Controls.SpinBox {
                                objectName: "sobjectBatchCount"
                                Layout.preferredWidth: 112
                                theme: root.theme
                                from: 2
                                to: 100
                                value: sobjectEditorController.batchCount
                                Accessible.name: qsTr("Number of objects")
                                enabled: !sobjectEditorController.busy
                                onRealValueEdited: value =>
                                    sobjectEditorController.set_batch_count(value)
                            }

                            Item {
                                Layout.fillWidth: true
                            }

                            Controls.Button {
                                objectName: "sobjectBatchInsertNumber"
                                Layout.preferredWidth: 70
                                theme: root.theme
                                text: "{n}"
                                leftPadding: 8
                                rightPadding: 8
                                toolTip: qsTr("Insert number")
                                focusPolicy: Qt.NoFocus
                                onClicked: root.insertBatchToken("{n}")
                            }

                            Controls.Button {
                                objectName: "sobjectBatchInsertTwoDigitNumber"
                                Layout.preferredWidth: 70
                                theme: root.theme
                                text: "{n:02}"
                                leftPadding: 8
                                rightPadding: 8
                                toolTip: qsTr("Insert a two-digit number")
                                focusPolicy: Qt.NoFocus
                                onClicked: root.insertBatchToken("{n:02}")
                            }

                            Controls.Button {
                                objectName: "sobjectBatchInsertPaddedNumber"
                                Layout.preferredWidth: 70
                                theme: root.theme
                                text: "{n:03}"
                                leftPadding: 8
                                rightPadding: 8
                                toolTip: qsTr("Insert a three-digit number")
                                focusPolicy: Qt.NoFocus
                                onClicked: root.insertBatchToken("{n:03}")
                            }

                            Controls.Button {
                                objectName: "sobjectBatchInsertFourDigitNumber"
                                Layout.preferredWidth: 70
                                theme: root.theme
                                text: "{n:04}"
                                leftPadding: 8
                                rightPadding: 8
                                toolTip: qsTr("Insert a four-digit number")
                                focusPolicy: Qt.NoFocus
                                onClicked: root.insertBatchToken("{n:04}")
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Place the caret in a text field and insert a number format. Numbers are substituted during preview.")
                                + (sobjectEditorController.batchExample.length > 0
                                    ? "  " + qsTr("Name preview") + ": "
                                        + sobjectEditorController.batchExample
                                    : "")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                Rectangle {
                    objectName: "sobjectBatchNavigator"
                    visible: sobjectEditorController.batchPreview
                    width: Math.max(0, parent.width - 40)
                    height: visible ? 58 : 0
                    x: 20
                    radius: root.theme.itemRadius
                    color: root.theme.surfaceContainerLow
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 9
                        spacing: 8

                        Controls.CompactIconButton {
                            objectName: "sobjectBatchPrevious"
                            theme: root.theme
                            iconName: "chevron-left"
                            toolTip: qsTr("Previous object")
                            enabled: !sobjectEditorController.busy
                                && sobjectEditorController.batchIndex > 0
                            onClicked: sobjectEditorController.show_batch_item(
                                sobjectEditorController.batchIndex - 1)
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1

                            Label {
                                Layout.fillWidth: true
                                text: qsTr("Object %1 of %2")
                                    .arg(sobjectEditorController.batchIndex + 1)
                                    .arg(sobjectEditorController.batchTotal)
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                            }

                            Label {
                                Layout.fillWidth: true
                                text: qsTr("Edit any fields for this object, then move to the next one.")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                        }

                        Controls.CompactIconButton {
                            objectName: "sobjectBatchNext"
                            theme: root.theme
                            iconName: "chevron-right"
                            toolTip: qsTr("Next object")
                            enabled: !sobjectEditorController.busy
                                && sobjectEditorController.batchIndex
                                    < sobjectEditorController.batchTotal - 1
                            onClicked: sobjectEditorController.show_batch_item(
                                sobjectEditorController.batchIndex + 1)
                        }
                    }
                }

                RowLayout {
                    width: Math.max(0, parent.width - 40)
                    x: 20
                    spacing: 8

                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Object fields")
                        visible: !sobjectEditorController.batchPreview
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                    }

                    Label {
                        objectName: "sobjectEditorFieldCount"
                        text: String(sobjectFieldModel.count)
                        visible: !sobjectEditorController.batchPreview
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                    }
                }

                SObjectFieldGrid {
                    id: fieldFlow
                    objectName: "sobjectEditorFieldFlow"
                    width: Math.max(0, parent.width - 40)
                    x: 20
                    theme: root.theme
                    fieldModel: sobjectFieldModel
                    itemPrefix: "sobjectEditorFieldItem_"
                    repeaterObjectName: "sobjectEditorFieldRepeater"
                    editorBusy: sobjectEditorController.busy
                    editorMode: sobjectEditorController.mode
                    minimumCellWidth: root.minimumFieldCardWidth
                    maximumColumns: root.maximumFieldColumns
                    onPreviewRequested: row => previewFileDialog.openForRow(row)
                }

                ColumnLayout {
                    visible: sobjectFieldModel.count === 0
                    && !sobjectEditorController.busy
                    width: Math.max(0, parent.width - 40)
                    x: 20
                    spacing: 8

                    Controls.MaterialIcon {
                        Layout.alignment: Qt.AlignHCenter
                        name: sobjectEditorController.error.length > 0
                            ? "warning" : "schema"
                        size: 30
                        color: sobjectEditorController.error.length > 0
                            ? root.theme.error : root.theme.secondaryText
                    }
                    Label {
                        Layout.fillWidth: true
                        text: sobjectEditorController.error.length > 0
                            ? sobjectEditorController.error
                            : qsTr("This edit view has no fields")
                        color: sobjectEditorController.error.length > 0
                            ? root.theme.error : root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }
                }
            }

            Controls.BusyIndicator {
                anchors.centerIn: parent
                uiTheme: root.theme
                running: sobjectEditorController.busy
                visible: running
            }
        }

        Controls.DockWorkspaceFooter {
            objectName: "sobjectEditorFooter"
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight
            theme: root.theme
            roundBottomLeft: false
            roundBottomRight: false

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: root.compact ? 16 : 22
                anchors.rightMargin: root.compact ? 16 : 22
                spacing: 8

                Controls.MaterialIcon {
                    name: sobjectFieldModel.valid
                        ? "check-circle" : "warning"
                    size: 16
                    color: sobjectFieldModel.valid
                        ? root.theme.secondaryText : root.theme.error
                }

                Label {
                    Layout.fillWidth: true
                    visible: !root.compact
                    text: sobjectFieldModel.valid
                        ? qsTr("Ready to save")
                        : qsTr("Correct the highlighted fields")
                    color: sobjectFieldModel.valid
                        ? root.theme.secondaryText : root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    elide: Text.ElideRight
                }

                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    enabled: !sobjectEditorController.busy
                    onClicked: windowModel.close_window(root.editorWindowId)
                }

                Controls.Button {
                    objectName: "sobjectBatchBack"
                    visible: sobjectEditorController.batchPreview
                    theme: root.theme
                    text: qsTr("Back")
                    enabled: !sobjectEditorController.busy
                    onClicked: sobjectEditorController.leave_batch_preview()
                }

                Controls.Button {
                    objectName: "sobjectEditorSubmit"
                    theme: root.theme
                    text: sobjectEditorController.mode === "edit"
                        ? qsTr("Save changes")
                        : sobjectEditorController.batchPreview
                            ? qsTr("Create %1 objects").arg(
                                sobjectEditorController.batchTotal)
                            : sobjectEditorController.batchEnabled
                                ? qsTr("Preview %1 objects").arg(
                                    sobjectEditorController.batchCount)
                                : qsTr("Create")
                    highlighted: true
                    enabled: !sobjectEditorController.busy
                        && sobjectFieldModel.valid
                        && sobjectFieldModel.count !== 0
                    onClicked: {
                        if (sobjectEditorController.batchEnabled
                                && !sobjectEditorController.batchPreview)
                            sobjectEditorController.preview_batch()
                        else
                            sobjectEditorController.submit()
                    }
                }
            }
        }
    }
}
