import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property string fieldType
    required property var fieldValue
    required property var fieldOptions
    property var fieldModel: null
    property string fieldName: ""
    property string editorMode: "edit"
    property string errorText: ""
    property bool readOnlyField: false
    property bool editorBusy: false
    property bool compact: false
    property bool autoActivate: false
    signal valueEdited(var value)
    signal cancelRequested()
    signal previewRequested()
    signal previewFilesAdded(var values)
    signal previewFileRemoved(int index)
    signal previewFilesCleared()

    implicitWidth: editorLoader.item ? editorLoader.item.implicitWidth : 0
    implicitHeight: editorLoader.item ? editorLoader.item.implicitHeight : 0

    Component.onCompleted: {
        if (autoActivate)
            activate()
    }

    function optionIndex(control) {
        const wanted = String(root.fieldValue ?? "")
        for (let index = 0; index < control.count; ++index) {
            if (String(control.valueAt(index)) === wanted)
                return index
        }
        return -1
    }

    function activate() {
        Qt.callLater(function() {
            const editor = editorLoader.item
            if (!editor)
                return
            if (editor.beginEditing)
                editor.beginEditing()
            else
                editor.forceActiveFocus(Qt.MouseFocusReason)
            if (root.fieldType === "enum"
                    || root.fieldType === "user"
                    || root.fieldType === "project"
                    || root.fieldType === "process"
                    || root.fieldType === "pipeline"
                    || root.fieldType === "status")
                editor.openPopupFromKeyboard()
            else if (editor.selectAll)
                editor.selectAll()
        })
    }

    function previewValues() {
        if (!root.fieldValue)
            return []
        if (typeof root.fieldValue !== "string"
                && root.fieldValue.length !== undefined) {
            const values = []
            for (let index = 0; index < root.fieldValue.length; ++index)
                values.push(root.fieldValue[index])
            return values
        }
        return [root.fieldValue]
    }

    Loader {
        id: editorLoader

        anchors.fill: parent
        sourceComponent: {
            if (root.fieldType === "multiline")
                return multilineEditor
            if (root.fieldType === "bool")
                return boolEditor
            if (root.fieldType === "user")
                return userEditor
            if (["enum", "project", "process", "pipeline", "status"]
                    .indexOf(root.fieldType) >= 0)
                return choiceEditor
            if (root.fieldType === "date" || root.fieldType === "datetime")
                return dateEditor
            if (root.fieldType === "preview")
                return previewEditor
            if (root.fieldType === "thumbnail")
                return thumbnailEditor
            if (root.fieldType === "parent")
                return parentEditor
            if (root.fieldType === "unsupported")
                return unsupportedEditor
            return textEditor
        }
    }

    Component {
        id: textEditor

        Controls.TextField {
            objectName: "sobjectValueTextEditor"
            theme: root.theme
            text: String(root.fieldValue ?? "")
            readOnly: root.readOnlyField
            enabled: !root.readOnlyField && !root.editorBusy
            errorState: root.errorText.length > 0
            echoMode: root.fieldType === "password"
                ? TextInput.Password : TextInput.Normal
            placeholderText: root.fieldType === "password"
                ? root.editorMode === "edit"
                    ? qsTr("Leave empty to keep the current password")
                    : qsTr("Enter a password")
                : ""
            inputMethodHints: root.fieldType === "integer"
                ? Qt.ImhDigitsOnly
                : root.fieldType === "float"
                    ? Qt.ImhFormattedNumbersOnly : Qt.ImhNone
            function insertBatchToken(token) {
                if (root.fieldType !== "string")
                    return
                insert(cursorPosition, token)
                root.valueEdited(text)
                forceActiveFocus(Qt.MouseFocusReason)
            }
            Keys.onEscapePressed: event => {
                root.cancelRequested()
                event.accepted = true
            }
            onTextEdited: root.valueEdited(text)
        }
    }

    Component {
        id: multilineEditor

        ScrollView {
            id: multilineScroll
            objectName: "sobjectValueMultilineEditor"
            implicitHeight: root.compact ? 84 : 112
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                objectName: "sobjectMultilineVerticalScrollBar_"
                    + root.fieldName
                theme: root.theme
                flickableTarget: multilineScroll.contentItem
            }

            function beginEditing() {
                multilineText.forceActiveFocus(Qt.MouseFocusReason)
            }

            Controls.TextArea {
                id: multilineText
                objectName: "sobjectValueMultilineTextEditor"
                theme: root.theme
                text: String(root.fieldValue ?? "")
                readOnly: root.readOnlyField
                enabled: !root.readOnlyField && !root.editorBusy
                errorState: root.errorText.length > 0
                wrapMode: TextEdit.Wrap
                function insertBatchToken(token) {
                    insert(cursorPosition, token)
                    root.valueEdited(text)
                    forceActiveFocus(Qt.MouseFocusReason)
                }
                Keys.onEscapePressed: event => {
                    root.cancelRequested()
                    event.accepted = true
                }
                onTextChanged: {
                    if (activeFocus)
                        root.valueEdited(text)
                }
            }
        }
    }

    Component {
        id: boolEditor

        Rectangle {
            objectName: "sobjectValueBoolEditor"
            implicitHeight: root.theme.controlHeight
            radius: root.theme.fieldRadius
            color: root.theme.surfaceContainerHigh
            border.width: 1
            border.color: root.theme.outlineVariant

            Controls.Switch {
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                theme: root.theme
                checked: Boolean(root.fieldValue)
                enabled: !root.readOnlyField && !root.editorBusy
                text: root.compact ? ""
                    : checked ? qsTr("Enabled") : qsTr("Disabled")
                Keys.onEscapePressed: event => {
                    root.cancelRequested()
                    event.accepted = true
                }
                onToggled: root.valueEdited(checked)
            }
        }
    }

    Component {
        id: choiceEditor

        Controls.ComboBox {
            id: choiceControl
            objectName: "sobjectValueChoiceEditor"
            theme: root.theme
            enabled: !root.readOnlyField && !root.editorBusy
            model: root.fieldOptions
            textRole: "label"
            valueRole: "value"
            colorRole: root.fieldType === "status"
                || root.fieldType === "process" ? "color" : ""
            iconRole: root.fieldType === "pipeline"
                || root.fieldType === "project" ? "icon" : ""
            leadingIcon: root.fieldType === "project" ? "workspaces" : ""
            translateDisplayText: false
            Component.onCompleted: currentIndex = root.optionIndex(choiceControl)
            onActivated: root.valueEdited(currentValue)
        }
    }

    Component {
        id: userEditor

        UserComboBox {
            id: userControl
            objectName: "sobjectValueUserEditor"
            theme: root.theme
            userModel: userListModel
            enabled: !root.readOnlyField && !root.editorBusy
            model: root.fieldOptions
            textRole: "label"
            valueRole: "value"
            translateDisplayText: false
            Component.onCompleted: currentIndex = root.optionIndex(userControl)
            onActivated: root.valueEdited(currentValue)
        }
    }

    Component {
        id: dateEditor

        Controls.DateField {
            objectName: "sobjectValueDateEditor"
            theme: root.theme
            text: String(root.fieldValue ?? "")
            readOnly: root.readOnlyField
            enabled: !root.readOnlyField && !root.editorBusy
            includeTime: root.fieldType === "datetime"
            placeholderText: includeTime
                ? qsTr("Date and time") : qsTr("Date")
            errorState: root.errorText.length > 0
            Keys.onEscapePressed: event => {
                root.cancelRequested()
                event.accepted = true
            }
            onAccepted: value => root.valueEdited(value)
            onEditingFinished: root.valueEdited(text)
        }
    }

    Component {
        id: parentEditor

        Rectangle {
            implicitHeight: root.theme.controlHeight
            radius: root.theme.fieldRadius
            color: root.theme.surfaceContainerHigh
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 8

                Controls.MaterialIcon {
                    name: "link"
                    size: 16
                    color: root.theme.secondaryText
                }
                Label {
                    Layout.fillWidth: true
                    text: String(root.fieldValue || qsTr("No parent object"))
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    elide: Text.ElideRight
                }
            }
        }
    }

    Component {
        id: previewEditor

        Rectangle {
            id: previewSurface
            readonly property var previewPaths: root.previewValues()

            implicitHeight: 194
            radius: root.theme.surfaceRadius
            color: previewDropArea.containsDrag
                ? root.theme.surfaceContainerHigh
                : root.theme.surfaceContainer
            border.width: 1
            border.color: previewDropArea.containsDrag
                ? root.theme.action : root.theme.outlineVariant

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    Controls.MaterialIcon {
                        name: "collections"
                        size: 18
                        color: root.theme.action
                    }
                    Label {
                        objectName: "sobjectPreviewCount"
                        Layout.fillWidth: true
                        text: previewSurface.previewPaths.length
                            ? qsTr("Preview images: %1").arg(
                                previewSurface.previewPaths.length)
                            : qsTr("Preview images")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                    }
                    Controls.Button {
                        theme: root.theme
                        compact: root.compact
                        text: root.compact ? "" : qsTr("Add images")
                        icon.name: "add-photo-alternate"
                        toolTip: qsTr("Add preview images")
                        enabled: !root.editorBusy
                        onClicked: root.previewRequested()
                    }
                    Controls.CompactIconButton {
                        visible: previewSurface.previewPaths.length > 0
                        theme: root.theme
                        iconName: "delete-sweep"
                        round: true
                        enabled: !root.editorBusy
                        toolTip: qsTr("Clear preview images")
                        onClicked: root.previewFilesCleared()
                    }
                }

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        visible: previewSurface.previewPaths.length === 0

                        Controls.MaterialIcon {
                            anchors.horizontalCenter: parent.horizontalCenter
                            name: "add-photo-alternate"
                            size: 30
                            color: root.theme.secondaryText
                        }
                        Label {
                            text: qsTr("Drop images here or choose them")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                        }
                    }

                    Flickable {
                        id: previewFlickable
                        objectName: "sobjectPreviewFlickable"
                        anchors.fill: parent
                        visible: previewSurface.previewPaths.length > 0
                        clip: true
                        contentWidth: previewRow.implicitWidth
                        contentHeight: height
                        boundsBehavior: Flickable.StopAtBounds
                        flickableDirection: Flickable.HorizontalFlick

                        Row {
                            id: previewRow
                            height: Math.max(0, parent.height - 12)
                            spacing: 8

                            Repeater {
                                id: previewRepeater
                                objectName: "sobjectPreviewRepeater"
                                model: previewSurface.previewPaths

                                delegate: Item {
                                    id: previewTile
                                    required property int index
                                    required property var modelData
                                    width: 112
                                    height: previewRow.height

                                    Controls.ItemPreview {
                                        objectName: "sobjectPreviewThumbnail_"
                                            + previewTile.index
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.bottom: previewName.top
                                        anchors.bottomMargin: 4
                                        theme: root.theme
                                        source: root.fieldModel
                                            ? root.fieldModel.preview_url(
                                                previewTile.modelData)
                                            : previewTile.modelData
                                        outlined: true
                                        fillMode: Image.PreserveAspectCrop
                                        animateAppearance: false
                                    }
                                    Label {
                                        id: previewName
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.bottom: parent.bottom
                                        height: 18
                                        text: root.fieldModel
                                            ? root.fieldModel.preview_name(
                                                previewTile.modelData)
                                            : String(previewTile.modelData)
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        elide: Text.ElideMiddle
                                    }
                                    Controls.CompactIconButton {
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: 2
                                        width: 28
                                        height: 28
                                        theme: root.theme
                                        iconName: "close"
                                        iconSize: 14
                                        round: true
                                        elevated: true
                                        enabled: !root.editorBusy
                                        toolTip: qsTr("Remove preview image")
                                        onClicked: root.previewFileRemoved(
                                            previewTile.index)
                                    }
                                }
                            }
                        }

                        ScrollBar.horizontal: Controls.ScrollBar {
                            objectName: "sobjectPreviewHorizontalScrollBar"
                            theme: root.theme
                        }
                    }
                }
            }

            DropArea {
                id: previewDropArea
                objectName: "sobjectPreviewDropArea"
                anchors.fill: parent
                enabled: !root.editorBusy
                z: 10
                onDropped: drop => {
                    if (!drop.hasUrls)
                        return
                    root.previewFilesAdded(drop.urls)
                    drop.acceptProposedAction()
                }

                Controls.DropTargetOverlay {
                    visible: previewDropArea.containsDrag
                    theme: root.theme
                    iconName: "add-photo-alternate"
                    promptText: qsTr("Drop images to add them")
                }
            }
        }
    }

    Component {
        id: thumbnailEditor

        Rectangle {
            implicitHeight: 62
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainerHigh
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 9
                Controls.MaterialIcon {
                    name: "image"
                    size: 22
                    color: root.theme.secondaryText
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Current thumbnail")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
            }
        }
    }

    Component {
        id: unsupportedEditor

        Rectangle {
            implicitHeight: 54
            radius: root.theme.fieldRadius
            color: root.theme.surfaceContainerHigh
            border.width: 1
            border.color: root.theme.outlineVariant

            Label {
                anchors.fill: parent
                anchors.margins: 12
                text: qsTr("This server field type is not editable here yet")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
