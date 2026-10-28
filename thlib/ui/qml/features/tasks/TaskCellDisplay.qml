import QtQuick
import "../../tactic_frame/features/tasks/cells.ui.mjs" as UI
import "../../tactic_frame/core/foundation.mjs" as Foundation
import "../.."
import "../../controls" as Controls

Item {
    id: root
    required property var theme
    required property var model
    property var userModel: null
    property string login: ""
    property string avatarSource: ""
    property string avatarInitials: ""
    property bool scrolling: false
    readonly property var scene: UI.choice(Object.assign({}, model, {
        textHeight: cellMetrics.height
    }), width, height)
    readonly property var surface: scene.nodes[0]
    readonly property var label: scene.nodes.find(node => node.id === "taskTableCellDisplayLabel")
    readonly property var avatar: scene.nodes.find(node => node.id === "taskTableCellAvatar")
    readonly property var accent: scene.nodes.find(node => node.id === "taskTableCellAccent")
    readonly property var indicator: scene.nodes.find(node => node.id === "taskTableCellIndicator")

    FontMetrics {
        id: cellMetrics
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: Foundation.textStyles[root.model.fontRole || "body"],
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    // Keep shared geometry, but do not build a recursive Frame tree for an idle value.
    Rectangle {
        objectName: "taskTableCellSurface"
        anchors.fill: parent
        radius: root.theme[root.surface.radiusRole]
        color: root.theme[root.surface.background]
        border.width: root.surface.border ? 1 : 0
        border.color: root.surface.border ? root.theme[root.surface.border] : "transparent"
    }
    Rectangle {
        objectName: "taskTableCellAccent"
        visible: !!root.accent
        x: root.accent ? root.accent.x : 0
        y: root.accent ? root.accent.y : 0
        width: root.accent ? root.accent.width : 0
        height: root.accent ? root.accent.height : 0
        radius: root.accent ? root.accent.radius : 0
        color: root.accent ? root.accent.background : "transparent"
    }
    Text {
        objectName: "taskTableCellDisplayLabel"
        x: root.label.x
        y: root.label.y
        width: root.label.width
        height: root.label.height
        text: root.label.text
        textFormat: Text.PlainText
        color: root.theme[root.label.color]
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: root.label.fontSize,
            weight: root.label.weight,
            hintingPreference: Font.PreferVerticalHinting
        })
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    Loader {
        objectName: "taskTableCellAvatar"
        active: !!root.avatar
        x: root.avatar ? root.avatar.x : 0
        y: root.avatar ? root.avatar.y : 0
        width: root.avatar ? root.avatar.width : 0
        height: root.avatar ? root.avatar.height : 0
        sourceComponent: UserAvatar {
            theme: root.theme
            userModel: root.userModel
            login: root.login
            effectsEnabled: !root.scrolling
            avatarUrl: root.avatarSource
            initials: profile.initials || root.avatarInitials
            previewSize: Math.max(0, Math.min(22, root.height - 4))
        }
    }
    Loader {
        active: !!root.indicator
        x: root.indicator ? root.indicator.x : 0
        y: root.indicator ? root.indicator.y : 0
        width: root.indicator ? root.indicator.width : 0
        height: root.indicator ? root.indicator.height : 0
        sourceComponent: Controls.MaterialIcon {
            name: root.indicator.icon
            size: root.indicator.width
            color: root.theme[root.indicator.color]
        }
    }
}
