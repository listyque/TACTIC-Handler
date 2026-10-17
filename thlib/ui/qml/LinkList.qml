import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/objects/links.ui.mjs" as UI

Rectangle {
    id: root

    required property var theme
    required property string title
    required property string emptyText
    required property var sourceModel
    property bool loading: false
    property bool canLoadMore: false
    property int totalCount: sourceModel ? sourceModel.count : 0
    property var selectedKeys: []
    property Item dragPreview: null
    property string dropDirection: ""
    property bool dropHovered: false
    signal rowSelected(int row, int modifiers)
    signal loadMoreRequested
    signal objectsDropped(var keys)

    readonly property var listScene: UI.list({
        scope: root.dropDirection === "remove" ? "available" : "linked",
        count: root.sourceModel ? root.sourceModel.count : 0,
        total: root.totalCount,
        loading: root.loading
    }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)

    radius: root.theme.surfaceRadius
    color: root.theme.panel
    border.width: 1
    border.color: root.theme.outlineVariant
    clip: true

    function requestNextPageIfNeeded() {
        if (!root.canLoadMore || root.loading)
            return;
        const underfilled = objectList.contentHeight <= objectList.height + 1;
        const remaining = objectList.contentHeight - (objectList.contentY + objectList.height);
        if (remaining > 160 || !verticalBar.takePaginationPermit(underfilled))
            return;
        root.loadMoreRequested();
    }

    onLoadingChanged: {
        if (!loading)
            Qt.callLater(root.requestNextPageIfNeeded);
    }
    onCanLoadMoreChanged: Qt.callLater(root.requestNextPageIfNeeded)

    function extractDropKeys(source, textValue) {
        const keys = [];
        const addKey = function (value) {
            const key = String(value || "").trim();
            if (key && keys.indexOf(key) < 0)
                keys.push(key);
        };

        if (source && source.transferKeys && source.transferKeys.length > 0)
            source.transferKeys.forEach(addKey);
        if (source && source.searchKey)
            addKey(source.searchKey);
        if (textValue)
            textValue.toString().split(/[\r\n;,]+/).forEach(addKey);
        return keys;
    }

    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.listScene
    }
    Item {
        x: root.listScene.body.x
        y: root.listScene.body.y
        width: root.listScene.body.width
        height: root.listScene.body.height

        Controls.SmoothListView {
            id: objectList
            theme: root.theme
            anchors.fill: parent
            objectName: "linkObjectList-" + root.dropDirection
            anchors.leftMargin: root.listScene.viewport.x
            anchors.rightMargin: root.width - root.listScene.viewport.x - root.listScene.viewport.width
            anchors.topMargin: root.listScene.viewport.y - root.listScene.body.y
            anchors.bottomMargin: root.listScene.body.height - (root.listScene.viewport.y - root.listScene.body.y) - root.listScene.viewport.height
            model: root.sourceModel
            clip: true
            spacing: 4
            topMargin: root.listScene.rowInsets.top
            bottomMargin: root.listScene.rowInsets.bottom
            leftMargin: root.listScene.rowInsets.left
            rightMargin: root.listScene.rowInsets.right
            onContentYChanged: root.requestNextPageIfNeeded()
            onMovementEnded: root.requestNextPageIfNeeded()
            onCountChanged: Qt.callLater(root.requestNextPageIfNeeded)

            ScrollBar.vertical: Controls.ScrollBar {
                id: verticalBar
                objectName: "linkObjectScrollBar-" + root.dropDirection
                theme: root.theme
                flickableTarget: objectList
            }

            delegate: Item {
                id: row
                objectName: "linkRow-" + root.dropDirection

                required property int index
                required property string searchKey
                required property string title
                required property string subtitle
                required property string previewUrl
                required property string fallbackText
                required property color accent
                required property bool selected

                width: objectList.width - objectList.leftMargin - objectList.rightMargin
                height: 64
                property string sourceDirection: root.dropDirection
                property var listSelectedKeys: root.selectedKeys
                property var transferKeys: row.selected && root.selectedKeys.length > 0 ? root.selectedKeys : [row.searchKey]
                // Dragging uses a separate compact proxy.  Keep the
                // source delegate, including its decoded preview, intact.
                opacity: 1

                Frame.FrameView {
                    anchors.fill: parent
                    theme: root.theme
                    interactive: false
                    scene: UI.row({
                        key: row.searchKey,
                        title: row.title,
                        subtitle: row.subtitle,
                        previewUrl: row.previewUrl,
                        fallbackText: row.fallbackText,
                        accent: row.accent,
                        selected: row.selected
                    }, width)
                }

                MouseArea {
                    id: rowPointer
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton
                    cursorShape: Qt.PointingHandCursor
                    drag.target: root.dragPreview
                    drag.axis: Drag.XAndYAxis
                    drag.smoothed: false
                    preventStealing: drag.active
                    property bool deferSingleSelection: false
                    property bool wasDragged: false

                    onPressed: function (mouse) {
                        wasDragged = false;
                        deferSingleSelection = row.selected && root.selectedKeys.length > 1 && mouse.modifiers === Qt.NoModifier;
                        if (!deferSingleSelection)
                            root.rowSelected(row.index, mouse.modifiers);
                        root.dragPreview.prepare(row, rowPointer, mouse);
                    }
                    onPositionChanged: {
                        if (drag.active)
                            wasDragged = true;
                    }
                    onReleased: function (mouse) {
                        if (root.dragPreview.Drag.active)
                            root.dragPreview.Drag.drop();
                        root.dragPreview.sourcePointer = null;
                        if (deferSingleSelection && !wasDragged)
                            root.rowSelected(row.index, mouse.modifiers);
                        deferSingleSelection = false;
                        wasDragged = false;
                    }
                    onCanceled: {
                        root.dragPreview.Drag.cancel();
                        root.dragPreview.sourcePointer = null;
                        deferSingleSelection = false;
                        wasDragged = false;
                    }
                }
            }
        }

        DropArea {
            id: objectDropArea
            objectName: "linkDropArea-" + root.dropDirection
            anchors.fill: parent
            z: 2
            keys: ["tactic-handler-link-sobjects"]
            onEntered: function (drag) {
                root.dropHovered = Boolean(drag.source && drag.source.sourceDirection !== root.dropDirection);
            }
            onPositionChanged: function (drag) {
                root.dropHovered = Boolean(drag.source && drag.source.sourceDirection !== root.dropDirection);
            }
            onExited: root.dropHovered = false
            onDropped: function (drop) {
                root.dropHovered = false;
                if (!drop.source || drop.source.sourceDirection === root.dropDirection)
                    return;
                const keys = root.extractDropKeys(drop.source, drop.text);
                if (!keys.length)
                    return;
                drop.acceptProposedAction();
                Qt.callLater(function () {
                    root.objectsDropped(keys);
                });
            }
        }

        Controls.DropTargetOverlay {
            z: 2
            visible: root.dropHovered
            theme: root.theme
            iconName: root.dropDirection === "add" ? "arrow-forward" : "arrow-back"
            promptText: root.dropDirection === "add" ? qsTr("Drop to link") : qsTr("Drop to unlink")
        }

        ContentLoadingOverlay {
            anchors.fill: parent
            z: 3
            theme: root.theme
            visible: root.loading && objectList.count === 0
            message: qsTr("Loading objects...")
        }
    }
}
