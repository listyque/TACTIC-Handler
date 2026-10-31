import QtQuick
import "../../controls" as Controls
import "../../tactic_frame/features/table/page.filters.mjs" as Filters
import "../../tactic_frame/core/strings.mjs" as Strings

Controls.SearchField {
    id: root
    required property var owner
    required property var definitions
    required property var values
    property string language: "en"
    property var records: []
    property int generation: 0
    signal applied(var values)
    objectName: "pageFilterSearch"
    placeholderText: Strings.translate("Search this page…", language)
    suggestionObjectNamePrefix: "pageFilterSuggestion"
    suggestionsUsePopupWindow: false
    readonly property var query: {
        try {
            return Filters.query(definitions, text);
        } catch (_) {
            return {
                text: text
            };
        }
    }
    highlightQuery: query.text
    suggestions: {
        try {
            return Filters.suggestions(definitions, text, records, language);
        } catch (_) {
            return [];
        }
    }
    function clearResults() {
        timer.stop();
        generation++;
        records = [];
        errorText = "";
    }
    function accept(result) {
        text = result.text;
        clearResults();
        if (result.apply)
            applied(Filters.values(definitions, result.draft));
        else {
            forceActiveFocus();
            timer.interval = 0;
            timer.restart();
        }
    }
    onSearchEdited: {
        clearResults();
        if (text.trim()) {
            timer.interval = 180;
            timer.restart();
        }
    }
    onDismissed: clearResults()
    onSuggestionAccepted: (index, record) => {
        try {
            accept(Filters.choose(definitions, values, suggestions[index]));
        } catch (error) {
            errorText = Strings.translate(String(error.message || error), language);
        }
    }
    onSearchRequested: {
        try {
            accept(Filters.submit(definitions, values, text, suggestions));
        } catch (error) {
            errorText = Strings.translate(String(error.message || error), language);
        }
    }
    Timer {
        id: timer
        onTriggered: {
            try {
                root.owner.request_filter_suggestions(Filters.query(root.definitions, root.text), String(root.generation));
            } catch (error) {
                root.errorText = Strings.translate(String(error.message || error), root.language);
            }
        }
    }
    Connections {
        target: root.owner
        ignoreUnknownSignals: true
        function onFilterSuggestionsReady(request, records, error) {
            if (request !== String(root.generation))
                return;
            root.records = records;
            root.errorText = Strings.translate(error, root.language);
        }
    }
    Component.onDestruction: generation++
}
