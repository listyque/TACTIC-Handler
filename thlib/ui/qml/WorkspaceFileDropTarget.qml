import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

DropArea {
    id: root

    required property var theme
    required property var controller
    required property string nodeId
    required property string nodeType
    required property string nodeTitle
    required property string targetProcess
    property bool spacious: false
    property int activeZone: -1
    property bool iconDropAvailable: false

    readonly property var processZones: [{
        "title": qsTr("Drop File to %1").arg(
            root.targetProcess || root.nodeTitle),
        "icon": "publish",
        "target": root.targetProcess || "publish"
    }]
    readonly property var iconZones: [
        {"title": qsTr("Add Icon"), "icon": "image", "target": "icon"},
        {"title": qsTr("Publish File"), "icon": "publish", "target": "publish"},
        {"title": qsTr("Attach File"), "icon": "attachment", "target": "attachment"}
    ]
    readonly property var fileZones: [
        {"title": qsTr("Publish File"), "icon": "publish", "target": "publish"},
        {"title": qsTr("Attach File"), "icon": "attachment", "target": "attachment"}
    ]
    readonly property var relationZones: [{
        "title": qsTr("Create Child Items"),
        "icon": "upload",
        "target": "ingest"
    }]
    readonly property var zoneModel: root.nodeType === "process"
        ? processZones : root.nodeType === "relation"
            ? relationZones : iconDropAvailable ? iconZones : fileZones

    function reset() {
        activeZone = -1
        iconDropAvailable = false
    }

    function updateCapabilities(urls) {
        iconDropAvailable = root.nodeType === "sobject"
            && controller.can_drop_as_icon(urls || [])
    }

    function updateZone(xPosition) {
        const count = Math.max(1, zoneModel.length)
        activeZone = Math.max(0, Math.min(
            count - 1,
            Math.floor(xPosition * count / Math.max(1, width))))
    }

    function activeTarget() {
        if (activeZone < 0 || activeZone >= zoneModel.length)
            return root.targetProcess || "publish"
        return String(zoneModel[activeZone].target || "publish")
    }

    objectName: "workspaceFileDropArea"
    z: 12
    enabled: root.nodeType === "sobject"
        || root.nodeType === "process"
        || root.nodeType === "relation"
    keys: ["text/uri-list"]
    onEntered: function(drag) {
        drag.acceptProposedAction()
        updateCapabilities(drag.urls)
        updateZone(drag.x)
    }
    onPositionChanged: function(drag) {
        updateZone(drag.x)
    }
    onExited: reset()
    onDropped: function(drop) {
        updateCapabilities(drop.urls)
        updateZone(drop.x)
        const targetNodeId = root.nodeId
        const target = activeTarget()
        const urls = drop.urls
        // Accept and clear the delegate-owned presentation before opening the
        // Commit Queue. Process rows can leave the result surface as a side
        // effect of that call, so the drop event must no longer depend on them.
        drop.acceptProposedAction()
        reset()
        controller.queue_dropped_files(targetNodeId, urls, target)
    }

    Loader {
        id: presentation
        objectName: "workspaceFileDropPresentation"
        anchors.fill: parent
        anchors.margins: root.spacious ? 3 : 0
        active: root.containsDrag
        z: 1
        sourceComponent: Rectangle {
            anchors.fill: parent
            anchors.margins: root.spacious ? 0 : 2
            clip: true
            radius: 12
            color: root.theme.panelRaised
            border.width: 0
            opacity: 0.98
            antialiasing: true

            Row {
                anchors.fill: parent
                anchors.margins: root.spacious ? 6 : 4
                spacing: root.spacious ? 5 : 4

                Repeater {
                    model: root.zoneModel

                    delegate: Rectangle {
                        required property int index
                        required property var modelData
                        readonly property bool active:
                            index === root.activeZone
                        width: (
                            parent.width - parent.spacing
                                * Math.max(0, root.zoneModel.length - 1)
                        ) / Math.max(1, root.zoneModel.length)
                        height: parent.height
                        clip: true
                        radius: root.spacious ? 10 : 9
                        color: active
                            ? root.theme.selected : "transparent"
                        border.width: active ? 1 : 0
                        border.color: root.theme.action
                        scale: active ? 1 : 0.96
                        opacity: active ? 1 : (root.spacious ? 0.56 : 0.58)
                        antialiasing: true

                        Behavior on color {
                            ColorAnimation { duration: root.theme.motionFast }
                        }
                        Behavior on scale {
                            NumberAnimation {
                                duration: root.theme.motionFast
                                easing.type: Easing.OutCubic
                            }
                        }
                        Behavior on opacity {
                            NumberAnimation { duration: root.theme.motionFast }
                        }

                        Column {
                            visible: root.spacious
                            anchors.centerIn: parent
                            width: Math.max(0, parent.width - 8)
                            spacing: 5

                            Controls.MaterialIcon {
                                anchors.horizontalCenter: parent.horizontalCenter
                                name: modelData.icon
                                size: active
                                    ? 26 : 21
                                color: active
                                    ? root.theme.action
                                    : root.theme.secondaryText

                                Behavior on size {
                                    NumberAnimation {
                                        duration: root.theme.motionFast
                                    }
                                }
                            }

                            Label {
                                width: parent.width
                                text: modelData.title
                                color: active
                                    ? root.theme.selectedText
                                    : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                font.weight: active
                                    ? Font.Bold : Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                            }
                        }

                        Row {
                            visible: !root.spacious
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: 6
                            anchors.rightMargin: 6
                            spacing: 5

                            Controls.MaterialIcon {
                                id: compactIcon
                                name: modelData.icon
                                size: active ? 18 : 16
                                color: active
                                    ? root.theme.action
                                    : root.theme.secondaryText

                                Behavior on size {
                                    NumberAnimation {
                                        duration: root.theme.motionFast
                                    }
                                }
                            }

                            Label {
                                width: Math.max(
                                    0,
                                    parent.width - compactIcon.width
                                        - parent.spacing
                                )
                                text: modelData.title
                                color: active
                                    ? root.theme.selectedText
                                    : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: active
                                    ? Font.Bold : Font.DemiBold
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                                maximumLineCount: 1
                            }
                        }
                    }
                }
            }
        }
    }
}
