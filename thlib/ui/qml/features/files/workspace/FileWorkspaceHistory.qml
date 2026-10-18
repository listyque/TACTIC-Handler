import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/table.ui.mjs" as UI

Item {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    objectName: "fileWorkspaceHistory"
    required property var theme
    required property var controller
    property var revision: ({})
    readonly property var state: controller.view_data
    readonly property var rows: state.history
    readonly property string filePath: state.history_path ? "//" + state.history_stream + "/" + state.history_path : ""
    readonly property var preview: state.history_preview?.revision === revision.code ? state.history_preview : ({})
    property string inspectorTab: "details"
    property bool expanded: true
    property string previewRequest: ""
    property alias listView: revisions
    readonly property var columns: UI.columns("history", width).map(column => column.width)
    readonly property var headings: UI.columns("history", width).map(column => qsTr(column.title))
    readonly property real tableWidth: columns.reduce((sum, value) => sum + value, 0)
    signal selected(var row, int modifiers, bool context)
    signal contextRequested(var item, real x, real y)
    signal keyPressed(var event)

    function date(value) {
        return value ? Qt.formatDateTime(new Date(value / 1000), "dd.MM.yyyy HH:mm:ss") : "—";
    }
    function size(value) {
        return value < 1024 ? value + " B" : value < 1048576 ? (value / 1024).toFixed(1) + " KiB" : (value / 1048576).toFixed(1) + " MiB";
    }
    function type(row) {
        const path = row.path || "";
        return row.file_type || (path.lastIndexOf(".") > path.lastIndexOf("/") ? path.slice(path.lastIndexOf(".") + 1).toUpperCase() : "—");
    }
    function cells(row) {
        return UI.cells("history", row);
    }
    function icon(row) {
        return row.action === "delete" || row.action === "move/delete" ? "delete" : row.action === "add" ? "add" : row.action === "move/add" ? "swap-horizontal" : "edit";
    }
    function loadPreview() {
        if (!visible || inspectorTab !== "preview" || !revision.code || revision.deleted || previewRequest === revision.code)
            return;
        previewRequest = revision.code;
        controller.action("history_preview", {
            revision: revision.code,
            path: revision.path,
            stream: revision.stream,
            published_change: revision.change
        });
    }
    function previewSelected() {
        inspectorTab = "preview";
        loadPreview();
    }
    readonly property string selectedCode: revision.code || ""
    onSelectedCodeChanged: {
        previewRequest = "";
        loadPreview();
    }
    onInspectorTabChanged: loadPreview()
    onVisibleChanged: loadPreview()

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    SplitView {
        id: split
        anchors.fill: parent
        orientation: Qt.Vertical
        handle: Controls.SplitterHandle {
            theme: root.theme
            vertical: false
        }
        onResizingChanged: if (!resizing)
            root.controller.set_value("history_details_height", inspector.height)
        ColumnLayout {
            SplitView.fillHeight: true
            SplitView.minimumHeight: 100
            spacing: 2
            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    text: root.filePath ? qsTr("History of file: %1").arg(root.filePath) : qsTr("Select a file to view history")
                    textFormat: Text.PlainText
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    elide: Text.ElideMiddle
                    leftPadding: 8
                    HoverHandler {
                        id: pathHover
                    }
                    Controls.ToolTip {
                        theme: root.theme
                        text: root.filePath
                        visible: pathHover.hovered && parent.truncated
                    }
                }
                Controls.CompactIconButton {
                    id: historyMenu
                    theme: root.theme
                    iconName: "more_vert"
                    toolTip: qsTr("Revision actions")
                    onClicked: root.contextRequested(historyMenu, 0, height)
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 28
                clip: true
                Row {
                    x: -revisions.contentX
                    Repeater {
                        model: root.headings
                        Label {
                            required property int index
                            required property string modelData
                            width: root.columns[index]
                            leftPadding: 8
                            text: modelData
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            elide: Text.ElideRight
                        }
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                visible: Boolean(root.filePath)
                spacing: 4
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: root.expanded ? "chevron-down" : "chevron-right"
                    toolTip: qsTr("Revisions")
                    onClicked: root.expanded = !root.expanded
                }
                Controls.MaterialIcon {
                    name: "file"
                    size: 18
                    color: root.theme.action
                }
                Label {
                    Layout.fillWidth: true
                    text: root.filePath
                    textFormat: Text.PlainText
                    color: root.theme.primaryText
                    elide: Text.ElideMiddle
                    font.family: root.theme.fontFamily
                }
            }
            ListView {
                id: revisions
                objectName: "workspaceHistoryRevisions"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: root.expanded ? root.rows : []
                contentWidth: Math.max(width - vertical.reservedExtent, root.tableWidth)
                flickableDirection: Flickable.HorizontalAndVerticalFlick
                bottomMargin: horizontal.reservedExtent
                Keys.onPressed: event => root.keyPressed(event)
                ScrollBar.vertical: Controls.ScrollBar {
                    id: vertical
                    theme: root.theme
                    flickableTarget: revisions
                }
                ScrollBar.horizontal: Controls.ScrollBar {
                    id: horizontal
                    theme: root.theme
                    flickableTarget: revisions
                }
                delegate: Controls.PopupAction {
                    id: row
                    required property var modelData
                    objectName: "historyRevision_" + modelData.number
                    property var theme: root.theme
                    width: revisions.contentWidth
                    height: 32
                    hoverEnabled: true
                    readonly property bool selected: root.revision.code === modelData.code || root.state.selection_scope === "history" && root.state.selection_ids.indexOf(modelData.code) >= 0
                    Accessible.name: qsTr("Revision") + " #" + modelData.number + ", " + modelData.action
                    background: Controls.ItemSurface {
                        theme: root.theme
                        selected: row.selected
                        hovered: row.hovered
                        normalColor: "transparent"
                        railVisible: false
                    }
                    contentItem: Frame.FrameView {
                        theme: root.theme
                        interactive: false
                        scene: UI.row({
                            view: "history",
                            row: row.modelData,
                            selected: row.selected,
                            hovered: row.hovered
                        }, root.width, root.language)
                    }
                    onClicked: root.selected(modelData, Qt.NoModifier, false)
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: mouse => {
                            revisions.forceActiveFocus();
                            root.selected(row.modelData, mouse.modifiers, mouse.button === Qt.RightButton);
                            if (mouse.button === Qt.RightButton)
                                root.contextRequested(row, mouse.x, mouse.y);
                        }
                        onDoubleClicked: mouse => {
                            if (mouse.button === Qt.LeftButton) {
                                root.selected(row.modelData, mouse.modifiers, false);
                                root.previewSelected();
                            }
                        }
                    }
                }
                Label {
                    anchors.centerIn: parent
                    width: parent.width - 20
                    visible: root.expanded && !revisions.count
                    text: root.filePath ? qsTr("No submitted revisions for this file") : qsTr("Select a file to view history")
                    wrapMode: Text.Wrap
                    horizontalAlignment: Text.AlignHCenter
                    color: root.theme.secondaryText
                }
            }
            Label {
                Layout.fillWidth: true
                visible: Boolean(root.state.history_more)
                text: qsTr("Showing latest %1 revisions").arg(root.rows.length)
                color: root.theme.secondaryText
                leftPadding: 8
            }
        }
        FileWorkspaceInspector {
            id: inspector
            theme: root.theme
            historyMode: true
            info: Object.assign({}, root.revision, {
                file: root.revision,
                provenance: root.revision.integrated_from
            })
            preview: root.revision.deleted ? ({}) : root.preview
            currentTab: root.inspectorTab
            busy: root.inspectorTab === "preview" && Boolean(root.revision.code) && !root.revision.deleted && !root.preview.kind && !root.preview.error
            onTabSelected: tab => root.inspectorTab = tab
            SplitView.preferredHeight: Math.min(root.state.history_details_height, split.height * 0.55)
            SplitView.minimumHeight: Math.min(110, split.height * 0.35)
        }
    }
}
