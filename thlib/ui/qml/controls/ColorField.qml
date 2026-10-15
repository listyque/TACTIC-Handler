import QtQuick
import QtQuick.Layouts

RowLayout {
    id: root

    required property var theme
    property string value: ""
    property string title: qsTr("Choose a color")
    signal colorChosen(string value)
    function focusEditor() { chooseButton.forceActiveFocus(); }

    implicitHeight: theme.controlHeight
    spacing: 8
    onEnabledChanged: if (!enabled && pickerLoader.picker) pickerLoader.picker.close()
    onVisibleChanged: if (!visible && pickerLoader.picker) pickerLoader.picker.close()

    Rectangle {
        Layout.preferredWidth: root.height
        Layout.preferredHeight: root.height
        Layout.minimumHeight: 0
        radius: root.theme.itemRadius
        color: root.value || root.theme.action
        border.width: 1
        border.color: root.theme.outlineVariant
        Accessible.ignored: true
    }
    Button {
        id: chooseButton
        objectName: root.objectName + "_choose"
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: 0
        theme: root.theme
        text: qsTr("Choose color")
        icon.name: "palette"
        Accessible.description: root.value
        onClicked: {
            if (pickerLoader.picker) pickerLoader.picker.open()
            else pickerLoader.active = true
        }
    }
    Loader {
        id: pickerLoader
        readonly property ColorPickerDialog picker: item as ColorPickerDialog
        visible: false
        active: false
        onLoaded: picker.open()
        sourceComponent: ColorPickerDialog {
            objectName: root.objectName + "_dialog"
            parent: root.Window.window ? root.Window.window.contentItem : null
            theme: root.theme
            title: root.title
            initialColor: root.value || root.theme.action
            onAccepted: root.colorChosen(selectedColor.toString())
        }
    }
}
