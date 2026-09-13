import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    required property var suggestionModel
    required property var controller
    property alias text: searchInput.text
    property bool popupOpen: suggestionsPopup.visible
    property bool openSuggestionsInNewTab: false
    property string placeholderText: qsTr("Search")

    implicitHeight: 38
    implicitWidth: 360

    function positionPopup() {
        if (!suggestionsPopup.parent)
            return
        suggestionsPopup.width = root.width
        suggestionsPopup.preparePositionAtItem(root, 0, root.height + 6)
    }

    function showSuggestions() {
        if (!searchInput.activeFocus || suggestionList.count < 1)
            return
        if (!suggestionsPopup.visible) {
            positionPopup()
            suggestionsPopup.open()
        }
    }

    function hideSuggestions() {
        suggestionsPopup.close()
        suggestionList.currentIndex = -1
    }

    function beginSearchInput() {
        searchInput.forceActiveFocus(Qt.MouseFocusReason)
        searchInput.selectAll()
        Qt.inputMethod.show()
    }

    function acceptCurrentSuggestion() {
        if (suggestionList.currentIndex < 0 || suggestionList.currentIndex >= suggestionList.count)
            return false
        suggestionTimer.stop()
        const delegateItem = suggestionList.itemAtIndex(suggestionList.currentIndex)
        if (delegateItem)
            searchInput.text = delegateItem.suggestionTitle
        const suggestionIndex = suggestionList.currentIndex
        hideSuggestions()
        searchInput.forceActiveFocus(Qt.MouseFocusReason)
        controller.accept_search_suggestion(suggestionIndex)
        return true
    }

    function acceptSuggestion(index, title) {
        suggestionTimer.stop()
        searchInput.text = title
        hideSuggestions()
        searchInput.forceActiveFocus(Qt.MouseFocusReason)
        // Accept last: the controller may synchronously replace the model and
        // destroy the delegate that initiated this call.
        controller.accept_search_suggestion(index)
    }

    Controls.SearchField {
        id: searchInput
        objectName: "tacticSearchInput"
        anchors.fill: parent
        theme: root.theme
        searchIconObjectName: "tacticSearchIcon"
        clearOnEscape: false
        placeholderText: root.placeholderText
        verticalAlignment: Text.AlignVCenter

        onSearchEdited: query => {
            root.controller.update_search_text(query)
            suggestionTimer.restart()
        }
        onCleared: {
            suggestionTimer.stop()
            root.controller.clear_search_suggestions()
            root.hideSuggestions()
        }
        onActiveFocusChanged: {
            if (activeFocus) {
                if (root.suggestionModel.count() > 0)
                    root.showSuggestions()
            } else {
                focusCloseTimer.restart()
            }
        }
        Keys.onPressed: function(event) {
            if (event.key === Qt.Key_Escape) {
                root.controller.clear_search_suggestions()
                root.hideSuggestions()
                event.accepted = true
            } else if (event.key === Qt.Key_Down && suggestionsPopup.visible) {
                suggestionList.currentIndex = Math.min(
                    suggestionList.count - 1,
                    suggestionList.currentIndex + 1
                )
                suggestionList.positionViewAtIndex(suggestionList.currentIndex, ListView.Contain)
                root.suggestionModel.select_row(suggestionList.currentIndex)
                event.accepted = true
            } else if (event.key === Qt.Key_Up && suggestionsPopup.visible) {
                suggestionList.currentIndex = suggestionList.currentIndex <= 0
                    ? suggestionList.count - 1 : suggestionList.currentIndex - 1
                suggestionList.positionViewAtIndex(suggestionList.currentIndex, ListView.Contain)
                root.suggestionModel.select_row(suggestionList.currentIndex)
                event.accepted = true
            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                suggestionTimer.stop()
                if (!root.acceptCurrentSuggestion()) {
                    root.controller.search(text)
                    root.hideSuggestions()
                }
                event.accepted = true
            }
        }
    }

    HoverHandler {
        id: fieldHover
        objectName: "tacticSearchCursorHandler"
        cursorShape: Qt.IBeamCursor
    }
    Controls.ToolTip {
        theme: root.theme
        visible: fieldHover.hovered && !root.popupOpen && !root.theme.suppressToolTips
        delay: 650
        text: root.placeholderText
    }

    Timer {
        id: suggestionTimer
        interval: 180
        onTriggered: root.controller.request_search_suggestions(searchInput.text)
    }
    Timer {
        id: focusCloseTimer
        interval: 120
        onTriggered: {
            if (!searchInput.activeFocus && !suggestionsPopup.hovered)
                root.hideSuggestions()
        }
    }

    Controls.Popup {
        id: suggestionsPopup
        objectName: "tacticSearchSuggestionsPopup"
        theme: root.theme
        parent: Overlay.overlay
        padding: 4
        modal: false
        focus: false
        settledClosePolicy: Popup.NoAutoClose
        height: Math.min(20, suggestionList.count) * 34 + topPadding + bottomPadding

        property bool hovered: popupHover.hovered

        contentItem: ListView {
            id: suggestionList
            objectName: "tacticSearchSuggestionList"
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: root.suggestionModel
            currentIndex: -1
            onCountChanged: {
                if (count > 0)
                    root.showSuggestions()
                else
                    root.hideSuggestions()
            }
            delegate: Controls.PopupAction {
                id: suggestionRow
                objectName: "tacticSearchSuggestionRow_" + index
                required property int index
                required property string title
                required property string description
                required property string keyword
                required property string code
                required property bool selected
                property string suggestionTitle: title
                width: suggestionList.width
                height: 34
                hoverEnabled: true
                leftPadding: 8
                rightPadding: 10
                Accessible.name: title

                function acceptSuggestion() {
                    root.acceptSuggestion(
                        suggestionRow.index, suggestionRow.title)
                }

                function openInNewTab() {
                    suggestionTimer.stop()
                    root.controller.open_search_suggestion_in_new_tab(
                        suggestionRow.index)
                }

                background: Rectangle {
                    color: suggestionRow.index === suggestionList.currentIndex
                        ? root.theme.selected
                        : suggestionRow.down
                            ? root.theme.surfaceContainerHighest
                            : suggestionRow.hovered
                            ? root.theme.rowHover
                            : suggestionRow.index % 2
                                ? root.theme.panelRaised : root.theme.row
                }
                contentItem: RowLayout {
                    spacing: 9
                    Controls.MaterialIcon {
                        name: "search"
                        size: 17
                        color: root.theme.secondaryText
                    }
                    Label {
                        Layout.preferredWidth: Math.min(190, Math.max(90, implicitWidth))
                        text: suggestionRow.title
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: suggestionRow.description.length > 0
                            ? "– " + suggestionRow.description : ""
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        elide: Text.ElideRight
                    }
                    Rectangle {
                        visible: suggestionRow.keyword.length > 0
                        Layout.preferredWidth: visible
                            ? keywordLabel.implicitWidth + 12 : 0
                        Layout.preferredHeight: 24
                        radius: 12
                        color: "transparent"
                        Label {
                            id: keywordLabel
                            anchors.centerIn: parent
                            text: qsTr("#") + suggestionRow.keyword
                            color: root.theme.action
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                    }
                }
                onPressedChanged: {
                    if (pressed)
                        suggestionRipple.burst(width / 2, height / 2)
                }
                onHoveredChanged: {
                    if (!hovered)
                        return
                    suggestionList.currentIndex = suggestionRow.index
                    root.suggestionModel.select_row(suggestionRow.index)
                }
                onClicked: suggestionRow.acceptSuggestion()
                TapHandler {
                    enabled: root.openSuggestionsInNewTab
                    acceptedButtons: Qt.MiddleButton
                    gesturePolicy: TapHandler.DragThreshold
                    onTapped: suggestionRow.openInNewTab()
                }
                Controls.MaterialRipple {
                    id: suggestionRipple
                    theme: root.theme
                    color: root.theme.ripple
                    shapeRadius: 6
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }
        }
        HoverHandler { id: popupHover }
    }

    Connections {
        target: root.controller
        function onSearch_text_changed() {
            if (searchInput.text !== root.controller.current_search_text)
                searchInput.text = root.controller.current_search_text
        }
    }
    Connections {
        target: root.suggestionModel
        function onContentReplaced() {
            Qt.callLater(function() {
                if (root.suggestionModel.count() > 0)
                    root.showSuggestions()
                else
                    root.hideSuggestions()
            })
        }
    }
    Connections {
        target: root
        function onWidthChanged() {
            suggestionsPopup.width = root.width
        }
    }
    Component.onCompleted: {
        searchInput.background.objectName = "tacticSearchBackground"
        searchInput.text = root.controller.current_search_text
    }
}
