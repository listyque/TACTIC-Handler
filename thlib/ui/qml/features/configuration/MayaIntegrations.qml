import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../../tactic_frame/core/foundation.mjs" as Foundation

Item {
    id: root
    required property var theme
    required property var controller

    ColumnLayout {
        anchors.fill: parent
        spacing: Foundation.spacing.compact

        Controls.Button {
            objectName: "mayaIntegrationFind"
            theme: root.theme
            text: root.controller.busy ? qsTr("Searching / applying…") : qsTr("Find Maya")
            enabled: !root.controller.busy
            onClicked: root.controller.reload()
        }
        ListView {
            id: installations
            objectName: "mayaIntegrationList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.controller.rows
            boundsBehavior: Flickable.StopAtBounds
            delegate: Controls.EditorListItem {
                required property var modelData
                width: installations.width - Foundation.controls.scrollBar.extent
                theme: root.theme
                text: "Maya " + modelData.version + (modelData.pids.length ? " · PID " + modelData.pids.join(", ") : "")
                description: modelData.profile
                badgeText: modelData.supported ? qsTr(modelData.status) : qsTr("Python 3 Maya required")
                selected: root.controller.selected.id === modelData.id
                enabled: !root.controller.busy
                onClicked: root.controller.choose(modelData.id)
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }
            Controls.SectionLabel {
                anchors.fill: parent
                visible: installations.count === 0
                theme: root.theme
                text: qsTr("Find installed or running Maya versions to manage their integrations.")
                wrapMode: Text.Wrap
                verticalAlignment: Text.AlignVCenter
            }
        }
        Controls.SelectableText {
            Layout.fillWidth: true
            Layout.maximumHeight: root.height / 4
            theme: root.theme
            visible: text.length > 0
            text: root.controller.selected.handlerRoot || ""
        }
        Flow {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            spacing: Foundation.spacing.compact
            Controls.Button {
                objectName: "mayaIntegrationInstall"
                theme: root.theme
                text: qsTr("Integrate into Maya")
                enabled: !root.controller.busy && !!root.controller.selected.supported
                onClicked: root.controller.install()
            }
            Controls.Button {
                objectName: "mayaIntegrationRemove"
                theme: root.theme
                text: qsTr("Remove integration")
                destructive: true
                enabled: !root.controller.busy && !!root.controller.selected.managed && !(root.controller.selected.pids || []).length
                onClicked: root.controller.remove()
            }
        }
        Controls.SelectableText {
            Layout.fillWidth: true
            Layout.maximumHeight: root.height / 4
            theme: root.theme
            text: root.controller.error ? qsTr(root.controller.error) : (root.controller.selected.pids || []).length ? qsTr("Close Maya before removing its integration. Installation applies on the next Maya start.") : root.controller.message ? qsTr(root.controller.message) : qsTr("Changes apply on the next Maya start. Existing shelves are preserved.")
        }
    }
}
