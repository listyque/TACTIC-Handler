import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.ScrollablePopup {
    id: root

    required property var historyModel
    required property bool historyLoaded
    required property bool historyLoading
    required property int historyCount
    required property string heading
    required property string emptyText
    property string entryObjectNamePrefix: root.objectName + "Entry-"
    readonly property real rowWidth: Math.max(
        0, viewport.width - verticalScrollBar.reservedExtent
    )
    signal revisionRequested(string revisionId)

    function toggleBelow(sourceItem) {
        toggleBelowItem(sourceItem, true, 6)
    }

    parent: Overlay.overlay
    preferredSurfaceWidth: 390
    minimumSurfaceWidth: 290
    maximumSurfaceHeight: 440
    contentSpacing: 4

    RowLayout {
        width: root.rowWidth
        height: root.theme.controlHeight
        spacing: 8

        Controls.MaterialIcon {
            name: "history"
            size: 18
            color: root.theme.action
        }
        Label {
            Layout.fillWidth: true
            text: root.heading
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }
        Controls.BusyIndicator {
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            uiTheme: root.theme
            running: root.historyLoading
            visible: running
        }
    }

    Label {
        width: root.rowWidth
        visible: root.historyLoaded && root.historyCount <= 1
        text: root.emptyText
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.caption
        wrapMode: Text.WordWrap
        leftPadding: 8
        rightPadding: 8
        topPadding: 8
        bottomPadding: 8
    }

    Repeater {
        model: root.historyModel

        delegate: Controls.PopupAction {
            id: revisionAction

            required property string revisionId
            required property int index
            required property string timestampPretty
            required property string timestampFull
            required property string actorDisplay
            required property string summary
            required property bool current
            required property bool selected

            objectName: root.entryObjectNamePrefix + index
            width: root.rowWidth
            height: 62
            leftPadding: 9
            rightPadding: 8
            Accessible.name: current
                ? qsTr("Current version")
                : timestampFull + ", " + actorDisplay + ", " + summary

            background: Rectangle {
                radius: root.theme.itemRadius
                color: revisionAction.down
                    ? root.theme.selected
                    : revisionAction.selected
                        ? root.theme.contentSelection
                        : revisionAction.hovered
                            ? root.theme.rowHover : "transparent"
            }

            contentItem: RowLayout {
                spacing: 9

                Controls.MaterialIcon {
                    name: revisionAction.current ? "check" : "history"
                    size: 16
                    color: revisionAction.current || revisionAction.selected
                        ? root.theme.action : root.theme.secondaryText
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Label {
                            Layout.fillWidth: true
                            text: revisionAction.current
                                ? qsTr("Current version")
                                : revisionAction.timestampPretty
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            font.weight: revisionAction.current
                                || revisionAction.selected
                                ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                            ToolTip.visible: revisionAction.hovered
                                && revisionAction.timestampFull.length > 0
                            ToolTip.text: revisionAction.timestampFull
                        }
                        Label {
                            visible: revisionAction.actorDisplay.length > 0
                            text: revisionAction.actorDisplay
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            elide: Text.ElideRight
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: revisionAction.summary
                        color: root.theme.disabledText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }
            }

            onClicked: {
                root.revisionRequested(revisionId)
                root.close()
            }
        }
    }
}
