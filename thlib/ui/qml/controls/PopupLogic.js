.pragma library

function protectOpeningFrom(control, sourceItem) {
    if (!sourceItem)
        return
    try {
        const activationAt = Number(sourceItem.lastActivationAt)
        const recentActivation = Number.isFinite(activationAt)
            && Date.now() - activationAt <= control.openingInputGuardDuration
        if (sourceItem.lastActivationWasTouch === true
                && (recentActivation || !Number.isFinite(activationAt)))
            control.protectNextOpenFromDuplicateInput = true
    } catch (error) {
        // Plain QML and native Qt controls do not expose activation type.
    }

}

function rememberSourceOpen(control) {
    control.sourceWasOpen = control.opened || control.visible

}

function wasJustClosedFrom(control, sourceItem) {
    return control.openingAnchorItem === sourceItem
        && control.popupCoordinator.wasJustClosed(
            control, control.sameSourceToggleWindow
        )

}

function suppressOwnerActivationOnce(control) {
    control._suppressOwnerActivationOnce = true

}

function availableGeometryAt(control, globalX, globalY) {
    if (control.pointerService) {
        try {
            const area = control.pointerService.available_geometry_at(
                Number(globalX), Number(globalY))
            if (area && Number(area.width) > 0
                    && Number(area.height) > 0) {
                return {
                    "x": Number(area.x),
                    "y": Number(area.y),
                    "width": Number(area.width),
                    "height": Number(area.height)
                }
            }
        } catch (error) {
            // Isolated QML tests do not expose the application service.
        }
    }
    const ownerWindow = control.ownerWindow
    const screen = ownerWindow ? ownerWindow.screen : null
    const area = screen ? screen.availableGeometry : null
    if (!area || Number(area.width) <= 0 || Number(area.height) <= 0)
        return null
    return {
        "x": Number(area.x),
        "y": Number(area.y),
        "width": Number(area.width),
        "height": Number(area.height)
    }

}

function clampedCoordinate(control, value, minimum, maximum) {
    return maximum < minimum
        ? minimum : Math.max(minimum, Math.min(maximum, value))

}

function prepareGlobalPosition(control, surfaceGlobalX, surfaceGlobalY) {
    if (!control.parent)
        return false

    control._requestedSurfaceGlobalX = Number(surfaceGlobalX)
    control._requestedSurfaceGlobalY = Number(surfaceGlobalY)
    control._placementPrepared = true
    return control.resolvePreparedPosition()

}

function resolvePreparedPosition(control) {
    if (!control.parent || !control._placementPrepared)
        return false

    const surfaceGlobalX = control._requestedSurfaceGlobalX
    const surfaceGlobalY = control._requestedSurfaceGlobalY

    const area = control.availableGeometryAt(surfaceGlobalX, surfaceGlobalY)
    if (area) {
        control.availableScreenWidth = area.width
        control.availableScreenHeight = area.height
    }

    let outerGlobalX = Number(surfaceGlobalX) - control.effectiveShadowMargin
    let outerGlobalY = Number(surfaceGlobalY) - control.effectiveShadowMargin
    if (area) {
        const popupWidth = Math.max(1, Number(control.width || control.implicitWidth || 1))
        const popupHeight = Math.max(
            1, Number(control.height || control.implicitHeight || 1))
        outerGlobalX = control.clampedCoordinate(
            outerGlobalX,
            area.x + control.screenMargin,
            area.x + area.width - popupWidth - control.screenMargin)
        outerGlobalY = control.clampedCoordinate(
            outerGlobalY,
            area.y + control.screenMargin,
            area.y + area.height - popupHeight - control.screenMargin)
    }

    if (control.anchorPointerVisible
            && Number.isFinite(control._anchorGlobalCenterX)) {
        control.anchorPointerCenter = control.clampedCoordinate(
            control._anchorGlobalCenterX - outerGlobalX,
            control.effectiveShadowMargin + control.surfaceRadius,
            Math.max(
                control.effectiveShadowMargin + control.surfaceRadius,
                control.width - control.effectiveShadowMargin - control.surfaceRadius
            )
        )
    }

    const localPoint = control.parent.mapFromGlobal(outerGlobalX, outerGlobalY)
    control._preparedX = Math.round(localPoint.x)
    control._preparedY = Math.round(localPoint.y)
    control.x = control._preparedX
    control.y = control._preparedY
    return true

}

function preparePositionAtItem(control, sourceItem, localX, localY) {
    if (!sourceItem || !control.parent)
        return false
    control.openingAnchorItem = sourceItem
    const point = sourceItem.mapToGlobal(localX, localY)
    return control.prepareGlobalPosition(point.x, point.y)

}

function requestOpenPrepared(control) {
    const generation = ++control._placementGeneration
    control._pendingGeneration = generation
    if (control.opened || control.visible) {
        control._reopenPending = true
        control.close()
        return
    }
    control._reopenPending = false
    control.resolvePreparedPosition()
    control.open()

}

function reopenAtPosition(control, targetX, targetY, globalX, globalY) {
    control.openingAnchorItem = null
    let resolvedGlobalX = Number(globalX)
    let resolvedGlobalY = Number(globalY)
    if (!Number.isFinite(resolvedGlobalX)
            || !Number.isFinite(resolvedGlobalY)) {
        if (!control.parent)
            return
        const point = control.parent.mapToGlobal(targetX, targetY)
        resolvedGlobalX = point.x
        resolvedGlobalY = point.y
    }
    control.prepareGlobalPosition(resolvedGlobalX, resolvedGlobalY)
    control.requestOpenPrepared()

}

