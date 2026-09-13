import QtQuick

Rectangle {
    id: root

    required property var theme

    objectName: "popupScrim"
    color: theme.scrim
    Behavior on opacity {
        NumberAnimation { duration: root.theme.popupMotionFast }
    }
}
