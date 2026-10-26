pragma ComponentBehavior: Bound
import "tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import "tactic_frame/core" as Frame
import "tactic_frame/controls/menus/action.ui.mjs" as MenuRow
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: actionRow
    required property var menu
    required property int index
    readonly property var modelData: menu.displayedActions[index] || ({})
    readonly property bool actionEnabled: modelData.enabled !== false
    readonly property bool hasAccent: !!modelData.accent
    readonly property color actionAccent: hasAccent ? modelData.accent : menu.theme.action
    readonly property color avatarAccent: modelData.avatarColor || actionAccent
    readonly property alias primaryTarget: primaryActionTarget
    visible: modelData.visible !== false
    width: parent.width
    height: visible ? menu.actionHeight(modelData) : 0
    TextMetrics {
        id: badgeMetrics
        text: Number(actionRow.modelData.badgeCount || 0) > 99 ? "99+" : String(Number(actionRow.modelData.badgeCount || 0))
        font: Qt.font({
            family: actionRow.menu.theme.fontFamily,
            pixelSize: 11,
            weight: Font.Bold
        })
    }
    Frame.FrameBranch {
        active: actionRow.menu.frameComposition
        anchors.fill: parent
        visible: actionRow.menu.frameComposition
        interactive: false
        theme: actionRow.menu.theme
        scene: actionRow.menu.frameComposition ? MenuRow.row(Object.assign({}, actionRow.modelData, {
            accent: actionRow.hasAccent ? String(actionRow.actionAccent) : undefined,
            avatarColor: String(actionRow.avatarAccent),
            title: actionRow.modelData.translate === false ? String(actionRow.modelData.title || "") : actionRow.menu.translate(actionRow.modelData.title || "", actionRow.modelData.titleArgs),
            status: actionRow.modelData.statusTranslate === false ? actionRow.modelData.status : actionRow.menu.translate(actionRow.modelData.status || "")
        }), actionRow.width, {
            extent: actionRow.menu.theme.compactControlHeight,
            badgeTextWidth: badgeMetrics.advanceWidth,
            radius: actionRow.menu.theme.itemRadius,
            hovered: actionRow.menu.hoveredAction === actionRow,
            pressed: primaryActionTarget.pressed,
            focused: !actionRow.menu.hoveredAction && primaryActionTarget.activeFocus
        }) : ({
                nodes: []
            })
    }
    Rectangle {
        visible: !actionRow.menu.frameComposition && !!actionRow.modelData.separator
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        height: 1
        color: actionRow.menu.theme.separator
    }
    Rectangle {
        objectName: "actionMenuRowSurface"
        radius: actionRow.menu.processPickerStyle ? 7 : actionRow.menu.theme.itemRadius
        visible: !actionRow.menu.frameComposition && !actionRow.modelData.separator && !actionRow.modelData.header
        anchors.fill: parent
        color: actionRow.menu.processPickerStyle ? primaryActionTarget.pressed ? actionRow.menu.theme.surfaceContainerHighest : primaryActionTarget.hovered ? actionRow.menu.theme.surfaceContainerHigh : actionRow.menu.theme.blend(actionRow.menu.surfaceColor, actionRow.menu.theme.primaryText, actionRow.menu.theme.dark ? 0.05 : 0.08) : actionRow.hasAccent && !!actionRow.modelData.checked ? actionRow.actionAccent : actionRow.menu.theme.primaryText
        opacity: actionRow.menu.processPickerStyle ? 1 : actionRow.hasAccent && !!actionRow.modelData.checked ? 0.14 : primaryActionTarget.pressed ? 0.12 : actionRow.menu.hoveredAction === actionRow ? 0.08 : !actionRow.menu.hoveredAction && primaryActionTarget.activeFocus ? 0.10 : 0
        border.width: actionRow.menu.processPickerStyle ? 1 : 0
        border.color: actionRow.menu.processPickerStyle ? actionRow.menu.theme.blend(actionRow.menu.surfaceColor, actionRow.menu.theme.primaryText, actionRow.menu.theme.dark ? 0.10 : 0.15) : actionRow.menu.theme.outlineVariant
        Behavior on opacity {
            NumberAnimation {
                duration: primaryActionTarget.pressed ? actionRow.menu.theme.clickMotionFast : primaryActionTarget.hovered ? actionRow.menu.theme.hoverMotionFast : actionRow.menu.theme.hoverMotionMedium
                easing.type: Easing.OutCubic
            }
        }
    }
    RowLayout {
        visible: !actionRow.menu.frameComposition && !actionRow.modelData.separator
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 8
        spacing: 9
        Rectangle {
            objectName: "actionMenuAccentMarker"
            visible: !actionRow.modelData.header && actionRow.hasAccent && !actionRow.modelData.accentIcon
            Layout.preferredWidth: actionRow.menu.processPickerStyle ? 11 : actionRow.modelData.compactAccent ? 12 : 24
            Layout.preferredHeight: Layout.preferredWidth
            radius: width / 2
            color: actionRow.modelData.compactAccent ? "transparent" : Qt.rgba(actionRow.actionAccent.r, actionRow.actionAccent.g, actionRow.actionAccent.b, 0.16)
            Rectangle {
                anchors.centerIn: parent
                width: actionRow.menu.processPickerStyle ? 11 : actionRow.modelData.compactAccent ? 8 : 10
                height: width
                radius: width / 2
                color: actionRow.actionAccent
            }
        }
        Controls.MaterialIcon {
            objectName: "actionMenuIcon"
            visible: !actionRow.modelData.header && !!actionRow.modelData.icon && !actionRow.modelData.avatarUrl && !actionRow.modelData.initials
            name: actionRow.modelData.icon || "info"
            size: actionRow.menu.processPickerStyle ? 15 : 16
            color: actionRow.modelData.accentIcon && actionRow.hasAccent ? actionRow.actionAccent : actionRow.menu.theme.secondaryText
            forceSolid: !!actionRow.modelData.accentIcon
        }
        Controls.ItemPreview {
            objectName: "actionMenuAvatar"
            visible: !actionRow.modelData.header && (!!actionRow.modelData.avatarUrl || !!actionRow.modelData.initials)
            Layout.preferredWidth: actionRow.menu.processPickerStyle ? 22 : 26
            Layout.preferredHeight: Layout.preferredWidth
            theme: actionRow.menu.theme
            source: actionRow.modelData.avatarUrl || ""
            fallbackIcon: "person"
            fallbackText: actionRow.modelData.initials || ""
            accent: actionRow.modelData.avatarColor || actionRow.actionAccent
            round: true
            outlined: true
            animateAppearance: false
            previewSize: Layout.preferredWidth
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Label {
                objectName: "actionMenuTitleLabel"
                Layout.fillWidth: true
                text: actionRow.modelData.translate === false ? String(actionRow.modelData.title || "") : actionRow.menu.translate(actionRow.modelData.title || "", actionRow.modelData.titleArgs)
                color: actionRow.modelData.header || !actionRow.actionEnabled ? actionRow.menu.processPickerStyle && actionRow.modelData.header ? actionRow.menu.theme.disabledText : actionRow.menu.theme.secondaryText : actionRow.hasAccent && !!actionRow.modelData.checked ? actionRow.actionAccent : actionRow.menu.theme.primaryText
                font.family: actionRow.menu.theme.fontFamily
                font.pixelSize: actionRow.menu.processPickerStyle ? 11 : actionRow.modelData.header ? 10 : 12
                font.weight: actionRow.modelData.header ? Font.DemiBold : Font.Normal
                elide: Text.ElideRight
            }
            Label {
                visible: !!actionRow.modelData.status && !actionRow.modelData.header
                Layout.fillWidth: true
                text: actionRow.modelData.statusTranslate === false ? String(actionRow.modelData.status || "") : actionRow.menu.translate(actionRow.modelData.status || "")
                color: actionRow.modelData.status === "Experimental" ? actionRow.menu.theme.action : actionRow.menu.theme.secondaryText
                font.family: actionRow.menu.theme.fontFamily
                font.pixelSize: Foundation.textStyles.secondary
                elide: Text.ElideRight
            }
        }
        Rectangle {
            objectName: "actionMenuBadge"
            readonly property int countValue: Number(actionRow.modelData.badgeCount || 0)
            visible: actionRow.modelData.badgeCount !== undefined && (countValue > 0 || !!actionRow.modelData.showZeroBadge)
            Layout.preferredWidth: Math.max(actionRow.menu.processPickerStyle ? 20 : 18, menuBadgeLabel.implicitWidth + 8)
            Layout.preferredHeight: actionRow.menu.processPickerStyle ? 20 : 18
            radius: height / 2
            color: actionRow.modelData.badgeUpdated === true ? actionRow.menu.theme.error : actionRow.menu.processPickerStyle ? actionRow.menu.theme.blend(actionRow.menu.theme.surfaceContainerHigh, actionRow.menu.theme.primaryText, actionRow.menu.theme.dark ? 0.12 : 0.06) : actionRow.modelData.badgeUpdated === false ? actionRow.menu.theme.secondaryText : actionRow.menu.theme.error
            Label {
                id: menuBadgeLabel
                anchors.centerIn: parent
                text: parent.countValue > 99 ? "99+" : String(parent.countValue)
                color: actionRow.menu.processPickerStyle ? actionRow.menu.theme.primaryText : actionRow.menu.theme.selectedText
                font.family: actionRow.menu.theme.fontFamily
                font.pixelSize: actionRow.menu.processPickerStyle ? 10 : 11
                font.weight: Font.Bold
            }
        }
        Controls.MaterialIcon {
            visible: !!actionRow.modelData.checked
            name: "check_circle"
            size: 18
            color: actionRow.hasAccent ? actionRow.actionAccent : actionRow.menu.theme.action
        }
        Controls.MaterialIcon {
            visible: !!actionRow.modelData.children || !!actionRow.modelData.submenuPopup
            name: "chevron-right"
            size: 16
            color: actionRow.menu.theme.secondaryText
        }
        Controls.MaterialIcon {
            visible: !!actionRow.modelData.secondaryCommand
            name: actionRow.modelData.secondaryIcon || "update"
            size: 15
            color: secondaryActionTarget.hovered ? actionRow.menu.theme.action : actionRow.menu.theme.secondaryText
        }
    }
    Controls.PopupAction {
        id: primaryActionTarget
        objectName: "actionMenuPrimaryTarget"
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.rightMargin: actionRow.modelData.secondaryCommand ? 30 : 0
        enabled: !actionRow.modelData.separator && !actionRow.modelData.header && actionRow.actionEnabled
        hoverEnabled: true
        onHoveredChanged: {
            if (hovered)
                actionRow.menu.hoverAction(actionRow);
            else if (actionRow.menu.hoveredAction === actionRow)
                actionRow.menu.hoveredAction = null;
        }
        focusPolicy: Qt.StrongFocus
        Keys.onRightPressed: actionRow.menu.openSubmenu(actionRow)
        Keys.onLeftPressed: event => {
            if (actionRow.menu.parentMenu)
                actionRow.menu.close();
            else
                event.accepted = false;
        }
        Keys.onDownPressed: actionRow.menu.focusRelativeAction(1)
        Keys.onUpPressed: actionRow.menu.focusRelativeAction(-1)
        Accessible.name: actionRow.modelData.translate === false ? String(actionRow.modelData.title || "") : actionRow.menu.translate(actionRow.modelData.title || "", actionRow.modelData.titleArgs)
        Accessible.role: actionRow.modelData.role === "menuitemcheckbox" ? Accessible.CheckBox : Accessible.Button
        Accessible.checkable: actionRow.modelData.role === "menuitemcheckbox"
        Accessible.checked: Accessible.checkable && !!actionRow.modelData.checked
        onActiveFocusChanged: {
            if (activeFocus)
                actionRow.menu.revealAction(actionRow);
        }
        background: null
        contentItem: null
        onPressedChanged: {
            if (pressed)
                actionRipple.burst(width / 2, height / 2);
        }
        onClicked: {
            if (actionRow.modelData.toggleAdvanced)
                actionRow.menu.toggleAdvanced();
            else if (actionRow.modelData.children || actionRow.modelData.submenuPopup)
                actionRow.menu.openSubmenu(actionRow);
            else
                actionRow.menu.dispatchAction(actionRow.modelData.command, false, !!actionRow.modelData.keepOpen);
        }
        HoverHandler {
            enabled: primaryActionTarget.enabled
            cursorShape: Qt.PointingHandCursor
        }
    }
    Controls.MaterialRipple {
        id: actionRipple
        theme: actionRow.menu.theme
        visible: !actionRow.modelData.separator && !actionRow.modelData.header
        color: actionRow.menu.theme.ripple
        shapeRadius: 10
    }
    Controls.PopupAction {
        id: secondaryActionTarget
        objectName: "actionMenuSecondaryTarget"
        visible: !actionRow.modelData.separator && !actionRow.modelData.header && !!actionRow.modelData.secondaryCommand
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        width: 30
        enabled: visible && actionRow.actionEnabled
        hoverEnabled: true
        focusPolicy: Qt.StrongFocus
        Accessible.name: actionRow.modelData.secondaryToolTip ? actionRow.menu.translate(actionRow.modelData.secondaryToolTip) : actionRow.menu.translate("Sync updates only")
        background: null
        contentItem: null
        onClicked: {
            actionRow.menu.dispatchAction(actionRow.modelData.secondaryCommand, true, !!actionRow.modelData.secondaryKeepOpen);
        }
        HoverHandler {
            enabled: secondaryActionTarget.enabled
            cursorShape: Qt.PointingHandCursor
        }
        Controls.ToolTip {
            theme: actionRow.menu.theme
            visible: secondaryActionTarget.hovered && !actionRow.menu.theme.suppressToolTips
            text: actionRow.modelData.secondaryToolTip ? actionRow.menu.translate(actionRow.modelData.secondaryToolTip) : actionRow.menu.translate("Sync updates only")
            delay: 400
        }
    }
}
