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
    property bool displayActive: true
    property bool scrolling: false
    readonly property string fontRole: root.model.fontRole || "body"
    readonly property bool hasAvatar: !!root.model.avatar
    readonly property bool hasAccent: !!(root.model.showAccent && root.model.accent)
    readonly property bool hasIndicator: !!root.model.indicator
    readonly property bool cellEnabled: !!root.model.enabled
    readonly property bool cellHovered: !!root.model.hovered
    readonly property bool actionField: root.model.actionField !== false
    readonly property bool isCardField: !!root.model.cardField
    readonly property var layout: UI.choiceLayout({
        avatar: root.hasAvatar,
        showAccent: root.hasAccent,
        accent: root.hasAccent,
        indicator: root.hasIndicator,
        fontRole: root.fontRole,
        cardField: root.isCardField,
        textHeight: cellMetrics ? cellMetrics.height : 0
    }, width, height)
    readonly property var surface: UI.choiceStyle({
        enabled: root.cellEnabled,
        hovered: root.cellHovered,
        actionField: root.actionField,
        cardField: root.isCardField
    })
    readonly property var label: layout.label
    readonly property var avatar: layout.avatar
    readonly property var accent: layout.accent
    readonly property var indicator: layout.indicator

    readonly property var cellMetrics: root.fontRole === "caption" ? Controls.Typography.captionMetrics : Controls.Typography.bodyMetrics
    // Keep shared geometry, but do not build a recursive Frame tree for an idle value.
    Rectangle {
        visible: root.displayActive
        objectName: "taskTableCellSurface"
        anchors.fill: parent
        radius: root.theme[root.surface.radiusRole]
        color: root.surface.background ? root.theme[root.surface.background] : "transparent"
        border.width: root.surface.border ? 1 : 0
        border.color: root.surface.border ? root.theme[root.surface.border] : "transparent"
    }
    Rectangle {
        objectName: "taskTableCellAccent"
        visible: root.displayActive && !!root.accent
        x: root.accent ? root.accent.x : 0
        y: root.accent ? root.accent.y : 0
        width: root.accent ? root.accent.width : 0
        height: root.accent ? root.accent.height : 0
        radius: root.accent ? root.accent.radius : 0
        color: root.accent ? root.model.accent : "transparent"
    }
    Text {
        visible: root.displayActive
        objectName: "taskTableCellDisplayLabel"
        x: root.label.x
        y: root.label.y
        width: root.label.width
        height: root.label.height
        text: root.model.text || ""
        textFormat: Text.PlainText
        color: root.theme[root.surface.textColor]
        font: cellMetrics ? cellMetrics.font : Qt.font({
            family: root.theme.fontFamily,
            pixelSize: Foundation.textStyles[root.fontRole],
            weight: Font.Normal,
            hintingPreference: Font.PreferVerticalHinting
        })
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    Loader {
        visible: root.displayActive
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
            initials: (profile && profile.initials) || root.avatarInitials
            previewSize: root.avatar ? root.avatar.width : 0
        }
    }
    Controls.MaterialIcon {
        visible: root.displayActive && !!root.indicator
        x: root.indicator ? root.indicator.x : 0
        y: root.indicator ? root.indicator.y : 0
        width: root.indicator ? root.indicator.width : 0
        height: root.indicator ? root.indicator.height : 0
        name: visible ? root.surface.indicatorIcon : ""
        size: root.indicator ? root.indicator.width : 0
        color: root.theme[root.surface.indicatorColor]
    }
}
