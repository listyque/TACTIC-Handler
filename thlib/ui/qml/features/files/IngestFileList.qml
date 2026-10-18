import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/files/ingest.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    required property var fileModel
    property string language: "en"
    ListView {
        id: list
        objectName: "ingestFilesList"
        x: 6
        y: 6
        width: Math.max(0, parent.width - 12)
        height: Math.max(0, parent.height - 12)
        model: root.fileModel
        spacing: 4
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        delegate: Frame.FrameView {
            required property int index
            required property string path
            required property string title
            required property string extension
            required property string status
            required property string error
            width: Math.max(0, list.width - 16)
            height: UI.fileHeight({
                error
            })
            theme: root.theme
            scene: UI.fileRow({
                busy: root.controller.busy
            }, {
                title,
                extension,
                status,
                error
            }, index, width, root.language)
            onEvent: action => root.controller.remove_file(action.index)
        }
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: list
        }
    }
}
