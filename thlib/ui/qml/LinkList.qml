import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

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
    signal loadMoreRequested()
    signal objectsDropped(var keys)

    radius: root.theme.surfaceRadius
    color: root.theme.panel
    border.width: 1
    border.color: root.theme.outlineVariant
    clip: true

    function requestNextPageIfNeeded() {
        if (!root.canLoadMore || root.loading)
            return
        const underfilled = objectList.contentHeight <= objectList.height + 1
        const remaining = objectList.contentHeight
            - (objectList.contentY + objectList.height)
        if (remaining > 160
                || !verticalBar.takePaginationPermit(underfilled))
            return
        root.loadMoreRequested()
    }

    onLoadingChanged: {
        if (!loading)
            Qt.callLater(root.requestNextPageIfNeeded)
    }
    onCanLoadMoreChanged:
        Qt.callLater(root.requestNextPageIfNeeded)

    function extractDropKeys(source, textValue) {
        const keys = []
        const addKey = function(value) {
            const key = String(value || "").trim()
            if (key && keys.indexOf(key) < 0)
                keys.push(key)
        }

        if (source && source.transferKeys && source.transferKeys.length > 0)
            source.transferKeys.forEach(addKey)
        if (source && source.searchKey)
            addKey(source.searchKey)
        if (textValue)
            textValue.toString().split(/[\r\n;,]+/).forEach(addKey)
        return keys
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            color: root.theme.panelRaised
            radius: root.radius
            antialiasing: true

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: parent.radius
                color: parent.color
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 10
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    text: root.title
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }

                Label {
                    text: {
                        const visibleCount = root.sourceModel
                            ? root.sourceModel.count : 0
                        if (root.totalCount > visibleCount)
                            return visibleCount + " / " + root.totalCount
                        return String(visibleCount)
                    }
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }

                Controls.BusyIndicator {
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                    uiTheme: root.theme
                    visible: root.loading
                    running: visible
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: root.theme.separator
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Controls.SmoothListView {
                theme: root.theme
                id: objectList
                anchors.fill: parent
                objectName: "linkObjectList-" + root.dropDirection
                anchors.leftMargin: 4
                anchors.rightMargin: 10
                anchors.topMargin: 4
                anchors.bottomMargin: 6
                model: root.sourceModel
                clip: true
                spacing: 4
                topMargin: 6
                bottomMargin: 6
                leftMargin: 6
                rightMargin: 6
                onContentYChanged: root.requestNextPageIfNeeded()
                onMovementEnded: root.requestNextPageIfNeeded()
                onCountChanged:
                    Qt.callLater(root.requestNextPageIfNeeded)

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

                    width: objectList.width
                        - objectList.leftMargin - objectList.rightMargin
                    height: 64
                    property string sourceDirection: root.dropDirection
                    property var listSelectedKeys: root.selectedKeys
                    property var transferKeys:
                        row.selected && root.selectedKeys.length > 0
                        ? root.selectedKeys : [row.searchKey]
                    // Dragging uses a separate compact proxy.  Keep the
                    // source delegate, including its decoded preview, intact.
                    opacity: 1

                    Controls.ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        selected: row.selected
                        hovered: rowPointer.containsMouse
                        pressed: rowPointer.pressed
                        accent: row.accent
                        railVisible: true
                        railX: 0
                        railWidth: 3
                        inset: 0
                        cornerRadius: root.theme.itemRadius
                        separatorVisible: false
                        normalColor: root.theme.row
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 10

                        Controls.ItemPreview {
                            objectName: "linkRowPreview-" + root.dropDirection
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            theme: root.theme
                            previewSize: 44
                            source: row.previewUrl
                            fallbackIcon: "sobject"
                            fallbackText: row.fallbackText
                            accent: row.accent
                            selected: row.selected
                            outlined: true
                            cornerRadius: root.theme.itemRadius
                            animateAppearance: false
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Label {
                                Layout.fillWidth: true
                                text: row.title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.bodyLarge
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            Label {
                                objectName: "linkRowSubtitle-" + root.dropDirection
                                Layout.fillWidth: true
                                visible: row.subtitle.length > 0
                                text: row.subtitle.replace(/[\r\n\t]+/g, " ")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                elide: Text.ElideRight
                                maximumLineCount: 1
                                wrapMode: Text.NoWrap
                            }
                        }

                        Controls.MaterialIcon {
                            visible: row.selected
                            name: "check-circle"
                            size: 16
                            color: root.theme.action
                        }
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

                        onPressed: function(mouse) {
                            wasDragged = false
                            deferSingleSelection = row.selected
                                && root.selectedKeys.length > 1
                                && mouse.modifiers === Qt.NoModifier
                            if (!deferSingleSelection)
                                root.rowSelected(row.index, mouse.modifiers)
                            root.dragPreview.prepare(row, rowPointer, mouse)
                        }
                        onPositionChanged: {
                            if (drag.active)
                                wasDragged = true
                        }
                        onReleased: function(mouse) {
                            if (root.dragPreview.Drag.active)
                                root.dragPreview.Drag.drop()
                            root.dragPreview.sourcePointer = null
                            if (deferSingleSelection && !wasDragged)
                                root.rowSelected(row.index, mouse.modifiers)
                            deferSingleSelection = false
                            wasDragged = false
                        }
                        onCanceled: {
                            root.dragPreview.Drag.cancel()
                            root.dragPreview.sourcePointer = null
                            deferSingleSelection = false
                            wasDragged = false
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
                onEntered: function(drag) {
                    root.dropHovered = Boolean(
                        drag.source
                        && drag.source.sourceDirection !== root.dropDirection
                    )
                }
                onPositionChanged: function(drag) {
                    root.dropHovered = Boolean(
                        drag.source
                        && drag.source.sourceDirection !== root.dropDirection
                    )
                }
                onExited: root.dropHovered = false
                onDropped: function(drop) {
                    root.dropHovered = false
                    if (!drop.source
                            || drop.source.sourceDirection === root.dropDirection)
                        return
                    const keys = root.extractDropKeys(
                        drop.source, drop.text
                    )
                    if (!keys.length)
                        return
                    drop.acceptProposedAction()
                    Qt.callLater(function() {
                        root.objectsDropped(keys)
                    })
                }
            }

            Controls.DropTargetOverlay {
                z: 2
                visible: root.dropHovered
                theme: root.theme
                iconName: root.dropDirection === "add"
                    ? "arrow-forward" : "arrow-back"
                promptText: root.dropDirection === "add"
                    ? qsTr("Drop to link") : qsTr("Drop to unlink")
            }

            Label {
                anchors.centerIn: parent
                width: Math.min(280, parent.width - 36)
                visible: objectList.count === 0 && !root.loading
                text: root.emptyText
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
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
}
