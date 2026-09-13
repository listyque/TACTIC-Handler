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

    signal processCountMenuRequested(string panel, var anchorItem)

    Loader {
        anchors.fill: parent
        sourceComponent: {
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
                text: root.textValue
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
                    || String(root.cell.error || "").length > 0
                    || label.truncated
                cursorShape: root.kind === "link"
                    ? Qt.PointingHandCursor : Qt.ArrowCursor
            }
            Controls.ToolTip {
                theme: root.theme
                visible: hover.hovered && (
                    String(root.cell.error || "").length > 0
                    || label.truncated
                )
                text: String(root.cell.error || "") || root.textValue
            }
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

        Controls.ItemPreview {
            objectName: "tableCellPreview"
            anchors.centerIn: parent
            width: Math.max(20, Math.min(64, parent.width - 20,
                                        parent.height - 12))
            height: width
            theme: root.theme
            active: root.previewActive
            source: root.previewUrl
            previewSize: width
            fallbackIcon: "sobject"
            fallbackText: root.title
            accent: root.accent
            round: false
            outlined: false
            animateAppearance: !root.previewRevealed && root.previewActive
            effectsEnabled: root.effectsEnabled
            Accessible.ignored: true
            onImageReady: {
                if (!root.previewRevealed)
                    root.controller.mark_item_preview_revealed(root.nodeId)
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
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.leftMargin: 7
                anchors.rightMargin: contentHeight > height ? 16 : 7
                anchors.topMargin: 4
                anchors.bottomMargin: 4
                visible: noteCell.noteRecords.length > 0
                model: noteCell.noteRecords
                spacing: 1
                clip: true
                reuseItems: true
                boundsBehavior: Flickable.StopAtBounds

                delegate: Item {
                        id: noteRecord

                        required property int index
                        required property var modelData
                        objectName: "tableNoteRecord_" + index
                        width: noteList.width
                        height: 22
                        Accessible.role: Accessible.Button
                        Accessible.name: String(
                            modelData.process || "publish"
                        ) + " (" + Number(modelData.badgeCount || 0) + ")"

                        RowLayout {
                            anchors.fill: parent
                            spacing: 5
                            Controls.MaterialIcon {
                                Layout.preferredWidth: 16
                                name: "comment"
                                size: 15
                                color: root.theme.secondaryText
                            }
                            Label {
                                Layout.fillWidth: true
                                text: String(
                                    noteRecord.modelData.process || "publish"
                                ) + " (" + Number(
                                    noteRecord.modelData.badgeCount || 0
                                ) + ")"
                                elide: Text.ElideRight
                                color: noteHover.hovered
                                    ? root.theme.action
                                    : root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
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
            anchors.margins: 6
            theme: root.theme
            controller: root.controller
            columnsController: root.columnsController
            userModel: root.userModel
            nodeId: root.nodeId
            records: root.cell.tasks || []
            options: root.displayOptions
            taskCount: root.tasks
            scrolling: root.scrolling
            onProcessPickerRequested: function(anchorItem) {
                root.processCountMenuRequested("tasks", anchorItem)
            }
        }
    }
}
