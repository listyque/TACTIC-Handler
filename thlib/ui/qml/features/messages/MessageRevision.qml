import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/messages/panels.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var record
    property string mode: "history"
    property bool busy: false
    property real bodyHeight: 18
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    signal activated(string messageId)
    implicitHeight: scene.height
    scene: UI.revision(Object.assign({}, record, {
        mode,
        busy
    }), width, bodyHeight, language)
    views: ({
            body: bodyPort
        })
    onEvent: action => activated(action.value)
    Component {
        id: bodyPort
        Text {
            id: body
            textFormat: Text.PlainText
            text: root.mode === "pin-history" ? root.record.summary || root.record.body || qsTr("Pinned message") : root.record.body || ""
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 13,
                hintingPreference: Font.PreferVerticalHinting
            })
            color: root.theme.primaryText
            wrapMode: Text.Wrap
            onContentHeightChanged: Qt.callLater(function () {
                root.bodyHeight = body.contentHeight;
            })
            Component.onCompleted: root.bodyHeight = contentHeight
        }
    }
}
