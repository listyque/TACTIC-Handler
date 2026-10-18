import QtQuick
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/activity/notifications.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var record
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    property var measured: ({})
    implicitHeight: scene.height
    scene: UI.row({
        kind: record.kind,
        group: record.group,
        detail: record.detail,
        time: record.timestampPretty || record.timestamp,
        hovered: hover.hovered
    }, width, measured, language)
    views: ({
            message: messagePort,
            time: timePort,
            detail: detailPort
        })
    function measure(part, item) {
        Qt.callLater(function () {
            if (item && item.contentHeight > 0 && root.measured[part] !== item.contentHeight)
                root.measured = Object.assign({}, root.measured, {
                    [part]: item.contentHeight
                });
        });
    }
    function rich(value) {
        return typeof appController !== "undefined" && appController.rich_text_html ? appController.rich_text_html(value) : value;
    }
    function activate(link) {
        if (typeof appController !== "undefined" && appController.open_rich_link)
            appController.open_rich_link(link);
    }
    HoverHandler {
        id: hover
    }
    Component {
        id: messagePort
        Controls.SelectableText {
            id: messageText
            objectName: "notificationMessageText"
            theme: root.theme
            richText: true
            text: root.rich(root.record.message)
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 14,
                weight: Font.DemiBold
            })
            onContentHeightChanged: root.measure("message", messageText)
            Component.onCompleted: root.measure("message", messageText)
            onLinkActivated: link => root.activate(link)
        }
    }
    Component {
        id: timePort
        Controls.SelectableText {
            id: timeText
            objectName: "notificationTimestampText"
            theme: root.theme
            text: root.record.timestampPretty || root.record.timestamp
            color: root.theme.secondaryText
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 11
            })
            horizontalAlignment: root.width >= 620 ? Text.AlignRight : Text.AlignLeft
            onContentHeightChanged: root.measure("time", timeText)
            Component.onCompleted: root.measure("time", timeText)
            HoverHandler {
                id: timeHover
            }
            Controls.ToolTip {
                theme: root.theme
                visible: timeHover.hovered && !!root.record.timestampFull
                text: root.record.timestampFull || ""
            }
        }
    }
    Component {
        id: detailPort
        Controls.SelectableText {
            id: detailText
            objectName: "notificationDetailText"
            theme: root.theme
            richText: true
            text: root.rich(root.record.detail)
            color: root.theme.secondaryText
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 12
            })
            onContentHeightChanged: root.measure("detail", detailText)
            Component.onCompleted: root.measure("detail", detailText)
            onLinkActivated: link => root.activate(link)
        }
    }
}
