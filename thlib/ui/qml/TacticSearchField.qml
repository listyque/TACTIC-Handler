import QtQuick
import "controls" as Controls

Item {
    id: root
    required property var theme
    required property var suggestionModel
    required property var controller
    property alias text: searchInput.text
    readonly property bool popupOpen: searchInput.popupOpen
    property bool openSuggestionsInNewTab: false
    property string placeholderText: qsTr("Search")

    implicitHeight: 38
    implicitWidth: 360
    function positionPopup() {
        searchInput.positionSuggestions();
    }
    function showSuggestions() {
        searchInput.showSuggestions();
    }
    function hideSuggestions() {
        searchInput.hideSuggestions();
    }
    function beginSearchInput() {
        searchInput.forceActiveFocus(Qt.MouseFocusReason);
        searchInput.selectAll();
        Qt.inputMethod.show();
    }
    function acceptCurrentSuggestion() {
        return searchInput.acceptCurrentSuggestion();
    }
    function acceptSuggestion(index, title) {
        suggestionTimer.stop();
        searchInput.text = title;
        hideSuggestions();
        searchInput.forceActiveFocus(Qt.MouseFocusReason);
        controller.accept_search_suggestion(index);
    }

    Controls.SearchField {
        id: searchInput
        objectName: "tacticSearchInput"
        anchors.fill: parent
        theme: root.theme
        searchIconObjectName: "tacticSearchIcon"
        suggestionObjectNamePrefix: "tacticSearchSuggestion"
        clearOnEscape: false
        placeholderText: root.placeholderText
        suggestions: root.suggestionModel
        openSuggestionsInNewTab: root.openSuggestionsInNewTab
        onSearchEdited: query => {
            root.controller.update_search_text(query);
            suggestionTimer.restart();
        }
        onCleared: {
            suggestionTimer.stop();
            root.controller.clear_search_suggestions();
            root.hideSuggestions();
        }
        onDismissed: {
            suggestionTimer.stop();
            root.controller.clear_search_suggestions();
        }
        onSearchRequested: {
            suggestionTimer.stop();
            root.controller.search(text);
        }
        onSuggestionAccepted: (index, record) => root.acceptSuggestion(index, record.title)
        onSuggestionOpened: (index, record) => {
            suggestionTimer.stop();
            root.controller.open_search_suggestion_in_new_tab(index);
        }
        onSuggestionHighlighted: index => root.suggestionModel.select_row(index)
    }
    Timer {
        id: suggestionTimer
        interval: 180
        onTriggered: root.controller.request_search_suggestions(searchInput.text)
    }
    Connections {
        target: root.controller
        function onSearch_text_changed() {
            if (searchInput.text !== root.controller.current_search_text)
                searchInput.text = root.controller.current_search_text;
        }
    }
    Connections {
        target: root.suggestionModel
        function onContentReplaced() {
            Qt.callLater(root.showSuggestions);
        }
    }
    Component.onCompleted: {
        searchInput.background.objectName = "tacticSearchBackground";
        searchInput.text = root.controller.current_search_text;
    }
}
