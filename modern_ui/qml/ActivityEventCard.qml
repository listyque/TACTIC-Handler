import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property string kind: "activity"
    property string eventTitle: ""
    property string detail: ""
    property string actor: ""
    property string timestamp: ""
    property string targetSearchKey: ""
    property string targetTitle: ""
    property string targetType: ""
    property string process: ""
    property string context: ""
    property string version: ""
    property bool canOpenActivity: false
    property bool canOpenTarget: false

    signal activityRequested()
    signal targetRequested()

    implicitHeight: Math.max(82, eventContent.implicitHeight + 20)

    function activityIcon(value) {
        switch (String(value || "")) {
        case "publication": return "snapshot"
        case "note": return "notes"
        case "message": return "messages"
        case "task": return "task"
        case "status": return "system-activity"
        default: return "activity-feed"
        }
    }

    function activityTitle(value, fallback) {
        switch (String(value || "")) {
        case "publication": return qsTr("Published snapshot")
        case "note": return qsTr("Added note")
        case "message": return qsTr("Sent message")
        case "task": return qsTr("Updated task")
        case "status": return qsTr("Status changed")
        default: return fallback
        }
    }

    function shortSearchType(value) {
        const parts = String(value || "").split("/")
        return parts.length
            ? parts[parts.length - 1].replace(/_/g, " ") : ""
    }

    readonly property color accent: kind === "publication"
        ? theme.green : kind === "task" ? theme.yellow : theme.action

    ItemSurface {
        anchors.fill: parent
        theme: root.theme
        hovered: cardPointer.hovered
        cornerRadius: root.theme.itemRadius
        inset: 1
        separatorVisible: false
        accent: root.accent
        railVisible: true
    }

    HoverHandler {
        id: cardPointer
    }

    RowLayout {
        id: eventContent
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        Rectangle {
            Layout.preferredWidth: 36
            Layout.preferredHeight: 36
            radius: 18
            color: root.theme.panelRaised

            MaterialIcon {
                anchors.centerIn: parent
                name: root.activityIcon(root.kind)
                size: 16
                color: root.accent
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    text: root.activityTitle(root.kind, root.eventTitle)
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    visible: root.actor.length > 0
                    text: root.actor
                    color: root.theme.action
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.caption
                    elide: Text.ElideRight
                    Layout.maximumWidth: 140
                }
                Label {
                    text: root.timestamp
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.caption
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 5

                MaterialIcon {
                    name: root.kind === "message" ? "messages" : "sobject"
                    size: 11
                    color: root.canOpenTarget
                        ? root.theme.action : root.theme.secondaryText
                }
                Label {
                    Layout.fillWidth: true
                    text: root.targetTitle.length
                        ? root.targetTitle : qsTr("Related object unavailable")
                    color: root.canOpenTarget
                        ? root.theme.action : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                    font.weight: Font.Medium
                    elide: Text.ElideRight

                    MouseArea {
                        anchors.fill: parent
                        enabled: root.canOpenTarget
                        cursorShape: enabled
                            ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onClicked: root.targetRequested()
                    }
                }
                Label {
                    text: root.shortSearchType(root.targetType)
                    visible: text.length > 0
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.caption
                }
                Label {
                    text: root.context.length ? root.context : root.process
                    visible: text.length > 0
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.caption
                }
                Label {
                    text: root.version.length
                        ? qsTr("Version %1").arg(root.version) : ""
                    visible: text.length > 0
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.caption
                }
            }

            Label {
                Layout.fillWidth: true
                text: root.detail
                visible: text.length > 0
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.label
                maximumLineCount: 2
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
            }
        }

        CompactIconButton {
            theme: root.theme
            visible: root.canOpenActivity && root.kind !== "status"
            iconName: "open-in-new"
            iconColor: root.theme.action
            toolTip: qsTr("Open activity")
            onClicked: root.activityRequested()
        }
        CompactIconButton {
            theme: root.theme
            visible: root.canOpenTarget
            iconName: root.kind === "message" ? "messages" : "arrow-forward"
            toolTip: root.kind === "message"
                ? qsTr("Open conversation") : qsTr("Open related object")
            onClicked: root.targetRequested()
        }
    }
}
