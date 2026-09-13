import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import QtQuick.Window
import "PopupLogic.js" as PopupLogic
import "." as Controls

// Shared popup contract for selectors and anchored panels.
// Placement is resolved before open(). A native Popup.Window must never be
// moved again from QML after it has been shown: doing so races Qt's own popup
// placement and produces the visible left/right jump seen on Windows.
QtControls.Popup {
    id: control

    readonly property var ownerWindow: parent ? parent.Window.window : null
    property var pointerService: typeof pointerController !== "undefined" ? pointerController : null
    readonly property var popupCoordinator: Controls.PopupCoordinator
    readonly property alias _openingInputTimer: openingInputGuard

    required property var theme
    property bool animationsEnabled: theme.popupAnimationsEnabled
    property real surfaceRadius: theme.menuRadius
    property bool usePopupWindow: true
    property bool coordinateGlobally: true
    property bool coordinateOpenPopups: coordinateGlobally
    property bool protectNextOpenFromDuplicateInput: false
    property int openingInputGuardDuration:
        theme.baseMotionExtended + theme.baseMotionFast
    property int settledClosePolicy: QtControls.Popup.CloseOnEscape
        | QtControls.Popup.CloseOnPressOutside
    property real shadowMargin: 12
    property real screenMargin: 4
    property real availableScreenWidth: 0
    property real availableScreenHeight: 0
    property bool sourceWasOpen: false
    property int sameSourceToggleWindow: 180
    property bool restoreOwnerActivationOnClose: true
    property var openingAnchorItem: null
    property bool anchorPointerVisible: false
    property real anchorPointerSize: 12
    property real anchorPointerWidth: anchorPointerSize * 1.35
    property real anchorPointerHeight: anchorPointerSize * 0.55
    property real anchorPointerCenter: width / 2
    property string anchorPointerEdge: "top"
    property color surfaceColor: theme.surfaceContainerHigh
    property color surfaceBorderColor: theme.outlineVariant
    property real surfaceBorderWidth: 1

    readonly property real maximumAvailableWidth:
        availableScreenWidth > 0
            ? Math.max(1, availableScreenWidth - 2 * screenMargin)
            : 1000000
    readonly property real maximumAvailableHeight:
        availableScreenHeight > 0
            ? Math.max(1, availableScreenHeight - 2 * screenMargin)
            : 1000000
    readonly property real effectiveShadowMargin:
        usePopupWindow ? shadowMargin : 0
    readonly property bool openingInputGuardActive:
        _openingInputGuardActive
    readonly property real anchorPointerInset:
        anchorPointerVisible ? Math.ceil(anchorPointerHeight) : 0

    property int _placementGeneration: 0
    property int _pendingGeneration: 0
    property bool _reopenPending: false
    property bool _openingInputGuardActive: false
    property bool _placementPrepared: false
    property real _preparedX: 0
    property real _preparedY: 0
    property real _requestedSurfaceGlobalX: 0
    property real _requestedSurfaceGlobalY: 0
    property real _anchorGlobalCenterX: Number.NaN
    property var _popupWindow: null
    property bool _nativeModalityApplied: false
    property bool _suppressOwnerActivationOnce: false

    padding: 6
    leftPadding: padding + effectiveShadowMargin
    rightPadding: padding + effectiveShadowMargin
    topPadding: padding + effectiveShadowMargin
        + (anchorPointerVisible && anchorPointerEdge === "top"
            ? anchorPointerInset : 0)
    bottomPadding: padding + effectiveShadowMargin
        + (anchorPointerVisible && anchorPointerEdge === "bottom"
            ? anchorPointerInset : 0)
    popupType: usePopupWindow
        ? QtControls.Popup.Window : QtControls.Popup.Item
    closePolicy: _openingInputGuardActive
        ? QtControls.Popup.CloseOnEscape : settledClosePolicy

    // Own the transitions explicitly: inherited Qt style durations do not
    // follow application preferences and cannot be safely toggled via null.
    enter: Transition {
        enabled: control.animationsEnabled
        NumberAnimation {
            property: "scale"; from: 0.9; to: 1
            duration: control.animationsEnabled ? control.theme.popupMotionSlow : 0
            easing.type: Easing.OutQuint
        }
        NumberAnimation {
            property: "opacity"; from: 0; to: 1
            duration: control.animationsEnabled ? control.theme.popupMotionFast : 0
            easing.type: Easing.OutCubic
        }
    }
    exit: Transition {
        enabled: control.animationsEnabled
        NumberAnimation {
            property: "scale"; from: 1; to: 0.9
            duration: control.animationsEnabled ? control.theme.popupMotionSlow : 0
            easing.type: Easing.OutQuint
        }
        NumberAnimation {
            property: "opacity"; from: 1; to: 0
            duration: control.animationsEnabled ? control.theme.popupMotionFast : 0
            easing.type: Easing.OutCubic
        }
    }
    Overlay.modal: Controls.PopupScrim { theme: control.theme }
    Overlay.modeless: Controls.PopupScrim { theme: control.theme }

    onAboutToShow: PopupLogic.aboutToShow(control)

    onOpened: PopupLogic.opened(control, contentItem ? contentItem.Window.window : null)

    onClosed: PopupLogic.closed(control)

    function protectOpeningFrom(sourceItem) { return PopupLogic.protectOpeningFrom(control, sourceItem) }

    function rememberSourceOpen() { return PopupLogic.rememberSourceOpen(control) }

    function wasJustClosedFrom(sourceItem) { return PopupLogic.wasJustClosedFrom(control, sourceItem) }

    function suppressOwnerActivationOnce() { return PopupLogic.suppressOwnerActivationOnce(control) }

    function availableGeometryAt(globalX, globalY) { return PopupLogic.availableGeometryAt(control, globalX, globalY) }

    function clampedCoordinate(value, minimum, maximum) { return PopupLogic.clampedCoordinate(control, value, minimum, maximum) }

    function prepareGlobalPosition(surfaceGlobalX, surfaceGlobalY) { return PopupLogic.prepareGlobalPosition(control, surfaceGlobalX, surfaceGlobalY) }

    function resolvePreparedPosition() { return PopupLogic.resolvePreparedPosition(control) }

    function preparePositionAtItem(sourceItem, localX, localY) { return PopupLogic.preparePositionAtItem(control, sourceItem, localX, localY) }

    function requestOpenPrepared() { return PopupLogic.requestOpenPrepared(control) }

    function reopenAtPosition(targetX, targetY, globalX, globalY) { return PopupLogic.reopenAtPosition(control, targetX, targetY, globalX, globalY) }

    function reopenAtItem(sourceItem, localX, localY, preferCursorPosition) { return PopupLogic.reopenAtItem(control, sourceItem, localX, localY, preferCursorPosition) }

    function openBelowItem(sourceItem, alignRight, gap, rightOverhang) { return PopupLogic.openBelowItem(control, sourceItem, alignRight, gap, rightOverhang) }

    function openCenteredIn(ownerItem) { return PopupLogic.openCenteredIn(control, ownerItem) }

    function toggleBelowItem(sourceItem, alignRight, gap) { return PopupLogic.toggleBelowItem(control, sourceItem, alignRight, gap) }

    function cancelPendingReopen() { return PopupLogic.cancelPendingReopen(control) }

    function finishPendingReopen() { return PopupLogic.finishPendingReopen(control) }

    Timer {
        id: openingInputGuard
        interval: control.openingInputGuardDuration
        onTriggered: control._openingInputGuardActive = false
    }

    background: Controls.PopupBackground { popup: control }
}
