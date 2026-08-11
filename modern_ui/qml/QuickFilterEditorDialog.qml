import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Md3Dialog {
    id: root

    required property var controller

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(680, Math.max(420, parent.width - 40))
    height: Math.min(720, Math.max(420, parent.height - 40))
    title: qsTr("Edit quick filters")
    modal: false
    closePolicy: Popup.CloseOnEscape

    contentItem: ColumnLayout {
        spacing: 12

        Label {
            Layout.fillWidth: true
            text: qsTr("Configure shared filters for %1").arg(
                root.controller.contextTitle
            )
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 10
            wrapMode: Text.WordWrap
        }

        Label {
            Layout.fillWidth: true
            visible: root.controller.error.length > 0
            text: root.controller.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pixelSize: 10
            wrapMode: Text.WordWrap
        }

        Flickable {
            id: editorFlickable
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: groupColumn.implicitHeight
            boundsBehavior: Flickable.StopAtBounds

            Column {
                id: groupColumn
                width: editorFlickable.width
                spacing: 10

                Repeater {
                    model: root.controller.groups

                    delegate: Rectangle {
                        id: groupCard
                        required property int index
                        required property var modelData
                        width: groupColumn.width
                        height: groupContent.implicitHeight + 24
                        radius: root.theme.cardRadius
                        color: root.theme.surfaceContainer
                        border.width: 1
                        border.color: root.theme.outlineVariant

                        ColumnLayout {
                            id: groupContent
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 12
                            spacing: 9

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Md3CheckBox {
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    text: qsTr(String(groupCard.modelData.title))
                                    checked: Boolean(groupCard.modelData.enabled)
                                    prominent: true
                                    enabled: !root.controller.busy
                                    onToggled: root.controller.set_group_enabled(
                                        groupCard.index, checked
                                    )
                                }
                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "arrow_upward"
                                    toolTip: qsTr("Move up")
                                    enabled: groupCard.index > 0
                                        && !root.controller.busy
                                    onClicked: root.controller.move_group(
                                        groupCard.index, -1
                                    )
                                }
                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "arrow_downward"
                                    toolTip: qsTr("Move down")
                                    enabled: groupCard.index
                                        < root.controller.groups.length - 1
                                        && !root.controller.busy
                                    onClicked: root.controller.move_group(
                                        groupCard.index, 1
                                    )
                                }
                            }

                            Flow {
                                Layout.fillWidth: true
                                spacing: 7
                                enabled: Boolean(groupCard.modelData.enabled)
                                opacity: enabled ? 1 : 0.45

                                Repeater {
                                    model: groupCard.modelData.options

                                    delegate: QuickFilterChip {
                                        required property int index
                                        required property var modelData
                                        theme: root.theme
                                        // Workflow values are project data.
                                        text: String(modelData.title || "")
                                        accent: modelData.accent
                                        showAccentMarker:
                                            modelData.showAccentMarker
                                        checked: Boolean(modelData.enabled)
                                        enabled: !root.controller.busy
                                        onClicked:
                                            root.controller.set_option_enabled(
                                                groupCard.index,
                                                index,
                                                !checked
                                            )
                                    }
                                }

                                Label {
                                    visible:
                                        groupCard.modelData.options.length === 0
                                    text: qsTr("Values are provided by the current workflow or search type.")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 9
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }
            }

            ScrollBar.vertical: Md3ScrollBar {
                theme: root.theme
                flickableTarget: editorFlickable
            }
        }
    }

    footer: Md3DialogActions {
        theme: root.theme

        Md3Button {
            theme: root.theme
            text: qsTr("Restore defaults")
            icon.name: "restart_alt"
            enabled: !root.controller.busy
            onClicked: root.controller.reset_defaults()
        }
        Md3Button {
            theme: root.theme
            text: qsTr("CANCEL")
            enabled: !root.controller.busy
            onClicked: {
                root.controller.discard()
                root.close()
            }
        }
        Md3Button {
            theme: root.theme
            text: root.controller.busy ? qsTr("Saving...") : qsTr("SAVE")
            icon.name: "save"
            highlighted: true
            enabled: root.controller.dirty && !root.controller.busy
            onClicked: root.controller.save()
        }
    }
}
