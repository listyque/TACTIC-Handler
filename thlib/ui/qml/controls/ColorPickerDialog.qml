import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Controls.Dialog {
    id: root

    property color initialColor: theme.action
    readonly property color selectedColor: Qt.hsva(hue, saturation, brightness, 1)
    property real hue: 0
    property real saturation: 0
    property real brightness: 1

    function setColor(color) {
        hue = Math.max(0, color.hsvHue)
        saturation = color.hsvSaturation
        brightness = color.hsvValue
    }

    modal: true
    focus: true
    title: qsTr("Choose a color")
    width: Math.min(380, parent ? parent.width - 32 : 380)
    height: Math.min(implicitHeight, parent ? parent.height - 32 : implicitHeight)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    closePolicy: Popup.CloseOnEscape
    onAboutToShow: setColor(initialColor)
    Overlay.modal: Rectangle { color: root.theme.scrim }

    contentItem: Flickable {
        id: viewport
        implicitHeight: fields.implicitHeight
        clip: true
        contentHeight: fields.implicitHeight
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: fields
            width: Math.max(0, viewport.width - bar.reservedExtent - 4)
            spacing: 12

            Rectangle {
                id: plane
                objectName: root.objectName + "_plane"
                Layout.fillWidth: true
                Layout.preferredHeight: 190
                color: Qt.hsva(root.hue, 1, 1, 1)
                activeFocusOnTab: true
                Accessible.role: Accessible.Slider
                Accessible.name: qsTr("Saturation and brightness")
                Accessible.description: qsTr("Use the arrow keys to adjust the color")
                function choose(x, y) {
                    root.saturation = Math.max(0, Math.min(1, x / width))
                    root.brightness = Math.max(0, Math.min(1, 1 - y / height))
                    forceActiveFocus()
                }
                Keys.onLeftPressed: root.saturation = Math.max(0, root.saturation - 0.01)
                Keys.onRightPressed: root.saturation = Math.min(1, root.saturation + 0.01)
                Keys.onUpPressed: root.brightness = Math.min(1, root.brightness + 0.01)
                Keys.onDownPressed: root.brightness = Math.max(0, root.brightness - 0.01)
                // White/black here are color-space endpoints, not UI styling.
                Rectangle {
                    anchors.fill: parent
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: Qt.rgba(1, 1, 1, 1) }
                        GradientStop { position: 1; color: Qt.rgba(1, 1, 1, 0) }
                    }
                }
                Rectangle {
                    anchors.fill: parent
                    gradient: Gradient {
                        GradientStop { position: 0; color: Qt.rgba(0, 0, 0, 0) }
                        GradientStop { position: 1; color: Qt.rgba(0, 0, 0, 1) }
                    }
                }
                Rectangle {
                    x: Math.max(0, Math.min(plane.width - width, root.saturation * plane.width - width / 2))
                    y: Math.max(0, Math.min(plane.height - height, (1 - root.brightness) * plane.height - height / 2))
                    width: 12; height: 12; radius: 6
                    color: root.selectedColor
                    border.width: 2
                    border.color: root.theme.readableText(root.selectedColor)
                }
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    border.width: plane.activeFocus ? 2 : 1
                    border.color: plane.activeFocus ? root.theme.action : root.theme.outlineVariant
                }
                Controls.ActivationHandler { onActivated: (modifiers, x, y) => plane.choose(x, y) }
                DragHandler {
                    target: null
                    onActiveChanged: if (active) plane.choose(centroid.position.x, centroid.position.y)
                    onCentroidChanged: if (active) plane.choose(centroid.position.x, centroid.position.y)
                }
            }
            Controls.SectionLabel { theme: root.theme; text: qsTr("Hue") }
            Controls.Slider {
                id: hueSlider
                objectName: root.objectName + "_hue"
                Layout.fillWidth: true
                Layout.minimumHeight: root.theme.controlHeight
                theme: root.theme
                Accessible.name: qsTr("Hue")
                from: 0; to: 1; stepSize: 0.005
                value: root.hue
                onMoved: root.hue = value
                background: Rectangle {
                    x: hueSlider.leftPadding
                    y: hueSlider.topPadding + hueSlider.availableHeight / 2 - height / 2
                    width: hueSlider.availableWidth
                    height: 6
                    radius: 3
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: Qt.hsva(0, 1, 1, 1) }
                        GradientStop { position: 1/6; color: Qt.hsva(1/6, 1, 1, 1) }
                        GradientStop { position: 2/6; color: Qt.hsva(2/6, 1, 1, 1) }
                        GradientStop { position: 3/6; color: Qt.hsva(3/6, 1, 1, 1) }
                        GradientStop { position: 4/6; color: Qt.hsva(4/6, 1, 1, 1) }
                        GradientStop { position: 5/6; color: Qt.hsva(5/6, 1, 1, 1) }
                        GradientStop { position: 1; color: Qt.hsva(1, 1, 1, 1) }
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Rectangle {
                    Layout.preferredWidth: root.theme.controlHeight
                    Layout.preferredHeight: root.theme.controlHeight
                    radius: root.theme.itemRadius
                    color: root.selectedColor
                    border.color: root.theme.outlineVariant
                }
                Controls.TextField {
                    id: hex
                    objectName: root.objectName + "_hex"
                    Layout.fillWidth: true
                    theme: root.theme
                    Accessible.name: qsTr("Color in HEX format")
                    text: root.selectedColor.toString()
                    validator: RegularExpressionValidator { regularExpression: /^#[0-9a-fA-F]{6}$/ }
                    onEditingFinished: if (acceptableInput) root.setColor(Qt.color(text))
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar { id: bar; theme: root.theme; flickableTarget: viewport }
    }
    footer: Controls.DialogActions {
        theme: root.theme
        Controls.Button { theme: root.theme; text: qsTr("Cancel"); onClicked: root.reject() }
        Controls.Button {
            theme: root.theme
            text: qsTr("OK")
            enabled: hex.acceptableInput
            onClicked: { root.setColor(Qt.color(hex.text)); root.accept() }
        }
    }
}
