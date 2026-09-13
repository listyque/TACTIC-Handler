import QtQuick
import "." as Controls

Item {
    id: root

    required property var theme
    property var model: []
    property string currentValue: ""
    property bool darkPreview: false
    signal activated(string value)

    implicitHeight: swatches.childrenRect.height

    Flow {
        id: swatches
        width: parent.width
        spacing: 7

        Repeater {
            model: root.model

            delegate: Item {
                id: swatch
                required property var modelData

                readonly property bool selected:
                    root.currentValue === String(modelData.value || "")
                readonly property color previewColor: root.darkPreview
                    ? modelData.dark : modelData.light
                readonly property color previewBase: root.darkPreview
                    ? modelData.darkBase : modelData.lightBase
                width: 36
                height: 36

                Rectangle {
                    id: surface
                    anchors.fill: parent
                    radius: root.theme.iconButtonRadius + 4
                    color: pointer.containsMouse
                        ? root.theme.blend(
                            swatch.previewBase, swatch.previewColor, 0.08
                        ) : swatch.previewBase
                    border.width: swatch.selected
                        || pointer.containsMouse ? 2 : 1
                    border.color: swatch.selected || pointer.containsMouse
                        ? swatch.previewColor : root.theme.outlineVariant

                    Rectangle {
                        anchors.centerIn: parent
                        width: 18
                        height: 18
                        radius: 9
                        color: swatch.previewColor

                        Controls.MaterialIcon {
                            anchors.centerIn: parent
                            visible: swatch.selected
                            name: "check"
                            size: 15
                            color: root.theme.readableText(
                                swatch.previewColor
                            )
                            forceSolid: true
                        }
                    }

                    Controls.MaterialRipple {
                        id: ripple
                        theme: root.theme
                        color: Qt.rgba(
                            swatch.previewColor.r,
                            swatch.previewColor.g,
                            swatch.previewColor.b,
                            0.28
                        )
                        shapeRadius: surface.radius
                    }
                }

                MouseArea {
                    id: pointer
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: function(mouse) {
                        ripple.burst(mouse.x, mouse.y)
                    }
                    onClicked: root.activated(
                        String(swatch.modelData.value || "")
                    )
                }

                Loader {
                    active: pointer.containsMouse
                        && !root.theme.suppressToolTips
                    sourceComponent: Controls.ToolTip {
                        theme: root.theme
                        visible: true
                        text: qsTr(String(swatch.modelData.label || ""))
                    }
                }
            }
        }
    }
}
