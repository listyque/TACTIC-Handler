import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/activity/calendar.ui.mjs" as UI

Controls.Popup {
    id: root
    property var dayCounts: ({})
    property bool busy: false
    property string selectedDay: ""
    property string localeName: "en_US"
    property real currentTime: Date.now()
    property date visibleMonth: new Date(currentTime)
    readonly property string language: localeName.indexOf("ru") === 0 ? "ru" : "en"
    signal accepted(string dateKey)
    objectName: "activityCalendarPopup"
    parent: Overlay.overlay
    width: Math.min(364, parent ? parent.width - 16 : 364)
    height: calendarLayout.scene.height + topPadding + bottomPadding
    padding: 10
    modal: true
    dim: true
    focus: true
    settledClosePolicy: Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutside
    Overlay.modal: Rectangle {
        objectName: "activityCalendarScrim"
        color: root.theme.scrim
    }
    function showBelow(anchorItem) {
        visibleMonth = UI.initialMonth(selectedDay, dayCounts, new Date(currentTime));
        toggleBelowItem(anchorItem, true, 6);
    }
    function acceptDay(value) {
        accepted(String(value || ""));
        close();
    }
    contentItem: Frame.FrameView {
        id: calendarLayout
        theme: root.theme
        scene: UI.describe({
            month: root.visibleMonth,
            now: new Date(root.currentTime),
            counts: root.dayCounts,
            selected: root.selectedDay,
            busy: root.busy
        }, width, root.language)
        views: ({
                busy: busyPort
            })
        onEvent: action => {
            if (action.type === "previous")
                root.visibleMonth = UI.moveMonth(root.visibleMonth, -1);
            else if (action.type === "next")
                root.visibleMonth = UI.moveMonth(root.visibleMonth, 1);
            else if (action.type === "day")
                root.acceptDay(action.value);
            else if (action.type === "close")
                root.close();
        }
    }
    Component {
        id: busyPort
        Controls.BusyIndicator {
            uiTheme: root.theme
            running: root.visible && root.busy
        }
    }
}
