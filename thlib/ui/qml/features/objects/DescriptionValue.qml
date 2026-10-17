import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame/features/objects/description.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var model
    property string value: ""
    property string html: ""
    property bool internalChange: false
    signal valueEdited(string value)
    signal editingFinished(string value)
    signal linkActivated(string link)
    function focusEditor() {
        editor.forceActiveFocus();
    }
    function syncText() {
        if (editor.text === value)
            return;
        internalChange = true;
        editor.text = value;
        internalChange = false;
    }
    onValueChanged: syncText()
    Component.onCompleted: syncText()
    Controls.TextArea {
        id: editor
        objectName: "descriptionTextInput"
        theme: root.theme
        anchors.fill: parent
        visible: root.model.editable
        enabled: root.model.enabled
        placeholderText: root.model.placeholder
        errorState: root.model.outline === "error"
        emphasizedOutline: root.model.emphasized
        activeOutlineColor: root.theme[root.model.outline]
        padding: UI.metrics.textPadding
        bottomPadding: root.model.bottomPadding
        font.pixelSize: root.model.fontRole === "menuHeading" ? 10 : 11
        onTextChanged: if (!root.internalChange && activeFocus)
            root.valueEdited(text)
        onActiveFocusChanged: if (!activeFocus && !root.model.managed)
            root.editingFinished(text)
    }
    Rectangle {
        anchors.fill: parent
        visible: !root.model.editable
        radius: root.theme.surfaceRadius
        color: root.theme.surfaceContainerHigh
        border.width: 1
        border.color: root.theme.outline
        Flickable {
            id: reader
            anchors.fill: parent
            anchors.margins: 1
            clip: true
            contentHeight: readText.height + UI.metrics.textPadding + root.model.bottomPadding
            boundsBehavior: Flickable.StopAtBounds
            Controls.SelectableText {
                id: readText
                x: UI.metrics.textPadding
                y: UI.metrics.textPadding
                width: Math.max(0, reader.width - UI.metrics.textPadding * 2 - 12)
                height: contentHeight
                theme: root.theme
                richText: root.value.length > 0
                text: root.value.length ? root.html : root.model.empty
                font: Qt.font({
                    family: root.theme.fontFamily,
                    pixelSize: 13,
                    hintingPreference: Font.PreferVerticalHinting
                })
                color: root.value.length ? root.theme.primaryText : root.theme.secondaryText
                onLinkActivated: link => root.linkActivated(link)
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }
        }
    }
}
