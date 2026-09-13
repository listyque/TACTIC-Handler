import QtQuick
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
    readonly property alias primaryTarget: primaryActionTarget
    visible: modelData.visible !== false
    width: parent.width
    height: visible ? menu.actionHeight(modelData) : 0
    Rectangle {
        visible: !!modelData.separator
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        height: 1
        color: menu.theme.separator
    }
    Rectangle {
        objectName: "actionMenuRowSurface"
        radius: menu.processPickerStyle ? 7 : menu.theme.itemRadius
        visible: !modelData.separator && !modelData.header
        anchors.fill: parent
        color: menu.processPickerStyle ? primaryActionTarget.pressed ? menu.theme.surfaceContainerHighest : primaryActionTarget.hovered ? menu.theme.surfaceContainerHigh : menu.theme.blend(menu.surfaceColor, menu.theme.primaryText, menu.theme.dark ? 0.05 : 0.08) : actionRow.hasAccent && !!modelData.checked ? actionRow.actionAccent : menu.theme.primaryText
        opacity: menu.processPickerStyle ? 1
            : actionRow.hasAccent && !!modelData.checked ? 0.14
            : primaryActionTarget.pressed ? 0.12
            : menu.hoveredAction === actionRow ? 0.08
            : !menu.hoveredAction && primaryActionTarget.activeFocus ? 0.10 : 0
        border.width: menu.processPickerStyle ? 1 : 0
        border.color: menu.processPickerStyle ? menu.theme.blend(menu.surfaceColor, menu.theme.primaryText, menu.theme.dark ? 0.10 : 0.15) : menu.theme.outlineVariant
        Behavior on opacity {
            NumberAnimation {
                duration: primaryActionTarget.pressed ? menu.theme.clickMotionFast : primaryActionTarget.hovered ? menu.theme.hoverMotionFast : menu.theme.hoverMotionMedium
                easing.type: Easing.OutCubic
            }
        }
    }
    RowLayout {
        visible: !modelData.separator
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 8
        spacing: 9
        Rectangle {
            objectName: "actionMenuAccentMarker"
            visible: !modelData.header && actionRow.hasAccent && !modelData.accentIcon
            Layout.preferredWidth: menu.processPickerStyle ? 11 : modelData.compactAccent ? 12 : 24
            Layout.preferredHeight: Layout.preferredWidth
            radius: width / 2
            color: modelData.compactAccent ? "transparent" : Qt.rgba(actionRow.actionAccent.r, actionRow.actionAccent.g, actionRow.actionAccent.b, 0.16)
            Rectangle {
                anchors.centerIn: parent
                width: menu.processPickerStyle ? 11 : modelData.compactAccent ? 8 : 10
                height: width
                radius: width / 2
                color: actionRow.actionAccent
            }
        }
        Controls.MaterialIcon {
            objectName: "actionMenuIcon"
            visible: !modelData.header && !!modelData.icon && !modelData.avatarUrl && !modelData.initials
            name: modelData.icon || "info"
            size: menu.processPickerStyle ? 15 : 16
            color: modelData.accentIcon && actionRow.hasAccent ? actionRow.actionAccent : menu.theme.secondaryText
            forceSolid: !!modelData.accentIcon
        }
        Controls.ItemPreview {
            objectName: "actionMenuAvatar"
            visible: !modelData.header && (!!modelData.avatarUrl || !!modelData.initials)
            Layout.preferredWidth: menu.processPickerStyle ? 22 : 26
            Layout.preferredHeight: Layout.preferredWidth
            theme: menu.theme
            source: modelData.avatarUrl || ""
            fallbackIcon: "person"
            fallbackText: modelData.initials || ""
            accent: modelData.avatarColor || actionRow.actionAccent
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
                text: modelData.translate === false
                    ? String(modelData.title || "")
                    : menu.translate(modelData.title || "", modelData.titleArgs)
                color: modelData.header || !actionRow.actionEnabled ? menu.processPickerStyle && modelData.header ? menu.theme.disabledText : menu.theme.secondaryText : actionRow.hasAccent && !!modelData.checked ? actionRow.actionAccent : menu.theme.primaryText
                font.family: menu.theme.fontFamily
                font.pixelSize: menu.processPickerStyle ? 11 : modelData.header ? 10 : 12
                font.weight: modelData.header ? Font.DemiBold : Font.Normal
                elide: Text.ElideRight
            }
            Label {
                visible: !!modelData.status && !modelData.header
                Layout.fillWidth: true
                text: modelData.statusTranslate === false ? String(modelData.status || "") : menu.translate(modelData.status || "")
                color: modelData.status === "Experimental" ? menu.theme.action : menu.theme.secondaryText
                font.family: menu.theme.fontFamily
                font.pointSize: Controls.Typography.label
                elide: Text.ElideRight
            }
        }
        Rectangle {
            objectName: "actionMenuBadge"
            readonly property int countValue: Number(modelData.badgeCount || 0)
            visible: modelData.badgeCount !== undefined && (countValue > 0 || !!modelData.showZeroBadge)
            Layout.preferredWidth: Math.max(menu.processPickerStyle ? 20 : 18, menuBadgeLabel.implicitWidth + 8)
            Layout.preferredHeight: menu.processPickerStyle ? 20 : 18
            radius: height / 2
            color: modelData.badgeUpdated === true ? menu.theme.error : menu.processPickerStyle ? menu.theme.blend(menu.theme.surfaceContainerHigh, menu.theme.primaryText, menu.theme.dark ? 0.12 : 0.06) : modelData.badgeUpdated === false ? menu.theme.secondaryText : menu.theme.error
            Label {
                id: menuBadgeLabel
                anchors.centerIn: parent
                text: parent.countValue > 99 ? "99+" : String(parent.countValue)
                color: menu.processPickerStyle ? menu.theme.primaryText : menu.theme.selectedText
                font.family: menu.theme.fontFamily
                font.pixelSize: menu.processPickerStyle ? 10 : 11
                font.weight: Font.Bold
            }
        }
        Controls.MaterialIcon {
            visible: !!modelData.checked
            name: "check_circle"
            size: 18
            color: actionRow.hasAccent ? actionRow.actionAccent : menu.theme.action
        }
        Controls.MaterialIcon {
            visible: !!modelData.children || !!modelData.submenuPopup
            name: "chevron-right"
            size: 16
            color: menu.theme.secondaryText
        }
        Controls.MaterialIcon {
            visible: !!modelData.secondaryCommand
            name: modelData.secondaryIcon || "update"
            size: 15
            color: secondaryActionTarget.hovered ? menu.theme.action : menu.theme.secondaryText
        }
    }
    Controls.PopupAction {
        id: primaryActionTarget
        objectName: "actionMenuPrimaryTarget"
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.rightMargin: modelData.secondaryCommand ? 30 : 0
        enabled: !modelData.separator && !modelData.header && actionRow.actionEnabled
        hoverEnabled: true
        onHoveredChanged: {
            if (hovered)
                menu.hoverAction(actionRow);
            else if (menu.hoveredAction === actionRow)
                menu.hoveredAction = null;
        }
        focusPolicy: Qt.StrongFocus
        Keys.onRightPressed: menu.openSubmenu(actionRow)
        Keys.onLeftPressed: event => {
            if (menu.parentMenu)
                menu.close()
            else
                event.accepted = false
        }
        Keys.onDownPressed: menu.focusRelativeAction(1)
        Keys.onUpPressed: menu.focusRelativeAction(-1)
        Accessible.name: modelData.translate === false
            ? String(modelData.title || "")
            : menu.translate(modelData.title || "", modelData.titleArgs)
        onActiveFocusChanged: {
            if (activeFocus)
                menu.revealAction(actionRow);
        }
        background: null
        contentItem: null
        onPressedChanged: {
            if (pressed)
                actionRipple.burst(width / 2, height / 2);
        }
        onClicked: {
            if (modelData.toggleAdvanced)
                menu.toggleAdvanced();
            else if (modelData.children || modelData.submenuPopup)
                menu.openSubmenu(actionRow);
            else
                menu.dispatchAction(modelData.command, false, !!modelData.keepOpen);
        }
        HoverHandler {
            enabled: primaryActionTarget.enabled
            cursorShape: Qt.PointingHandCursor
        }
    }
    Controls.MaterialRipple {
        id: actionRipple
        theme: menu.theme
        visible: !modelData.separator && !modelData.header
        color: menu.theme.ripple
        shapeRadius: 10
    }
    Controls.PopupAction {
        id: secondaryActionTarget
        objectName: "actionMenuSecondaryTarget"
        visible: !modelData.separator && !modelData.header && !!modelData.secondaryCommand
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        width: 30
        enabled: visible && actionRow.actionEnabled
        hoverEnabled: true
        focusPolicy: Qt.StrongFocus
        Accessible.name: modelData.secondaryToolTip ? menu.translate(modelData.secondaryToolTip) : menu.translate("Sync updates only")
        background: null
        contentItem: null
        onClicked: {
            menu.dispatchAction(modelData.secondaryCommand, true, !!modelData.secondaryKeepOpen);
        }
        HoverHandler {
            enabled: secondaryActionTarget.enabled
            cursorShape: Qt.PointingHandCursor
        }
        Controls.ToolTip {
            theme: menu.theme
            visible: secondaryActionTarget.hovered && !menu.theme.suppressToolTips
            text: modelData.secondaryToolTip ? menu.translate(modelData.secondaryToolTip) : menu.translate("Sync updates only")
            delay: 400
        }
    }
}
