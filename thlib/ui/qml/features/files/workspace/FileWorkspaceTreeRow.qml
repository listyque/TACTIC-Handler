import QtQuick
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/rows.ui.mjs" as UI

Item {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    required property var theme
    required property var row
    required property string caption
    property string subtitle: ""
    property bool selected: false
    readonly property bool branch: ["depot", "stream", "workspace", "directory", "change"].indexOf(row.kind) >= 0
    property bool focused: false
    onFocusedChanged: if (focused)
        forceActiveFocus()
    property var dragData: ({})
    signal selectedByUser(int modifiers)
    signal menuRequested(var source, real x, real y)
    signal dragRequested
    signal dropped(var payload, var urls)
    property bool acceptsDrop: false
    property var dropReason: null
    property var dropCaption: null
    property string dragCaption: ""
    property string dragFeedback: ""
    Drag.active: rowDrag.active
    Drag.dragType: Drag.Automatic
    Drag.supportedActions: Qt.CopyAction | Qt.MoveAction
    Drag.mimeData: dragData
    signal disclosure
    signal activated
    signal doubleActivated
    implicitHeight: rowMetrics.height
    objectName: "workspaceTreeRow:" + row.id
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: caption
    Accessible.description: subtitle || row.path || ""
    Controls.ToolTip {
        theme: root.theme
        visible: hover.hovered && !root.theme.suppressToolTips
        delay: 500
        text: root.caption + "\n" + root.subtitle
    }
    Accessible.onPressAction: if (enabled) {
        if (row.kind === "change")
            doubleActivated();
        else
            activated();
    }
    Keys.onRightPressed: if (branch && !row.expanded)
        disclosure()
    Keys.onLeftPressed: if (branch && row.expanded)
        disclosure()
    Keys.onReturnPressed: if (row.kind === "change")
        doubleActivated()
    else
        activated()
    Keys.onSpacePressed: activated()
    HoverHandler {
        id: hover
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
    readonly property var rowMetrics: UI.treeMetrics(row, subtitle)
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        interactive: false
        scene: UI.treeRow({
            row: root.row,
            caption: root.caption,
            subtitle: root.subtitle,
            selected: root.selected,
            hovered: hover.hovered,
            pressed: activation.pressed
        }, width)
    }
    Controls.CompactIconButton {
        theme: root.theme
        iconSize: 14
        width: 22
        height: 24
        x: root.rowMetrics.indent
        y: (root.height - height) / 2
        visible: root.branch
        iconName: root.row.expanded ? "expand-more" : "chevron-right"
        toolTip: (root.row.expanded ? qsTr("Collapse %1") : qsTr("Expand %1")).arg(root.caption)
        Accessible.name: toolTip
        objectName: "workspaceDisclosure:" + root.row.id
        onClicked: root.disclosure()
    }
    Item {
        x: root.rowMetrics.captionX
        width: Math.max(0, root.width - x)
        height: root.height
        Controls.ActivationHandler {
            id: activation
            repeatPointerTaps: true
            enabled: root.enabled
            onActivated: (modifiers, x, y) => {
                root.forceActiveFocus();
                root.selectedByUser(modifiers);
                if (!(modifiers & (Qt.ControlModifier | Qt.ShiftModifier)))
                    root.activated();
            }
            onDoubleActivated: {
                if (root.row.kind === "change")
                    root.doubleActivated();
                else if (root.branch)
                    root.disclosure();
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        onClicked: mouse => root.menuRequested(root, mouse.x, mouse.y)
    }
    DragHandler {
        id: rowDrag
        target: null
        acceptedButtons: Qt.LeftButton
        onActiveChanged: if (active)
            root.dragRequested()
    }
    DropArea {
        id: dropTarget
        anchors.fill: parent
        enabled: root.acceptsDrop
        keys: ["application/x-tactic-file-workspace", "text/uri-list"]
        onEntered: drag => {
            root.dragCaption = root.dropCaption ? root.dropCaption(drag.getDataAsString("application/x-tactic-file-workspace"), drag.urls) : "";
            root.dragFeedback = root.dropReason ? root.dropReason(drag.getDataAsString("application/x-tactic-file-workspace"), drag.urls) : "";
            pointerY = scrollView ? root.mapToItem(scrollView, drag.x, drag.y).y : 0;
            drag.accepted = true;
        }
        onExited: root.dragFeedback = ""
        onDropped: drop => {
            const payload = drop.getDataAsString("application/x-tactic-file-workspace");
            const reason = root.dropReason ? root.dropReason(payload, drop.urls) : "";
            if (reason) {
                root.dragFeedback = "";
                drop.accepted = false;
                return;
            }
            root.dropped(payload, drop.urls);
            drop.acceptProposedAction();
            root.dragFeedback = "";
        }
        readonly property var scrollView: root.ListView.view || (root.parent ? root.parent.ListView.view : null)
        property real pointerY: 0
        onPositionChanged: drag => {
            if (scrollView)
                pointerY = root.mapToItem(scrollView, drag.x, drag.y).y;
        }
        Timer {
            interval: 400
            running: dropTarget.containsDrag && !root.dragFeedback && root.branch && !root.row.expanded
            onTriggered: root.disclosure()
        }
        Timer {
            interval: 30
            repeat: true
            running: dropTarget.containsDrag && Boolean(dropTarget.scrollView)
            onTriggered: {
                const view = dropTarget.scrollView;
                const direction = dropTarget.pointerY < 24 ? -1 : dropTarget.pointerY > view.height - 24 ? 1 : 0;
                view.contentY = Math.max(0, Math.min(view.contentHeight - view.height, view.contentY + direction * 12));
            }
        }
        Rectangle {
            anchors.fill: parent
            visible: dropTarget.containsDrag
            color: "transparent"
            border.width: 2
            border.color: root.dragFeedback ? root.theme.red : root.theme.action
            radius: root.theme.surfaceRadius
        }
    }
    Controls.ToolTip {
        theme: root.theme
        visible: dropTarget.containsDrag
        delay: 0
        text: root.dragFeedback || root.dragCaption || qsTr("Add to changelist #%1").arg(root.row.number || root.row.code)
    }
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape && rowDrag.active) {
            root.Drag.cancel();
            event.accepted = true;
        } else if (event.key === Qt.Key_Menu || (event.key === Qt.Key_F10 && (event.modifiers & Qt.ShiftModifier))) {
            root.menuRequested(root, 8, height);
            event.accepted = true;
        }
    }
    Controls.ToolTip {
        theme: root.theme
        visible: hover.hovered && !root.theme.suppressToolTips
        delay: 500
        text: (root.row.path || root.caption) + (root.subtitle ? "\n" + root.subtitle : "")
    }
}
