pragma Singleton

import QtQuick

// Owns one active transient branch. A popup opened from inside another popup
// joins that branch, while a sibling replaces only the previous child and a
// new root popup closes the complete previous branch.
QtObject {
    property var popupStack: []
    property var activeMenu: null
    property var lastClosedMenu: null
    property double lastClosedAt: -1000

    function isDescendantOf(item, ancestor) {
        let current = item
        let remainingDepth = 256
        while (current && remainingDepth > 0) {
            if (current === ancestor)
                return true
            current = current.parent
            --remainingDepth
        }
        return false
    }

    function parentPopupIndex(menu, stack) {
        const anchor = menu.openingAnchorItem || menu.parent
        if (!anchor)
            return -1
        for (let index = stack.length - 1; index >= 0; --index) {
            const candidate = stack[index]
            if (candidate && candidate !== menu && candidate.contentItem
                    && isDescendantOf(anchor, candidate.contentItem))
                return index
        }
        return -1
    }

    function publishStack(stack) {
        popupStack = stack
        activeMenu = stack.length > 0 ? stack[stack.length - 1] : null
    }

    function wasJustClosed(menu, interval) {
        return lastClosedMenu === menu
            && Date.now() - lastClosedAt <= interval
    }

    function closePopup(menu) {
        if (!menu)
            return
        if (typeof menu.cancelOpeningRecovery === "function")
            menu.cancelOpeningRecovery()
        if (typeof menu.cancelPendingReopen === "function")
            menu.cancelPendingReopen()
        if (typeof menu.suppressOwnerActivationOnce === "function")
            menu.suppressOwnerActivationOnce()
        if (menu.opened || menu.visible)
            menu.close()
    }

    function activate(menu) {
        if (!menu)
            return false

        const current = popupStack.slice()
        const existingIndex = current.indexOf(menu)
        const retainedIndex = existingIndex >= 0
            ? existingIndex : parentPopupIndex(menu, current)
        const closing = current.slice(retainedIndex + 1)
        let next = current.slice(0, retainedIndex + 1)
        if (next.indexOf(menu) < 0)
            next.push(menu)

        // Publish first so delayed onClosed signals from replaced popups
        // cannot remove the popup that is currently being opened.
        publishStack(next)
        for (let index = closing.length - 1; index >= 0; --index) {
            if (closing[index] !== menu)
                closePopup(closing[index])
        }
        return closing.length > 0
    }

    function release(menu) {
        if (!menu || menu._reopenPending)
            return
        lastClosedMenu = menu
        lastClosedAt = Date.now()
        const current = popupStack.slice()
        const index = current.indexOf(menu)
        if (index < 0)
            return

        const descendants = current.slice(index + 1)
        publishStack(current.slice(0, index))
        for (let childIndex = descendants.length - 1;
                childIndex >= 0; --childIndex)
            closePopup(descendants[childIndex])
    }
}
