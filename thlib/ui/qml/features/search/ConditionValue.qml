import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/search/conditions.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var application
    required property var recordsModel
    required property var suggestions
    required property int index
    required property string column
    required property var value
    property bool rowEnabled: true
    property bool presentationActive: true
    onPresentationActiveChanged: {
        if (!presentationActive) {
            filterSuggestionTimer.stop();
            filterSuggestionCloseTimer.stop();
            filterSuggestionPopup.close();
            if (application.advanced_filter_suggestion_row === index)
                application.clear_advanced_filter_suggestions();
        }
    }
    Controls.TextField {
        id: valueField
        theme: root.theme
        anchors.fill: parent

        enabled: root.rowEnabled && root.presentationActive
        text: root.value === null || root.value === undefined ? "" : String(root.value)
        placeholderText: root.column === "_expression" ? qsTr("TACTIC expression") : qsTr("Value")
        onTextEdited: filterSuggestionTimer.restart()
        onActiveFocusChanged: {
            if (!activeFocus)
                filterSuggestionCloseTimer.restart();
        }
        onEditingFinished: root.recordsModel.set_value(root.index, "value", text)
        Keys.onDownPressed: {
            if (filterSuggestionPopup.opened && root.suggestions.count() > 0)
                advancedSuggestionList.currentIndex = (advancedSuggestionList.currentIndex + 1) % root.suggestions.count();
        }
        Keys.onUpPressed: {
            if (filterSuggestionPopup.opened && root.suggestions.count() > 0)
                advancedSuggestionList.currentIndex = (advancedSuggestionList.currentIndex - 1 + root.suggestions.count()) % root.suggestions.count();
        }
        Keys.onReturnPressed: {
            if (filterSuggestionPopup.opened && advancedSuggestionList.currentIndex >= 0) {
                root.application.accept_advanced_filter_suggestion(root.index, advancedSuggestionList.currentIndex);
                filterSuggestionPopup.close();
                return;
            }
            root.recordsModel.set_value(root.index, "value", text);
            root.application.apply_search_filters();
        }
    }

    Timer {
        id: filterSuggestionTimer
        interval: 180
        onTriggered: {
            if (root.presentationActive && valueField.enabled)
                root.application.request_advanced_filter_suggestions(root.index, root.column, valueField.text);
        }
    }

    Timer {
        id: filterSuggestionCloseTimer
        interval: 140
        onTriggered: {
            if (!valueField.activeFocus && !filterSuggestionPopup.hovered)
                filterSuggestionPopup.close();
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
        height: Math.min(7, root.suggestions.count()) * 34 + 8
        property bool hovered: filterPopupHover.hovered

        function reposition() {
            preparePositionAtItem(valueField, 0, valueField.height + 4);
        }

        onAboutToShow: {
            advancedSuggestionList.currentIndex = -1;
            reposition();
        }
        HoverHandler {
            id: filterPopupHover
        }
        contentItem: ListView {
            id: advancedSuggestionList
            clip: true
            model: root.suggestions
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
                leftPadding: 0
                rightPadding: 0
                Accessible.name: title
                onClicked: {
                    root.application.accept_advanced_filter_suggestion(root.index, advancedSuggestionRow.index);
                    filterSuggestionPopup.close();
                    valueField.forceActiveFocus();
                }
                background: Rectangle {
                    radius: root.theme.itemRadius
                    color: advancedSuggestionRow.down ? root.theme.surfaceContainerHighest : (advancedSuggestionRow.hovered || advancedSuggestionList.currentIndex === advancedSuggestionRow.index) ? root.theme.secondaryContainer : "transparent"
                }
                TextMetrics {
                    id: titleMetrics
                    text: advancedSuggestionRow.title
                    font.family: root.theme.fontFamily
                    font.hintingPreference: Font.PreferVerticalHinting
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }
                TextMetrics {
                    id: keywordMetrics
                    text: "#" + advancedSuggestionRow.keyword
                    font.family: root.theme.fontFamily
                    font.hintingPreference: Font.PreferVerticalHinting
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
                contentItem: Frame.FrameView {
                    theme: root.theme
                    interactive: false
                    scene: UI.suggestion({
                        title: advancedSuggestionRow.title,
                        description: advancedSuggestionRow.description,
                        keyword: advancedSuggestionRow.keyword,
                        titleWidth: titleMetrics.advanceWidth,
                        keywordWidth: keywordMetrics.advanceWidth
                    }, width)
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: advancedSuggestionList
            }
        }
    }

    Connections {
        target: root.suggestions
        enabled: root.presentationActive
        function onContentReplaced() {
            if (root.application.advanced_filter_suggestion_row === root.index && valueField.activeFocus && root.suggestions.count() > 0) {
                if (!filterSuggestionPopup.opened) {
                    filterSuggestionPopup.reposition();
                    filterSuggestionPopup.open();
                }
            } else {
                filterSuggestionPopup.close();
            }
        }
    }
}
