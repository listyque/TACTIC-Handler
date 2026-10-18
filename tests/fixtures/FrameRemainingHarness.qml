import QtQuick
import "../../thlib/ui/qml/tactic_frame" as Frame
import "../../thlib/ui/qml/tactic_frame/features/knowledge/commands.ui.mjs" as Commands
import "../../thlib/ui/qml/tactic_frame/features/knowledge/format.ui.mjs" as Formatting
import "../../thlib/ui/qml/tactic_frame/features/knowledge/navigation.ui.mjs" as Navigation
import "../../thlib/ui/qml/tactic_frame/features/workhours/sheet.ui.mjs" as Sheet
import "../../thlib/ui/qml/tactic_frame/features/workhours/reports.ui.mjs" as Reports
import "../../thlib/ui/qml/tactic_frame/features/support/collaboration/initialization.ui.mjs" as Collaboration

Frame.FrameView {
    id: root
    required property string screen
    required property var model
    readonly property string language: localizationController.current_language
    scene: screen === "editor" ? Commands.editor(model, width, language) : screen === "viewer" ? Commands.viewer(model, width, language) : screen === "format" ? Formatting.describe(model, width, language) : screen === "navigation" ? Navigation.row(model, true, "", width, language) : screen === "entry" ? Sheet.entry(model, width, language) : screen === "hourEditor" ? Sheet.editor(model, width, language) : screen === "summary" ? Sheet.summary(model, width, language) : screen === "initializeState" ? Collaboration.state(model, width, height, language) : screen === "initializeConfirm" ? Collaboration.confirmation(model, width, height, language) : Reports.valueRow(model, width, language)
}
