import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

Item {
    id: root

    required property var theme
    property bool filtersExpanded: true
    property bool optionsExpanded: true

    function columnIndex(value) {
        for (let row = 0; row < filterColumnModel.count(); ++row) {
            if (filterColumnModel.get(row).value === value)
                return row
        }
        return -1
    }

    Component.onCompleted: appController.ensure_search_filter()

    Rectangle {
        anchors.fill: parent
        color: root.theme.surfaceContainerLow
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            radius: 14
            color: root.theme.surfaceContainerHigh

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 8
                spacing: 6

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
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
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
            MouseArea {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.rightMargin: 72
                cursorShape: Qt.PointingHandCursor
                onClicked: root.filtersExpanded = !root.filtersExpanded
            }
        }

        ListView {
            id: filtersList
            Layout.fillWidth: true
            Layout.fillHeight: root.filtersExpanded
            Layout.preferredHeight: root.filtersExpanded ? 180 : 0
            Layout.minimumHeight: root.filtersExpanded ? 96 : 0
            visible: root.filtersExpanded
            clip: true
            spacing: 7
            model: filterModel
            boundsBehavior: Flickable.StopAtBounds

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

                function relationIndex(value) {
                    for (let row = 0; row < relationChoices.length; ++row) {
                        if (relationChoices[row].value === value)
                            return row
                    }
                    return -1
                }

                width: filtersList.width
                height: 118
                radius: 14
                color: root.theme.surfaceContainerHigh
                border.width: 1
                border.color: root.theme.outlineVariant
                opacity: rowEnabled ? 1 : 0.58
                Behavior on opacity { NumberAnimation { duration: 120 } }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    anchors.topMargin: 7
                    anchors.bottomMargin: 7
                    spacing: 5

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

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
                                font.pixelSize: 9
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

                        Item { Layout.fillWidth: true }

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

                    Md3ComboBox {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.preferredHeight: 30
                        theme: root.theme
                        enabled: filterRow.rowEnabled
                        model: filterColumnModel
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: root.columnIndex(filterRow.column)
                        onActivated: appController.set_search_filter_column(
                            filterRow.index, currentValue)
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Md3ComboBox {
                            Layout.preferredWidth: Math.min(
                                154, Math.max(88, filterRow.width * 0.38))
                            Layout.minimumWidth: 0
                            Layout.preferredHeight: 30
                            theme: root.theme
                            enabled: filterRow.rowEnabled
                            model: filterRow.relationChoices
                            textRole: "label"
                            valueRole: "value"
                            currentIndex: filterRow.relationIndex(
                                filterRow.relation)
                            font.pixelSize: 9
                            onActivated: filterModel.set_value(
                                filterRow.index, "relation", currentValue)
                        }

                        Md3TextField {
                            theme: root.theme
                            id: valueField
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            Layout.preferredHeight: 30
                            enabled: filterRow.rowEnabled
                            text: filterRow.value === null
                                || filterRow.value === undefined
                                ? "" : String(filterRow.value)
                            placeholderText: filterRow.column === "_expression"
                                ? qsTr("TACTIC expression") : qsTr("Value")
                            color: root.theme.primaryText
                            placeholderTextColor: root.theme.secondaryText
                            selectionColor: root.theme.action
                            font.family: root.theme.fontFamily
                            font.pixelSize: 10
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
                            background: Rectangle {
                                radius: 9
                                color: root.theme.surfaceContainerLow
                                border.width: parent.activeFocus ? 2 : 1
                                border.color: parent.activeFocus
                                    ? root.theme.action : root.theme.outline
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
                                    font.pixelSize: 10
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: advancedSuggestionRow.description
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 9
                                    elide: Text.ElideRight
                                }
                                Label {
                                    visible:
                                        advancedSuggestionRow.keyword.length > 0
                                    text: qsTr("#") + advancedSuggestionRow.keyword
                                    color: root.theme.action
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 9
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

            ScrollBar.vertical: Md3ScrollBar {
                theme: root.theme
                flickableTarget: filtersList
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: root.optionsExpanded ? 116 : 46
            radius: 14
            color: root.theme.surfaceContainerHigh
            clip: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 46

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 10
                        spacing: 7
                        MaterialIcon {
                            name: root.optionsExpanded
                                ? "keyboard_arrow_down"
                                : "keyboard_arrow_right"
                            size: 18
                            color: root.theme.secondaryText
                        }
                        MaterialIcon {
                            name: "tune"
                            size: 17
                            color: root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Search Options")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked:
                            root.optionsExpanded = !root.optionsExpanded
                    }
                }

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: root.optionsExpanded ? 70 : 0
                    visible: root.optionsExpanded
                    clip: true

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        anchors.bottomMargin: 10
                        spacing: 4

                        Label {
                            text: qsTr("Search tab name")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 9
                        }
                        Md3TextField {
                            theme: root.theme
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            Layout.preferredHeight: 36
                            text: appController.current_search_tab_title
                            color: root.theme.primaryText
                            selectionColor: root.theme.action
                            font.family: root.theme.fontFamily
                            font.pixelSize: 11
                            onEditingFinished:
                                appController.set_search_tab_title(text)
                            background: Rectangle {
                                radius: 10
                                color: root.theme.surfaceContainerLow
                                border.width: parent.activeFocus ? 2 : 1
                                border.color: parent.activeFocus
                                    ? root.theme.action : root.theme.outline
                            }
                        }
                    }
                }
            }
        }

        Md3Button {
            Layout.alignment: Qt.AlignRight
            Layout.preferredWidth: 132
            Layout.preferredHeight: 40
            theme: root.theme
            highlighted: true
            enabled: appController.search_state !== "loading"
            text: appController.search_state === "loading"
                ? qsTr("Searching...") : qsTr("Apply filters")
            icon.name: appController.search_state === "loading"
                ? "hourglass_empty" : "search"
            onClicked: appController.apply_search_filters()

        }
    }
}
