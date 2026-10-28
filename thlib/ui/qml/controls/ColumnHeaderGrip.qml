import QtQuick

Rectangle {
    id: root
    required property var theme
    property bool highlighted: false
    objectName: "columnHeaderGrip"
    anchors.right: parent.right
    anchors.verticalCenter: parent.verticalCenter
    width: 1
    height: parent.height * 0.5
    color: highlighted ? theme.action : theme.secondaryText
    opacity: highlighted ? 1 : 0.6
    Accessible.ignored: true
}
