import QtQuick
import "features/support/feedback" as Feedback
import "tactic_frame" as Frame
import "tactic_frame/features/support/feedback/error.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property bool expanded: false
    property real requestHeight: 0
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            title: qsTr(debugLog.error_title),
            kind: debugLog.error_kind,
            errorType: debugLog.error_type,
            message: debugLog.error_message,
            stacktrace: debugLog.error_stacktrace,
            expanded,
            requestHeight,
            canRetry: debugLog.can_retry,
            canConfigure: true
        })
    Connections {
        target: debugLog
        function onError_changed() {
            if (debugLog.error_visible)
                root.expanded = false;
        }
    }
    function dispatch(action) {
        if (action.type === "expand")
            expanded = !expanded;
        else if (action.type === "copyStacktrace")
            debugLog.copy_error_stacktrace();
        else if (action.type === "debug") {
            debugLog.dismiss_error();
            debugLog.show();
        } else if (action.type === "help") {
            debugLog.dismiss_error();
            windowModel.open_help("errors");
        } else if (action.type === "primary")
            debugLog.primary_error_action();
        else if (action.type === "dismiss")
            debugLog.dismiss_error();
        else if (action.type === "retry" && debugLog.can_retry)
            debugLog.retry_error();
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.panel
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, root.width, root.height, root.language)
        views: ({
                requests: requestsComponent
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: requestsComponent
        Feedback.ErrorRequestBlocks {
            theme: root.theme
            onContentHeightChanged: root.requestHeight = contentHeight
        }
    }
}
