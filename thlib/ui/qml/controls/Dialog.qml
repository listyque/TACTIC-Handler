import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Controls.Basic as Basic
import Qt5Compat.GraphicalEffects
import "." as Controls

Basic.Dialog {
    id: control

    required property var theme
    property bool translateTitle: true

    modal: false
    spacing: 12
    padding: 20
    leftPadding: padding
    rightPadding: padding
    topPadding: padding
    bottomPadding: padding
    leftInset: 0
    rightInset: 0
    topInset: 0
    bottomInset: 0

    Overlay.modal: Controls.PopupScrim { theme: control.theme }

    header: Item {
        implicitHeight: control.title.length > 0 ? 62 : 0
        visible: implicitHeight > 0
        clip: true

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: parent.height + control.theme.dialogRadius
            radius: control.theme.dialogRadius
            color: control.theme.surfaceContainerHighest
            border.width: 1
            border.color: control.theme.outlineVariant
        }

        Text {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: control.leftPadding
            anchors.rightMargin: control.rightPadding
            text: control.translateTitle ? qsTr(control.title) : control.title
            color: control.theme.primaryText
            font.family: control.theme.fontFamily
            font.pixelSize: 16
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: control.theme.outlineVariant
        }
    }

    background: Item {
        DropShadow {
            anchors.fill: surface
            source: surface
            horizontalOffset: 0
            verticalOffset: 6
            radius: 14
            samples: 29
            color: control.theme.dialogShadow
            transparentBorder: true
        }
        Rectangle {
            id: surface
            anchors.fill: parent
            radius: control.theme.dialogRadius
            color: control.theme.surfaceContainerHigh
            border.width: 1
            border.color: control.theme.outlineVariant
        }
    }
}
