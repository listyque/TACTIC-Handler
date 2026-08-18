import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property bool filtersExpanded: true
    readonly property bool compactLayout: width < 560
    readonly property bool hasSelectedPreset:
        filterEditorController.selected_preset >= 0
        && filterEditorController.selected_preset < savedSearchCombo.count
    property string presetAction: "save"

    function columnIndex(value) {
        for (let row = 0; row < filterColumnModel.count(); ++row) {
            if (filterColumnModel.get(row).value === value)
                return row
        }
        return -1
    }

    function openPresetDialog(action) {
        presetAction = action
        presetName.text = action === "rename"
            ? filterEditorController.tab_title
            : action === "duplicate"
                ? filterEditorController.tab_title + " copy"
                : appController.current_search_tab_title
        presetDialog.open()
        presetName.forceActiveFocus()
        presetName.selectAll()
    }

    function reloadPresetsForCurrentSearch() {
        Qt.callLater(function() {
            filterEditorController.sync_search_session()
        })
    }

    Component.onCompleted: {
        filterEditorController.sync_search_session()
    }

    Connections {
        target: appController
        function onProject_changed() {
            root.reloadPresetsForCurrentSearch()
        }
        function onSection_state_changed() {
            root.reloadPresetsForCurrentSearch()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.surfaceContainerLow
    }

    Flickable {
        id: searchFlickable
        anchors.fill: parent
        clip: true
        contentWidth: width
        contentHeight: searchCards.implicitHeight + 20
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: searchCards
            x: 10
            y: 10
            width: Math.max(0, searchFlickable.width - 20)
            spacing: 10

        Rectangle {
            width: parent.width
            height: 56
            radius: root.theme.itemRadius
            color: root.theme.panelDeep

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 10
                spacing: 8

                MaterialIcon {
                    name: "save"
                    size: 17
                    color: root.theme.action
                }

                Label {
                    visible: !root.compactLayout
                    text: qsTr("Saved searches")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                    font.weight: Font.DemiBold
                }

                Md3ComboBox {
                    id: savedSearchCombo
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Layout.preferredHeight: root.theme.controlHeight
                    theme: root.theme
                    model: filterPresetModel
                    textRole: "title"
                    translateDisplayText: false
                    currentIndex: filterEditorController.selected_preset
                    enabled: count > 0 && !filterEditorController.busy
                    displayText: currentIndex >= 0 && currentIndex < count
                        ? currentText : qsTr("Select a saved search")
                    onActivated:
                        filterEditorController
                            .select_preset_for_current_search(currentIndex)
                }

                Md3BusyIndicator {
                    uiTheme: root.theme
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                    running: filterEditorController.busy
                    visible: running
                }

                CompactIconButton {
                    theme: root.theme
                    iconName: "save"
                    toolTip: qsTr("Update selected preset")
                    enabled: root.hasSelectedPreset
                        && !filterEditorController.busy
                    onClicked:
                        filterEditorController
                            .update_selected_from_current_search()
                }
                CompactIconButton {
                    theme: root.theme
                    iconName: "add"
                    toolTip: qsTr("Save as new preset")
                    enabled: !filterEditorController.busy
                    onClicked: root.openPresetDialog("save")
                }
                CompactIconButton {
                    id: presetMoreButton
                    theme: root.theme
                    iconName: "more_vert"
                    toolTip: qsTr("Saved search actions")
                    onClicked: presetActions.toggleBelow(presetMoreButton)
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 50
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainerHigh

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.filtersExpanded = !root.filtersExpanded
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8

                MaterialIcon {
                    name: root.filtersExpanded
                        ? "keyboard_arrow_down" : "keyboard_arrow_right"
                    size: 18
                    color: root.theme.secondaryText
                }
                MaterialIcon {
                    name: "filter_alt"
                    size: 17
                    color: root.theme.action
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Search Filters")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }
                Md3Button {
                    Layout.preferredHeight: root.theme.controlHeight
                    theme: root.theme
                    highlighted: true
                    compact: root.compactLayout
                    enabled: appController.search_state !== "loading"
                    text: appController.search_state === "loading"
                        ? qsTr("Searching...") : qsTr("Apply filters")
                    toolTip: text
                    icon.name: appController.search_state === "loading"
                        ? "hourglass_empty" : "search"
                    onClicked: appController.apply_search_filters()
                }
                CompactIconButton {
                    theme: root.theme
                    iconName: "add"
                    round: true
                    toolTip: qsTr("Add filter")
                    onClicked: appController.add_search_filter()
                }
                CompactIconButton {
                    theme: root.theme
                    iconName: "delete"
                    round: true
                    toolTip: qsTr("Reset filters")
                    onClicked: appController.clear_search_filters()
                }
            }
        }

        Column {
            id: filtersColumn
            width: parent.width
            height: root.filtersExpanded ? implicitHeight : 0
            visible: root.filtersExpanded
            spacing: 7

            Repeater {
                model: filterModel

            delegate: Rectangle {
                id: filterRow

                required property int index
                required property string column
                required property var relation
                required property var value
                required property bool rowEnabled
                required property string operator
                required property bool isDefault

                readonly property var relationChoices:
                    appController.search_filter_relations(column)
                readonly property bool compact: width < 560

                function relationIndex(value) {
                    for (let row = 0; row < relationChoices.length; ++row) {
                        if (relationChoices[row].value === value)
                            return row
                    }
                    return -1
                }

                width: filtersColumn.width
                implicitHeight: filterContent.implicitHeight + 20
                height: implicitHeight
                radius: root.theme.itemRadius
                color: root.theme.surfaceContainerHigh
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true
                opacity: rowEnabled ? 1 : 0.58
                Behavior on opacity { NumberAnimation { duration: 120 } }

                ColumnLayout {
                    id: filterContent
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 7

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Md3CheckBox {
                            theme: root.theme
                            id: filterEnabledCheck
                            checked: filterRow.rowEnabled
                            onToggled: filterModel.toggle_checked(filterRow.index)
                            Md3ToolTip {
                                theme: root.theme
                                visible: filterEnabledCheck.hovered
                                    && !root.theme.suppressToolTips
                                text: filterEnabledCheck.checked
                                    ? qsTr("Disable filter") : qsTr("Enable filter")
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: filterRow.isDefault ? 58 : 68
                            Layout.preferredHeight: 28
                            radius: 14
                            color: root.theme.secondaryContainer

                            Label {
                                anchors.centerIn: parent
                                text: filterRow.isDefault
                                    ? qsTr("WHERE") : filterRow.operator.toUpperCase()
                                color: root.theme.action
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                                font.weight: Font.Bold
                            }
                            MouseArea {
                                anchors.fill: parent
                                enabled: !filterRow.isDefault
                                cursorShape: enabled
                                    ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onClicked: filterModel.set_value(
                                    filterRow.index,
                                    "operator",
                                    filterRow.operator === "or" ? "and" : "or")
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            text: {
                                const row = root.columnIndex(filterRow.column)
                                return row >= 0
                                    ? filterColumnModel.get(row).label : ""
                            }
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.body
                            elide: Text.ElideRight
                        }

                        CompactIconButton {
                            theme: root.theme
                            iconName: filterRow.isDefault ? "add" : "close"
                            round: true
                            toolTip: filterRow.isDefault
                                ? qsTr("Add filter") : qsTr("Remove filter")
                            onClicked: {
                                if (filterRow.isDefault)
                                    appController.add_search_filter()
                                else
                                    filterModel.remove(filterRow.index)
                            }
                        }
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: filterRow.compact ? 1 : 3
                        columnSpacing: 8
                        rowSpacing: 7

                        Md3ComboBox {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            Layout.preferredWidth: filterRow.compact
                                ? filterRow.width - 20
                                : filterRow.width * 0.34
                            Layout.preferredHeight: root.theme.controlHeight
                            theme: root.theme
                            enabled: filterRow.rowEnabled
                            model: filterColumnModel
                            textRole: "label"
                            valueRole: "value"
                            // Column labels come from the active TACTIC
                            // Search Type schema and are project data.
                            translateDisplayText: false
                            currentIndex: root.columnIndex(filterRow.column)
                            onActivated:
                                appController.set_search_filter_column(
                                    filterRow.index, currentValue)
                        }

                        Md3ComboBox {
                            Layout.fillWidth: true
                            Layout.preferredWidth: filterRow.compact
                                ? filterRow.width - 20
                                : filterRow.width * 0.24
                            Layout.minimumWidth: 0
                            Layout.preferredHeight: root.theme.controlHeight
                            theme: root.theme
                            enabled: filterRow.rowEnabled
                            model: filterRow.relationChoices
                            textRole: "label"
                            valueRole: "value"
                            currentIndex: filterRow.relationIndex(
                                filterRow.relation)
                            onActivated: filterModel.set_value(
                                filterRow.index, "relation", currentValue)
                        }

                        Md3TextField {
                            theme: root.theme
                            id: valueField
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            Layout.preferredHeight: root.theme.controlHeight
                            enabled: filterRow.rowEnabled
                            text: filterRow.value === null
                                || filterRow.value === undefined
                                ? "" : String(filterRow.value)
                            placeholderText: filterRow.column === "_expression"
                                ? qsTr("TACTIC expression") : qsTr("Value")
                            onTextEdited: filterSuggestionTimer.restart()
                            onActiveFocusChanged: {
                                if (!activeFocus)
                                    filterSuggestionCloseTimer.restart()
                            }
                            onEditingFinished: filterModel.set_value(
                                filterRow.index, "value", text)
                            Keys.onReturnPressed: {
                                filterModel.set_value(
                                    filterRow.index, "value", text)
                                appController.apply_search_filters()
                            }
                        }
                    }
                }

                Timer {
                    id: filterSuggestionTimer
                    interval: 180
                    onTriggered:
                        appController.request_advanced_filter_suggestions(
                            filterRow.index,
                            filterRow.column,
                            valueField.text)
                }
                Timer {
                    id: filterSuggestionCloseTimer
                    interval: 140
                    onTriggered: {
                        if (!valueField.activeFocus
                                && !filterSuggestionPopup.hovered)
                            filterSuggestionPopup.close()
                    }
                }
                Md3Popup {
                    id: filterSuggestionPopup
                    theme: root.theme
                    parent: Overlay.overlay
                    padding: 4
                    modal: false
                    focus: false
                    closePolicy: Popup.NoAutoClose
                    width: Math.max(190, valueField.width)
                    height: Math.min(
                        7, advancedFilterSuggestionModel.count()) * 34 + 8
                    property bool hovered: filterPopupHover.hovered

                    function reposition() {
                        const point = valueField.mapToItem(
                            parent, 0, valueField.height + 4)
                        x = Math.max(4, Math.min(
                            parent.width - width - 4, point.x))
                        y = Math.max(4, Math.min(
                            parent.height - height - 4, point.y))
                    }

                    onAboutToShow: reposition()
                    HoverHandler { id: filterPopupHover }
                    contentItem: ListView {
                        id: advancedSuggestionList
                        clip: true
                        model: advancedFilterSuggestionModel
                        boundsBehavior: Flickable.StopAtBounds
                        delegate: Rectangle {
                            id: advancedSuggestionRow
                            required property int index
                            required property string title
                            required property string description
                            required property string keyword
                            width: advancedSuggestionList.width
                            height: 34
                            radius: root.theme.itemRadius
                            color: advancedSuggestionMouse.containsMouse
                                ? root.theme.secondaryContainer
                                : "transparent"
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 7
                                MaterialIcon {
                                    name: "search"
                                    size: 14
                                    color: root.theme.secondaryText
                                }
                                Label {
                                    Layout.preferredWidth: Math.min(
                                        150, implicitWidth)
                                    text: advancedSuggestionRow.title
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.body
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: advancedSuggestionRow.description
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.label
                                    elide: Text.ElideRight
                                }
                                Label {
                                    visible:
                                        advancedSuggestionRow.keyword.length > 0
                                    text: qsTr("#") + advancedSuggestionRow.keyword
                                    color: root.theme.action
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.label
                                    font.weight: Font.DemiBold
                                }
                            }
                            MouseArea {
                                id: advancedSuggestionMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    appController
                                        .accept_advanced_filter_suggestion(
                                            filterRow.index,
                                            advancedSuggestionRow.index)
                                    filterSuggestionPopup.close()
                                    valueField.forceActiveFocus()
                                }
                            }
                        }
                        ScrollBar.vertical: Md3ScrollBar {
                            theme: root.theme
                            flickableTarget: advancedSuggestionList
                        }
                    }
                }
                Connections {
                    target: advancedFilterSuggestionModel
                    function onContentReplaced() {
                        if (
                            appController.advanced_filter_suggestion_row
                                === filterRow.index
                            && valueField.activeFocus
                            && advancedFilterSuggestionModel.count() > 0
                        ) {
                            filterSuggestionPopup.reposition()
                            filterSuggestionPopup.open()
                        } else {
                            filterSuggestionPopup.close()
                        }
                    }
                }
            }

            }
        }

        Rectangle {
            width: parent.width
            height: 68
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainerHigh

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 12
                spacing: 10

                MaterialIcon {
                    name: "tab"
                    size: 18
                    color: root.theme.action
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 3

                    Label {
                        text: qsTr("Search tab name")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.label
                    }
                    Md3TextField {
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.preferredHeight: root.theme.controlHeight
                        text: appController.current_search_tab_title
                        onEditingFinished:
                            appController.set_search_tab_title(text)
                    }
                }

            }
        }

        }

        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            flickableTarget: searchFlickable
        }
    }

    ActionMenu {
        id: presetActions
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {
                "title": "Saved search actions",
                "header": true
            },
            {
                "title": "Rename preset",
                "icon": "rename",
                "command": "rename",
                "enabled": root.hasSelectedPreset
                    && !filterEditorController.busy
            },
            {
                "title": "Duplicate preset",
                "icon": "duplicate",
                "command": "duplicate",
                "enabled": root.hasSelectedPreset
                    && !filterEditorController.busy
            },
            {
                "title": "Delete preset",
                "icon": "delete",
                "command": "delete",
                "enabled": root.hasSelectedPreset
                    && !filterEditorController.busy
            },
            {"separator": true},
            {
                "title": "Refresh saved searches",
                "icon": "refresh",
                "command": "refresh",
                "enabled": !filterEditorController.busy
            }
        ]
        onTriggered: command => {
            if (command === "rename")
                root.openPresetDialog("rename")
            else if (command === "duplicate")
                root.openPresetDialog("duplicate")
            else if (command === "delete")
                deleteDialog.open()
            else if (command === "refresh")
                filterEditorController.begin_search_session()
        }
    }

    Md3Dialog {
        id: presetDialog
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(390, root.width - 24)
        modal: true
        title: root.presetAction === "rename" ? qsTr("Rename preset")
            : root.presetAction === "duplicate" ? qsTr("Duplicate preset")
            : qsTr("Save filter preset")
        onAccepted: {
            if (root.presetAction === "rename")
                filterEditorController.rename(presetName.text)
            else if (root.presetAction === "duplicate")
                filterEditorController.duplicate_current_search(presetName.text)
            else
                filterEditorController.save_current_search_as(presetName.text)
        }
        contentItem: Md3TextField {
            id: presetName
            theme: root.theme
            width: Math.max(220, presetDialog.width - 48)
            placeholderText: qsTr("Preset name")
            Keys.onReturnPressed: presetDialog.accept()
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Save")
                highlighted: true
                enabled: presetName.text.trim().length > 0
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }

    Md3Dialog {
        id: deleteDialog
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(390, root.width - 24)
        modal: true
        title: qsTr("Delete saved filter?")
        onAccepted: filterEditorController.delete_selected()
        contentItem: Label {
            width: Math.max(220, deleteDialog.width - 48)
            text: qsTr("The preset will be removed from the TACTIC server.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Delete")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }
}
