import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var theme
    required property string title
    required property string emptyText
    required property var sourceModel
    required property string actionIcon
    signal actionRequested(string searchKey)

    radius: 14
    color: root.theme.panel
    border.width: 1
    border.color: root.theme.outline

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 7
        Label {
            text: root.title
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 12
            font.weight: Font.DemiBold
        }
        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.sourceModel
            clip: true
            spacing: 5
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
            delegate: Rectangle {
                required property string searchKey
                required property string title
                required property string subtitle
                width: list.width
                height: 58
                radius: 10
                color: rowMouse.containsMouse
                    ? root.theme.rowHover : root.theme.panelRaised
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 6
                    spacing: 7
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Label {
                            Layout.fillWidth: true
                            text: title
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 11
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: subtitle
                            visible: text.length > 0
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 9
                            elide: Text.ElideRight
                        }
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: root.actionIcon
                        round: true
                        onClicked: root.actionRequested(searchKey)
                    }
                }
                MouseArea {
                    id: rowMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton
                }
            }
            Label {
                anchors.centerIn: parent
                visible: list.count === 0 && !sobjectLinkController.busy
                text: root.emptyText
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 10
            }
        }
    }
}
