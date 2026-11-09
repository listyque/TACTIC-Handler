import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/messages/message.ui.mjs" as UI

Frame.FrameView {
    id: root
    property string sender: ""
    property string body: ""
    property bool available: true
    property bool dismissible: false
    property bool forwarded: false
    property int attachmentCount: 0
    property real bodyHeight: 19
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    signal activated
    signal dismissed
    implicitHeight: scene.height
    scene: UI.reference({
        sender,
        body,
        available,
        dismissible,
        forwarded,
        attachments: attachmentCount
    }, width, language, bodyHeight)
    views: ({
            body: bodyPort
        })
    onEvent: action => {
        if (action.type === "open")
            root.activated();
        else if (action.type === "dismiss")
            root.dismissed();
    }
    Component {
        id: bodyPort
        Item {
            Text {
                id: bodyText
                width: parent.width
                height: implicitHeight
                textFormat: Text.PlainText
                text: root.body
                font: Qt.font({
                    family: root.theme.fontFamily,
                    pixelSize: 14
                })
                color: root.theme.primaryText
                wrapMode: Text.Wrap
                maximumLineCount: root.forwarded ? 3 : 2
                elide: Text.ElideRight
                function measure() {
                    const apply = function () {
                        if (bodyText.contentHeight > 0 && root.bodyHeight !== bodyText.contentHeight)
                            root.bodyHeight = bodyText.contentHeight;
                    };
                    if (root.inSceneChange)
                        Qt.callLater(apply);
                    else
                        apply();
                }
                onContentHeightChanged: measure()
                Component.onCompleted: measure()
            }
        }
    }
}
