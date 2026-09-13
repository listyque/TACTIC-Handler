import QtQuick
import QtQuick.Controls
import "." as Controls

// Shared bounded surface for popup content that may outgrow the available
// screen. Feature code supplies only the column content; this component owns
// the viewport, scrollbar gutter, and screen-aware size limits.
Controls.Popup {
    id: root

    default property alias popupContent: popupColumn.data
    property real preferredSurfaceWidth: 440
    property real minimumSurfaceWidth: 280
    property real maximumSurfaceHeight: 360
    property real fixedSurfaceHeight: -1
    property real contentSpacing: 12
    property real minimumSurfaceHeight: 0

    readonly property alias viewport: popupViewport
    readonly property alias contentColumn: popupColumn
    readonly property alias verticalScrollBar: popupScrollBar
    readonly property real surfaceWidth: Math.max(
        0, width - 2 * effectiveShadowMargin
    )
    readonly property real surfaceHeight: Math.max(
        0, height - 2 * effectiveShadowMargin
    )
    readonly property real naturalOuterHeight:
        popupColumn.implicitHeight + topPadding + bottomPadding
    readonly property real availableOuterHeight: Math.min(
        maximumAvailableHeight,
        parent && parent.height > 0
            ? Math.max(1, parent.height - 8) : maximumAvailableHeight
    )
    readonly property real requestedOuterHeight: {
        if (fixedSurfaceHeight >= 0)
            return fixedSurfaceHeight + 2 * effectiveShadowMargin
        const minimumOuterHeight = Math.min(
            minimumSurfaceHeight + 2 * effectiveShadowMargin,
            availableOuterHeight
        )
        const boundedNaturalHeight = Math.min(
            naturalOuterHeight,
            maximumSurfaceHeight + 2 * effectiveShadowMargin,
            availableOuterHeight
        )
        return Math.max(minimumOuterHeight, boundedNaturalHeight)
    }

    width: {
        const availableWidth = Math.min(
            maximumAvailableWidth,
            parent && parent.width > 0
                ? Math.max(1, parent.width - 8) : maximumAvailableWidth
        )
        const requestedWidth = Math.max(
            minimumSurfaceWidth, preferredSurfaceWidth
        ) + 2 * effectiveShadowMargin
        return Math.min(requestedWidth, availableWidth)
    }
    // Popup.Window may assign height from implicitHeight again when dynamic
    // delegates change. Bound the implicit size itself so that a late model
    // update cannot expand the native window to the full content height.
    implicitHeight: Math.min(requestedOuterHeight, availableOuterHeight)
    height: implicitHeight

    padding: 12
    modal: false
    focus: true
    settledClosePolicy:
        Popup.CloseOnEscape | Popup.CloseOnPressOutside

    onAboutToShow: popupViewport.contentY = popupViewport.originY

    contentItem: Flickable {
        id: popupViewport

        objectName: "scrollablePopupViewport"
        readonly property real scrollBarReserve:
            popupScrollBar.hasOverflow
                ? popupScrollBar.reservedExtent : 0

        clip: true
        contentWidth: width
        contentHeight: popupColumn.implicitHeight
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: popupColumn

            objectName: "scrollablePopupContent"
            width: Math.max(
                0, popupViewport.width - popupViewport.scrollBarReserve
            )
            spacing: root.contentSpacing
        }

        ScrollBar.vertical: Controls.ScrollBar {
            id: popupScrollBar

            objectName: "scrollablePopupScrollBar"
            theme: root.theme
            flickableTarget: popupViewport
        }
    }
}
