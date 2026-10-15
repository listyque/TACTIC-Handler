import QtQuick
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    required property var controller
    signal optionsPressed()
    signal optionsRequested(var sourceItem)

    height: 46
    color: root.theme.panel

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 8
        spacing: 6

        Controls.CompactIconButton {
            id: settingsButton
            Layout.preferredWidth: 36
            Layout.preferredHeight: 36
            theme: root.theme
            round: true
            backgroundColor: root.theme.surfaceContainerHigh
            iconName: "more_vert"
            iconSize: 16
            toolTip: qsTr("Snapshot Browser options")
            onPressed: root.optionsPressed()
            onClicked: root.optionsRequested(settingsButton)
        }
        Item { Layout.fillWidth: true }
        Controls.SegmentedButton {
            objectName: "snapshotPreviewImageMode"
            Layout.preferredWidth: implicitWidth
            Layout.preferredHeight: 34
            visible: root.controller.snapshot_browser_content_mode !== "files"
            theme: root.theme
            segmentWidth: 100
            minimumSegmentWidth: 88
            currentValue: root.controller.snapshot_browser_image_mode
            model: [
                {value: "fit", label: "Fit"},
                {value: "fill", label: "Fill"}
            ]
            onActivated: value =>
                root.controller.set_snapshot_browser_image_mode(value)
        }
        Item { Layout.fillWidth: true }
        RefreshIconButton {
            Layout.preferredWidth: 36
            Layout.preferredHeight: 36
            theme: root.theme
            backgroundColor: root.theme.surfaceContainerHigh
            iconSize: 16
            toolTip: qsTr("Refresh snapshots")
            onClicked: root.controller.refresh_snapshot_browser()
        }
    }

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: root.theme.separator
    }
}
