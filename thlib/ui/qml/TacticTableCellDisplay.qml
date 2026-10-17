pragma ComponentBehavior: Bound

import QtQuick
import "tactic_frame/features/table/cells.ui.mjs" as Cells
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "features/table" as Table

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
    readonly property string safeHref: Cells.link(cell.href, controller ? controller.server_url || "" : "")
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    signal taskPreviewHoverChanged(bool hovered)

    signal processCountMenuRequested(string panel, var anchorItem)

    Loader {
        anchors.fill: parent
        sourceComponent: {
            if (root.cell.error)
                return textCell;
            if (root.kind === "unsupported")
                return unsupportedCell;
            if (root.kind === "group_completion")
                return groupedCompletionCell;
            if (root.kind === "fields")
                return fieldsCell;
            if (root.kind === "status_flag")
                return flagCell;
            if (root.kind === "selection")
                return selectionCell;
            if (root.kind === "check")
                return checkCell;
            if (root.kind === "locked")
                return lockedCell;
            if (root.kind === "structured")
                return structuredCell;
            if (root.kind === "boolean")
                return booleanCell;
            if (root.kind === "thumbnail")
                return thumbnailCell;
            if (root.kind === "notes")
                return notesCell;
            if (["sobject_detail", "checkin", "explorer", "file_list", "metadata", "delete"].indexOf(root.kind) >= 0)
                return actionCell;
            if (root.kind === "completion")
                return completionCell;
            if (root.kind === "task_summary" && root.cell.summaryMode === "minimal")
                return summaryCell;
            if (root.kind === "task_summary" || root.kind === "tasks")
                return tasksCell;
            return textCell;
        }
    }

    Component {
        id: unsupportedCell
        Label {
            text: qsTr("Widget unavailable")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: Cells.metrics.bodyFont
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            leftPadding: 10
            rightPadding: 10
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
                textFormat: Text.PlainText
                text: Cells.text(root.cell, root.textValue, root.language)
                elide: Text.ElideRight
                color: root.cell.error ? root.theme.error : root.kind === "link" ? root.theme.action : root.theme[Cells.textRole(root.cell)]
                font.family: root.theme.fontFamily
                font.pixelSize: Cells.metrics.bodyFont
                font.weight: root.columnIndex === 0 ? Font.DemiBold : Font.Normal
                font.underline: root.kind === "link"
            }
            TapHandler {
                enabled: root.kind === "link" && root.safeHref.length > 0
                acceptedButtons: Qt.LeftButton
                onTapped: Qt.openUrlExternally(root.safeHref)
            }
            HoverHandler {
                id: hover
                enabled: root.kind === "link" || String(root.cell.tooltip || "").length > 0 || String(root.cell.error || "").length > 0 || label.truncated
                cursorShape: root.kind === "link" ? Qt.PointingHandCursor : Qt.ArrowCursor
            }
            Controls.ToolTip {
                theme: root.theme
                visible: hover.hovered && (String(root.cell.error || "").length > 0 || String(root.cell.tooltip || "").length > 0 || label.truncated)
                text: String(root.cell.error || root.cell.tooltip || "") || root.textValue
            }
        }
    }

    Component {
        id: structuredCell

        TacticStructuredTableCell {
            theme: root.theme
            cell: root.cell
            maximumHeight: Number(String(root.displayOptions.height || (root.cell.language === "xml" ? 600 : 300)).replace("px", ""))
        }
    }

    Component {
        id: booleanCell

        Controls.CheckBox {
            anchors.centerIn: parent
            enabled: false
            theme: root.theme
            checked: Cells.checked(root.cell, root.textValue)
        }
    }

    Component {
        id: thumbnailCell

        Item {
            Controls.ItemPreview {
                objectName: "tableCellPreview"
                anchors.centerIn: parent
                width: Cells.previewSize(parent.width, parent.height)
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
                        root.controller.mark_item_preview_revealed(root.nodeId);
                }
            }
        }
    }

    Component {
        id: notesCell

        Item {
            id: noteCell
            readonly property var noteRecords: {
                const countRevision = root.comments;
                return root.controller.process_count_actions(root.nodeId, "notes").filter(record => Number(record.badgeCount || 0) > 0);
            }
            ListView {
                id: noteList
                objectName: "tableNoteList"
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 7
                anchors.rightMargin: contentHeight > height ? 16 : 7
                y: Math.round(Math.max(4, (parent.height - height) / 2))
                height: Math.min(Math.max(0, parent.height - 8), noteCell.noteRecords.length * 26 + Math.max(0, noteCell.noteRecords.length - 1) * spacing)
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
                    readonly property color accentColor: String(modelData.accent || "").length > 0 ? modelData.accent : root.theme.action
                    readonly property string processTitle: String(modelData.title || modelData.process || "publish")
                    objectName: "tableNoteRecord_" + index
                    width: noteList.width
                    height: 26
                    radius: root.theme.itemRadius
                    color: root.theme.overlay(root.theme.surfaceContainerHigh, accentColor, noteHover.hovered ? 0.16 : 0.08)
                    border.width: 1
                    border.color: root.theme.overlay(root.theme.outlineVariant, accentColor, 0.32)
                    Accessible.role: Accessible.Button
                    Accessible.name: processTitle + " (" + Number(modelData.badgeCount || 0) + ")"

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
                            font.pixelSize: Cells.metrics.bodyFont
                            font.weight: Font.DemiBold
                        }
                        Label {
                            objectName: "tableNoteCount_" + noteRecord.index
                            text: "(" + Number(noteRecord.modelData.badgeCount || 0) + ")"
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
                        onActivated: root.controller.open_process_details(root.nodeId, "notes", String(noteRecord.modelData.process || "publish"))
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
                onClicked: root.processCountMenuRequested("notes", noteButton)
            }
        }
    }

    Component {
        id: actionCell

        TacticTableActionCell {
            theme: root.theme
            kind: root.kind
            cell: root.cell
            onClicked: root.controller.invoke_table_widget_action(root.kind, root.nodeId, root.cell)
        }
    }

    Component {
        id: fieldsCell
        Table.ValueFieldsCell {
            anchors.fill: parent
            anchors.topMargin: 4
            anchors.bottomMargin: 4
            theme: root.theme
            entries: root.cell.entries || []
        }
    }
    Component {
        id: flagCell
        Controls.MaterialIcon {
            anchors.centerIn: parent
            visible: root.cell.good !== undefined && root.cell.good !== null
            name: root.cell.good ? "check-circle" : "error"
            color: root.cell.good ? root.theme.green : root.theme.error
            size: 17
            Accessible.name: Cells.text(root.cell, root.textValue, root.language)
        }
    }

    Component {
        id: selectionCell
        Controls.CheckBox {
            anchors.centerIn: parent
            theme: root.theme
            checked: root.controller.selected_result_node_ids.indexOf(root.nodeId) >= 0
            Accessible.name: root.title
            onClicked: root.controller.select_result_node(root.nodeId, String(root.cell.search_key || ""), "sobject", Qt.ControlModifier, false)
        }
    }

    Component {
        id: checkCell
        Controls.MaterialIcon {
            anchors.centerIn: parent
            name: "check"
            size: 18
            color: root.theme.text
            visible: Cells.checked(root.cell, root.textValue)
            Accessible.name: root.textValue
        }
    }

    Component {
        id: lockedCell
        Controls.MaterialIcon {
            anchors.centerIn: parent
            name: "lock"
            size: 18
            color: root.theme.secondaryText
            visible: Cells.checked(root.cell, root.textValue)
            Accessible.name: qsTr("Locked")
        }
    }

    Component {
        id: groupedCompletionCell
        Item {
            id: completionGroupHost
            readonly property var layout: Cells.completionGroups((root.cell.groups || []).length, width, height)
            ListView {
                id: groups
                anchors.fill: parent
                anchors.rightMargin: completionGroupHost.layout.gutter
                model: root.cell.groups || []
                spacing: completionGroupHost.layout.gap
                clip: true
                reuseItems: true
                delegate: TacticCompletionCell {
                    required property var modelData
                    width: groups.width
                    height: completionGroupHost.layout.rowHeight
                    theme: root.theme
                    percent: Number(modelData.completion || 0)
                    text: String(modelData.text || "")
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    parent: completionGroupHost
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    theme: root.theme
                    flickableTarget: groups
                }
            }
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
        id: summaryCell
        Table.TaskSummaryCell {
            anchors.fill: parent
            anchors.topMargin: 3
            anchors.bottomMargin: 3
            theme: root.theme
            controller: root.controller
            nodeId: root.nodeId
            records: root.cell.tasks || []
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
