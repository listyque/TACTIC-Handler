import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    required property var record
    property bool compact: false
    property bool busy: false
    property bool clipboardHasImage: false
    property string statusText: ""
    property string statusIcon: "inventory_2"
    property color statusAccent: theme.secondaryText
    property bool contextEditing: false

    signal previewRequested(bool hasPreviews)
    signal moreRequested(var sourceItem)
    signal actionRequested(string command)
    signal contextBranchEdited(string branch)

    function beginContextEdit() {
        contextEditor.text = String(root.record.contextBranch || "")
        root.contextEditing = true
        Qt.callLater(function() {
            contextEditor.forceActiveFocus()
            contextEditor.selectAll()
        })
    }

    function finishContextEdit() {
        if (!root.contextEditing)
            return
        const branch = contextEditor.text
        root.contextEditing = false
        root.contextBranchEdited(branch)
    }

    function cancelContextEdit() {
        root.contextEditing = false
        contextEditor.text = String(root.record.contextBranch || "")
    }

    objectName: "commitQueueOperationSummary"
    implicitHeight: 98
    radius: theme.surfaceRadius
    color: theme.surfaceContainerLow

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        Controls.ItemPreview {
            theme: root.theme
            Layout.preferredWidth: 72
            Layout.preferredHeight: 72
            previewSize: 72
            source: root.record.previewUrl || ""
            fallbackText: root.record.previewExtension || "FILE"
            accent: root.theme.action
            cornerRadius: root.theme.itemRadius
            animateAppearance: false
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 4
            Label {
                Layout.fillWidth: true
                text: root.record.objectTitle || qsTr("Operation details")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                text: root.record.futureFileName || root.record.title
                    || qsTr("Snapshot")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                elide: Text.ElideMiddle
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Label {
                    text: root.record.process || "publish"
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    elide: Text.ElideRight
                }
                Label {
                    text: "·"
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.StatusChip {
                    id: contextChip
                    objectName: "commitQueueContextChip"
                    visible: !root.contextEditing
                    theme: root.theme
                    interactive: Boolean(root.record.canEdit) && !root.busy
                    iconName: "edit"
                    text: root.record.contextBranch
                        ? qsTr("Context: %1").arg(root.record.contextBranch)
                        : qsTr("Add context")
                    accentColor: root.record.contextBranch
                        ? root.theme.action : root.theme.secondaryText
                    Accessible.role: Accessible.Button
                    Accessible.name: text
                    onClicked: root.beginContextEdit()
                }
                Controls.TextField {
                    id: contextEditor
                    objectName: "commitQueueContextField"
                    visible: root.contextEditing
                    theme: root.theme
                    Layout.preferredWidth: 170
                    Layout.preferredHeight: 28
                    enabled: Boolean(root.record.canEdit) && !root.busy
                    placeholderText: qsTr("Context branch")
                    font.pointSize: Controls.Typography.label
                    onAccepted: root.finishContextEdit()
                    onEditingFinished: root.finishContextEdit()
                    Keys.onEscapePressed: event => {
                        root.cancelContextEdit()
                        event.accepted = true
                    }
                }
                Label {
                    visible: Boolean(root.record.fileSummary)
                    text: "·"
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Label {
                    Layout.fillWidth: true
                    visible: Boolean(root.record.fileSummary)
                    text: root.record.fileSummary || ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    elide: Text.ElideRight
                }
            }
        }

        Controls.StatusChip {
            objectName: "commitQueueOperationStatus"
            visible: !root.compact
            theme: root.theme
            text: root.statusText
            iconName: root.statusIcon
            accentColor: root.statusAccent
        }
        Controls.CompactIconButton {
            objectName: "commitQueueCapturePreviewButton"
            visible: !root.compact
            theme: root.theme
            iconName: "photo_camera"
            toolTip: qsTr("Capture screenshot")
            enabled: !root.busy && Boolean(root.record.canEdit)
            onClicked: root.actionRequested("capture")
        }
        Controls.CompactIconButton {
            objectName: "commitQueueChoosePreviewButton"
            visible: !root.compact
            theme: root.theme
            iconName: "add-photo-alternate"
            toolTip: qsTr("Choose preview images")
            enabled: !root.busy && Boolean(root.record.canEdit)
            onClicked: root.actionRequested("choose")
        }
        Controls.CompactIconButton {
            objectName: "commitQueuePastePreviewButton"
            visible: !root.compact
            theme: root.theme
            iconName: "content-paste"
            toolTip: qsTr("Paste preview image from clipboard")
            enabled: !root.busy && Boolean(root.record.canEdit)
                && root.clipboardHasImage
            onClicked: root.actionRequested("paste")
        }
        Controls.CompactIconButton {
            objectName: "commitQueueManagePreviewButton"
            visible: !root.compact
            theme: root.theme
            iconName: "collections"
            toolTip: qsTr("Manage selected previews")
            enabled: Number(root.record.previewCount || 0) > 0
            onClicked: root.actionRequested("manage")
        }
        Controls.CompactIconButton {
            objectName: "commitQueueClearPreviewsButton"
            visible: !root.compact
            theme: root.theme
            iconName: "delete_sweep"
            toolTip: qsTr("Clear operation previews")
            enabled: !root.busy && Boolean(root.record.canEdit)
                && Number(root.record.previewCount || 0) > 0
            onClicked: root.actionRequested("clear")
        }
        Controls.CompactIconButton {
            objectName: "commitQueuePreviewButton"
            visible: root.compact
            theme: root.theme
            readonly property bool hasPreviews:
                Number(root.record.previewCount || 0) > 0
            iconName: hasPreviews ? "collections" : "add-photo-alternate"
            toolTip: hasPreviews
                ? qsTr("Manage selected previews")
                : qsTr("Choose preview images")
            enabled: !root.busy
                && (hasPreviews || Boolean(root.record.canEdit))
            onClicked: root.previewRequested(hasPreviews)
        }
        Controls.CompactIconButton {
            id: previewOverflowButton
            objectName: "commitQueuePreviewOverflowButton"
            visible: root.compact
            theme: root.theme
            iconName: "more_vert"
            toolTip: qsTr("More preview actions")
            enabled: !root.busy
            onClicked: root.moreRequested(previewOverflowButton)
        }
    }
}
