import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/calendar.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property bool agenda: false
    property int projectionRevision: 0
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var geometry: UI.layout(width, height)
    readonly property var days: {
        const revision = projectionRevision;
        const result = [];
        for (let index = 0; index < taskCalendarModel.count(); index++)
            result.push(taskCalendarModel.get(index));
        return result;
    }
    readonly property string monthDate: {
        const first = days.find(day => day.inMonth);
        return first ? first.date.slice(0, 7) + "-01" : "";
    }
    readonly property var model: ({
            monthDate,
            selectedDay: tasksController.selectedDay,
            busy: tasksController.advancedBusy,
            hasMore: tasksController.advancedHasMore
        })
    readonly property var agendaRows: UI.agendaRows(days, tasksController.selectedDay)

    function action(event) {
        if (event.type === "previous")
            tasksController.change_calendar_month(-1);
        else if (event.type === "next")
            tasksController.change_calendar_month(1);
        else if (event.type === "today")
            tasksController.calendar_today();
        else if (event.type === "clear")
            tasksController.select_calendar_day("");
        else if (event.type === "day")
            tasksController.select_calendar_day(event.value);
        else if (event.type === "agenda")
            agenda = !agenda;
        else if (event.type === "inspect")
            tasksController.activate_calendar_task(event.value, event.parentKey, event.process);
        else if (event.type === "load-more")
            tasksController.load_more_advanced();
        else if (event.type === "tasks")
            tasksController.open_workspace();
        else if (event.type === "milestone")
            milestoneController.open_manager();
        else if (event.type === "month-value" && /^\d{4}-\d{2}-\d{2}$/.test(event.value)) {
            const year = Number(event.value.slice(0, 4)), month = Number(event.value.slice(5, 7));
            if (year < 2 || year > 9997 || month < 1 || month > 12)
                return;
            const offset = (year - Number(monthDate.slice(0, 4))) * 12 + month - Number(monthDate.slice(5, 7));
            tasksController.change_calendar_month(offset);
        }
    }
    Connections {
        target: taskCalendarModel
        function onContentReplaced() {
            root.projectionRevision++;
        }
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }
    Frame.FrameView {
        theme: root.theme
        x: root.geometry.margin
        y: root.geometry.margin
        width: root.geometry.inner
        height: 34
        scene: UI.navigation(root.model, width, root.language)
        onEvent: event => root.action(event)
    }
    Repeater {
        model: 7
        delegate: Frame.FrameView {
            required property int index
            theme: root.theme
            visible: !root.agenda
            x: root.geometry.margin + index * (root.geometry.cellWidth + root.geometry.cellGap)
            y: root.geometry.margin + 34 + root.geometry.gap
            width: root.geometry.cellWidth
            height: 22
            scene: UI.weekday(index, width, root.language)
        }
    }
    Repeater {
        model: root.days
        delegate: Frame.FrameView {
            id: cell
            required property int index
            required property var modelData
            theme: root.theme
            visible: !root.agenda
            x: root.geometry.margin + index % 7 * (root.geometry.cellWidth + root.geometry.cellGap)
            y: root.geometry.gridY + Math.floor(index / 7) * (root.geometry.cellHeight + root.geometry.cellGap)
            width: root.geometry.cellWidth
            height: root.geometry.cellHeight
            opacity: modelData.inMonth ? 1 : 0.55
            clip: true
            scene: UI.day(Object.assign({}, modelData, {
                index,
                compact: root.geometry.compact,
                selected: modelData.date === tasksController.selectedDay,
                hovered: hover.hovered,
                busy: tasksController.advancedBusy,
                radius: root.theme.itemRadius
            }), width, height, root.language)
            onEvent: event => root.action(event)
            HoverHandler {
                id: hover
            }
        }
    }
    Controls.SmoothListView {
        id: agendaList
        theme: root.theme
        visible: root.agenda
        x: root.geometry.margin
        y: root.geometry.margin + 34 + root.geometry.gap
        width: root.geometry.inner
        height: Math.max(0, root.geometry.footerY - y - root.geometry.gap)
        clip: true
        model: root.agendaRows
        delegate: Frame.FrameView {
            required property var modelData
            theme: root.theme
            width: agendaList.width - 14
            height: 34
            scene: UI.agendaRow(modelData, width)
            onEvent: event => root.action(event)
        }
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: agendaList
        }
    }
    Frame.FrameView {
        theme: root.theme
        x: root.geometry.margin
        y: root.geometry.footerY
        width: root.geometry.inner
        height: 28
        scene: UI.footer(root.model, width, root.language)
        onEvent: event => root.action(event)
    }
}
