import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/table.ui.mjs" as UI

Rectangle {
    id: root
    required property var theme
    property var rows: []
    property bool tasks: false
    property string emptyText: qsTr("No files")
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    readonly property string view: tasks ? "changelistTasks" : "changelistFiles"
    readonly property var widths: UI.columns(view, width).map(column => column.width)
    readonly property real tableWidth: widths.reduce((sum, value) => sum + value, 0)
    function cells(row) {
        return UI.cells(view, row, language);
    }
    color: theme.panelDeep
    border.color: theme.outlineVariant
    radius: theme.itemRadius
    implicitHeight: 190
    Item {
        x: 6
        y: 6
        width: Math.max(0, parent.width - 12)
        height: 28
        clip: true
        Frame.FrameView {
            x: -list.contentX
            width: root.tableWidth
            height: 28
            theme: root.theme
            scene: UI.header(root.view, root.width, root.language)
        }
    }
    ListView {
        id: list
        objectName: "changelistContentsList"
        x: 6
        y: 36
        width: Math.max(0, parent.width - 12)
        height: Math.max(0, parent.height - 42)
        clip: true
        model: root.rows
        contentWidth: root.tableWidth
        flickableDirection: Flickable.HorizontalAndVerticalFlick
        bottomMargin: horizontal.reservedExtent
        ScrollBar.vertical: Controls.ScrollBar {
            id: vertical
            theme: root.theme
            flickableTarget: list
        }
        ScrollBar.horizontal: Controls.ScrollBar {
            id: horizontal
            theme: root.theme
            flickableTarget: list
        }
        delegate: Frame.FrameView {
            required property var modelData
            width: root.tableWidth
            height: 32
            theme: root.theme
            interactive: false
            scene: UI.row({
                view: root.view,
                row: modelData
            }, root.width, root.language)
        }
        Label {
            anchors.centerIn: parent
            visible: !list.count
            width: parent.width - vertical.reservedExtent
            text: root.emptyText
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            color: root.theme.secondaryText
        }
    }
}
