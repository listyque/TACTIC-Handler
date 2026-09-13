import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    required property var controller
    property int currentIndex: 0
    property string recordSignature: ""

    readonly property var records: root.controller
        ? root.controller.linkedObjects || [] : []
    readonly property int count: root.records.length
    readonly property var currentPreview: root.count > 0
        ? root.records[Math.min(root.currentIndex, root.count - 1)] : ({})

    objectName: "knowledgeLinkedObjectHeader"
    visible: root.count > 0
    implicitHeight: visible ? 88 : 0
    radius: root.theme.surfaceRadius
    color: root.theme.surfaceContainer
    border.width: 1
    border.color: root.theme.outlineVariant

    function synchronizeRecords() {
        let keys = []
        for (let index = 0; index < root.count; ++index)
            keys.push(String(root.records[index].searchKey || ""))
        const signature = keys.join("\u001f")
        if (signature !== root.recordSignature) {
            root.recordSignature = signature
            root.currentIndex = 0
            return
        }
        if (root.count < 1)
            root.currentIndex = 0
        else if (root.currentIndex >= root.count)
            root.currentIndex = root.count - 1
    }

    Component.onCompleted: root.synchronizeRecords()

    Connections {
        target: root.controller || null
        function onStateChanged() { root.synchronizeRecords() }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        Item {
            id: previewAction

            objectName: "knowledgeLinkedObjectPreviewAction"
            Layout.preferredWidth: 66
            Layout.preferredHeight: 66
            enabled: String(
                root.currentPreview.searchKey || ""
            ).length > 0 && root.currentPreview.status !== "loading"
            activeFocusOnTab: enabled
            Accessible.role: Accessible.Button
            Accessible.name: qsTr("Open linked object")
            Accessible.onPressAction: root.controller.open_reference(
                String(root.currentPreview.searchKey || ""))

            Keys.onPressed: event => {
                if (event.key !== Qt.Key_Return
                        && event.key !== Qt.Key_Enter
                        && event.key !== Qt.Key_Space)
                    return
                root.controller.open_reference(
                    String(root.currentPreview.searchKey || ""))
                event.accepted = true
            }

            Controls.ItemPreview {
                objectName: "knowledgeLinkedObjectPreview"
                anchors.fill: parent
                theme: root.theme
                source: String(root.currentPreview.previewUrl || "")
                fallbackIcon: "sobject"
                fallbackText: ""
                previewSize: 66
                round: false
                outlined: true
                selected: previewAction.activeFocus
                accent: root.theme.action
                animateAppearance: false
            }

            Controls.ActivationHandler {
                enabled: previewAction.enabled
                onActivated: root.controller.open_reference(
                    String(root.currentPreview.searchKey || ""))
            }

            HoverHandler {
                enabled: previewAction.enabled
                cursorShape: Qt.PointingHandCursor
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Label {
                objectName: "knowledgeLinkedObjectTitle"
                Layout.fillWidth: true
                text: String(root.currentPreview.title || qsTr("Linked object"))
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                objectName: "knowledgeLinkedObjectDescription"
                Layout.fillWidth: true
                text: String(
                    root.currentPreview.description
                    || root.currentPreview.detail || "")
                visible: text.length > 0
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
            Label {
                objectName: "knowledgeLinkedObjectSubtitle"
                Layout.fillWidth: true
                text: String(root.currentPreview.subtitle || "")
                visible: text.length > 0
                color: root.theme.action
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                elide: Text.ElideRight
            }
        }

        RowLayout {
            visible: root.count > 1
            spacing: 2

            Controls.CompactIconButton {
                objectName: "knowledgeLinkedObjectPrevious"
                theme: root.theme
                iconName: "chevron-left"
                toolTip: qsTr("Previous linked object")
                enabled: root.currentIndex > 0
                onClicked: root.currentIndex -= 1
            }
            Label {
                objectName: "knowledgeLinkedObjectCounter"
                text: (root.currentIndex + 1) + " / " + root.count
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
            }
            Controls.CompactIconButton {
                objectName: "knowledgeLinkedObjectNext"
                theme: root.theme
                iconName: "chevron-right"
                toolTip: qsTr("Next linked object")
                enabled: root.currentIndex + 1 < root.count
                onClicked: root.currentIndex += 1
            }
        }

        Controls.CompactIconButton {
            objectName: "knowledgeLinkedObjectUnlink"
            visible: Boolean(root.controller && root.controller.editing)
            theme: root.theme
            iconName: "link_off"
            iconColor: root.theme.error
            toolTip: qsTr("Unlink object from article")
            enabled: String(root.currentPreview.searchKey || "").length > 0
            onClicked: {
                if (root.controller)
                    root.controller.unlink_object(
                        String(root.currentPreview.searchKey || ""))
            }
        }

        Controls.CompactIconButton {
            objectName: "knowledgeLinkedObjectOpen"
            theme: root.theme
            iconName: "open_in_new"
            toolTip: qsTr("Open linked object")
            enabled: String(root.currentPreview.searchKey || "").length > 0
                && root.currentPreview.status !== "loading"
            onClicked: {
                if (root.controller)
                    root.controller.open_reference(
                        String(root.currentPreview.searchKey || ""))
            }
        }
    }
}
