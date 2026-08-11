import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme

    Connections {
        target: sobjectLinkController
        function onSaved() {
            windowModel.close_window("link_sobjects")
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ColumnLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.topMargin: 16
            Layout.bottomMargin: 12
            spacing: 8
            Label {
                text: qsTr("Link sObjects")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            Md3TextField {
                id: linkSearch
                theme: root.theme
                Layout.fillWidth: true
                placeholderText: qsTr("Search available objects")
                color: root.theme.primaryText
                placeholderTextColor: root.theme.secondaryText
                enabled: !sobjectLinkController.busy
                selectByMouse: true
                onTextEdited: searchDelay.restart()
                onAccepted: {
                    searchDelay.stop()
                    sobjectLinkController.search(text)
                }
                background: Rectangle {
                    radius: 12
                    color: root.theme.panelRaised
                    border.width: 1
                    border.color: linkSearch.activeFocus
                        ? root.theme.action : root.theme.outline
                }
            }
            Timer {
                id: searchDelay
                interval: 320
                onTriggered: sobjectLinkController.search(linkSearch.text)
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.bottomMargin: 12
            spacing: 12

            LinkList {
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                title: qsTr("Available")
                emptyText: linkSearch.text.length
                    ? qsTr("No matching objects")
                    : qsTr("No available objects")
                sourceModel: linkAvailableModel
                actionIcon: "arrow_forward"
                onActionRequested:
                    searchKey => sobjectLinkController.add(searchKey)
            }
            LinkList {
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                title: qsTr("Linked")
                emptyText: qsTr("No linked objects")
                sourceModel: linkCurrentModel
                actionIcon: "link_off"
                onActionRequested:
                    searchKey => sobjectLinkController.remove(searchKey)
            }
        }

        Label {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.bottomMargin: visible ? 10 : 0
            visible: sobjectLinkController.error.length > 0
            text: sobjectLinkController.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pixelSize: 10
            wrapMode: Text.WordWrap
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            color: root.theme.panel
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: root.theme.separator
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                Md3BusyIndicator {
                    uiTheme: root.theme
                    running: sobjectLinkController.busy
                    visible: running
                }
                Item { Layout.fillWidth: true }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    enabled: !sobjectLinkController.busy
                    onClicked: windowModel.close_window("link_sobjects")
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Save links")
                    highlighted: true
                    enabled: !sobjectLinkController.busy
                        && sobjectLinkController.dirty
                    onClicked: sobjectLinkController.save()
                }
            }
        }
    }
}
