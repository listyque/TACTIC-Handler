import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property string editorWindowId
    property int fileTargetRow: -1

    function setFieldValue(row, value) {
        sobjectFieldModel.setValue(row, value)
    }

    Connections {
        target: sobjectEditorController
        function onSaved(searchKey) {
            windowModel.close_window(root.editorWindowId)
        }
    }

    FileDialog {
        id: previewFileDialog
        title: qsTr("Choose preview image")
        nameFilters: [
            "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp)",
            "All files (*)"
        ]
        onAccepted: {
            if (root.fileTargetRow >= 0)
                root.setFieldValue(
                    root.fileTargetRow,
                    selectedFile
                )
            root.fileTargetRow = -1
        }
        onRejected: root.fileTargetRow = -1
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            Layout.topMargin: 18
            Layout.bottomMargin: 10

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: sobjectEditorController.mode === "edit"
                        ? qsTr("Edit sObject") : qsTr("New sObject")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
                Label {
                    text: qsTr(sobjectEditorController.title)
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 11
                }
            }
            RefreshIconButton {
                theme: root.theme
                toolTip: qsTr("Reload schema")
                enabled: !sobjectEditorController.busy
                onClicked: sobjectEditorController.begin_session()
            }
        }

        ScrollView {
            id: formScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

            Column {
                width: formScroll.availableWidth
                topPadding: 4
                bottomPadding: 20
                spacing: 10

                Repeater {
                    model: sobjectFieldModel

                    delegate: ColumnLayout {
                        required property int index
                        required property string fieldName
                        required property string title
                        required property string fieldType
                        required property string originalType
                        required property var fieldValue
                        required property var defaultValue
                        required property bool fieldRequired
                        required property bool fieldReadOnly
                        required property var fieldOptions
                        required property string fieldError

                        width: Math.max(0, formScroll.availableWidth - 48)
                        x: 24
                        spacing: 4

                        Label {
                            text: title + (fieldRequired ? " *" : "")
                            color: parent.fieldError
                                ? root.theme.error : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }

                        Loader {
                            Layout.fillWidth: true
                            sourceComponent: {
                                if (fieldType === "multiline")
                                    return multilineDelegate
                                if (fieldType === "bool")
                                    return boolDelegate
                                if (fieldType === "enum"
                                        || fieldType === "user"
                                        || fieldType === "process"
                                        || fieldType === "project")
                                    return enumDelegate
                                if (fieldType === "date"
                                        || fieldType === "datetime")
                                    return dateDelegate
                                if (fieldType === "preview")
                                    return previewDelegate
                                if (fieldType === "thumbnail")
                                    return thumbnailDelegate
                                return textDelegate
                            }
                        }

                        Label {
                            visible: fieldError.length > 0
                            text: fieldError
                            color: root.theme.error
                            font.family: root.theme.fontFamily
                            font.pixelSize: 10
                        }

                        Component {
                            id: dateDelegate
                            Md3DateField {
                                theme: root.theme
                                text: String(fieldValue ?? "")
                                readOnly: fieldReadOnly
                                enabled: !fieldReadOnly
                                    && !sobjectEditorController.busy
                                includeTime: fieldType === "datetime"
                                placeholderText: fieldType === "datetime"
                                    ? "Date and time" : "Date"
                                errorState: fieldError.length > 0
                                onAccepted: value => root.setFieldValue(
                                    index, value
                                )
                                onEditingFinished:
                                    root.setFieldValue(index, text)
                            }
                        }

                        Component {
                            id: textDelegate
                            Md3TextField {
                                theme: root.theme
                                text: String(fieldValue ?? "")
                                readOnly: fieldReadOnly
                                enabled: !fieldReadOnly
                                    && !sobjectEditorController.busy
                                placeholderText: fieldType === "date"
                                    ? "YYYY-MM-DD"
                                    : fieldType === "datetime"
                                        ? "YYYY-MM-DD HH:MM:SS"
                                        : ""
                                color: root.theme.primaryText
                                placeholderTextColor: root.theme.secondaryText
                                selectByMouse: true
                                inputMethodHints: fieldType === "integer"
                                    ? Qt.ImhDigitsOnly
                                    : fieldType === "float"
                                        ? Qt.ImhFormattedNumbersOnly
                                        : Qt.ImhNone
                                onEditingFinished:
                                    root.setFieldValue(index, text)
                                background: Rectangle {
                                    radius: 10
                                    color: root.theme.panelRaised
                                    border.width: 1
                                    border.color: fieldError
                                        ? root.theme.error : root.theme.outline
                                }
                            }
                        }

                        Component {
                            id: multilineDelegate
                            Md3TextArea {
                                theme: root.theme
                                text: String(fieldValue ?? "")
                                readOnly: fieldReadOnly
                                enabled: !fieldReadOnly
                                    && !sobjectEditorController.busy
                                color: root.theme.primaryText
                                placeholderTextColor: root.theme.secondaryText
                                selectByMouse: true
                                wrapMode: TextEdit.Wrap
                                implicitHeight: 104
                                onActiveFocusChanged: {
                                    if (!activeFocus)
                                        root.setFieldValue(index, text)
                                }
                                background: Rectangle {
                                    radius: 10
                                    color: root.theme.panelRaised
                                    border.width: 1
                                    border.color: fieldError
                                        ? root.theme.error : root.theme.outline
                                }
                            }
                        }

                        Component {
                            id: boolDelegate
                            Md3Switch {
                                theme: root.theme
                                checked: Boolean(fieldValue)
                                enabled: !fieldReadOnly
                                    && !sobjectEditorController.busy
                                text: checked
                                    ? qsTr("Enabled") : qsTr("Disabled")
                                onToggled:
                                    root.setFieldValue(index, checked)
                            }
                        }

                        Component {
                            id: enumDelegate
                            Md3ComboBox {
                                id: enumControl
                                theme: root.theme
                                enabled: !fieldReadOnly
                                    && !sobjectEditorController.busy
                                model: fieldOptions
                                textRole: "label"
                                valueRole: "value"
                                Component.onCompleted: {
                                    var wanted = String(fieldValue ?? "")
                                    for (var i = 0; i < count; ++i) {
                                        if (String(valueAt(i)) === wanted) {
                                            currentIndex = i
                                            break
                                        }
                                    }
                                }
                                onActivated:
                                    root.setFieldValue(index, currentValue)
                                background: Rectangle {
                                    radius: 10
                                    color: root.theme.panelRaised
                                    border.width: 1
                                    border.color: fieldError
                                        ? root.theme.error : root.theme.outline
                                }
                            }
                        }

                        Component {
                            id: previewDelegate
                            RowLayout {
                                spacing: 8
                                Md3Button {
                                    theme: root.theme
                                    text: fieldValue
                                        ? qsTr("Change image")
                                        : qsTr("Choose image")
                                    enabled: !sobjectEditorController.busy
                                    onClicked: {
                                        root.fileTargetRow = index
                                        previewFileDialog.open()
                                    }
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: String(fieldValue
                                        || qsTr("No image selected"))
                                    color: fieldValue
                                        ? root.theme.primaryText
                                        : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 10
                                    elide: Text.ElideMiddle
                                }
                                CompactIconButton {
                                    visible: Boolean(fieldValue)
                                    theme: root.theme
                                    iconName: "close"
                                    round: true
                                    enabled: !sobjectEditorController.busy
                                    onClicked: root.setFieldValue(index, "")
                                }
                            }
                        }

                        Component {
                            id: thumbnailDelegate
                            Rectangle {
                                implicitHeight: 74
                                radius: 10
                                color: root.theme.panelRaised
                                border.width: 1
                                border.color: root.theme.outline
                                Label {
                                    anchors.centerIn: parent
                                    text: qsTr("Current thumbnail")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 10
                                }
                            }
                        }
                    }
                }

                BusyIndicator {
                    anchors.horizontalCenter: parent.horizontalCenter
                    running: sobjectEditorController.busy
                    visible: running
                }

                Label {
                    width: Math.max(0, parent.width - 48)
                    x: 24
                    visible: sobjectEditorController.error.length > 0
                    text: sobjectEditorController.error
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            color: root.theme.panel
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: root.theme.separator
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                Label {
                    Layout.fillWidth: true
                    text: sobjectFieldModel.valid
                        ? qsTr("Schema values are valid")
                        : qsTr("Correct the highlighted fields")
                    color: sobjectFieldModel.valid
                        ? root.theme.secondaryText : root.theme.error
                    font.family: root.theme.fontFamily
                    font.pixelSize: 10
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    enabled: !sobjectEditorController.busy
                    onClicked: windowModel.close_window(root.editorWindowId)
                }
                Md3Button {
                    theme: root.theme
                    text: sobjectEditorController.submitLabel
                    highlighted: true
                    enabled: !sobjectEditorController.busy
                        && sobjectFieldModel.valid
                        && sobjectFieldModel.count !== 0
                    onClicked: sobjectEditorController.submit()
                }
            }
        }
    }
}
