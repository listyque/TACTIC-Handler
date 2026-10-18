import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/cells.ui.mjs" as UI
import "../../tactic_frame/core/foundation.mjs" as Foundation
import "../.."

Frame.FrameView {
    id: root
    required property var model
    property var userModel: null
    property string login: ""
    property string avatarSource: ""
    property string avatarInitials: ""
    property bool scrolling: false
    FontMetrics {
        id: cellMetrics
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: Foundation.textStyles[root.model.fontRole || "body"],
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    scene: UI.choice(Object.assign({}, model, {
        textHeight: cellMetrics.height
    }), width, height)
    views: ({
            avatar: {
                component: avatarPort
            }
        })
    Component {
        id: avatarPort
        UserAvatar {
            theme: root.theme
            userModel: root.userModel
            login: root.login
            effectsEnabled: !root.scrolling
            avatarUrl: root.avatarSource
            initials: profile.initials || root.avatarInitials
            previewSize: Math.max(0, Math.min(22, root.height - 4))
        }
    }
}
