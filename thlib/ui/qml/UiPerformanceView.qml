import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property var selectedSample: ({})

    function milliseconds(value) {
        return value >= 0 ? Number(value).toFixed(1) + " " + qsTr("ms") : "—"
    }
    function actionText(value) {
        return value.indexOf("Search tab: ") === 0
            ? qsTr("Search tab") + ": " + value.slice(12) : qsTr(value)
    }

    Rectangle { anchors.fill: parent; color: root.theme.workspace }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: qsTr("UI responsiveness")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
            }
            Controls.Button {
                objectName: "pauseUiMeasurements"
                theme: root.theme
                text: uiPerformance.recording ? qsTr("Pause measurements") : qsTr("Resume measurements")
                onClicked: uiPerformance.set_recording(!uiPerformance.recording)
            }
            Controls.CompactIconButton {
                objectName: "copyUiMeasurements"
                theme: root.theme
                iconName: "content-copy"
                toolTip: qsTr("Copy measurements")
                onClicked: uiPerformance.copy_results()
            }
            Controls.CompactIconButton {
                objectName: "clearUiMeasurements"
                theme: root.theme
                iconName: "delete"
                toolTip: qsTr("Clear measurements")
                onClicked: uiPerformance.clear()
            }
        }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Target: a visible response within 50 ms. Input measures the next frame of the clicked window; controller rows measure work and its ready frame. A frame is not proof that asynchronous loading has finished.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
        }
        Label {
            Layout.fillWidth: true
            text: qsTr("Samples: %1 · Frames over 50 ms: %2 · p95: %3 · Maximum: %4")
                .arg(uiPerformance.summary.count).arg(uiPerformance.summary.overBudget)
                .arg(root.milliseconds(uiPerformance.summary.p95))
                .arg(root.milliseconds(uiPerformance.summary.maximum))
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.rightMargin: 22
            Label { Layout.fillWidth: true; text: qsTr("Action / window"); color: root.theme.secondaryText }
            Label { Layout.preferredWidth: 96; text: qsTr("Handler"); color: root.theme.secondaryText }
            Label { Layout.preferredWidth: 96; text: qsTr("First frame"); color: root.theme.secondaryText }
            Label { Layout.preferredWidth: 96; text: qsTr("Ready frame"); color: root.theme.secondaryText }
        }
        Controls.SmoothListView {
            id: samples
            theme: root.theme
            objectName: "uiPerformanceSamples"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 4
            model: uiPerformanceModel
            delegate: Rectangle {
                id: row
                required property string action
                required property string window
                required property real handlerMs
                required property real frameMs
                required property real readyMs
                required property string details
                required property string status
                required property bool slow
                width: samples.width - 22
                height: 54
                radius: 6
                color: root.theme.panel
                border.width: row.slow ? 1 : 0
                border.color: root.theme.red
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label { Layout.fillWidth: true; text: root.actionText(row.action); elide: Text.ElideRight; color: root.theme.primaryText }
                        Label { Layout.fillWidth: true; text: row.window || qsTr(row.status); elide: Text.ElideRight; color: root.theme.secondaryText }
                    }
                    Label { Layout.preferredWidth: 96; text: root.milliseconds(row.handlerMs); color: root.theme.primaryText }
                    Label { Layout.preferredWidth: 96; text: root.milliseconds(row.frameMs); color: row.frameMs > 50 ? root.theme.red : root.theme.primaryText }
                    Label { Layout.preferredWidth: 88; text: root.milliseconds(row.readyMs); color: root.theme.primaryText }
                }
                Controls.ActivationHandler {
                    onActivated: root.selectedSample = {"action": row.action, "details": row.details, "status": row.status}
                }
            }
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
        }
        Flickable {
            Layout.fillWidth: true
            Layout.preferredHeight: 95
            clip: true
            contentHeight: detailText.height
            contentWidth: width
            Controls.TextArea {
                id: detailText
                objectName: "uiMeasurementDetails"
                width: parent.width - 20
                height: Math.max(95, implicitHeight)
                readOnly: true
                selectByMouse: true
                wrapMode: TextEdit.Wrap
                text: (root.selectedSample.action || qsTr("Select a measurement for details"))
                    + "\n" + (root.selectedSample.details || "")
                theme: root.theme
            }
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
        }
    }
}
