import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property bool layoutReady: false

    Component.onCompleted: {
        Qt.callLater(function() { root.layoutReady = true })
    }

    function levelColor(value) {
        if (value === "CRITICAL" || value === "ERROR"
                || value === "EXCEPTION")
            return theme.red
        if (value === "WARNING")
            return theme.yellow
        if (value === "MISSING")
            return theme.yellow
        if (value === "INFO")
            return theme.green
        if (value === "API")
            return theme.action
        return theme.secondaryText
    }

    FileDialog {
        id: sessionFileDialog
        title: qsTr("Open debug session")
        nameFilters: [
            "TACTIC session logs (*.jsonl)",
            "All files (*)"
        ]
        onAccepted: debugLog.load_session_file(selectedFile.toString())
    }

    Timer {
        id: layoutSave
        interval: 180
        onTriggered: {
            if (root.layoutReady)
                debugLog.save_layout(
                    sourcePanel.width,
                    detailPanel.height
                )
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: toolbarContent.implicitHeight + 20
            radius: 14
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant

            ColumnLayout {
                id: toolbarContent
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Rectangle {
                        id: searchSurface
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        radius: height / 2
                        color: root.theme.surfaceContainerHigh
                        border.width: searchInput.activeFocus ? 1 : 0
                        border.color: root.theme.action
                        antialiasing: true

                        Controls.MaterialIcon {
                            anchors.left: parent.left
                            anchors.leftMargin: 14
                            anchors.verticalCenter: parent.verticalCenter
                            name: "search"
                            size: 18
                            color: searchInput.activeFocus
                                ? root.theme.action : root.theme.secondaryText
                        }
                        TextInput {
                            id: searchInput
                            anchors.left: parent.left
                            anchors.leftMargin: 42
                            anchors.right: clearSearch.left
                            anchors.rightMargin: 4
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            verticalAlignment: Text.AlignVCenter
                            color: root.theme.primaryText
                            selectionColor: root.theme.selected
                            selectedTextColor: root.theme.selectedText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 12
                            selectByMouse: true
                            clip: true
                            onTextChanged: debugLog.set_search(text)

                            HoverHandler {
                                objectName: "debugSearchCursorHandler"
                                cursorShape: searchInput.enabled
                                    ? Qt.IBeamCursor : Qt.ArrowCursor
                            }
                        }
                        Label {
                            anchors.fill: searchInput
                            visible: searchInput.text.length === 0
                            verticalAlignment: Text.AlignVCenter
                            text: qsTr("Search messages, modules, groups or commands")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 12
                        }
                        Controls.CompactIconButton {
                            id: clearSearch
                            anchors.right: parent.right
                            anchors.rightMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            visible: searchInput.text.length > 0
                            theme: root.theme
                            round: true
                            iconName: "close"
                            iconSize: 15
                            toolTip: qsTr("Clear search")
                            onClicked: searchInput.clear()
                        }
                    }

                    Controls.ComboBox {
                        Layout.preferredWidth: 190
                        Layout.preferredHeight: 36
                        theme: root.theme
                        model: debugLog.session_history_model
                        textRole: "label"
                        valueRole: "path"
                        displayText: debugLog.active_session_label
                        onActivated: function(index) {
                            debugLog.load_session_row(index)
                        }
                    }
                    Controls.CompactIconButton {
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        theme: root.theme
                        round: true
                        backgroundColor: root.theme.surfaceContainerHigh
                        iconName: "folder_open"
                        iconSize: 16
                        toolTip: qsTr("Open saved debug session")
                        onClicked: sessionFileDialog.open()
                    }
                    Controls.CompactIconButton {
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        visible: debugLog.viewing_history
                        theme: root.theme
                        round: true
                        backgroundColor: root.theme.secondaryContainer
                        iconName: "sensors"
                        iconSize: 16
                        toolTip: qsTr("Return to live session")
                        onClicked: debugLog.show_live_session()
                    }
                    Rectangle {
                        Layout.preferredHeight: 32
                        Layout.preferredWidth: eventCount.implicitWidth + 24
                        radius: 10
                        color: root.theme.secondaryContainer
                        Label {
                            id: eventCount
                            anchors.centerIn: parent
                            text: debugLog.entry_count + " events"
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }
                    }
                    Controls.CompactIconButton {
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        theme: root.theme
                        round: true
                        backgroundColor: root.theme.surfaceContainerHigh
                        iconName: "content_copy"
                        iconSize: 16
                        toolTip: qsTr("Copy session log path")
                        onClicked: debugLog.copy_session_path()
                    }
                    Controls.CompactIconButton {
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        theme: root.theme
                        round: true
                        backgroundColor: root.theme.surfaceContainerHigh
                        iconName: "delete"
                        iconSize: 16
                        toolTip: qsTr("Clear session")
                        onClicked: debugLog.clear()
                    }
                }

                Flow {
                    id: levelFilters
                    objectName: "debugLogLevelFilters"
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(28, childrenRect.height)
                    spacing: 6
                    Label {
                        width: implicitWidth + 2
                        height: 28
                        text: qsTr("LEVEL")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.DemiBold
                        verticalAlignment: Text.AlignVCenter
                    }
                    Repeater {
                        model: debugLog.levels
                        delegate: QuickFilterChip {
                            id: levelChip
                            objectName: "debugLogLevelChip"
                            required property string modelData
                            theme: root.theme
                            text: levelChip.modelData
                            checked: true
                            accent: root.levelColor(modelData)
                            subtle: true
                            cornerRadius: 8
                            iconName: checked ? "check" : "close"
                            width: implicitWidth
                            height: 28
                            onClicked: {
                                levelChip.checked = !levelChip.checked
                                debugLog.set_level_enabled(
                                    levelChip.modelData,
                                    levelChip.checked
                                )
                            }
                        }
                    }
                }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal
            handle: Rectangle {
                implicitWidth: 10
                color: "transparent"
                Rectangle {
                    anchors.centerIn: parent
                    width: 1
                    height: Math.max(0, parent.height - 18)
                    color: root.theme.outlineVariant
                }
            }

            Rectangle {
                id: sourcePanel
                SplitView.preferredWidth: debugLog.group_panel_width
                SplitView.minimumWidth: 170
                onWidthChanged: if (root.layoutReady) layoutSave.restart()
                radius: 12
                color: root.theme.panel
                border.width: 1
                border.color: root.theme.outlineVariant

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 4
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        Layout.leftMargin: 6
                        Layout.rightMargin: 6
                        Controls.MaterialIcon {
                            name: "account_tree"
                            size: 16
                            color: root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Sources")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        Label {
                            text: groupList.count
                            color: root.theme.secondaryText
                            font.pointSize: Controls.Typography.label
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: root.theme.outlineVariant
                    }
                    ListView {
                        id: groupList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: debugGroupModel
                        spacing: 2
                        delegate: Item {
                            id: groupRow
                            required property string label
                            required property string key
                            required property int count
                            required property int depth
                            required property bool selected
                            width: ListView.view ? ListView.view.width : 0
                            height: 36
                            Rectangle {
                                anchors.fill: parent
                                radius: 8
                                color: groupRow.selected
                                    ? root.theme.secondaryContainer
                                    : groupMouse.containsMouse
                                        ? root.theme.rowHover : "transparent"
                                Behavior on color {
                                    ColorAnimation { duration: theme.hoverMotionFast }
                                }
                            }
                            Rectangle {
                                visible: groupRow.selected
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                width: 3
                                height: 20
                                radius: 2
                                color: root.theme.action
                            }
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10 + groupRow.depth * 13
                                anchors.rightMargin: 8
                                spacing: 7
                                Controls.MaterialIcon {
                                    name: groupRow.depth > 0
                                        ? "subdirectory_arrow_right" : "folder"
                                    size: 14
                                    color: groupRow.selected
                                        ? root.theme.action
                                        : root.theme.secondaryText
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: groupRow.label
                                    elide: Text.ElideMiddle
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                }
                                Rectangle {
                                    Layout.preferredWidth:
                                        Math.max(22, groupCount.implicitWidth + 12)
                                    Layout.preferredHeight: 20
                                    radius: 7
                                    color: root.theme.surfaceContainerHigh
                                    Label {
                                        id: groupCount
                                        anchors.centerIn: parent
                                        text: groupRow.count
                                        color: root.theme.secondaryText
                                        font.pointSize: Controls.Typography.caption
                                    }
                                }
                            }
                            MouseArea {
                                id: groupMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: debugLog.select_group(groupRow.key)
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            theme: root.theme
                        }
                    }
                }
            }

            SplitView {
                SplitView.fillWidth: true
                orientation: Qt.Vertical
                handle: Rectangle {
                    implicitHeight: 10
                    color: "transparent"
                    Rectangle {
                        anchors.centerIn: parent
                        width: Math.max(0, parent.width - 18)
                        height: 1
                        color: root.theme.outlineVariant
                    }
                }

                Rectangle {
                    SplitView.fillHeight: true
                    SplitView.minimumHeight: 150
                    radius: 12
                    color: root.theme.panel
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 6
                        spacing: 4
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 38
                            Layout.leftMargin: 6
                            Layout.rightMargin: 6
                            spacing: 8
                            Controls.MaterialIcon {
                                name: "bug-report"
                                size: 16
                                color: root.theme.action
                            }
                            Label {
                                text: qsTr("Activity")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.bodyLarge
                                font.weight: Font.DemiBold
                            }
                            Item { Layout.fillWidth: true }
                            Label {
                                text: qsTr("Newest events appear at the bottom")
                                color: root.theme.secondaryText
                                font.pointSize: Controls.Typography.caption
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: root.theme.outlineVariant
                        }
                        ListView {
                            id: eventList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            model: debugLogModel
                            spacing: 2
                            onCountChanged: if (count > 0) positionViewAtEnd()
                            delegate: Item {
                                id: eventRow
                                required property int index
                                required property int eventId
                                required property string timestamp
                                required property string level
                                required property string message
                                required property string module
                                required property string functionName
                                required property int line
                                required property string group
                                required property string source
                                required property string command
                                required property string stacktrace
                                required property real duration
                                required property real sizeKb
                                required property string thread
                                required property string details
                                required property bool selected
                                readonly property color accent:
                                    root.levelColor(level)
                                width: ListView.view ? ListView.view.width : 0
                                height: 60
                                Rectangle {
                                    anchors.fill: parent
                                    radius: 8
                                    color: eventRow.selected
                                        ? root.theme.secondaryContainer
                                        : eventMouse.containsMouse
                                            ? root.theme.rowHover
                                            : eventRow.index % 2
                                                ? root.theme.row : root.theme.panel
                                    Behavior on color {
                                        ColorAnimation { duration: theme.hoverMotionFast }
                                    }
                                }
                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 3
                                    height: 36
                                    radius: 2
                                    color: eventRow.accent
                                }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 11
                                    anchors.rightMargin: 9
                                    spacing: 9
                                    Rectangle {
                                        Layout.preferredWidth: 76
                                        Layout.preferredHeight: 24
                                        radius: 7
                                        color: Qt.rgba(eventRow.accent.r,
                                            eventRow.accent.g,
                                            eventRow.accent.b, 0.14)
                                        Label {
                                            anchors.centerIn: parent
                                            text: eventRow.level
                                            color: eventRow.accent
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.caption
                                            font.weight: Font.DemiBold
                                        }
                                    }
                                    Item {
                                        Layout.preferredWidth: 20
                                        Layout.preferredHeight: 24
                                        Controls.MaterialIcon {
                                            anchors.centerIn: parent
                                            visible: eventRow.command.length > 0
                                            name: "terminal"
                                            size: 13
                                            color: root.theme.action
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 2
                                        Label {
                                            Layout.fillWidth: true
                                            text: eventRow.message.replace(/\s+/g, " ")
                                            elide: Text.ElideRight
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
                                            font.weight: Font.Medium
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: (eventRow.group.length
                                                ? eventRow.group + "  •  " : "")
                                                + eventRow.module + " / "
                                                + eventRow.functionName + "():"
                                                + eventRow.line
                                            elide: Text.ElideMiddle
                                            color: root.theme.secondaryText
                                            font.family: "Consolas"
                                            font.pointSize: Controls.Typography.caption
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.preferredWidth: 108
                                        spacing: 1
                                        Label {
                                            Layout.fillWidth: true
                                            horizontalAlignment: Text.AlignRight
                                            text: eventRow.timestamp.slice(11, 23)
                                            color: root.theme.secondaryText
                                            font.family: "Consolas"
                                            font.pointSize: Controls.Typography.caption
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            horizontalAlignment: Text.AlignRight
                                            text: (eventRow.duration > 0
                                                ? eventRow.duration.toFixed(3) + " s"
                                                : "")
                                                + (eventRow.duration > 0
                                                    && eventRow.sizeKb > 0
                                                    ? "  •  " : "")
                                                + (eventRow.sizeKb > 0
                                                    ? eventRow.sizeKb.toFixed(1)
                                                        + " KB"
                                                    : "")
                                            color: root.theme.secondaryText
                                            font.family: "Consolas"
                                            font.pointSize: Controls.Typography.caption
                                        }
                                    }
                                }
                                MouseArea {
                                    id: eventMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    acceptedButtons: Qt.LeftButton
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: debugLog.select_entry(eventRow.index)
                                }
                            }
                            ScrollBar.vertical: Controls.ScrollBar {
                                theme: root.theme
                            }
                        }
                    }
                }

                Rectangle {
                    id: detailPanel
                    SplitView.preferredHeight: debugLog.detail_panel_height
                    SplitView.minimumHeight: 110
                    onHeightChanged: if (root.layoutReady) layoutSave.restart()
                    readonly property var entry: debugLog.selected_entry
                    radius: 12
                    color: root.theme.panel
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 6
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            spacing: 8
                            Controls.MaterialIcon {
                                name: "info"
                                size: 16
                                color: detailPanel.entry.eventId
                                    ? root.levelColor(detailPanel.entry.level)
                                    : root.theme.secondaryText
                            }
                            Label {
                                Layout.fillWidth: true
                                text: detailPanel.entry.eventId
                                    ? qsTr("Event #") + detailPanel.entry.eventId
                                        + "  •  " + detailPanel.entry.level
                                        + "  •  "
                                        + detailPanel.entry.timestamp.slice(11, 23)
                                    : qsTr("Event details")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.bodyLarge
                                font.weight: Font.DemiBold
                            }
                            Controls.CompactIconButton {
                                visible: detailPanel.entry.eventId > 0
                                theme: root.theme
                                round: true
                                iconName: "content_copy"
                                iconSize: 15
                                toolTip: qsTr("Copy event")
                                onClicked: debugLog.copy_selected()
                            }
                            Controls.CompactIconButton {
                                visible: (detailPanel.entry.command || "").length > 0
                                theme: root.theme
                                round: true
                                iconName: "terminal"
                                iconSize: 15
                                toolTip: qsTr("Copy runtime command")
                                onClicked: debugLog.copy_selected_command()
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: root.theme.outlineVariant
                        }
                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            ScrollBar.vertical: Controls.ScrollBar {
                                theme: root.theme
                            }
                            ScrollBar.horizontal: Controls.ScrollBar {
                                theme: root.theme
                            }
                            Controls.TextArea {
                                theme: root.theme
                                readOnly: true
                                selectByMouse: true
                                wrapMode: TextEdit.NoWrap
                                color: detailPanel.entry.eventId
                                    ? root.theme.primaryText
                                    : root.theme.secondaryText
                                font.family: "Consolas"
                                font.pointSize: Controls.Typography.body
                                text: {
                                    const entry = detailPanel.entry
                                    if (!entry.eventId)
                                        return qsTr("Select an event to inspect its ")
                                            + qsTr("message, runtime command and stacktrace.")
                                    let value = entry.message || ""
                                    if (entry.details)
                                        value += "\n\nDetails:\n" + entry.details
                                    if (entry.command)
                                        value += "\n\nRuntime command:\n"
                                            + entry.command
                                    if (entry.stacktrace)
                                        value += "\n\nStacktrace:\n"
                                            + entry.stacktrace
                                    return value
                                }
                                background: Item {}
                            }
                        }
                    }
                }
            }
        }
    }
}
