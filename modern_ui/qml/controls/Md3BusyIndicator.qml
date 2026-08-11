import QtQuick
import QtQuick.Controls

BusyIndicator {
    id: root

    required property var uiTheme

    implicitWidth: 24
    implicitHeight: 24
    palette.highlight: root.uiTheme.action
    palette.dark: root.uiTheme.action
    palette.light: root.uiTheme.action
}
