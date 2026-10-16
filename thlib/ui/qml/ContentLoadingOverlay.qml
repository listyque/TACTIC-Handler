import "tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property string message: qsTr("Loading…")
    property bool cancellable: false
    signal cancelRequested

    opacity: visible ? 1 : 0

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
        opacity: Foundation.controls.loadingOverlay.surfaceOpacity
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        hoverEnabled: true
    }

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(Foundation.controls.loadingOverlay.maximumWidth, Math.max(Foundation.controls.loadingOverlay.minimumWidth, root.width - Foundation.controls.loadingOverlay.horizontalMargin))
        spacing: Foundation.controls.loadingOverlay.spacing

        Controls.BusyIndicator {
            uiTheme: root.theme
            Layout.alignment: Qt.AlignHCenter
            running: root.visible
        }
        Label {
            Layout.fillWidth: true
            text: root.message
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 12
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }
        Controls.Button {
            visible: root.cancellable
            Layout.alignment: Qt.AlignHCenter
            theme: root.theme
            text: qsTr("Cancel")
            onClicked: root.cancelRequested()
        }
    }
}
