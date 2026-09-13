import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import "." as Controls

QtControls.ScrollBar {
    id: root

    required property var theme
    LayoutMirroring.enabled: false
    LayoutMirroring.childrenInherit: false
    // Attached ScrollBars are re-parented to their Flickable by Qt.  The
    // explicit target can be supplied for complex/re-parented list layouts.
    property var flickableTarget: parent
    readonly property bool expanded: hovered || pressed
    // Paged views use this shared permit instead of interpreting contentY
    // changes locally.  A thumb drag is navigation over already loaded
    // content and must never become an implicit request for another page.
    property bool _paginationArmed: false
    property bool _paginationReleasePending: false
    readonly property bool paginationBlocked:
        pressed || _paginationReleasePending
    readonly property bool paginationArmed:
        _paginationArmed && !paginationBlocked
    readonly property real reservedExtent: 12
    readonly property real visualExtent: expanded ? 11 : 6
    readonly property real thumbExtent: expanded ? 8 : 5
    readonly property bool verticalBar:
        orientation === Qt.Vertical
    readonly property real viewportExtent: {
        if (!flickableTarget)
            return 0
        return verticalBar
            ? Number(flickableTarget.height || 0)
            : Number(flickableTarget.width || 0)
    }
    readonly property real contentExtent: {
        if (!flickableTarget)
            return 0
        return verticalBar
            ? Number(flickableTarget.contentHeight || 0)
            : Number(flickableTarget.contentWidth || 0)
    }
    readonly property bool hasOverflow:
        viewportExtent > 0
        && contentExtent > viewportExtent + 0.5

    function armPagination() {
        if (!paginationBlocked)
            _paginationArmed = true
    }

    function resetPagination() {
        _paginationArmed = false
    }

    function takePaginationPermit(allowUnderfilled) {
        if (paginationBlocked
                || (!allowUnderfilled && !_paginationArmed))
            return false
        _paginationArmed = false
        return true
    }

    function releasePaginationGuard() {
        // Qt can emit the final content-position and extent notifications
        // after pressed becomes false.  Keep those release frames blocked.
        Qt.callLater(function() {
            Qt.callLater(function() {
                if (!root.pressed)
                    root._paginationReleasePending = false
            })
        })
    }

    onPressedChanged: {
        if (pressed) {
            _paginationReleasePending = true
            resetPagination()
            if (!flickableTarget)
                return
            if (typeof flickableTarget.cancelWheelScroll === "function")
                flickableTarget.cancelWheelScroll()
            if (typeof flickableTarget.cancelFlick === "function")
                flickableTarget.cancelFlick()
        } else if (_paginationReleasePending) {
            releasePaginationGuard()
        }
    }

    Connections {
        target: root.flickableTarget
        ignoreUnknownSignals: true

        function onMovementStarted() {
            root.armPagination()
        }

        function onWheelScrollRequested() {
            root.armPagination()
        }

        function onFlickStarted() {
            root.armPagination()
        }

        function onInteractionMovingChanged() {
            if (root.flickableTarget
                    && root.flickableTarget.interactionMoving)
                root.armPagination()
        }
    }

    // Do not inherit the platform style's transient opacity.  The bar is
    // continuously visible while scrolling is possible and absent otherwise.
    policy: hasOverflow ? QtControls.ScrollBar.AlwaysOn : QtControls.ScrollBar.AlwaysOff
    visible: hasOverflow
    enabled: hasOverflow
    opacity: hasOverflow ? 1 : 0
    z: 10000
    hoverEnabled: true
    interactive: true
    minimumSize: 0.06
    padding: 1
    // The hit target never changes size on hover.  Only the painted thumb
    // changes emphasis, so neighboring content and the drag mapping stay put.
    implicitWidth: verticalBar ? reservedExtent : 0
    implicitHeight: verticalBar ? 0 : reservedExtent
    // Qt does not assign an extent to a custom attached ScrollBar when its
    // vertical implicit height is intentionally zero. Bind the long axis to
    // the actual viewport so an overflowing view never produces a visible
    // zero-sized scrollbar.
    width: verticalBar ? implicitWidth : viewportExtent
    height: verticalBar ? viewportExtent : implicitHeight
    // Scroll direction must not move the application's chrome.  Qt mirrors an
    // attached vertical ScrollBar to the left in an inherited mirrored layout,
    // but TACTIC Handler reserves the scrollbar gutter on the physical right.
    x: verticalBar && parent ? Math.max(0, parent.width - width) : 0
    y: verticalBar || !parent ? 0 : Math.max(0, parent.height - height)

    Behavior on opacity {
        enabled: !root.theme.suppressTransientMotion
        NumberAnimation {
            duration: root.theme.hoverMotionFast
            easing.type: Easing.OutCubic
        }
    }
    background: Item {
        Rectangle {
            anchors.centerIn: parent
            width: root.verticalBar ? root.visualExtent : parent.width
            height: root.verticalBar ? parent.height : root.visualExtent
            radius: Math.min(width, height) / 2
            color: root.theme.outline
            opacity: root.expanded ? 0.15 : 0.055

            Behavior on width {
                enabled: !root.theme.suppressTransientMotion
                NumberAnimation {
                    duration: root.theme.hoverMotionMedium
                    easing.type: Easing.OutCubic
                }
            }
            Behavior on height {
                enabled: !root.theme.suppressTransientMotion
                NumberAnimation {
                    duration: root.theme.hoverMotionMedium
                    easing.type: Easing.OutCubic
                }
            }
            Behavior on opacity {
                enabled: !root.theme.suppressTransientMotion
                NumberAnimation { duration: root.theme.hoverMotionFast }
            }
        }
    }

    contentItem: Item {
        Rectangle {
            anchors.centerIn: parent
            width: root.verticalBar ? root.thumbExtent : parent.width
            height: root.verticalBar ? parent.height : root.thumbExtent
            radius: Math.min(width, height) / 2
            color: root.theme.secondaryText
            opacity: !root.enabled ? 0.18
                : root.pressed ? 0.90
                : root.hovered ? 0.72 : 0.42

            Behavior on width {
                enabled: !root.theme.suppressTransientMotion
                NumberAnimation {
                    duration: root.theme.hoverMotionMedium
                    easing.type: Easing.OutCubic
                }
            }
            Behavior on height {
                enabled: !root.theme.suppressTransientMotion
                NumberAnimation {
                    duration: root.theme.hoverMotionMedium
                    easing.type: Easing.OutCubic
                }
            }
            Behavior on opacity {
                enabled: !root.theme.suppressTransientMotion
                NumberAnimation { duration: root.theme.hoverMotionFast }
            }
        }
    }

    HoverHandler {
        cursorShape: root.enabled && root.interactive
            ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}
