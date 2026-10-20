import "../../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls.Material as MaterialControls

// The native Material indicator keeps its scene-graph animation and accessibility.
MaterialControls.ProgressBar {
    id: control
    required property var theme
    implicitHeight: Foundation.controls.feedback.progressHeight
    padding: 0
    MaterialControls.Material.accent: theme.action
}
