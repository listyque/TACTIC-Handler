import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    required property string value
    property bool tagsMode: false
    property var tags: value.split(/[,\n]+/).map(s => s.trim()).filter(s => s.length > 0)
    signal saved(string value)
    signal cancelled()

    function addTags() {
        const next = tags.slice()
        for (const tag of tagInput.text.split(/[,\n]+/).map(s => s.trim())) {
            if (tag.length && next.indexOf(tag) < 0)
                next.push(tag)
        }
        tags = next
        tagInput.clear()
    }

    Component.onCompleted: Qt.callLater(function() {
        panel.openBelowItem(root, true, 4)
    })

    Controls.ScrollablePopup {
        id: panel
        objectName: "tableTextEditorPopup"
        parent: Overlay.overlay
        theme: root.theme
        preferredSurfaceWidth: 620
        maximumSurfaceHeight: 520
        settledClosePolicy: Popup.CloseOnEscape
        onOpened: {
            if (root.tagsMode) tagInput.forceActiveFocus()
            else description.forceActiveFocus()
        }
        onClosed: root.cancelled()

        Label {
            text: root.tagsMode ? qsTr("Edit tags") : qsTr("Edit description")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.bold: true
        }
        Flow {
            width: parent.width
            spacing: 6
            visible: root.tagsMode
            Repeater {
                model: root.tags
                delegate: Controls.Button {
                    required property int index
                    required property string modelData
                    theme: root.theme
                    text: modelData
                    icon.name: "close"
                    toolTip: qsTr("Remove tag") + ": " + modelData
                    width: Math.min(implicitWidth, parent.width)
                    onClicked: root.tags = root.tags.filter((_, i) => i !== index)
                }
            }
        }
        RowLayout {
            width: parent.width
            visible: root.tagsMode
            Controls.TextField {
                id: tagInput
                objectName: "tableTagInput"
                theme: root.theme
                Layout.fillWidth: true
                placeholderText: qsTr("Enter tags separated by commas")
                onAccepted: root.addTags()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Add")
                onClicked: { root.addTags(); tagInput.forceActiveFocus() }
            }
        }
        ScrollView {
            id: descriptionScroll
            width: parent.width
            height: 260
            visible: !root.tagsMode
            clip: true
            contentWidth: availableWidth
            rightPadding: descriptionBar.reservedExtent + 4
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                id: descriptionBar
                theme: root.theme
                flickableTarget: descriptionScroll.contentItem
            }
            Controls.TextArea {
                id: description
                objectName: "tableDescriptionInput"
                theme: root.theme
                text: root.value
                wrapMode: TextEdit.Wrap
            }
        }
        RowLayout {
            width: parent.width
            Item { Layout.fillWidth: true }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: panel.close()
            }
            Controls.Button {
                objectName: "tableTextEditorSave"
                theme: root.theme
                text: qsTr("Save")
                onClicked: {
                    if (root.tagsMode) root.addTags()
                    root.saved(root.tagsMode ? root.tags.join(", ") : description.text)
                }
            }
        }
    }
}
