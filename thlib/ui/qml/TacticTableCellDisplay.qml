pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property var columnsController
    required property var userModel
    required property string nodeId
    required property string kind
    required property var cell
    required property string textValue
    required property int columnIndex
    required property bool previewActive
    required property string previewUrl
    required property bool previewRevealed
    required property string title
    required property string accent
    required property int comments
    required property int tasks
    required property var displayOptions
    property bool effectsEnabled: true
    property bool scrolling: false
    property bool selectedTaskPreviewActive: false
    signal taskPreviewHoverChanged(bool hovered)

    signal processCountMenuRequested(string panel, var anchorItem)

    Loader {
        anchors.fill: parent
        sourceComponent: {
            if (root.kind === "structured")
                return structuredCell
            if (root.kind === "boolean")
                return booleanCell
            if (root.kind === "thumbnail")
                return thumbnailCell
            if (root.kind === "notes")
                return notesCell
            if ([
                    "sobject_detail", "checkin", "explorer", "file_list",
                    "metadata", "delete"
                ].indexOf(root.kind) >= 0)
                return actionCell
            if (root.kind === "completion")
                return completionCell
            if (root.kind === "tasks")
                return tasksCell
            return textCell
        }
    }

    Component {
        id: textCell

        Item {
            Label {
                id: label
                anchors.fill: parent
                leftPadding: root.columnIndex === 0 ? 14 : 10
                rightPadding: 10
                verticalAlignment: Text.AlignVCenter
                text: root.cell.label === "No version" ? qsTr("No version")
                    : root.cell.label === "Latest" ? qsTr("Latest")
                    : root.cell.label === "Current" ? qsTr("Current")
                    : root.textValue
                elide: Text.ElideRight
                color: root.kind === "link"
                    ? root.theme.action : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: root.columnIndex === 0
                    ? Font.DemiBold : Font.Normal
                font.underline: root.kind === "link"
            }
            TapHandler {
                enabled: root.kind === "link"
                    && String(root.cell.href || "").length > 0
                acceptedButtons: Qt.LeftButton
                onTapped: Qt.openUrlExternally(String(root.cell.href))
            }
            HoverHandler {
                id: hover
                enabled: root.kind === "link"
                    || String(root.cell.tooltip || "").length > 0
                    || String(root.cell.error || "").length > 0
                    || label.truncated
                cursorShape: root.kind === "link"
                    ? Qt.PointingHandCursor : Qt.ArrowCursor
            }
            Controls.ToolTip {
                theme: root.theme
                visible: hover.hovered && (
                    String(root.cell.error || "").length > 0
                    || String(root.cell.tooltip || "").length > 0
                    || label.truncated
                )
                text: String(root.cell.error || root.cell.tooltip || "")
                    || root.textValue
            }
        }
    }

    Component {
        id: structuredCell

        TacticStructuredTableCell {
            theme: root.theme
            cell: root.cell
            maximumHeight: Number(String(root.displayOptions.height
                || (root.cell.language === "xml" ? 600 : 300)).replace("px", ""))
        }
    }

    Component {
        id: booleanCell

        Controls.CheckBox {
            anchors.centerIn: parent
            enabled: false
            theme: root.theme
            checked: ["1", "true", "yes", "on"].indexOf(
                root.textValue.toLowerCase()
            ) >= 0
        }
    }

    Component {
        id: thumbnailCell

        Item {
            Controls.ItemPreview {
                objectName: "tableCellPreview"
                anchors.centerIn: parent
                width: Math.max(0, Math.min(parent.width, parent.height) - 8)
                height: width
                theme: root.theme
                active: root.previewActive
                source: root.previewUrl
                previewSize: width
                fallbackIcon: "sobject"
                fallbackText: root.title
                accent: root.accent
                round: true
                outlined: false
                fillMode: Image.PreserveAspectCrop
                animateAppearance: !root.previewRevealed && root.previewActive
                effectsEnabled: root.effectsEnabled
                Accessible.ignored: true
                onImageReady: {
                    if (!root.previewRevealed)
                        root.controller.mark_item_preview_revealed(root.nodeId)
                }
            }
        }
    }

    Component {
        id: notesCell

        Item {
            id: noteCell
            readonly property var noteRecords: {
                const countRevision = root.comments
                return root.controller.process_count_actions(
                    root.nodeId, "notes"
                ).filter(record => Number(record.badgeCount || 0) > 0)
            }
            ListView {
                id: noteList
                objectName: "tableNoteList"
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 7
                anchors.rightMargin: contentHeight > height ? 16 : 7
                y: Math.round(Math.max(4, (parent.height - height) / 2))
                height: Math.min(
                    Math.max(0, parent.height - 8),
                    noteCell.noteRecords.length * 26
                        + Math.max(0, noteCell.noteRecords.length - 1) * spacing
                )
                visible: noteCell.noteRecords.length > 0
                model: noteCell.noteRecords
                spacing: 2
                clip: true
                reuseItems: true
                boundsBehavior: Flickable.StopAtBounds

                delegate: Rectangle {
                        id: noteRecord

                        required property int index
                        required property var modelData
                        readonly property color accentColor:
                            String(modelData.accent || "").length > 0
                                ? modelData.accent : root.theme.action
                        readonly property string processTitle: String(
                            modelData.title || modelData.process || "publish"
                        )
                        objectName: "tableNoteRecord_" + index
                        width: noteList.width
                        height: 26
                        radius: root.theme.itemRadius
                        color: root.theme.overlay(
                            root.theme.surfaceContainerHigh,
                            accentColor, noteHover.hovered ? 0.16 : 0.08
                        )
                        border.width: 1
                        border.color: root.theme.overlay(
                            root.theme.outlineVariant, accentColor, 0.32
                        )
                        Accessible.role: Accessible.Button
                        Accessible.name: processTitle + " ("
                            + Number(modelData.badgeCount || 0) + ")"

                        Rectangle {
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            width: 3
                            radius: width / 2
                            color: noteRecord.accentColor
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 7
                            anchors.rightMargin: 7
                            spacing: 5
                            Controls.MaterialIcon {
                                Layout.preferredWidth: 16
                                name: "comment"
                                size: 14
                                color: noteRecord.accentColor
                            }
                            Label {
                                Layout.fillWidth: true
                                text: noteRecord.processTitle
                                elide: Text.ElideRight
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                            }
                            Label {
                                objectName: "tableNoteCount_" + noteRecord.index
                                text: "(" + Number(
                                    noteRecord.modelData.badgeCount || 0
                                ) + ")"
                                color: noteRecord.accentColor
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.DemiBold
                            }
                        }
                        HoverHandler {
                            id: noteHover
                            cursorShape: Qt.PointingHandCursor
                        }
                        Controls.ActivationHandler {
                            onActivated: root.controller.open_process_details(
                                root.nodeId, "notes", String(
                                    noteRecord.modelData.process || "publish"
                                )
                            )
                        }
                }

                ScrollBar.vertical: Controls.ScrollBar {
                    objectName: "tableNotesScrollBar"
                    theme: root.theme
                    flickableTarget: noteList
                }
            }

            Controls.ItemCountActionButton {
                id: noteButton
                objectName: "tableCellNotes"
                anchors.centerIn: parent
                visible: noteCell.noteRecords.length === 0
                width: 34
                height: 34
                theme: root.theme
                iconName: "comment"
                count: root.comments
                activeColor: root.theme.error
                toolTip: qsTr("Add note")
                onClicked:
                    root.processCountMenuRequested("notes", noteButton)
            }
        }
    }

    Component {
        id: actionCell

        TacticTableActionCell {
            theme: root.theme
            kind: root.kind
            cell: root.cell
            onClicked: root.controller.invoke_table_widget_action(
                root.kind, root.nodeId, root.cell
            )
        }
    }

    Component {
        id: completionCell

        TacticCompletionCell {
            theme: root.theme
            percent: Number(root.cell.percent || 0)
            text: root.textValue
        }
    }

    Component {
        id: tasksCell

        TacticTaskCell {
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 6
            anchors.topMargin: 3
            anchors.bottomMargin: 3
            theme: root.theme
            controller: root.controller
            columnsController: root.columnsController
            userModel: root.userModel
            nodeId: root.nodeId
            records: root.cell.tasks || []
            options: root.displayOptions
            taskCount: root.tasks
            scrolling: root.scrolling
            selectedPreviewActive: root.selectedTaskPreviewActive
            onPreviewHoverChanged: hovered => root.taskPreviewHoverChanged(hovered)
        }
    }
}
