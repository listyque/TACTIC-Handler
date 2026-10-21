import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame/features/table/parent.ui.mjs" as UI

Controls.ScrollablePopup {
    id: popup
    objectName: "tableParentGroupPopup"
    required property var owner
    property bool closingFromOwner: false
    parent: Overlay.overlay
    padding: UI.popupMetrics.padding
    preferredSurfaceWidth: UI.popupMetrics.width
    fixedSurfaceHeight: Math.min(UI.popupMetrics.height, availableOuterHeight - 2 * effectiveShadowMargin)
    coordinateGlobally: false
    settledClosePolicy: Popup.NoAutoClose
    onClosed: {
        if (!closingFromOwner)
            owner.shutdown();
        closingFromOwner = false;
    }
    onOpened: {
        closingFromOwner = false;
        if (body.item)
            Qt.callLater(body.item.focusQuery);
    }
    Loader {
        id: body
        width: parent.width
        height: Math.max(UI.popupMetrics.minimumBody, popup.viewport.height)
        active: popup.visible || popup.owner.isOpen
        sourceComponent: ParentGroupView {
            width: body.width
            height: body.height
            theme: popup.theme
            owner: popup.owner
        }
    }
    Connections {
        target: popup.owner
        function onOpened(anchor) {
            popup.openBelowItem(anchor, true, 4);
        }
        function onClosed() {
            popup.closingFromOwner = true;
            popup.close();
        }
    }
}
