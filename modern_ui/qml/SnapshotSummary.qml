import QtQuick
import QtQuick.Controls

Item {
    id: root

    required property var theme
    property string title: ""
    property string description: ""
    property string version: ""
    property string revision: ""
    property string repository: ""
    property string repositoryColor: ""
    property string fileSize: ""
    property string author: ""
    property string timestamp: ""
    property bool fileExists: true
    property bool isLatest: false
    property var infoChips: []
    property bool selected: false

    implicitHeight: 59

    Column {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: 4

        Row {
            width: parent.width
            spacing: 7

            Label {
                width: Math.max(80, parent.width - snapshotMeta.implicitWidth - 10)
                text: root.title
                color: root.selected
                    ? root.theme.selectedText : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 11
                font.weight: Font.DemiBold
                elide: Text.ElideMiddle
            }

            Row {
                id: snapshotMeta
                spacing: 5

                Rectangle {
                    visible: root.isLatest
                    width: visible ? latestLabel.implicitWidth + 10 : 0
                    height: 16
                    radius: 8
                    color: root.theme.selected

                    Label {
                        id: latestLabel
                        anchors.centerIn: parent
                        text: qsTr("LATEST")
                        color: root.theme.action
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
                        font.weight: Font.Bold
                    }
                }

                Label {
                    text: root.version
                    color: root.theme.action
                    font.family: root.theme.fontFamily
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                }

                Label {
                    visible: root.revision.length > 0
                    text: root.revision
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 9
                }

                Label {
                    visible: root.repository.length > 0
                    text: root.repository
                    color: root.repositoryColor || root.theme.action
                    font.family: root.theme.fontFamily
                    font.pixelSize: 9
                }
            }
        }

        Row {
            width: parent.width
            height: 17
            spacing: 5
            clip: true

            Repeater {
                model: [
                    {"text": root.fileSize, "alert": false},
                    {"text": root.author, "alert": false},
                    {"text": root.timestamp, "alert": false},
                    {"text": root.fileExists ? "" : "FILE OFFLINE", "alert": true}
                ]

                delegate: Rectangle {
                    required property var modelData
                    visible: modelData.text.length > 0
                    width: visible
                        ? Math.min(
                            142, Math.ceil(snapshotInfoMetrics.advanceWidth) + 12
                        ) : 0
                    height: 17
                    radius: height / 2
                    color: modelData.alert
                        ? root.theme.errorContainer
                        : root.selected ? root.theme.selected : "transparent"
                    border.width: 1
                    border.color: modelData.alert
                        ? root.theme.missingFile
                        : root.selected ? root.theme.action : root.theme.outline

                    TextMetrics {
                        id: snapshotInfoMetrics
                        text: modelData.text
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
                        font.weight: modelData.alert ? Font.Bold : Font.Normal
                    }

                    Label {
                        id: snapshotInfoText
                        anchors.centerIn: parent
                        width: parent.width - 10
                        text: modelData.text
                        color: modelData.alert
                            ? root.theme.missingFile
                            : root.selected
                                ? root.theme.selectedText
                                : root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
                        font.weight: modelData.alert ? Font.Bold : Font.Normal
                        elide: Text.ElideRight
                    }
                }
            }
        }

        Row {
            width: parent.width
            height: 18
            spacing: 9
            clip: true

            Label {
                width: root.infoChips && root.infoChips.length
                    ? Math.max(48, parent.width * 0.36) : parent.width
                visible: root.description.length > 0
                text: root.description
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 9
                elide: Text.ElideRight
            }

            Repeater {
                model: root.infoChips || []

                delegate: Rectangle {
                    required property var modelData
                    height: 17
                    width: Math.min(132, snapshotChipText.implicitWidth + 12)
                    radius: height / 2
                    color: root.selected
                        ? root.theme.selected : root.theme.panelRaised
                    border.width: 1
                    border.color: root.selected
                        ? root.theme.action : root.theme.outline

                    Label {
                        id: snapshotChipText
                        anchors.centerIn: parent
                        width: parent.width - 10
                        text: modelData.label + ": " + modelData.value
                        color: root.selected
                            ? root.theme.selectedText : root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }
}
