import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/activity/toast.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var record
    property string replyText: ""
    property bool replyWasOpen: false
    property var measured: ({})
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    signal requested(var action)
    implicitHeight: scene.height
    scene: UI.describe(Object.assign({}, record, {
        replyText
    }), width, measured, language)
    views: ({
            message: messagePort,
            detail: detailPort,
            error: errorPort,
            progress: progressPort
        })
    function measure(part, item) {
        Qt.callLater(function () {
            if (item && item.contentHeight > 0 && root.measured[part] !== item.contentHeight)
                root.measured = Object.assign({}, root.measured, {
                    [part]: item.contentHeight
                });
        });
    }
    onRecordChanged: {
        if (record.replyOpen && !replyWasOpen)
            Qt.callLater(function () {
                root.focusControl("notificationReplyField");
            });
        replyWasOpen = !!record.replyOpen;
    }
    onEvent: action => {
        if (action.type === "text")
            replyText = action.value;
        else
            requested(Object.assign({}, action, {
                text: replyText
            }));
    }
    Component {
        id: messagePort
        Label {
            id: message
            textFormat: Text.PlainText
            objectName: "notificationMessage"
            text: root.record.sourceType ? root.record.message : qsTr(root.record.message)
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 13,
                weight: Font.DemiBold
            })
            color: root.theme.primaryText
            wrapMode: Text.Wrap
            onContentHeightChanged: root.measure("message", message)
            Component.onCompleted: root.measure("message", message)
        }
    }
    Component {
        id: detailPort
        Label {
            id: detail
            textFormat: Text.PlainText
            objectName: "notificationDetail"
            text: root.record.detail
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 11
            })
            color: root.theme.secondaryText
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
            onContentHeightChanged: root.measure("detail", detail)
            Component.onCompleted: root.measure("detail", detail)
        }
    }
    Component {
        id: errorPort
        Label {
            id: error
            textFormat: Text.PlainText
            text: root.record.replyError === "Unable to send message" ? qsTr("Unable to send message") : root.record.replyError
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 11
            })
            color: root.theme.error
            wrapMode: Text.Wrap
            onContentHeightChanged: root.measure("error", error)
            Component.onCompleted: root.measure("error", error)
        }
    }
    Component {
        id: progressPort
        ProgressBar {
            Material.accent: root.theme.action
            indeterminate: root.record.progress < 0
            value: root.record.progress
        }
    }
}
