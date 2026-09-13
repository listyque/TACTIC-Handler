import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Menu {
    id: root
    property var actions: []
    property real preferredWidth: 244
    property double lastClosedAt: 0
    property var lastSourceItem: null
    property string pendingCommand: ""
    property bool pendingSecondary: false
    property int commandCloseGeneration: 0
    property bool processPickerStyle: false
    property bool alignBelowRight: false
    property real belowRightOverhang: 0
    property int focusedActionIndex: -1
    property bool advancedExpanded: false
    property bool compact: hasAdvancedActions
    property var parentMenu: null
    property var submenuAnchor: null
    property var hoveredAction: null
    property var activeSubmenu: null
    property var actionSubmenu: null
    property var pendingSubmenuRow: null
    readonly property bool keyboardActive: root.visible
        && !(root.activeSubmenu && root.activeSubmenu.visible)
    readonly property bool hasAdvancedActions: (actions || []).some(
        action => action.advanced === true && action.visible !== false)
    readonly property var displayedActions: {
        if (!hasAdvancedActions)
            return actions || []
        const result = []
        let separatorPending = false
        for (const action of actions) {
            if (action.visible === false || (action.advanced && !advancedExpanded))
                continue
            if (action.separator) {
                separatorPending = result.length > 0
                continue
            }
            if (separatorPending)
                result.push({separator: true})
            result.push(action)
            separatorPending = false
        }
        if (result.length)
            result.push({separator: true})
        result.push({
            title: advancedExpanded ? qsTr("Basic menu") : qsTr("Advanced menu"),
            translate: false,
            icon: "more-horiz",
            toggleAdvanced: true
        })
        return result
    }
    signal triggered(string command)
    signal secondaryTriggered(string command)
    readonly property real resolvedWidth: Math.min(
        preferredWidth,
        maximumAvailableWidth - 2 * effectiveShadowMargin,
        usePopupWindow || parentMenu || !parent || parent.width <= 0
            ? preferredWidth : Math.max(0, parent.width - 8)
    ) + 2 * effectiveShadowMargin
    width: resolvedWidth
    readonly property real menuHeightLimit:
        usePopupWindow && availableScreenHeight > 0
            ? maximumAvailableHeight
            : Math.min(
                parent && parent.height > 0
                    ? Math.max(0, parent.height - 8)
                    : maximumAvailableHeight,
                maximumAvailableHeight
            )
    readonly property real calculatedContentHeight: {
        let total = 0
        let visibleRows = 0
        const records = root.displayedActions
        for (let index = 0; index < records.length; ++index) {
            const action = records[index] || ({})
            if (action.visible === false)
                continue
            if (visibleRows > 0)
                total += processPickerStyle ? 2 : 1
            total += root.actionHeight(action)
            ++visibleRows
        }
        return total
    }
    height: implicitHeight
    padding: 6
    surfaceRadius: processPickerStyle ? 8 : theme.menuRadius
    surfaceColor: processPickerStyle
        ? theme.blend(
            theme.panelDeep,
            theme.blackMix,
            theme.dark ? 0.18 : 0.04
        ) : theme.surfaceContainerHigh
    surfaceBorderColor: processPickerStyle
        ? theme.blend(
            surfaceColor,
            theme.primaryText,
            theme.dark ? 0.16 : 0.22
        ) : theme.outlineVariant
    surfaceBorderWidth: 1
    anchorPointerSize: processPickerStyle ? 14 : 12
    usePopupWindow: true
    modal: false
    dim: false
    focus: true
    settledClosePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    // Badge menus expose already-loaded counts and always open immediately.
    animationsEnabled: !processPickerStyle && theme.popupAnimationsEnabled
    implicitHeight: Math.min(
        calculatedContentHeight + topPadding + bottomPadding,
        menuHeightLimit
    )
    onAboutToShow: {
        ++root.commandCloseGeneration
        root.advancedExpanded = false
    }
    onActionsChanged: {
        root.advancedExpanded = false
        root.pendingSubmenuRow = null
        if (activeSubmenu)
            activeSubmenu.close()
    }
    onOpened: {
        clampToViewport()
        Qt.callLater(root.focusFirstAction)
    }
    onWidthChanged: {
        if (opened)
            Qt.callLater(clampToViewport)
    }
    onHeightChanged: {
        if (opened)
            Qt.callLater(clampToViewport)
    }
    onClosed: {
        lastClosedAt = Date.now()
        submenuHover.stop()
        hoveredAction = null
        pendingSubmenuRow = null
        if (activeSubmenu)
            activeSubmenu.close()
        root.advancedExpanded = false
        root.flushPendingCommand()
        if (parentMenu && parentMenu.opened && submenuAnchor)
            submenuAnchor.primaryTarget.forceActiveFocus(Qt.PopupFocusReason)
    }

    function actionHeight(action) {
        if (action.separator)
            return 5
        if (action.header)
            return processPickerStyle ? 22 : 28
        if (processPickerStyle)
            return action.status ? 42 : 32
        return action.status ? 48 : theme.compactControlHeight
    }

    function translate(text, args) {
        let translated = qsTr(text || "")
        for (const value of args || [])
            translated = translated.arg(value)
        return translated
    }

    function toggleAdvanced() {
        const generation = root.commandCloseGeneration
        Qt.callLater(function() {
            if (!root.opened || generation !== root.commandCloseGeneration)
                return
            root.advancedExpanded = !root.advancedExpanded
            menuFlickable.contentY = 0
            Qt.callLater(root.focusFirstAction)
        })
    }

    function clampToViewport() {
        if (root.usePopupWindow || !root.parent)
            return
        root.x = Math.max(
            4,
            Math.min(Math.max(4, root.parent.width - root.width - 4), root.x)
        )
        root.y = Math.max(
            4,
            Math.min(Math.max(4, root.parent.height - root.height - 4), root.y)
        )
    }

    function dispatchAndClose(command, secondary) {
        root.pendingCommand = String(command || "")
        root.pendingSecondary = !!secondary
        if (!root.opened) {
            root.flushPendingCommand()
            return
        }
        // Keep the native popup alive until the activating pointer release has
        // completely left Qt's delivery stack. Closing its window directly
        // from TapHandler.onTapped can let the tail of the same Windows input
        // sequence reach the sObject delegate underneath.
        const generation = ++root.commandCloseGeneration
        Qt.callLater(function() {
            if (generation !== root.commandCloseGeneration)
                return
            if (root.opened)
                root.close()
            else
                root.flushPendingCommand()
        })
    }

    function dispatchAction(command, secondary, keepOpen) {
        const stableCommand = String(command || "")
        if (!stableCommand)
            return
        if (root.parentMenu) {
            root.parentMenu.dispatchAction(stableCommand, secondary, keepOpen)
            return
        }
        if (!keepOpen) {
            root.dispatchAndClose(stableCommand, secondary)
            return
        }
        // Drill-down rows replace this popup's records in place. Closing and
        // reopening against the same anchor is both visually noisy and is
        // correctly rejected by the duplicate-input guard.
        Qt.callLater(function() {
            if (secondary)
                root.secondaryTriggered(stableCommand)
            else
                root.triggered(stableCommand)
        })
    }

    function replaceActions(nextActions) {
        root.actions = nextActions || []
        menuFlickable.contentY = 0
    }

    function revealAction(row) {
        focusedActionIndex = row.index
        if (row.y < menuFlickable.contentY)
            menuFlickable.contentY = row.y
        else if (row.y + row.height > menuFlickable.contentY + menuFlickable.height)
            menuFlickable.contentY = row.y + row.height - menuFlickable.height
    }

    function focusFirstAction() {
        focusedActionIndex = -1
        for (let index = 0; index < actionRepeater.count; ++index) {
            const row = actionRepeater.itemAt(index)
            if (row && row.primaryTarget && row.primaryTarget.enabled
                    && row.visible) {
                focusedActionIndex = index
                row.primaryTarget.forceActiveFocus(Qt.PopupFocusReason)
                return
            }
        }
    }

    function focusRelativeAction(step) {
        if (actionRepeater.count <= 0)
            return
        let index = focusedActionIndex
        for (let offset = 0; offset < actionRepeater.count; ++offset) {
            index = (
                index + step + actionRepeater.count
            ) % actionRepeater.count
            const row = actionRepeater.itemAt(index)
            if (row && row.primaryTarget && row.primaryTarget.enabled
                    && row.visible) {
                focusedActionIndex = index
                row.primaryTarget.forceActiveFocus(Qt.TabFocusReason)
                return
            }
        }
    }

    function activateFocusedAction() {
        const row = actionRepeater.itemAt(focusedActionIndex)
        if (row && row.primaryTarget && row.primaryTarget.enabled)
            row.primaryTarget.click()
    }

    function openSubmenu(row) {
        if (!row || !row.actionEnabled)
            return
        if (root.activeSubmenu && root.activeSubmenu.opened) {
            if (root.activeSubmenu.openingAnchorItem === row)
                return
            root.pendingSubmenuRow = row
            root.activeSubmenu.close()
            return
        }
        root.pendingSubmenuRow = null
        const generation = root.commandCloseGeneration
        const sourceActions = root.actions
        if (row.modelData.submenuPopup) {
            const popup = row.modelData.submenuPopup
            Qt.callLater(function() {
                if (root.opened && row && sourceActions === root.actions
                        && generation === root.commandCloseGeneration) {
                    root.activeSubmenu = popup
                    popup.openAsSubmenu(row, row)
                }
            })
            return
        }
        if (!row.modelData.children)
            return
        Qt.callLater(function() {
            if (!root.opened || !row || sourceActions !== root.actions
                    || generation !== root.commandCloseGeneration)
                return
            if (!root.actionSubmenu) {
                // Qt's screen-edge flip reads padding from the QObject parent menu.
                root.actionSubmenu = Qt.createComponent(Qt.resolvedUrl("ActionMenu.qml")).createObject(root, {
                    theme: root.theme, compact: true, parentMenu: root,
                    preferredWidth: root.preferredWidth,
                    usePopupWindow: root.usePopupWindow
                })
                root.addMenu(root.actionSubmenu)
            }
            const submenu = root.actionSubmenu
            if (submenu.opened && submenu.submenuAnchor === row)
                return
            root.activeSubmenu = submenu
            submenu.submenuAnchor = row
            submenu.actions = row.modelData.children
            if (root.usePopupWindow)
                submenu.openAsSubmenu(row, row)
            else
                submenu.openAt(row, row.width, -submenu.padding, false)
        })
    }

    Connections {
        target: root.activeSubmenu
        ignoreUnknownSignals: true
        function onClosed() {
            const row = root.pendingSubmenuRow
            root.pendingSubmenuRow = null
            if (root.opened && row)
                root.openSubmenu(row)
        }
    }

    function hoverAction(row) {
        hoveredAction = row
        row.primaryTarget.forceActiveFocus(Qt.MouseFocusReason)
        if (pendingSubmenuRow)
            pendingSubmenuRow = row
        submenuHover.restart()
    }

    Timer {
        id: submenuHover
        interval: root.theme.baseMotionMedium
        onTriggered: {
            const row = root.hoveredAction
            if (!root.opened || !row || !row.primaryTarget.hovered)
                return
            if (row.modelData.children || row.modelData.submenuPopup)
                root.openSubmenu(row)
            else if (root.activeSubmenu) {
                root.pendingSubmenuRow = null
                root.activeSubmenu.close()
            }
        }
    }


    Shortcut {
        sequence: "Space"
        context: Qt.WindowShortcut
        enabled: root.keyboardActive && root.focusedActionIndex >= 0
        onActivated: root.activateFocusedAction()
    }
    Shortcut {
        sequence: "Return"
        context: Qt.WindowShortcut
        enabled: root.keyboardActive && root.focusedActionIndex >= 0
        onActivated: root.activateFocusedAction()
    }
    Shortcut {
        sequence: "Enter"
        context: Qt.WindowShortcut
        enabled: root.keyboardActive && root.focusedActionIndex >= 0
        onActivated: root.activateFocusedAction()
    }
    Shortcut {
        sequence: "Esc"
        context: Qt.WindowShortcut
        enabled: root.keyboardActive
        onActivated: root.close()
    }

    function flushPendingCommand() {
        const stableCommand = root.pendingCommand
        const secondary = root.pendingSecondary
        root.pendingCommand = ""
        root.pendingSecondary = false
        if (!stableCommand)
            return
        Qt.callLater(function() {
            if (secondary)
                root.secondaryTriggered(stableCommand)
            else
                root.triggered(stableCommand)
        })
    }

    function openAt(
            sourceItem, localX, localY, preferCursorPosition) {
        root.protectOpeningFrom(sourceItem)
        const useCursor = preferCursorPosition === undefined
            ? true : !!preferCursorPosition
        if (!sourceItem || !root.parent) {
            root.open()
            return
        }
        if (root.usePopupWindow) {
            root.reopenAtItem(
                sourceItem, localX, localY, useCursor)
            return
        }
        const point = sourceItem.mapToItem(root.parent, localX, localY)
        root.x = Math.max(
            4,
            Math.min(root.parent.width - root.width - 4, point.x)
        )
        root.y = Math.max(
            4,
            Math.min(root.parent.height - root.height - 4, point.y)
        )
        root.open()
    }

    function openBelow(sourceItem) {
        if (root.openingInputGuardActive) {
            root.sourceWasOpen = false
            return
        }
        root.protectOpeningFrom(sourceItem)
        const sameSource = root.lastSourceItem === sourceItem
        if (sameSource && (
                root.opened || Date.now() - root.lastClosedAt < 140)) {
            if (root.opened)
                root.close()
            return
        }
        if (!sourceItem || !root.parent) {
            root.lastSourceItem = sourceItem
            root.open()
            return
        }

        const gap = 6
        if (root.usePopupWindow) {
            root.openBelowItem(
                sourceItem,
                root.alignBelowRight,
                gap,
                root.belowRightOverhang
            )
            root.lastSourceItem = sourceItem
            return
        }
        const surfaceWidth = Math.max(
            1, root.width - 2 * root.effectiveShadowMargin
        )
        const localX = root.alignBelowRight
            ? sourceItem.width - surfaceWidth + root.belowRightOverhang : 0
        const topLeft = sourceItem.mapToItem(root.parent, localX, 0)
        const below = sourceItem.mapToItem(
            root.parent, localX, sourceItem.height
        )
        const sourceCenter = sourceItem.mapToItem(
            root.parent, sourceItem.width / 2, 0
        )
        const targetX = Math.max(
            4,
            Math.min(root.parent.width - root.width - 4, topLeft.x)
        )

        const targetY = below.y + gap + root.height <= root.parent.height - 4
            ? below.y + gap : Math.max(4, topLeft.y - root.height - gap)
        root.anchorPointerEdge = targetY >= below.y ? "top" : "bottom"
        root.anchorPointerCenter = Math.max(
            root.surfaceRadius,
            Math.min(
                root.width - root.surfaceRadius,
                sourceCenter.x - targetX
            )
        )

        root.x = targetX
        root.y = targetY
        root.lastSourceItem = sourceItem
        root.open()
    }

    function toggleBelow(sourceItem) {
        if (root.openingInputGuardActive) {
            root.sourceWasOpen = false
            return
        }
        if (root.sourceWasOpen || root.opened) {
            root.close()
        } else {
            root.openBelow(sourceItem)
        }
        root.sourceWasOpen = false
    }

    contentItem: Flickable {
        id: menuFlickable
        objectName: "actionMenuFlickable"
        implicitWidth: Math.max(
            0, root.resolvedWidth - root.leftPadding - root.rightPadding)
        clip: true
        contentWidth: width
        contentHeight: menuColumn.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        interactive: contentHeight > height + 0.5

        Column {
            id: menuColumn
            width: Math.max(0, menuFlickable.width - (
                menuScrollBar.hasOverflow ? menuScrollBar.reservedExtent + 4 : 0))
            spacing: root.processPickerStyle ? 2 : 1
            Repeater {
                id: actionRepeater
                objectName: "actionMenuRepeater"
                // Compact menus retain their small row set between uses.
                // Index bindings refresh counts/labels without rebuilding
                // every delegate for each new object's actions array.
                model: root.processPickerStyle || root.opened
                    ? root.displayedActions.length : 0
                delegate: ActionMenuRow {
                    menu: root
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: menuScrollBar
            objectName: "actionMenuScrollBar"
            theme: root.theme
            flickableTarget: menuFlickable
        }
    }
}
