import "../../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls as QtControls

// The native Material indicator keeps its scene-graph animation and accessibility.
QtControls.ProgressBar {
    id: control
    required property var theme
    implicitHeight: Foundation.controls.feedback.progressHeight
    padding: 0
    Material.accent: theme.action
    palette.highlight: theme.action
    palette.dark: Qt.rgba(theme.action.r, theme.action.g, theme.action.b, 0.25)
    palette.light: palette.dark
}
