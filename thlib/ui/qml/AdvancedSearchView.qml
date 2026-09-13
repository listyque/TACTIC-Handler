import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property bool presentationActive:
        parent ? parent.visible : visible
    property bool filtersExpanded: true
    readonly property bool compactLayout: width < 560


    function columnIndex(value) {
        for (let row = 0; row < filterColumnModel.count(); ++row) {
            if (filterColumnModel.get(row).value === value)
                return row
        }
        return -1
    }

    function reloadPresetsForCurrentSearch() {
        if (!root.presentationActive)
            return
        Qt.callLater(function() {
            if (!root.presentationActive)
                return
            filterEditorController.sync_search_session()
        })
    }

    Component.onCompleted: reloadPresetsForCurrentSearch()

    onPresentationActiveChanged: reloadPresetsForCurrentSearch()

    Connections {
        target: appController
        enabled: root.presentationActive
        function onProject_changed() {
            root.reloadPresetsForCurrentSearch()
        }
        function onSection_state_changed() {
            root.reloadPresetsForCurrentSearch()
        }
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
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
            width: Math.max(0, searchFlickable.width - 20 - searchScrollBar.reservedExtent)
            spacing: 10

        SearchPresetBar {
            width: parent.width
            theme: root.theme
            controller: filterEditorController
            application: appController
            presets: filterPresetModel
        }

        Rectangle {
            width: parent.width
            height: 50
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainerHigh

            Controls.ActivationHandler {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onActivated: root.filtersExpanded = !root.filtersExpanded
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8

                Controls.MaterialIcon {
                    name: root.filtersExpanded
                        ? "keyboard_arrow_down" : "keyboard_arrow_right"
                    size: 18
                    color: root.theme.secondaryText
                }
                Controls.MaterialIcon {
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
                Controls.Button {
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
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "add"
                    round: true
                    toolTip: qsTr("Add filter")
                    onClicked: appController.add_search_filter()
                }
                Controls.CompactIconButton {
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
                required property var generatedFilterKind
                required property var generatedFilterState

                readonly property var relationChoices:
                    appController.search_filter_relations(column)
                readonly property bool compact: root.compactLayout
                readonly property bool generatedQuickFilter:
                    generatedFilterKind === "quick_filters"

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
                Behavior on opacity { NumberAnimation { duration: theme.motionFast } }

                ColumnLayout {
                    id: filterContent
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 7

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Controls.CheckBox {
                            theme: root.theme
                            id: filterEnabledCheck
                            visible: !filterRow.generatedQuickFilter
                            checked: filterRow.rowEnabled
                            onToggled: filterModel.toggle_checked(filterRow.index)
                            Controls.ToolTip {
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
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.Bold
                            }
                            Controls.ActivationHandler {
                                anchors.fill: parent
                                enabled: !filterRow.isDefault
                                    && !filterRow.generatedQuickFilter
                                cursorShape: enabled
                                    ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onActivated: filterModel.set_value(
                                    filterRow.index,
                                    "operator",
                                    filterRow.operator === "or" ? "and" : "or")
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            text: {
                                if (filterRow.generatedQuickFilter) {
                                    const state = filterRow.generatedFilterState || ({})
                                    const title = String(
                                        state.title || "Quick filter"
                                    )
                                    return state.translatable
                                        ? qsTr(title) : title
                                }
                                const row = root.columnIndex(filterRow.column)
                                return row >= 0
                                    ? filterColumnModel.get(row).label : ""
                            }
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            elide: Text.ElideRight
                        }

                        Controls.CompactIconButton {
                            visible: filterRow.generatedQuickFilter
                            theme: root.theme
                            iconName: "edit"
                            round: true
                            toolTip: qsTr("Edit as custom filter")
                            onClicked:
                                appController.detach_generated_search_filter(
                                    filterRow.index)
                        }

                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: filterRow.generatedQuickFilter
                                ? "close"
                                : filterRow.isDefault ? "add" : "close"
                            round: true
                            toolTip: filterRow.generatedQuickFilter
                                ? qsTr("Remove quick filter")
                                : filterRow.isDefault
                                ? qsTr("Add filter") : qsTr("Remove filter")
                            onClicked: {
                                if (filterRow.generatedQuickFilter)
                                    filterModel.remove(filterRow.index)
                                else if (filterRow.isDefault)
                                    appController.add_search_filter()
                                else
                                    filterModel.remove(filterRow.index)
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        visible: filterRow.generatedQuickFilter
                        spacing: 8

                        Controls.MaterialIcon {
                            name: "filter_alt"
                            size: 17
                            color: root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Managed by Quick Filters")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            wrapMode: Text.WordWrap
                        }
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        visible: !filterRow.generatedQuickFilter
                        columns: filterRow.compact ? 1 : 3
                        columnSpacing: 8
                        rowSpacing: 7

                        Controls.ComboBox {
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

                        Controls.ComboBox {
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

                        Controls.TextField {
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
                Controls.Popup {
                    id: filterSuggestionPopup
                    theme: root.theme
                    parent: Overlay.overlay
                    padding: 4
                    modal: false
                    focus: false
                    settledClosePolicy: Popup.NoAutoClose
                    width: Math.max(190, valueField.width)
                    height: Math.min(
                        7, advancedFilterSuggestionModel.count()) * 34 + 8
                    property bool hovered: filterPopupHover.hovered

                    function reposition() {
                        preparePositionAtItem(
                            valueField, 0, valueField.height + 4)
                    }

                    onAboutToShow: reposition()
                    HoverHandler { id: filterPopupHover }
                    contentItem: ListView {
                        id: advancedSuggestionList
                        clip: true
                        model: advancedFilterSuggestionModel
                        boundsBehavior: Flickable.StopAtBounds
                        delegate: Controls.PopupAction {
                            id: advancedSuggestionRow
                            required property int index
                            required property string title
                            required property string description
                            required property string keyword
                            width: advancedSuggestionList.width
                            height: 34
                            hoverEnabled: true
                            leftPadding: 8
                            rightPadding: 8
                            Accessible.name: title
                            onClicked: {
                                appController
                                    .accept_advanced_filter_suggestion(
                                        filterRow.index,
                                        advancedSuggestionRow.index)
                                filterSuggestionPopup.close()
                                valueField.forceActiveFocus()
                            }
                            background: Rectangle {
                                radius: root.theme.itemRadius
                                color: advancedSuggestionRow.down
                                    ? root.theme.surfaceContainerHighest
                                    : advancedSuggestionRow.hovered
                                        ? root.theme.secondaryContainer
                                        : "transparent"
                            }
                            contentItem: RowLayout {
                                spacing: 7
                                Controls.MaterialIcon {
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
                                    font.pointSize: Controls.Typography.body
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: advancedSuggestionRow.description
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    elide: Text.ElideRight
                                }
                                Label {
                                    visible:
                                        advancedSuggestionRow.keyword.length > 0
                                    text: qsTr("#") + advancedSuggestionRow.keyword
                                    color: root.theme.action
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    font.weight: Font.DemiBold
                                }
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            theme: root.theme
                            flickableTarget: advancedSuggestionList
                        }
                    }
                }
                Connections {
                    target: advancedFilterSuggestionModel
                    enabled: root.presentationActive
                    function onContentReplaced() {
                        if (
                            appController.advanced_filter_suggestion_row
                                === filterRow.index
                            && valueField.activeFocus
                            && advancedFilterSuggestionModel.count() > 0
                        ) {
                            if (!filterSuggestionPopup.opened) {
                                filterSuggestionPopup.reposition()
                                filterSuggestionPopup.open()
                            }
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

                Controls.MaterialIcon {
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
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.TextField {
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

        ScrollBar.vertical: Controls.ScrollBar {
            id: searchScrollBar
            theme: root.theme
            flickableTarget: searchFlickable
        }
    }

}
