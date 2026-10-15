"""Batch scheduler QML view and window lifecycle."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, qmlEngine

from tactic_handler_api import get_api

from .scheduler_core import BatchDispatcherController

# QML view


QML_SOURCE = r"""
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import "__APP_QML_URL__" as App
import "__CONTROLS_URL__" as Controls

Window {
    id: root
    required property var applicationRoot
    required property var controller
    readonly property var theme: batchTheme
    readonly property var webThemeSnapshot: ({
        "dark": theme.dark,
        "style": theme.style,
        "fontFamily": theme.fontFamily,
        "iconSet": typeof appController !== "undefined"
            ? String(appController.icon_set || "automatic")
            : "automatic",
        "workspace": String(theme.workspace),
        "topBar": String(theme.topBar),
        "toolBar": String(theme.toolBar),
        "panel": String(theme.panel),
        "panelRaised": String(theme.panelRaised),
        "panelDeep": String(theme.panelDeep),
        "row": String(theme.row),
        "rowHover": String(theme.rowHover),
        "contentSelection": String(theme.contentSelection),
        "outline": String(theme.outline),
        "separator": String(theme.separator),
        "primaryText": String(theme.primaryText),
        "selectedText": String(theme.selectedText),
        "secondaryText": String(theme.secondaryText),
        "disabledText": String(theme.disabledText),
        "action": String(theme.action),
        "green": String(theme.green),
        "yellow": String(theme.yellow),
        "red": String(theme.red),
        "fieldRadius": theme.fieldRadius,
        "buttonRadius": theme.buttonRadius,
        "itemRadius": theme.itemRadius,
        "surfaceRadius": theme.surfaceRadius,
        "menuRadius": theme.menuRadius,
        "iconButtonRadius": theme.iconButtonRadius,
        "controlHeight": theme.controlHeight,
        "compactControlHeight": theme.compactControlHeight
    })
    readonly property bool narrow: width < 1200
    property string detailPage: "log"
    property bool followLog: true
    property bool freezeLog: false
    property bool updatingLog: false
    property bool logPanelVisible: true
    property bool restoringWindowState: false
    property bool windowStateReady: false
    property int episodeContextRow: -1
    property string queueContextId: ""
    property string draggedQueueId: ""
    property string dragTargetQueueId: ""
    property string draggedQueueTitle: ""
    property int draggedQueueIndex: -1
    property int dragTargetQueueIndex: -1
    property real dragPointerX: 0
    property real dragPointerY: 0

    function restoreWindowState() {
        const state = controller.windowState || ({})
        if (!state.width || !state.height)
            return
        restoringWindowState = true
        width = state.width
        height = state.height
        x = state.x
        y = state.y
        episodeDock.SplitView.preferredWidth = state.episodeWidth || 350
        logPanel.SplitView.preferredHeight = state.detailHeight || 235
        logPanelVisible = state.logPanelVisible !== false
        detailPage = state.detailPage || "log"
        followLog = state.followLog !== false
        freezeLog = state.freezeLog === true
        visibility = state.maximized ? Window.Maximized : Window.Windowed
        restoringWindowState = false
        windowStateReady = true
    }
    function saveWindowState() {
        if (!windowStateReady || restoringWindowState)
            return
        controller.saveWindowState({
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "maximized": visibility === Window.Maximized,
            "episodeWidth": episodeDock.width,
            "detailHeight": logPanel.height,
            "logPanelVisible": logPanelVisible,
            "detailPage": detailPage,
            "followLog": followLog,
            "freezeLog": freezeLog,
            "episodeStatuses": controller.visibleEpisodeStatuses
        })
    }
    function scheduleWindowStateSave() {
        if (windowStateReady && !restoringWindowState
                && visibility === Window.Windowed)
            windowStateSave.restart()
    }
    function closeDispatcher() {
        windowStateSave.stop()
        saveWindowState()
        controller.closeWindow()
    }

    Timer {
        id: windowStateSave
        interval: 400
        onTriggered: root.saveWindowState()
    }
    onXChanged: scheduleWindowStateSave()
    onYChanged: scheduleWindowStateSave()
    onWidthChanged: scheduleWindowStateSave()
    onHeightChanged: scheduleWindowStateSave()
    onLogPanelVisibleChanged: scheduleWindowStateSave()
    onDetailPageChanged: scheduleWindowStateSave()
    onFollowLogChanged: scheduleWindowStateSave()
    onFreezeLogChanged: scheduleWindowStateSave()
    onVisibilityChanged: {
        windowStateSave.stop()
        if (windowStateReady && visibility === Window.Maximized)
            saveWindowState()
        else
            scheduleWindowStateSave()
    }

    App.Theme {
        id: batchTheme
        dark: root.applicationRoot.dark
        styleName: root.applicationRoot.applicationThemeStyleName
        accentColor: root.applicationRoot.applicationThemeAccentColor
        baseColor: root.applicationRoot.applicationThemeBaseColor
    }
    Rectangle {
        id: queueDragPreview
        objectName: "batchQueueDragPreview"
        visible: root.draggedQueueId.length > 0
        x: Math.max(8, Math.min(root.width - width - 8, root.dragPointerX + 14))
        y: Math.max(8, Math.min(root.height - height - 8, root.dragPointerY + 14))
        width: Math.min(300, dragPreviewLabel.implicitWidth + 58)
        height: 42
        z: 1000
        radius: theme.surfaceRadius
        color: theme.surfaceContainerHigh
        border.width: 1
        border.color: theme.action
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 12
            spacing: 8
            Controls.DockDragGrip {
                theme: root.theme
                enabled: false
                Layout.preferredWidth: 24
                Layout.preferredHeight: 30
            }
            BatchLabel {
                id: dragPreviewLabel
                objectName: "batchQueueDragPreviewLabel"
                Layout.fillWidth: true
                text: root.draggedQueueTitle
                elide: Text.ElideRight
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
            }
        }
    }
    component BatchCard: Controls.ItemSurface {
        railX: inset + 3; railWidth: 3
        railTopMargin: 12; railBottomMargin: 12
        inset: 4; cornerRadius: theme.surfaceRadius
        borderWidth: 1; borderColor: theme.outlineVariant
        elevated: true; shadowVerticalOffset: 3
        separatorVisible: false
        normalColor: theme.surfaceContainerLow
        selectedColor: theme.contentSelection
    }
    component BatchLabel: Label {
        color: root.theme.primaryText
        font.family: root.theme.fontFamily
        renderType: Text.NativeRendering
    }
    component BatchButton: Controls.Button { theme: root.theme }
    component BatchIconButton: Controls.CompactIconButton { theme: root.theme }
    component BatchTextField: Controls.TextField { theme: root.theme }
    component BatchScrollBar: Controls.ScrollBar { theme: root.theme }
    function stateColor(state) {
        if (state === "failed") return theme.error
        if (state === "completed") return theme.green
        if (state === "rendering") return theme.action
        if (state === "paused" || state === "preparing" || state === "saving")
            return theme.yellow
        return theme.secondaryText
    }
    function detailRows(detail) {
        if (!detail || !detail.id)
            return []
        return [
            {"label": qsTr("Этап"), "value": detail.stage},
            {"label": qsTr("Состояние"), "value": detail.state},
            {"label": qsTr("Кадры"), "value": detail.frames},
            {"label": qsTr("Попытка"), "value": detail.attempt},
            {"label": "PID", "value": detail.pid},
            {"label": qsTr("Код выхода"), "value": detail.exitCode},
            {"label": qsTr("Прошло"), "value": detail.elapsed},
            {"label": qsTr("Сцена"), "value": detail.scene},
            {"label": qsTr("Вывод"), "value": detail.output},
            {"label": qsTr("Лог"), "value": detail.logPath},
            {"label": qsTr("Команда"), "value": detail.command},
            {"label": qsTr("Ошибка"), "value": detail.error}
        ].filter(row => row.value !== "" && row.value !== undefined
            && row.value !== null)
    }
    function queueAction(command, identity) {
        if (command === "only") controller.runOnly(identity)
        else if (command === "hold") controller.holdQueue(identity)
        else if (command === "retry") controller.retryQueue(identity)
        else if (command === "cancel") controller.cancelQueue(identity)
        else if (command === "up") controller.moveQueue(identity, -1)
        else if (command === "down") controller.moveQueue(identity, 1)
        else if (command === "test") controller.testQueue(identity)
        else if (command === "frames") frameDialog.edit(identity)
        else if (command === "remove") controller.removeEpisode(identity)
        else if (command === "log") controller.openPath(controller.selectedDetail.logPath)
        else if (command === "output") controller.showQueueDestination(identity)
    }
    function allows(actions, command) {
        return !!actions && actions.indexOf(command) >= 0
    }
    function updateLog() {
        if (root.freezeLog || root.updatingLog || logText.selectedText.length) return
        root.updatingLog = true
        const next = controller.logText
        if (next.indexOf(logText.text) === 0)
            logText.insert(logText.length, next.slice(logText.length))
        else if (!logText.selectedText.length)
            logText.text = next
        if (root.followLog && !logText.selectedText.length)
            logScroll.contentItem.contentY = Math.max(0, logText.height - logScroll.height)
        root.updatingLog = false
    }
    function episodeActions() {
        return [
            {"title": "Добавить эпизод в очередь", "translate": false,
             "icon": "playlist_add", "command": "add"},
            {"title": "Установить статус", "translate": false,
             "icon": "flag", "children":
                controller.episodeStatusChoices(root.episodeContextRow).map(value => ({
                    "title": value.title, "translate": false, "command": "status:" + value.title,
                    "accent": value.accent, "compactAccent": true, "checked": value.checked
                }))}
        ]
    }
    function episodeFilterActions() {
        const actions = controller.episodeFilterChoices.map(value => ({
            "title": value.title + " · " + value.count,
            "translate": false,
            "command": "status:" + value.value,
            "accent": theme.blend(
                Qt.lighter(value.statusAccent || theme.action, 1),
                theme.primaryText,
                theme.dark ? 0.55 : 0.35),
            "compactAccent": true,
            "checked": value.active
        }))
        actions.push({"separator": true})
        actions.push({
            "title": "Следить за серверной очередью",
            "translate": false,
            "command": "watch",
            "icon": "sync",
            "checked": controller.schedulerRunning
        })
        return actions
    }
    function executionActions(allowed, state) {
        return [
            {title: "Запустить только это", translate: false,
             command: "only", icon: "play_arrow",
             enabled: root.allows(allowed, "only")},
            {title: state === "paused" ? "Продолжить рендер"
                 : state === "rendering" ? "Поставить рендер на паузу"
                 : "Удержать / продолжить",
             translate: false, command: "hold",
             icon: state === "held" || state === "paused" ? "play_circle" : "pause",
             enabled: root.allows(allowed, "hold")},
            {title: "Повторить ошибочные / отменённые", translate: false,
             command: "retry", icon: "refresh",
             enabled: root.allows(allowed, "retry")},
            {title: "Отменить", translate: false,
             command: "cancel", icon: "stop",
             enabled: root.allows(allowed, "cancel")}
        ]
    }
    function queueActions() {
        const details = controller.selectedDetail
        const actions = root.executionActions(details.actions, details.state)
        actions.push(
            {title: "Тестовый рендер · первый кадр", translate: false,
             command: "test", icon: "science",
             enabled: root.allows(details.actions, "test")},
            {title: "Файлы", translate: false, icon: "folder", children: [
                {title: "Открыть лог рендера", translate: false,
                 command: "log", enabled: !!details.logPath},
                {title: "Показать папку вывода", translate: false,
                 command: "output"}
            ]}
        )
        if (details.child === false) {
            actions.push({separator: true})
            actions.push({title: "Удалить эпизод из очереди", translate: false,
                          command: "remove",
                          icon: "delete", enabled: root.allows(details.actions, "remove")})
        }
        return actions
    }
    title: qsTr("Диспетчер батч-рендера")
    width: 1440
    height: 920
    minimumWidth: 950
    minimumHeight: 650
    color: theme.workspace
    visible: false
    onClosing: close => {
        close.accepted = false
        if (controller.running)
            closeDialog.open()
        else
            closeDispatcher()
    }

    onWebThemeSnapshotChanged: controller.setWebTheme(webThemeSnapshot)
    Component.onCompleted: {
        controller.setWebTheme(webThemeSnapshot)
        Qt.callLater(root.restoreWindowState)
    }

    Connections {
        target: controller
        function onWindowStateChanged() { root.restoreWindowState() }
        function onLogChanged() { root.updateLog() }
        function onQueueSelected(index, alignTop) {
            if (index >= 0) queueList.positionViewAtIndex(
                index, alignTop ? ListView.Beginning : ListView.Contain)
        }
        function onEpisodeSelected(index) {
            if (index < 0) return
            episodeSearch.text = ""
            episodeList.positionViewAtIndex(index, ListView.Beginning)
        }
        function onLogScopeChanged() {
            root.updatingLog = true
            logText.deselect()
            logText.text = ""
            root.updatingLog = false
        }
    }

    // Header and summary
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Controls.MaterialIcon { name: "view_list"; size: 24; color: theme.action }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                BatchLabel {
                    objectName: "batchWindowTitle"
                    Layout.fillWidth: true
                    text: qsTr("Диспетчер батч-рендера")
                    color: theme.primaryText
                    font.pointSize: Controls.Typography.title
                    font.weight: Font.DemiBold
                }
                BatchLabel {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: controller.statusText
                    color: theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
            }
            BatchButton {
                objectName: "batchStartQueue"
                text: controller.paused ? qsTr("Запустить очередь") : qsTr("Пауза после шота")
                icon.name: controller.paused ? "play_arrow" : "pause"
                enabled: controller.ready && !controller.closePending
                onClicked: controller.toggleScheduler()
            }
            BatchIconButton {
                iconName: "stop"; toolTip: qsTr("Остановить очередь сейчас")
                enabled: controller.running
                onClicked: controller.interruptRender()
            }
            BatchIconButton {
                objectName: "batchOpenRenderDestination"
                iconName: "folder_open"
                toolTip: qsTr("Открыть общую папку секвенций")
                onClicked: controller.showDestination()
            }
            BatchIconButton {
                objectName: "batchOpenWeb"
                iconName: "language"
                toolTip: controller.webError.length
                    ? controller.webError
                    : qsTr("Открыть веб-диспетчер")
                enabled: controller.webUrl.length > 0
                onClicked: controller.openWeb()
            }
            BatchIconButton {
                objectName: "batchCopyWebUrl"
                iconName: "content_copy"
                toolTip: controller.settings.webSecurity
                    ? qsTr("Скопировать защищённую LAN-ссылку")
                    : qsTr("Скопировать LAN-ссылку")
                enabled: controller.webUrl.length > 0
                onClicked: controller.copyWebUrl()
            }
            BatchIconButton {
                objectName: "batchSettingsButton"
                iconName: "settings"; toolTip: qsTr("Настройки рендера")
                enabled: !controller.running
                onClicked: settingsDialog.open()
            }
            BatchIconButton {
                iconName: "window-minimize"; toolTip: qsTr("Свернуть")
                onClicked: root.showMinimized()
            }
        }

        Rectangle {
            objectName: "batchSummaryBar"
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            color: theme.surfaceContainer
            radius: theme.surfaceRadius
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 12
                Repeater {
                    model: [
                        {"label": qsTr("В ОЧЕРЕДИ"), "value": controller.summary.pending},
                        {"label": qsTr("ГОТОВО / ОШИБКИ"),
                         "value": controller.summary.completed + " / " + controller.summary.failed},
                        {"label": qsTr("ПРОШЛО"), "value": controller.summary.elapsed},
                        {"label": qsTr("ОСТАЛОСЬ"), "value": controller.summary.eta}
                    ]
                    delegate: RowLayout {
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        spacing: 6
                        BatchLabel {
                            Layout.fillWidth: true
                            text: modelData.label
                            color: theme.secondaryText
                            elide: Text.ElideRight
                            font.pointSize: Controls.Typography.micro
                        }
                        BatchLabel {
                            text: String(modelData.value)
                            color: theme.primaryText
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                        }
                        Rectangle {
                            Layout.preferredWidth: 1
                            Layout.preferredHeight: 22
                            visible: index < 3
                            color: theme.outlineVariant
                        }
                    }
                }
                RowLayout {
                    Layout.preferredWidth: root.narrow ? 130 : 230
                    spacing: 8
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 4
                        radius: 2
                        color: theme.outlineVariant
                        Rectangle {
                            width: parent.width * controller.summary.progress
                            height: parent.height
                            radius: 2
                            color: theme.action
                        }
                    }
                    BatchLabel {
                        text: qsTr("Всего: %1%").arg(
                            Math.floor(controller.summary.progress * 100))
                        color: theme.secondaryText
                        font.pointSize: Controls.Typography.micro
                    }
                }
            }
        }

        BatchLabel {
            Layout.fillWidth: true
            visible: controller.errorText.length > 0
            text: controller.errorText
            color: theme.error
            wrapMode: Text.WrapAnywhere
            maximumLineCount: 3
        }

        // Episode catalog and render queue
        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            handle: Rectangle {
                objectName: "batchDockSplitter"
                implicitWidth: 10
                color: "transparent"
                Rectangle {
                    anchors.centerIn: parent
                    width: 1
                    height: Math.max(0, parent.height - 18)
                    color: root.theme.outlineVariant
                }
            }

            Rectangle {
                id: episodeDock
                objectName: "batchEpisodeDock"
                SplitView.preferredWidth: root.narrow ? 270 : 350
                SplitView.minimumWidth: 250
                onWidthChanged: root.scheduleWindowStateSave()
                color: theme.panelDeep
                border.width: 1
                border.color: theme.outlineVariant
                radius: theme.surfaceRadius
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 8; spacing: 6
                    RowLayout {
                        Layout.fillWidth: true
                        BatchTextField {
                            id: episodeSearch
                            Layout.fillWidth: true
                            Layout.minimumWidth: 80
                            placeholderText: qsTr("Найти эпизод")
                        }
                        BatchLabel {
                            text: episodeList.count; color: theme.secondaryText
                        }
                        BatchIconButton {
                            objectName: "batchEpisodeFilterButton"
                            iconName: "filter_alt"
                            iconColor: theme.action
                            toolTip: qsTr("Фильтр эпизодов")
                            enabled: !controller.busy
                            onClicked: {
                                episodeFilterMenu.actions = root.episodeFilterActions()
                                episodeFilterMenu.openBelow(this)
                            }
                        }
                        BatchIconButton {
                            iconName: "refresh"
                            toolTip: controller.busy ? qsTr("Обновление…") : qsTr("Обновить список")
                            enabled: !controller.busy && controller.ready
                            onClicked: controller.refresh()
                        }
                    }
                    ListView {
                        id: episodeList
                        objectName: "batchEpisodeList"
                        Layout.fillWidth: true; Layout.fillHeight: true
                        model: controller.episodesModel
                        spacing: 3; clip: true; pixelAligned: true
                        delegate: Item {
                            id: episodeRow
                            required property int index
                            required property string title
                            required property string subtitle
                            required property string searchKey
                            required property bool selected
                            required property url previewUrl
                            required property string renderStatus
                            required property color statusColor
                            required property bool queued
                            objectName: "batchEpisodeRow_" + index
                            readonly property bool matchesName: !episodeSearch.text
                                || (title + " " + subtitle).toLowerCase().indexOf(episodeSearch.text.toLowerCase()) >= 0
                            readonly property bool matches: matchesName
                            width: episodeList.width - episodeBar.reservedExtent - 4
                            height: matches ? 104 : 0
                            visible: matches
                            BatchCard {
                                objectName: "batchEpisodeSurface_" + episodeRow.index
                                anchors.fill: parent
                                theme: root.theme
                                selected: episodeRow.selected
                                hovered: episodeHover.hovered
                                pressed: episodeActivation.pressed
                                accent: episodeRow.statusColor
                                railWidth: 4
                                normalColor: episodeRow.queued
                                    ? theme.panelDeep : theme.surfaceContainerLow
                            }
                            HoverHandler { id: episodeHover }
                            Controls.ActivationHandler {
                                id: episodeActivation
                                anchors.rightMargin: 44
                                onActivated: controller.selectEpisode(episodeRow.index)
                            }
                            TapHandler {
                                acceptedDevices: PointerDevice.Mouse
                                    | PointerDevice.TouchPad
                                acceptedButtons: Qt.LeftButton
                                gesturePolicy: TapHandler.DragThreshold
                                onDoubleTapped: controller.renderEpisode(
                                    episodeRow.index, false)
                            }
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 12
                                anchors.leftMargin: 18; spacing: 10
                                Controls.ItemPreview {
                                    theme: root.theme
                                    Layout.preferredWidth: 58; Layout.preferredHeight: 58
                                    source: episodeRow.previewUrl
                                    fallbackIcon: "movie"
                                    fallbackText: episodeRow.title.slice(0, 2)
                                    animateAppearance: false
                                    selected: episodeRow.selected
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true; spacing: 2
                                    Layout.minimumWidth: 0
                                    clip: true
                                    BatchLabel {
                                        Layout.fillWidth: true; text: episodeRow.title
                                        textFormat: Text.PlainText; maximumLineCount: 1
                                        color: theme.primaryText; elide: Text.ElideRight
                                        font.pointSize: Controls.Typography.label
                                        font.weight: Font.DemiBold
                                    }
                                    BatchLabel {
                                        objectName: "batchEpisodeDescription_" + episodeRow.index
                                        Layout.fillWidth: true
                                        Layout.minimumWidth: 0
                                        text: episodeRow.subtitle.replace(/\s+/g, " ")
                                        textFormat: Text.PlainText; maximumLineCount: 1
                                        visible: text.length > 0
                                        color: theme.secondaryText; elide: Text.ElideRight
                                        font.pointSize: Controls.Typography.micro
                                    }
                                    BatchLabel {
                                        Layout.fillWidth: true
                                        text: episodeRow.queued
                                            ? qsTr("Уже в очереди")
                                            : episodeRow.renderStatus
                                        textFormat: Text.PlainText; maximumLineCount: 1
                                        color: episodeRow.statusColor
                                        elide: Text.ElideRight
                                        font.pointSize: Controls.Typography.micro
                                    }
                                }
                                BatchIconButton {
                                    objectName: "batchEpisodeAdd_" + episodeRow.index
                                    iconName: "add"
                                    toolTip: qsTr("Добавить эпизод в очередь")
                                    visible: !episodeRow.queued
                                    enabled: controller.ready
                                    onClicked: controller.renderEpisode(episodeRow.index, false)
                                }
                            }
                            MouseArea {
                                anchors.fill: parent; acceptedButtons: Qt.RightButton
                                onClicked: mouse => {
                                    root.episodeContextRow = episodeRow.index
                                    episodeMenu.openAt(episodeRow, mouse.x, mouse.y, true)
                                }
                            }
                        }
                        ScrollBar.vertical: BatchScrollBar { id: episodeBar }
                    }
                }
            }

            Rectangle {
                objectName: "batchQueueDock"
                SplitView.fillWidth: true
                SplitView.minimumWidth: 620
                color: theme.panelDeep
                border.width: 1
                border.color: theme.outlineVariant
                radius: theme.surfaceRadius
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        BatchLabel {
                            objectName: "batchQueueTitle"
                            text: qsTr("ОЧЕРЕДЬ РЕНДЕРА")
                            color: theme.secondaryText
                            font.pointSize: Controls.Typography.label
                        }
                    Item { Layout.fillWidth: true }
                    BatchIconButton {
                        objectName: "batchMoveFirst"
                        iconName: "angle-double-up"
                        toolTip: qsTr("Переместить в начало")
                        enabled: root.allows(controller.selectedDetail.actions, "move")
                        onClicked: controller.moveQueue(
                            controller.selectedDetail.id, -1000000)
                    }
                    BatchIconButton {
                        objectName: "batchMoveUp"
                        iconName: "arrow_upward"
                        toolTip: qsTr("Переместить выше")
                        enabled: root.allows(controller.selectedDetail.actions, "move")
                        onClicked: controller.moveQueue(controller.selectedDetail.id, -1)
                    }
                    BatchIconButton {
                        objectName: "batchMoveDown"
                        iconName: "arrow_downward"
                        toolTip: qsTr("Переместить ниже")
                        enabled: root.allows(controller.selectedDetail.actions, "move")
                        onClicked: controller.moveQueue(controller.selectedDetail.id, 1)
                    }
                    BatchIconButton {
                        objectName: "batchMoveLast"
                        iconName: "angle-double-down"
                        toolTip: qsTr("Переместить в конец")
                        enabled: root.allows(controller.selectedDetail.actions, "move")
                        onClicked: controller.moveQueue(
                            controller.selectedDetail.id, 1000000)
                    }
                    Controls.CheckBox {
                        objectName: "batchAutoClear"
                        theme: root.theme
                        compact: true
                        text: qsTr("Автоочистка")
                        checked: controller.autoClearFinished
                        onClicked: controller.setAutoClearFinished(checked)
                    }
                    BatchIconButton {
                        objectName: "batchLogPanelShow"
                        iconName: "terminal"
                        iconColor: root.logPanelVisible
                            ? theme.action : theme.primaryText
                        backgroundColor: root.logPanelVisible
                            ? theme.secondaryContainer : "transparent"
                        toolTip: root.logPanelVisible
                            ? qsTr("Скрыть лог процесса")
                            : qsTr("Показать лог процесса")
                        onClicked: root.logPanelVisible = !root.logPanelVisible
                    }
                    BatchButton {
                        text: qsTr("Очистить завершённые")
                        icon.name: "delete_sweep"
                        onClicked: controller.clearCompleted()
                    }
                }

                SplitView {
                    objectName: "batchQueueDetailSplitter"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    orientation: Qt.Vertical
                    handle: Rectangle {
                        implicitHeight: 10
                        color: "transparent"
                        Rectangle {
                            anchors.centerIn: parent
                            width: Math.max(0, parent.width - 18)
                            height: 1
                            color: root.theme.outlineVariant
                        }
                    }

                Rectangle {
                    SplitView.fillWidth: true
                    SplitView.fillHeight: true
                    SplitView.minimumHeight: 160
                    color: theme.surfaceContainer
                    radius: theme.surfaceRadius
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 8
                        spacing: 6
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 20
                            clip: true
                            RowLayout {
                                x: 16 - queueList.contentX
                                width: queueList.contentWidth - queueBar.reservedExtent - 32
                                height: parent.height
                                spacing: 10
                                Item { Layout.preferredWidth: 28 }
                                Item { Layout.preferredWidth: 28 }
                                Item { Layout.preferredWidth: 44 }
                                BatchLabel {
                                    objectName: "batchQueueHeaderTitle"
                                    Layout.fillWidth: true
                                    text: qsTr("ЗАДАЧА / ЭТАП"); color: theme.secondaryText
                                    font.pointSize: Controls.Typography.micro
                                }
                                BatchLabel {
                                    objectName: "batchQueueHeaderProgress"
                                    Layout.preferredWidth: 112
                                    text: qsTr("ПРОГРЕСС"); color: theme.secondaryText
                                    font.pointSize: Controls.Typography.micro
                                }
                                BatchLabel {
                                    objectName: "batchQueueHeaderFrames"
                                    Layout.preferredWidth: 78
                                    text: qsTr("КАДРЫ"); color: theme.secondaryText
                                    font.pointSize: Controls.Typography.micro
                                }
                                BatchLabel {
                                    objectName: "batchQueueHeaderElapsed"
                                    Layout.preferredWidth: 86
                                    text: qsTr("ПРОШЛО / ОСТАЛОСЬ"); color: theme.secondaryText
                                    font.pointSize: Controls.Typography.micro
                                }
                                Item { Layout.preferredWidth: 218 }
                            }
                        }
                        ListView {
                            id: queueList
                            objectName: "batchQueueList"
                            Layout.fillWidth: true; Layout.fillHeight: true
                            model: controller.queueModel
                            clip: true; spacing: 3; pixelAligned: true
                            contentWidth: Math.max(width, 1020)
                            flickableDirection: Flickable.AutoFlickDirection
                            bottomMargin: queueHBar.reservedExtent + 4
                            delegate: Item {
                                id: queueRow
                                objectName: "batchQueueRow_" + index
                                required property int index
                                required property string jobId
                                required property string title
                                required property string subtitle
                                required property string state
                                required property string stage
                                required property bool selected
                                required property bool expanded
                                required property real progress
                                required property string frames
                                required property string elapsed
                                required property string eta
                                required property int depth
                                required property bool test
                                required property var pid
                                required property bool included
                                required property var actions
                                required property bool indeterminate
                                required property url previewUrl
                                readonly property bool dragSource:
                                    root.draggedQueueId === queueRow.jobId
                                readonly property bool dragTarget:
                                    root.dragTargetQueueId === queueRow.jobId
                                    && !queueRow.dragSource
                                width: queueList.contentWidth - queueBar.reservedExtent - 4
                                height: depth ? 80 : 88
                                clip: true
                                opacity: dragSource ? 0.58 : 1
                                scale: dragSource ? 0.985 : 1
                                Behavior on opacity {
                                    NumberAnimation { duration: theme.hoverMotionFast }
                                }
                                Behavior on scale {
                                    NumberAnimation { duration: theme.hoverMotionFast }
                                }
                                BatchCard {
                                    objectName: "batchQueueSurface_" + queueRow.index
                                    anchors.fill: parent
                                    anchors.leftMargin: queueRow.depth * 24
                                    theme: root.theme
                                    selected: queueRow.selected
                                    hovered: queueHover.hovered
                                    pressed: queueActivation.pressed
                                    accent: root.stateColor(queueRow.state)

                                }
                                Rectangle {
                                    objectName: "batchQueueDropIndicator_" + queueRow.index
                                    visible: queueRow.dragTarget
                                    x: 4 + queueRow.depth * 24
                                    y: root.dragTargetQueueIndex > root.draggedQueueIndex
                                        ? queueRow.height - height : 0
                                    width: queueRow.width - x - 4
                                    height: 3
                                    radius: 1.5
                                    color: theme.action
                                    z: 20
                                }
                                HoverHandler { id: queueHover }
                                Controls.ActivationHandler {
                                    id: queueActivation
                                    anchors.leftMargin: queueRow.depth * 24
                                    anchors.rightMargin: quickActions.width + 54
                                    onActivated: controller.selectQueue(queueRow.jobId)
                                }
                                TapHandler {
                                    acceptedDevices: PointerDevice.Mouse
                                        | PointerDevice.TouchPad
                                    acceptedButtons: Qt.LeftButton
                                    gesturePolicy: TapHandler.DragThreshold
                                    onDoubleTapped: {
                                        controller.selectQueue(queueRow.jobId)
                                        if (!queueRow.depth)
                                            controller.toggleExpanded(queueRow.jobId)
                                    }
                                }
                                RowLayout {
                                    anchors.fill: parent; anchors.margins: 12
                                    anchors.leftMargin: 16 + queueRow.depth * 24
                                    spacing: 10
                                    Controls.DockDragGrip {
                                        id: orderGrip
                                        objectName: "batchQueueGrip_" + queueRow.index
                                        theme: root.theme
                                        Layout.preferredWidth: 28
                                        Layout.preferredHeight: 28
                                        toolTip: qsTr("Перетащить в очереди")
                                        enabled: root.allows(queueRow.actions, "move")
                                        onClicked: controller.selectQueue(queueRow.jobId)
                                        onDragStarted: (pressX, pressY) => {
                                            const cursor = orderGrip.mapToItem(
                                                root.contentItem, pressX, pressY)
                                            controller.selectQueue(queueRow.jobId)
                                            root.draggedQueueId = queueRow.jobId
                                            root.dragTargetQueueId = queueRow.jobId
                                            root.draggedQueueTitle = queueRow.title
                                            root.draggedQueueIndex = queueRow.index
                                            root.dragTargetQueueIndex = queueRow.index
                                            root.dragPointerX = cursor.x
                                            root.dragPointerY = cursor.y
                                        }
                                        onDragMoved: (pointerX, pointerY) => {
                                            const cursor = orderGrip.mapToItem(
                                                root.contentItem, pointerX, pointerY)
                                            root.dragPointerX = cursor.x
                                            root.dragPointerY = cursor.y
                                            const point = orderGrip.mapToItem(
                                                queueList.contentItem,
                                                pointerX, pointerY)
                                            const targetIndex = queueList.indexAt(
                                                point.x, point.y)
                                            if (targetIndex >= 0) {
                                                root.dragTargetQueueId =
                                                    controller.queueModel.get(
                                                        targetIndex).jobId || ""
                                                root.dragTargetQueueIndex = targetIndex
                                            }
                                        }
                                        onDragFinished: {
                                            controller.moveQueueTo(
                                                root.draggedQueueId,
                                                root.dragTargetQueueId)
                                            root.draggedQueueId = ""
                                            root.dragTargetQueueId = ""
                                            root.draggedQueueIndex = -1
                                            root.dragTargetQueueIndex = -1
                                        }
                                        onDragCanceled: {
                                            root.draggedQueueId = ""
                                            root.dragTargetQueueId = ""
                                            root.draggedQueueIndex = -1
                                            root.dragTargetQueueIndex = -1
                                        }
                                    }
                                    BatchIconButton {
                                        visible: !queueRow.depth
                                        iconName: queueRow.expanded ? "expand_more" : "chevron_right"
                                        toolTip: qsTr("Развернуть / свернуть")
                                        onClicked: controller.toggleExpanded(queueRow.jobId)
                                    }
                                    Controls.CheckBox {
                                        objectName: "batchInclude_" + queueRow.index
                                        theme: root.theme; compact: true
                                        Layout.preferredWidth: 28
                                        visible: queueRow.depth > 0
                                        checked: queueRow.included
                                        enabled: root.allows(queueRow.actions, "include")
                                        Accessible.name: qsTr("Включить шот") + " " + queueRow.title
                                        onClicked: controller.toggleIncluded(queueRow.jobId)
                                    }
                                    Controls.ItemPreview {
                                        objectName: "batchQueuePreview_" + queueRow.index
                                        theme: root.theme
                                        Layout.minimumWidth: 44; Layout.maximumWidth: 44
                                        Layout.preferredWidth: 44; Layout.preferredHeight: 44
                                        source: queueRow.previewUrl
                                        fallbackIcon: "movie"
                                        fallbackText: queueRow.title.slice(0, 2)
                                        selected: queueRow.selected
                                        animateAppearance: false
                                    }
                                    ColumnLayout {
                                        objectName: "batchQueueTitle_" + queueRow.index
                                        Layout.fillWidth: true
                                        Layout.minimumWidth: 210
                                        spacing: 2
                                        BatchLabel {
                                            Layout.fillWidth: true
                                            text: queueRow.title + (queueRow.test ? " · TEST" : "")
                                            textFormat: Text.PlainText; maximumLineCount: 1
                                            color: theme.primaryText; elide: Text.ElideRight
                                            font.pointSize: Controls.Typography.label
                                            font.weight: queueRow.depth ? Font.Normal : Font.DemiBold
                                        }
                                        BatchLabel {
                                            Layout.fillWidth: true
                                            objectName: "batchQueueStage_" + queueRow.index
                                            text: queueRow.stage.replace(/\s+/g, " ")
                                            textFormat: Text.PlainText; maximumLineCount: 1
                                            color: root.stateColor(queueRow.state)
                                            elide: Text.ElideRight
                                            font.pointSize: Controls.Typography.micro
                                        }
                                        BatchLabel {
                                            Layout.fillWidth: true
                                            text: queueRow.subtitle + (queueRow.pid ? " · PID " + queueRow.pid : "")
                                            textFormat: Text.PlainText; maximumLineCount: 1
                                            color: theme.secondaryText; elide: Text.ElideRight
                                            font.pointSize: Controls.Typography.micro
                                        }
                                    }
                                    ColumnLayout {
                                        objectName: "batchQueueProgress_" + queueRow.index
                                        Layout.minimumWidth: 112; Layout.maximumWidth: 112
                                        Layout.preferredWidth: 112; spacing: 5
                                        BatchLabel {
                                            text: queueRow.indeterminate ? qsTr("Выполняется…")
                                                : Math.floor(queueRow.progress * 100) + "%"
                                            color: theme.primaryText
                                            font.pointSize: Controls.Typography.micro
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true; Layout.preferredHeight: 4
                                            radius: 2; color: theme.outlineVariant
                                            Rectangle {
                                                width: parent.width * queueRow.progress
                                                height: parent.height; radius: 2
                                                color: root.stateColor(queueRow.state)
                                            }
                                        }
                                    }
                                    BatchLabel {
                                        objectName: "batchQueueFrames_" + queueRow.index
                                        Layout.minimumWidth: 78; Layout.maximumWidth: 78
                                        Layout.preferredWidth: 78; text: queueRow.frames
                                        color: theme.secondaryText
                                        font.pointSize: Controls.Typography.label
                                    }
                                    ColumnLayout {
                                        objectName: "batchQueueElapsed_" + queueRow.index
                                        Layout.minimumWidth: 86; Layout.maximumWidth: 86
                                        Layout.preferredWidth: 86; spacing: 4
                                        BatchLabel {
                                            text: queueRow.elapsed; color: theme.primaryText
                                            font.pointSize: Controls.Typography.label
                                        }
                                        BatchLabel {
                                            text: queueRow.eta; color: theme.secondaryText
                                            font.pointSize: Controls.Typography.micro
                                        }
                                    }
                                    RowLayout {
                                        id: quickActions
                                        Layout.minimumWidth: 180
                                        Layout.maximumWidth: Layout.minimumWidth
                                        spacing: 2
                                        Repeater {
                                            model: [{command: "frames", icon: "edit",
                                                     title: qsTr("Выбрать кадры"),
                                                     enabled: root.allows(queueRow.actions, "frames"),
                                                     visible: queueRow.depth > 0}
                                                   ].concat(root.executionActions(queueRow.actions,
                                                                                  queueRow.state))
                                                    .concat([{
                                                        command: "output", icon: "folder_open",
                                                        title: qsTr("Открыть папку секвенции"),
                                                        enabled: true,
                                                        visible: queueRow.depth === 0
                                                    }, {
                                                        command: "remove", icon: "delete",
                                                        title: qsTr("Удалить эпизод из очереди"),
                                                        enabled: root.allows(queueRow.actions, "remove"),
                                                        visible: queueRow.depth === 0
                                                    }])
                                            delegate: BatchIconButton {
                                                required property var modelData
                                                objectName: "batchQueueAction_" + modelData.command + "_" + queueRow.index
                                                iconName: modelData.icon; toolTip: modelData.title
                                                visible: modelData.visible !== false
                                                enabled: modelData.enabled && !controller.closePending
                                                iconColor: modelData.command === "remove"
                                                    ? theme.error : theme.primaryText
                                                Accessible.name: modelData.title
                                                onClicked: root.queueAction(modelData.command, queueRow.jobId)
                                            }
                                        }
                                    }
                                    BatchIconButton {
                                        iconName: "more_vert"; toolTip: qsTr("Действия задачи")
                                        onClicked: {
                                            root.queueContextId = queueRow.jobId
                                            controller.selectQueue(queueRow.jobId)
                                            queueMenu.openAt(this, 0, height, false)
                                        }
                                    }
                                }
                                MouseArea {
                                    anchors.fill: parent; acceptedButtons: Qt.RightButton
                                    onClicked: mouse => {
                                        root.queueContextId = queueRow.jobId
                                        controller.selectQueue(queueRow.jobId)
                                        queueMenu.openAt(queueRow, mouse.x, mouse.y, true)
                                    }
                                }
                            }
                            BatchLabel {
                                anchors.centerIn: parent
                                visible: queueList.count === 0
                                text: qsTr("Очередь рендера пуста\nДобавьте эпизод кнопкой + и запустите очередь")
                                horizontalAlignment: Text.AlignHCenter
                                color: theme.secondaryText
                            }
                            ScrollBar.vertical: BatchScrollBar { id: queueBar }
                            ScrollBar.horizontal: BatchScrollBar { id: queueHBar }
                        }
                    }

                }

                // Process log and selected job details
                Rectangle {
                    id: logPanel
                    objectName: "batchLogPanel"
                    SplitView.fillWidth: true
                    SplitView.preferredHeight: root.height < 760 ? 170 : 235
                    SplitView.minimumHeight: 120
                    visible: root.logPanelVisible
                    color: theme.surfaceContainer; radius: theme.surfaceRadius
                    onHeightChanged: if (visible) root.scheduleWindowStateSave()
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 8; spacing: 6
                        RowLayout {
                            Layout.fillWidth: true
                            Controls.SegmentedButton {
                                theme: root.theme; currentValue: root.detailPage
                                segmentWidth: 104
                                model: [{"label": qsTr("Лог"), "value": "log"},
                                        {"label": qsTr("Превью"), "value": "preview"},
                                        {"label": qsTr("Параметры"), "value": "details"}]
                                onActivated: value => root.detailPage = value
                            }
                            BatchLabel {
                                Layout.fillWidth: true
                                text: controller.selectedDetail.title || qsTr("Все задачи")
                                color: theme.secondaryText; elide: Text.ElideRight
                            }
                            BatchIconButton {
                                iconName: "select_all"; toolTip: qsTr("Показать все логи")
                                onClicked: controller.selectQueue("")
                            }
                            BatchIconButton {
                                objectName: "batchOpenLog"
                                iconName: "open_in_new"
                                toolTip: controller.selectedDetail.logPath
                                    ? qsTr("Открыть лог рендера")
                                    : controller.selectedDetail.child
                                        ? qsTr("Лог появится после запуска шота")
                                        : qsTr("Выберите шот, чтобы открыть его лог")
                                onClicked: controller.openSelectedLog()
                            }
                            Controls.CheckBox {
                                theme: root.theme; text: qsTr("Следить"); checked: root.followLog
                                visible: root.detailPage === "log"
                                onClicked: { root.followLog = checked; root.updateLog() }
                            }
                            Controls.CheckBox {
                                theme: root.theme; text: qsTr("Зафиксировать"); checked: root.freezeLog
                                visible: root.detailPage === "log"
                                onClicked: { root.freezeLog = checked; root.updateLog() }
                            }
                        }
                        ScrollView {
                            id: logScroll
                            Layout.fillWidth: true; Layout.fillHeight: true
                            visible: root.detailPage === "log"
                            clip: true
                            rightPadding: logBar.reservedExtent + 4
                            contentWidth: availableWidth
                            Controls.TextArea {
                                id: logText
                                objectName: "batchLogText"
                                theme: root.theme
                                width: logScroll.availableWidth
                                readOnly: true
                                textFormat: TextEdit.PlainText
                                wrapMode: TextEdit.WrapAnywhere
                                font.pointSize: Controls.Typography.micro
                                background: Item {}
                                onSelectedTextChanged: if (!selectedText.length) root.updateLog()
                            }
                            ScrollBar.vertical: BatchScrollBar { id: logBar }
                        }
                        Item {
                            id: previewPage
                            objectName: "batchRenderPreviewPage"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: root.detailPage === "preview"
                            readonly property var items: controller.renderPreviews || []
                            property string currentOwner: ""
                            property string currentPath: ""
                            property url currentUrl: ""
                            ListModel { id: previewModel }

                            onItemsChanged: {
                                const owner = items.length ? String(items[0].jobId) : ""
                                if (owner !== currentOwner) {
                                    currentOwner = owner
                                    currentPath = ""
                                    currentUrl = ""
                                    previewModel.clear()
                                }
                                while (previewModel.count > items.length)
                                    previewModel.remove(items.length)
                                for (let index = previewModel.count;
                                     index < items.length; ++index)
                                    previewModel.append(items[index])
                                if (!currentPath && items.length) {
                                    currentPath = String(items[0].path)
                                    currentUrl = items[0].url
                                    return
                                }
                                for (let index = 0; index < items.length; ++index) {
                                    if (String(items[index].path) === currentPath) {
                                        currentUrl = items[index].url
                                        break
                                    }
                                }
                            }

                            RowLayout {
                                anchors.fill: parent
                                spacing: 0
                                ListView {
                                    id: previewStrip
                                    objectName: "batchRenderPreviewStrip"
                                    Layout.preferredWidth: Math.min(280,
                                        Math.max(190, previewPage.width * 0.25))
                                    Layout.fillHeight: true
                                    model: previewModel
                                    spacing: 4
                                    pixelAligned: true
                                    clip: true
                                    rightMargin: previewBar.reservedExtent + 4
                                    delegate: Controls.ItemSurface {
                                        id: previewTile
                                        required property int index
                                        required property string path
                                        required property url url
                                        required property string title
                                        width: previewStrip.width
                                            - previewBar.reservedExtent - 4
                                        height: 62
                                        theme: root.theme
                                        selected: path === previewPage.currentPath
                                        hovered: previewMouse.containsMouse
                                        pressed: previewMouse.pressed
                                        railVisible: false
                                        separatorVisible: false
                                        cornerRadius: theme.itemRadius
                                        borderWidth: selected ? 1 : 0
                                        borderColor: theme.action
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 6
                                            spacing: 8
                                            Controls.ItemPreview {
                                                theme: root.theme
                                                Layout.preferredWidth: 72
                                                Layout.preferredHeight: 48
                                                source: previewTile.url
                                                fallbackIcon: "image"
                                                selected: previewTile.selected
                                                outlined: true
                                                animateAppearance: false
                                            }
                                            BatchLabel {
                                                Layout.fillWidth: true
                                                text: previewTile.title
                                                elide: Text.ElideMiddle
                                                maximumLineCount: 2
                                                wrapMode: Text.Wrap
                                                font.pointSize: Controls.Typography.micro
                                            }
                                        }
                                        MouseArea {
                                            id: previewMouse
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                previewPage.currentPath = String(
                                                    previewTile.path)
                                                previewPage.currentUrl =
                                                    previewTile.url
                                            }
                                            onDoubleClicked: controller.openPath(
                                                previewTile.path)
                                        }
                                    }
                                    ScrollBar.vertical: BatchScrollBar { id: previewBar }
                                }
                                Rectangle {
                                    Layout.fillHeight: true
                                    Layout.preferredWidth: 1
                                    color: theme.outlineVariant
                                }
                                Item {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    Controls.ItemPreview {
                                        objectName: "batchRenderPreviewImage"
                                        anchors.fill: parent; anchors.margins: 8
                                        visible: previewPage.currentPath.length > 0
                                        theme: root.theme
                                        source: previewPage.currentUrl
                                        fallbackIcon: "image"
                                        fillMode: Image.PreserveAspectFit
                                        outlined: previewPage.currentPath.length > 0
                                        animateAppearance: false
                                    }
                                    BatchLabel {
                                        anchors.centerIn: parent
                                        visible: previewPage.currentPath.length === 0
                                        text: qsTr("Готовые кадры появятся здесь во время рендера")
                                        color: theme.secondaryText
                                    }
                                    TapHandler {
                                        enabled: previewPage.currentPath.length > 0
                                        onDoubleTapped: controller.openPath(previewPage.currentPath)
                                    }
                                }
                            }
                        }
                        Item {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            visible: root.detailPage === "details"
                            BatchLabel {
                                anchors.centerIn: parent
                                visible: !controller.selectedDetail.id
                                text: qsTr("Выберите задачу, чтобы увидеть процесс и файлы")
                                color: theme.secondaryText
                            }
                            ListView {
                                id: detailRows
                                objectName: "batchDetailRows"
                                anchors.fill: parent
                                anchors.margins: 8
                                visible: Boolean(controller.selectedDetail.id)
                                model: root.detailRows(controller.selectedDetail)
                                spacing: 0
                                pixelAligned: true
                                clip: true
                                rightMargin: detailsBar.reservedExtent + 4
                                delegate: Item {
                                    required property var modelData
                                    width: detailRows.width
                                        - detailsBar.reservedExtent - 4
                                    height: Math.max(20, detailValue.contentHeight + 2)
                                    RowLayout {
                                        anchors.fill: parent
                                        spacing: 8
                                        BatchLabel {
                                            Layout.preferredWidth: 105
                                            Layout.alignment: Qt.AlignTop
                                            text: modelData.label
                                            color: theme.secondaryText
                                        }
                                        TextEdit {
                                            id: detailValue
                                            Layout.fillWidth: true
                                            Layout.alignment: Qt.AlignTop
                                            text: String(modelData.value)
                                            readOnly: true
                                            selectByMouse: true
                                            textFormat: TextEdit.PlainText
                                            wrapMode: TextEdit.WrapAnywhere
                                            color: theme.primaryText
                                            selectionColor: theme.action
                                            selectedTextColor: theme.selectedText
                                            font.family: theme.fontFamily
                                            font.pointSize: Controls.Typography.micro
                                        }
                                    }
                                }
                                ScrollBar.vertical: BatchScrollBar { id: detailsBar }
                            }
                        }
                    }
                }
                }
            }
        }
    }
    }

    // Menus and dialogs
    App.ActionMenu {
        id: episodeMenu; parent: Overlay.overlay; theme: root.theme; compact: true
        objectName: "batchEpisodeMenu"
        actions: []
        onAboutToShow: actions = root.episodeActions()
        onTriggered: command => {
            if (command === "add") controller.renderEpisode(root.episodeContextRow, false)
            else if (command.indexOf("status:") === 0)
                controller.setEpisodeStatus(root.episodeContextRow, command.slice(7))
        }
    }
    App.ActionMenu {
        id: episodeFilterMenu
        parent: Overlay.overlay
        theme: root.theme
        compact: true
        preferredWidth: 270
        objectName: "batchEpisodeFilterMenu"
        actions: []
        onTriggered: command => {
            if (command === "watch")
                controller.watchServer(!controller.schedulerRunning)
            else if (command.indexOf("status:") === 0) {
                controller.toggleEpisodeStatusFilter(command.slice(7))
                if (root.windowStateReady)
                    windowStateSave.restart()
            }
        }
    }
    App.ActionMenu {
        id: queueMenu; parent: Overlay.overlay; theme: root.theme; compact: true
        objectName: "batchQueueMenu"
        actions: []
        onAboutToShow: actions = root.queueActions()
        onTriggered: command => root.queueAction(command, root.queueContextId)
    }

    Controls.Dialog {
        id: frameDialog
        objectName: "batchFrameDialog"
        parent: Overlay.overlay; theme: root.theme
        title: qsTr("Кадры для рендера")
        width: Math.min(520, root.width - 40)
        modal: true; anchors.centerIn: parent
        property string jobId: ""
        function edit(identity) {
            jobId = identity
            controller.selectQueue(identity)
            frameInput.text = controller.selectedDetail.frameSpec
            open()
        }
        onOpened: {
            frameInput.forceActiveFocus()
            frameInput.selectAll()
        }
        contentItem: ColumnLayout {
            spacing: 8
            BatchTextField {
                id: frameInput
                objectName: "batchFrameInput"
                Layout.fillWidth: true
                placeholderText: qsTr("1-20, 50, 66, 68, 70-150")
                onAccepted: if (controller.setFrameSpec(frameDialog.jobId, text)) frameDialog.close()
            }
            BatchLabel {
                Layout.fillWidth: true
                text: qsTr("Разделяйте отдельные кадры и диапазоны запятыми. Кадры должны входить в диапазон шота.")
                color: theme.secondaryText
                font.pointSize: Controls.Typography.micro; wrapMode: Text.Wrap
            }
        }
        footer: Controls.DialogActions {
            theme: root.theme
            BatchButton {
                text: qsTr("Отмена")
                onClicked: frameDialog.close()
            }
            BatchButton {
                objectName: "batchFrameSave"
                text: qsTr("Применить"); highlighted: true
                enabled: frameInput.text.trim().length > 0
                onClicked: if (controller.setFrameSpec(frameDialog.jobId, frameInput.text)) frameDialog.close()
            }
        }
    }

    Controls.Dialog {
        id: closeDialog
        parent: Overlay.overlay; theme: root.theme
        title: qsTr("Остановить работу и закрыть?")
        modal: true; anchors.centerIn: parent
        contentItem: BatchLabel {
            text: qsTr("Активный рендер будет остановлен. Остальные задачи сохранятся на паузе.")
            color: theme.primaryText
        }
        footer: Controls.DialogActions {
            theme: root.theme
            BatchButton { text: qsTr("Продолжить работу"); onClicked: closeDialog.close() }
            BatchButton {
                text: qsTr("Остановить и закрыть")
                onClicked: { closeDialog.close(); root.closeDispatcher() }
            }
        }
    }

    Controls.Dialog {
        id: settingsDialog
        objectName: "batchSettingsDialog"
        parent: Overlay.overlay; theme: root.theme
        title: qsTr("Настройки рендера")
        width: Math.min(680, root.width - 40)
        height: Math.min(720, root.height - 40)
        modal: true; anchors.centerIn: parent
        onAboutToShow: {
            mayaPath.text = controller.settings.mayaPath
            outputPath.text = controller.settings.savePath
            camera.text = controller.settings.camera
            timeout.value = controller.settings.timeout
            logCheckin.currentIndex = Math.max(
                0, logCheckin.values.indexOf(controller.settings.logCheckin))
            skipDependencyErrors.checked = controller.settings.skipDependencyErrors
            pollInterval.value = controller.settings.pollInterval
            webEnabled.checked = controller.settings.webEnabled
            webPort.value = controller.settings.webPort
            webSecurity.checked = controller.settings.webSecurity
            stopOnError.checked = controller.settings.stopOnError
        }
        contentItem: ScrollView {
            id: settingsScroll
            clip: true
            contentWidth: availableWidth
            rightPadding: settingsBar.reservedExtent + 4
            ColumnLayout {
                width: settingsScroll.availableWidth
                spacing: 18
                App.ConfigurationSection {
                    theme: root.theme; Layout.fillWidth: true
                    title: qsTr("Maya")
                    description: qsTr("Рендер, папка назначения и камера сцены")
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 10
                        BatchLabel { text: qsTr("Render.exe"); color: theme.secondaryText }
                        RowLayout {
                            Layout.fillWidth: true
                            BatchTextField { id: mayaPath; Layout.fillWidth: true }
                            BatchIconButton {
                                iconName: "folder"; toolTip: qsTr("Выбрать")
                                onClicked: mayaDialog.open()
                            }
                        }
                        BatchLabel { text: qsTr("Папка вывода"); color: theme.secondaryText }
                        RowLayout {
                            Layout.fillWidth: true
                            BatchTextField { id: outputPath; Layout.fillWidth: true }
                            BatchIconButton {
                                iconName: "folder"; toolTip: qsTr("Выбрать")
                                onClicked: outputDialog.open()
                            }
                        }
                        BatchLabel { text: qsTr("Камера"); color: theme.secondaryText }
                        BatchTextField {
                            id: camera; Layout.fillWidth: true
                            placeholderText: qsTr("Использовать настройки сцены")
                        }
                    }
                }
                App.ConfigurationSection {
                    theme: root.theme; Layout.fillWidth: true
                    title: qsTr("Выполнение очереди")
                    description: qsTr("Контроль зависших рендеров и обработка ошибок")
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 12
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Максимальное время одного шота, минуты")
                            description: qsTr("Если Maya зависнет или перестанет отвечать, диспетчер остановит шот по истечении этого времени. 0 — ждать без ограничения.")
                            Controls.SpinBox { id: timeout; theme: root.theme; from: 0; to: 10080 }
                        }
                        Controls.Switch {
                            id: stopOnError; theme: root.theme
                            text: qsTr("Ставить очередь на паузу после ошибки")
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Пропускать недоступные зависимости")
                            description: qsTr("Продолжить подготовку эпизода, записав ошибку файла в лог")
                            Controls.CheckBox {
                                id: skipDependencyErrors; theme: root.theme
                            }
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Чек-ин логов в TACTIC")
                            description: qsTr("Локальные логи сохраняются всегда")
                            Controls.ComboBox {
                                id: logCheckin; theme: root.theme
                                Layout.preferredWidth: 210
                                property var values: ["always", "failed", "never"]
                                model: [qsTr("Всегда"), qsTr("Только при ошибке"), qsTr("Никогда")]
                            }
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Проверка серверной очереди, секунды")
                            description: qsTr("Интервал действует, когда включено слежение за очередью")
                            Controls.SpinBox {
                                id: pollInterval; theme: root.theme
                                from: 5; to: 3600; editable: true
                            }
                        }
                    }
                }
                App.ConfigurationSection {
                    theme: root.theme; Layout.fillWidth: true
                    title: qsTr("Веб-диспетчер")
                    description: qsTr("Доступ к очереди из локальной сети")
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 12
                        Controls.Switch {
                            id: webEnabled; theme: root.theme
                            text: qsTr("Запускать веб-диспетчер")
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Порт веб-диспетчера")
                            description: qsTr("Постоянный порт для доступа из локальной сети")
                            Controls.SpinBox {
                                id: webPort; theme: root.theme
                                enabled: webEnabled.checked
                                from: 1; to: 65535; editable: true
                            }
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Защита веб-диспетчера")
                            description: qsTr("Требовать секретную ссылку; без неё диспетчер доступен всей локальной сети")
                            Controls.CheckBox {
                                id: webSecurity; theme: root.theme
                                enabled: webEnabled.checked
                            }
                        }
                    }
                }
            }
            ScrollBar.vertical: BatchScrollBar { id: settingsBar }
        }
        footer: Controls.DialogActions {
            objectName: "batchSettingsFooter"
            theme: root.theme
            BatchButton { text: qsTr("Отмена"); onClicked: settingsDialog.close() }
            BatchButton {
                text: qsTr("Сохранить"); highlighted: true; icon.name: "save"
                enabled: mayaPath.text.trim().length > 0 && outputPath.text.trim().length > 0
                onClicked: {
                    controller.saveSettings(mayaPath.text, outputPath.text, camera.text,
                                            stopOnError.checked, timeout.value,
                                            logCheckin.values[logCheckin.currentIndex],
                                            skipDependencyErrors.checked,
                                            pollInterval.value, webEnabled.checked,
                                            webPort.value, webSecurity.checked)
                    settingsDialog.close()
                }
            }
        }
    }
    FileDialog {
        id: mayaDialog
        title: qsTr("Исполняемый файл Maya Render")
        onAccepted: mayaPath.text = root.controller.localPath(selectedFile)
    }
    FolderDialog {
        id: outputDialog
        title: qsTr("Папка вывода")
        onAccepted: outputPath.text = root.controller.localPath(selectedFolder)
    }
}
"""
# Window lifecycle


_RUNTIME_WINDOWS = globals().get("_RUNTIME_WINDOWS", [])


def _handler_context(parent):
    if parent is None:
        raise RuntimeError("TACTIC Handler main window is not available")
    engine = qmlEngine(parent)
    if engine is None:
        raise RuntimeError("TACTIC Handler QML engine is not available")
    application = engine.rootContext().contextProperty("appController")
    if application is None:
        raise RuntimeError("TACTIC Handler application controller is unavailable")
    return engine, application


def _create_window(engine, application_root, parent, controller):
    source = QML_SOURCE.replace(
        "__APP_QML_URL__",
        QUrl.fromLocalFile(str(application_root / "thlib/ui/qml")).toString(),
    ).replace(
        "__CONTROLS_URL__",
        QUrl.fromLocalFile(str(application_root / "thlib/ui/qml/controls")).toString(),
    )
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl.fromLocalFile(str(Path(__file__))))
    if component.isError():
        details = "\n".join(error.toString() for error in component.errors())
        component.deleteLater()
        raise RuntimeError(f"Cannot load Batch Dispatcher QML:\n{details}")
    window = component.createWithInitialProperties(
        {"applicationRoot": parent, "controller": controller}
    )
    if window is None:
        details = "\n".join(error.toString() for error in component.errors())
        component.deleteLater()
        raise RuntimeError(f"Cannot create Batch Dispatcher window:\n{details}")
    return component, window


def _windows_to_hide(parent, application, enabled):
    if not enabled:
        return [], []
    hidden_windows = [parent] if parent.isVisible() else []
    window_model = getattr(application, "window_model", None)
    hidden_ids = []
    if window_model is not None and window_model.is_window_visible("script_editor"):
        hidden_ids.append("script_editor")
    return hidden_windows, hidden_ids


def show(parent=None, project_code=None, *, hide_handler=True):
    """Show the local batch scheduler backed by the public Handler API."""
    from thlib.environment import env_inst, env_mode

    if _RUNTIME_WINDOWS:
        window = _RUNTIME_WINDOWS[0]["window"]
        window.showNormal()
        window.requestActivate()
        return window

    parent = parent or env_inst.ui_main
    engine, application = _handler_context(parent)
    project_code = str(
        project_code or getattr(application, "current_project_code", "") or ""
    )
    if not project_code:
        raise RuntimeError("Select a project before opening Batch Dispatcher")

    controller = BatchDispatcherController(
        get_api(),
        project_code,
        offline=os.environ.get("TACTIC_QML_SMOKE_OFFLINE", "") == "1",
    )
    application_root = Path(env_mode.get_current_path())
    component, window = _create_window(engine, application_root, parent, controller)

    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    controller.setParent(window)
    hidden_windows, hidden_window_ids = _windows_to_hide(
        parent, application, hide_handler
    )
    entry = {
        "window": window,
        "component": component,
        "controller": controller,
        "application": application,
        "hidden_windows": hidden_windows,
        "hidden_window_ids": hidden_window_ids,
    }
    _RUNTIME_WINDOWS.append(entry)
    controller.windowCloseRequested.connect(lambda: _dispose_window(window))
    controller.attach_window(window)
    window.show()
    window.requestActivate()
    for hidden_window in hidden_windows:
        hidden_window.hide()
    for window_id in hidden_window_ids:
        application.window_model.close_window(window_id)
    controller.initialize()
    return window


def _dispose_window(window):
    entry = next((item for item in _RUNTIME_WINDOWS if item["window"] is window), None)
    if entry is None:
        return
    _RUNTIME_WINDOWS.remove(entry)
    entry["controller"].shutdown()
    window.hide()
    window.deleteLater()
    entry["component"].deleteLater()
    for hidden_window in entry["hidden_windows"]:
        hidden_window.show()
        hidden_window.raise_()
        hidden_window.requestActivate()
    for window_id in entry["hidden_window_ids"]:
        entry["application"].window_model.show_window(window_id)
