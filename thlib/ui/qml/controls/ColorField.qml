import QtQuick
import QtQuick.Layouts

RowLayout {
    id: root

    required property var theme
    property string value: ""
    property string title: qsTr("Choose a color")
    signal colorChosen(string value)

    spacing: 8
    onVisibleChanged: if (!visible && pickerLoader.item) pickerLoader.item.close()

    Rectangle {
        Layout.preferredWidth: root.theme.controlHeight
        Layout.preferredHeight: root.theme.controlHeight
        radius: root.theme.itemRadius
        color: root.value || root.theme.action
        border.width: 1
        border.color: root.theme.outlineVariant
        Accessible.ignored: true
    }
    Button {
        objectName: root.objectName + "_choose"
        Layout.fillWidth: true
        theme: root.theme
        text: qsTr("Choose color")
        icon.name: "palette"
        Accessible.description: root.value
        onClicked: {
            if (pickerLoader.item) pickerLoader.item.open()
            else pickerLoader.active = true
        }
    }
    Loader {
        id: pickerLoader
        visible: false
        active: false
        onLoaded: item.open()
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
