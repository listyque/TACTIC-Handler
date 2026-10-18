import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../controls" as Controls
import "../../.." as TH
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/table.ui.mjs" as UI

Rectangle {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    objectName: "workspaceStreams"
    required property var theme
    required property var controller
    readonly property var state: controller.view_data
    property var expanded: []
    property string selectedCode: ""
    property bool treeMode: true
    property string query: ""
    property var records: []
    readonly property var rows: treeRows()
    readonly property var widths: UI.columns("streams", width).map(column => column.width)
    readonly property real tableWidth: widths.reduce((total, value) => total + value, 0)
    signal editStream(var row, bool child)
    color: theme.panelDeep
    clip: true
    function readRecords() {
        const result = [];
        for (let i = 0; i < controller.catalog_model.count(); i++)
            result.push(controller.catalog_model.get(i).node);
        records = result;
    }
    Component.onCompleted: readRecords()
    Connections {
        target: root.controller.catalog_model
        function onContentReplaced() {
            root.readRecords();
        }
    }
    function choose(row) {
        selectedCode = row.code;
        controller.set_value("catalog_detail", row);
    }
    function treeRows() {
        const byParent = {}, known = new Set(records.map(row => row.code)), result = [], seen = new Set();
        for (const row of records) {
            const parent = known.has(row.parent) ? row.parent : "";
            (byParent[parent] || (byParent[parent] = [])).push(row);
        }
        function visit(parent, depth) {
            for (const row of (byParent[parent] || [])) {
                if (seen.has(row.code))
                    continue;
                seen.add(row.code);
                const matches = !query || [row.code, row.title, row.description, row.parent].join(" ").toLowerCase().includes(query.toLowerCase());
                if (matches)
                    result.push(Object.assign({}, row, {
                        depth: treeMode && !query ? depth : 0,
                        children: Boolean(byParent[row.code]?.length)
                    }));
                if (!treeMode || query || expanded.indexOf(row.code) >= 0)
                    visit(row.code, depth + 1);
            }
        }
        visit("", 0);
        return result;
    }
    function toggle(code) {
        expanded = expanded.indexOf(code) >= 0 ? expanded.filter(item => item !== code) : expanded.concat([code]);
    }
    function menu(row, item, x, y) {
        if (row)
            choose(row);
        context.actions = [
            {
                title: qsTr("New stream"),
                translate: false,
                icon: "add",
                command: "new"
            }
        ];
        if (row)
            context.actions = context.actions.concat([
                {
                    title: qsTr("New child stream"),
                    translate: false,
                    icon: "source-branch",
                    command: "child",
                    enabled: Boolean(row.writable)
                },
                {
                    title: qsTr("Edit stream"),
                    translate: false,
                    icon: "edit",
                    command: "edit",
                    enabled: Boolean(row.writable)
                }
            ]);
        context.actions = context.actions.concat([
            {
                title: qsTr("Refresh"),
                translate: false,
                icon: "refresh",
                command: "refresh"
            }
        ]);
        context.openAt(item, x, y);
    }
    TH.ActionMenu {
        id: context
        theme: root.theme
        onTriggered: command => {
            if (command === "refresh")
                root.controller.action("catalog_page", {});
            else
                root.editStream(command === "new" ? ({}) : root.state.catalog_detail, command === "child");
        }
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 4
        RowLayout {
            Layout.fillWidth: true
            Controls.TextField {
                theme: root.theme
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                placeholderText: qsTr("Filter loaded streams")
                onTextEdited: root.query = text
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: root.treeMode ? "file-tree" : "view-list"
                toolTip: root.treeMode ? qsTr("Tree view") : qsTr("List view")
                onClicked: root.treeMode = !root.treeMode
            }
            Controls.CompactIconButton {
                objectName: "streamNewButton"
                theme: root.theme
                iconName: "add"
                toolTip: qsTr("New stream")
                onClicked: root.editStream({}, false)
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "refresh"
                toolTip: qsTr("Refresh")
                onClicked: root.controller.action("catalog_page", {})
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 28
            clip: true
            Row {
                x: -list.contentX
                Repeater {
                    model: [qsTr("Stream"), qsTr("Stream root"), qsTr("Parent"), qsTr("Type"), qsTr("Description")]
                    Label {
                        required property string modelData
                        required property int index
                        width: root.widths[index]
                        leftPadding: 8
                        text: modelData
                        color: root.theme.secondaryText
                        elide: Text.ElideRight
                    }
                }
            }
        }
        ListView {
            id: list
            objectName: "streamTreeList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.rows
            clip: true
            contentWidth: Math.max(width - bar.reservedExtent, root.tableWidth)
            flickableDirection: Flickable.HorizontalAndVerticalFlick
            bottomMargin: horizontal.reservedExtent
            ScrollBar.vertical: Controls.ScrollBar {
                id: bar
                theme: root.theme
                flickableTarget: list
            }
            ScrollBar.horizontal: Controls.ScrollBar {
                id: horizontal
                theme: root.theme
                flickableTarget: list
            }
            MouseArea {
                z: -1
                anchors.fill: parent
                acceptedButtons: Qt.RightButton
                onClicked: event => root.menu(null, list, event.x, event.y)
            }
            Keys.onPressed: event => {
                const row = model[currentIndex];
                if (event.key === Qt.Key_N && (event.modifiers & Qt.ControlModifier)) {
                    root.editStream({}, false);
                    event.accepted = true;
                } else if (row && (event.key === Qt.Key_Return || event.key === Qt.Key_Enter)) {
                    root.editStream(row, false);
                    event.accepted = true;
                } else if (row && (event.key === Qt.Key_Right || event.key === Qt.Key_Left)) {
                    if ((root.expanded.indexOf(row.code) >= 0) !== (event.key === Qt.Key_Right))
                        root.toggle(row.code);
                    event.accepted = true;
                }
            }
            onCurrentIndexChanged: if (currentIndex >= 0 && currentIndex < model.length)
                root.selectedCode = model[currentIndex].code
            delegate: Controls.PopupAction {
                id: item
                required property var modelData
                required property int index
                objectName: "streamRow_" + modelData.code
                property var theme: root.theme
                width: list.contentWidth
                height: 34
                hoverEnabled: true
                Accessible.name: modelData.title || modelData.code
                background: Controls.ItemSurface {
                    theme: root.theme
                    selected: root.selectedCode === item.modelData.code
                    hovered: item.hovered
                    normalColor: "transparent"
                    railVisible: false
                }
                contentItem: Frame.FrameView {
                    theme: root.theme
                    scene: UI.row({
                        view: "streams",
                        row: item.modelData,
                        selected: root.selectedCode === item.modelData.code,
                        hovered: item.hovered,
                        treeMode: root.treeMode,
                        expanded: root.expanded.includes(item.modelData.code)
                    }, root.width, root.language)
                    onEvent: action => {
                        if (action.type === "toggle")
                            root.toggle(action.key);
                    }
                }
                onClicked: {
                    list.currentIndex = index;
                    list.forceActiveFocus();
                    root.choose(modelData);
                }
                onDoubleClicked: root.editStream(modelData, false)
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.RightButton
                    onClicked: event => root.menu(item.modelData, item, event.x, event.y)
                }
            }
            Label {
                anchors.centerIn: parent
                visible: !list.count
                text: qsTr("No streams on this page")
                color: root.theme.secondaryText
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: qsTr("Loaded streams: %1").arg(root.records.length)
                color: root.theme.secondaryText
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Load more")
                visible: Boolean(root.state.catalog_after)
                enabled: root.records.length < 2000
                onClicked: root.controller.action("catalog_page", {
                    more: true
                })
            }
        }
    }
}
