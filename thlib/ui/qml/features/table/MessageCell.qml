import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/cells.ui.mjs" as Cells

Frame.FrameView {
    id: root
    property var cell: ({})
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    scene: Cells.message(cell, width, height, language)
}
