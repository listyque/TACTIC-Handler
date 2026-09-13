import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var metrics
    required property var snapshotProcessModel
    required property var controller

    spacing: 10

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 64
        radius: root.theme.surfaceRadius
        color: root.theme.panel
        border.width: 1
        border.color: root.theme.separator

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 14
            spacing: 10
            Controls.MaterialIcon {
                name: "account-tree"
                size: 18
                color: root.theme.action
            }
            Label {
                Layout.fillWidth: true
                text: qsTr("SNAPSHOTS BY PROCESS")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
            }
            Label {
                text: qsTr("%1 processes · %2 snapshots · %3 files")
                    .arg(root.metrics.snapshotProcesses || 0)
                    .arg(root.metrics.snapshots || 0)
                    .arg(root.metrics.files || 0)
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
            }
        }
    }

    Repeater {
        id: snapshotProcessRepeater
        model: root.snapshotProcessModel
        delegate: Rectangle {
            id: processRow

            required property string value
            required property string label
            required property string accent
            required property int snapshotCount
            required property int fileCount
            required property string sizeText
            required property var snapshots
            required property var files
            property bool expanded: false

            Layout.fillWidth: true
            Layout.preferredHeight: processLayout.implicitHeight + 16
            radius: root.theme.surfaceRadius
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.separator

            ColumnLayout {
                id: processLayout
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 62

                    Controls.ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        hovered: processHover.hovered
                        normalColor: root.theme.surfaceContainerHigh
                        separatorVisible: false
                        railVisible: true
                        accent: processRow.accent
                    }
                    HoverHandler {
                        id: processHover
                        cursorShape: Qt.PointingHandCursor
                    }
                    Controls.ActivationHandler {
                        onActivated: processRow.expanded = !processRow.expanded
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10
                        Controls.MaterialIcon {
                            name: processRow.expanded
                                ? "keyboard-arrow-down" : "keyboard-arrow-right"
                            size: 18
                            color: root.theme.secondaryText
                        }
                        Rectangle {
                            Layout.preferredWidth: 38
                            Layout.preferredHeight: 38
                            radius: 12
                            color: root.theme.panelRaised
                            Controls.MaterialIcon {
                                anchors.centerIn: parent
                                name: "workflow"
                                size: 17
                                color: processRow.accent
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: processRow.label
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.bodyLarge
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: qsTr("%1 snapshots · %2 files · %3")
                                    .arg(processRow.snapshotCount)
                                    .arg(processRow.fileCount)
                                    .arg(processRow.sizeText)
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                        Controls.StatusChip {
                            theme: root.theme
                            text: String(processRow.snapshotCount)
                            iconName: "snapshot"
                            accentColor: processRow.accent
                        }
                    }
                }

                Loader {
                    id: branchLoader
                    Layout.fillWidth: true
                    Layout.preferredHeight: active && item ? item.implicitHeight : 0
                    active: processRow.expanded
                    visible: active

                    sourceComponent: Component {
                        ColumnLayout {
                            width: branchLoader.width
                            spacing: 8

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                Layout.leftMargin: 10
                                Layout.rightMargin: 10
                                color: root.theme.separator
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.leftMargin: 10
                                Layout.rightMargin: 10
                                Controls.MaterialIcon {
                                    name: "snapshot"
                                    size: 15
                                    color: processRow.accent
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("SNAPSHOTS AND VERSIONS")
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    font.weight: Font.DemiBold
                                }
                                Label {
                                    text: qsTr("%1 snapshots").arg(processRow.snapshotCount)
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                }
                            }
                            Repeater {
                                model: processRow.snapshots
                                delegate: Item {
                                    id: snapshotRow
                                    required property int modelIndex
                                    required property string title
                                    required property string context
                                    required property string version
                                    required property string author
                                    required property string timestamp
                                    required property string timestampPretty
                                    required property string timestampFull
                                    required property string previewUrl
                                    required property int fileCount
                                    required property string sizeText
                                    required property string repository
                                    required property bool isLatest
                                    required property bool isVersionless

                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 72
                                    Controls.ItemSurface {
                                        anchors.fill: parent
                                        theme: root.theme
                                        hovered: snapshotHover.hovered
                                        normalColor: root.theme.surfaceContainerHigh
                                        separatorVisible: false
                                        railVisible: true
                                        accent: processRow.accent
                                    }
                                    HoverHandler {
                                        id: snapshotHover
                                        cursorShape: Qt.PointingHandCursor
                                    }
                                    Controls.ActivationHandler {
                                        onActivated: root.controller.open_snapshot(snapshotRow.modelIndex)
                                    }
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 10
                                        Controls.ItemPreview {
                                            Layout.preferredWidth: 54
                                            Layout.preferredHeight: 54
                                            theme: root.theme
                                            source: snapshotRow.previewUrl
                                            fallbackIcon: "snapshot"
                                            fallbackText: snapshotRow.version
                                            previewSize: 54
                                            outlined: true
                                            animateAppearance: false
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 3
                                            Label {
                                                Layout.fillWidth: true
                                                text: snapshotRow.title
                                                color: root.theme.primaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Controls.Typography.bodyLarge
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                            }
                                            Label {
                                                Layout.fillWidth: true
                                                text: [snapshotRow.context, snapshotRow.author,
                                                    snapshotRow.repository]
                                                    .filter(value => String(value).length > 0)
                                                    .join("  ·  ")
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Controls.Typography.caption
                                                elide: Text.ElideRight
                                            }
                                            Label {
                                                id: snapshotTimestampLabel
                                                Layout.fillWidth: true
                                                text: qsTr("%1 files · %2 · %3")
                                                    .arg(snapshotRow.fileCount)
                                                    .arg(snapshotRow.sizeText)
                                                    .arg(snapshotRow.timestampPretty)
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Controls.Typography.caption
                                                elide: Text.ElideRight
                                                ToolTip.visible: snapshotTimestampHover.hovered
                                                    && snapshotRow.timestampFull.length > 0
                                                ToolTip.text: snapshotRow.timestampFull
                                                HoverHandler { id: snapshotTimestampHover }
                                            }
                                        }
                                        Controls.StatusChip {
                                            theme: root.theme
                                            text: snapshotRow.version
                                            iconName: snapshotRow.isVersionless
                                                ? "sync" : "history"
                                            accentColor: snapshotRow.isLatest
                                                ? root.theme.green : root.theme.action
                                        }
                                        Controls.MaterialIcon {
                                            name: "arrow-forward"
                                            size: 15
                                            color: root.theme.secondaryText
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.leftMargin: 10
                                Layout.rightMargin: 10
                                Layout.topMargin: 4
                                visible: processRow.files.length > 0
                                Controls.MaterialIcon {
                                    name: "folder"
                                    size: 15
                                    color: processRow.accent
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("FILES")
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    font.weight: Font.DemiBold
                                }
                                Label {
                                    text: qsTr("%1 files · %2")
                                        .arg(processRow.fileCount).arg(processRow.sizeText)
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                }
                            }
                            Repeater {
                                model: processRow.files
                                delegate: AttachmentCard {
                                    id: fileRow
                                    required property string token
                                    required property bool exists
                                    Layout.fillWidth: true
                                    theme: root.theme
                                    local: fileRow.exists
                                    animatePreview: false
                                    onActivated: root.controller.activate_file(fileRow.token)
                                    onContextRequested: (x, y) => {
                                        if (fileRow.exists)
                                            root.controller.show_file_folder(fileRow.token)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.preferredHeight: 72
        visible: snapshotProcessRepeater.count === 0
        Item { Layout.fillWidth: true }
        Controls.MaterialIcon {
            name: "snapshot"
            size: 20
            color: root.theme.secondaryText
        }
        Label {
            text: qsTr("No snapshots found")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
        }
        Item { Layout.fillWidth: true }
    }
}