function reopenAtItem(control, sourceItem, localX, localY, preferCursorPosition) {
    if (!sourceItem || !control.parent)
        return
    control.openingAnchorItem = sourceItem
    let point = sourceItem.mapToGlobal(localX, localY)
    if (preferCursorPosition
            && control.pointerService) {
        try {
            const cursorPoint = control.pointerService.global_position()
            if (cursorPoint)
                point = cursorPoint
        } catch (error) {
            // Isolated QML tests do not expose the pointer service.
        }
    }
    control.prepareGlobalPosition(point.x, point.y)
    control.requestOpenPrepared()

}

function openBelowItem(control, sourceItem, alignRight, gap, rightOverhang) {
    if (!sourceItem || !control.parent) {
        control.open()
        return
    }
    control.openingAnchorItem = sourceItem
    control.protectOpeningFrom(sourceItem)
    const resolvedGap = Number(gap || 0)
    const surfaceWidth = Math.max(
        1, control.width - 2 * control.effectiveShadowMargin)
    const surfaceHeight = Math.max(
        1, control.height - 2 * control.effectiveShadowMargin)
    const resolvedRightOverhang = Number(rightOverhang || 0)
    const localX = alignRight
        ? sourceItem.width - surfaceWidth + resolvedRightOverhang : 0
    const below = sourceItem.mapToGlobal(
        localX, sourceItem.height + resolvedGap)
    const sourceTop = sourceItem.mapToGlobal(localX, 0)
    const sourceCenter = sourceItem.mapToGlobal(
        sourceItem.width / 2, 0)
    const area = control.availableGeometryAt(below.x, below.y)
    let targetY = below.y
    if (area && below.y + surfaceHeight > area.y + area.height
            && sourceTop.y - resolvedGap - surfaceHeight >= area.y)
        targetY = sourceTop.y - resolvedGap - surfaceHeight
    control._anchorGlobalCenterX = sourceCenter.x
    control.anchorPointerEdge = targetY === below.y ? "top" : "bottom"
    control.prepareGlobalPosition(below.x, targetY)
    control.requestOpenPrepared()

}

function openCenteredIn(control, ownerItem) {
    if (!ownerItem || !control.parent) {
        control.open()
        return
    }
    control.openingAnchorItem = null
    const surfaceWidth = Math.max(
        1, control.width - 2 * control.effectiveShadowMargin)
    const surfaceHeight = Math.max(
        1, control.height - 2 * control.effectiveShadowMargin)
    const point = ownerItem.mapToGlobal(
        (ownerItem.width - surfaceWidth) / 2,
        (ownerItem.height - surfaceHeight) / 2)
    control.prepareGlobalPosition(point.x, point.y)
    control.requestOpenPrepared()

}

function toggleBelowItem(control, sourceItem, alignRight, gap) {
    control.protectOpeningFrom(sourceItem)
    if (control.openingInputGuardActive) {
        control.sourceWasOpen = false
        return
    }
    if (control.sourceWasOpen || control.opened || control.visible
            || control.wasJustClosedFrom(sourceItem)) {
        control.cancelPendingReopen()
        if (control.opened || control.visible)
            control.close()
    } else {
        control.openBelowItem(sourceItem, alignRight, gap)
    }
    control.sourceWasOpen = false

}

function cancelPendingReopen(control) {
    control._reopenPending = false
    ++control._placementGeneration
    if (control.coordinateOpenPopups && !control.opened && !control.visible)
        control.popupCoordinator.release(control)

}

function finishPendingReopen(control) {
    if (!control._reopenPending)
        return
    const generation = control._pendingGeneration
    control._reopenPending = false
    Qt.callLater(function() {
        if (generation === control._placementGeneration)
            control.open()
    })

}

function aboutToShow(control) {
    control._openingInputGuardActive = control.protectNextOpenFromDuplicateInput
    control.protectNextOpenFromDuplicateInput = false
    if (control._openingInputGuardActive)
        control._openingInputTimer.restart()
    else
        control._openingInputTimer.stop()

    if (control._placementPrepared)
        control.resolvePreparedPosition()
    if (control.coordinateOpenPopups)
        control.popupCoordinator.activate(control)

}

function opened(control, popupWindow) {
    // Popup.Window creates its transient QQuickPopupWindow during open().
    if (!control.usePopupWindow || !control.contentItem)
        return
    if (!popupWindow)
        return
    control._popupWindow = popupWindow
    control._nativeModalityApplied = control.modal
    if (control._nativeModalityApplied)
        popupWindow.modality = Qt.WindowModal
    // A click that reactivates the owner can finish after open() and put the
    // owner above this window. Raise the popup after that input turn.
    Qt.callLater(function() {
        if (!control.opened || control._popupWindow !== popupWindow)
            return
        popupWindow.raise()
    })

}

function closed(control) {
    control._openingInputTimer.stop()
    control._openingInputGuardActive = false
    control.protectNextOpenFromDuplicateInput = false
    const ownerWindow = control._popupWindow
        ? control._popupWindow.transientParent : null
    if (control._popupWindow && control._nativeModalityApplied)
        control._popupWindow.modality = Qt.NonModal
    control._popupWindow = null
    control._nativeModalityApplied = false
    // Restore the owner only while it is still the active application
    // window. Never reactivate it after the user switched applications.
    if (control.restoreOwnerActivationOnClose
            && !control._suppressOwnerActivationOnce
            && ownerWindow && ownerWindow.active)
        ownerWindow.requestActivate()
    control._suppressOwnerActivationOnce = false
    if (control.coordinateOpenPopups)
        control.popupCoordinator.release(control)
    control.finishPendingReopen()

}
