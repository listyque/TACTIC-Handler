import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "." as Controls

Controls.TextField {
    id: root

    property bool clearOnEscape: true
    property string searchIconObjectName: "searchFieldIcon"
    signal searchEdited(string query)
    signal cleared
    property var suggestions: null
    property string errorText: ""
    property bool openSuggestionsInNewTab: false
    property bool suggestionsUsePopupWindow: true
    property string suggestionObjectNamePrefix: "searchSuggestion"
    readonly property Controls.SearchSuggestionsPopup suggestionsPopup: suggestionLoader.item as Controls.SearchSuggestionsPopup
    readonly property bool popupOpen: !!root.suggestionsPopup && root.suggestionsPopup.visible
    signal suggestionAccepted(int index, var record)
    signal suggestionOpened(int index, var record)
    signal suggestionHighlighted(int index)
    signal searchRequested
    signal dismissed

    function hideSuggestions() {
        if (root.suggestionsPopup)
            root.suggestionsPopup.close();
    }
    function positionSuggestions() {
        const popup = root.suggestionsPopup;
        const owner = root.Window.window;
        if (!popup || !owner)
            return;
        const point = root.mapToItem(owner.contentItem, 0, 0);
        const desired = root.errorText.length ? 50 : popup.count * Foundation.controls.search.rowHeight + Foundation.controls.search.popupPadding * 2;
        const below = Math.max(0, owner.height - point.y - root.height - 10);
        const above = Math.max(0, point.y - 10);
        const up = below < Math.min(desired, 180) && above > below;
        popup.width = Math.min(Math.max(Foundation.controls.search.popupMinimumWidth, root.width), Math.max(0, owner.width - 8));
        popup.height = Math.min(desired, up ? above : below);
        popup.preparePositionAtItem(root, 0, up ? -popup.height - Foundation.controls.search.popupGap : root.height + Foundation.controls.search.popupGap);
    }
    function showSuggestions() {
        const popup = root.suggestionsPopup;
        if (!popup)
            return;
        if (!root.enabled || root.readOnly || !root.activeFocus || (!popup.count && !root.errorText.length)) {
            hideSuggestions();
            return;
        }
        positionSuggestions();
        if (!popup.visible)
            popup.open();
    }
    function acceptCurrentSuggestion() {
        return root.suggestionsPopup && root.suggestionsPopup.currentIndex >= 0 ? root.suggestionsPopup.choose(root.suggestionsPopup.currentIndex, false) : false;
    }
    onSuggestionsChanged: Qt.callLater(root.showSuggestions)
    onErrorTextChanged: Qt.callLater(root.showSuggestions)
    onEnabledChanged: if (!enabled)
        hideSuggestions()
    onReadOnlyChanged: if (readOnly)
        hideSuggestions()
    onActiveFocusChanged: if (activeFocus)
        showSuggestions()
    else
        focusCloseTimer.restart()
    onWidthChanged: if (popupOpen)
        positionSuggestions()
    onHeightChanged: if (popupOpen)
        positionSuggestions()

    Timer {
        id: focusCloseTimer
        interval: 120
        onTriggered: if (!root.activeFocus && root.suggestionsPopup && !root.suggestionsPopup.hovered)
            root.hideSuggestions()
    }
    Loader {
        id: suggestionLoader
        active: root.suggestions !== null || root.errorText.length > 0
        onLoaded: Qt.callLater(root.showSuggestions)
        sourceComponent: Controls.SearchSuggestionsPopup {
            theme: root.theme
            rows: root.suggestions || []
            namePrefix: root.suggestionObjectNamePrefix
            errorText: root.errorText
            openInNewTab: root.openSuggestionsInNewTab
            usePopupWindow: root.suggestionsUsePopupWindow
            parent: Overlay.overlay
            onCountChanged: Qt.callLater(root.showSuggestions)
            onAcceptedSuggestion: (index, record) => {
                root.forceActiveFocus();
                root.suggestionAccepted(index, record);
            }
            onOpenSuggestion: (index, record) => {
                root.forceActiveFocus();
                root.suggestionOpened(index, record);
            }
            onHighlighted: index => root.suggestionHighlighted(index)
        }
    }

    leftPadding: Foundation.controls.search.padding
    rightPadding: Foundation.controls.search.padding
    placeholderText: qsTr("Search")
    Accessible.name: placeholderText
    onTextEdited: {
        root.hideSuggestions();
        root.searchEdited(text);
    }

    function clearSearch() {
        if (!enabled || readOnly || text.length === 0)
            return;
        clear();
        searchEdited("");
        cleared();
        forceActiveFocus();
    }

    Keys.onPressed: event => {
        if (root.inputMethodComposing)
            return;
        if (event.key === Qt.Key_Escape) {
            if (root.clearOnEscape && !root.readOnly && root.text.length > 0)
                root.clearSearch();
            else {
                root.hideSuggestions();
                root.dismissed();
            }
            event.accepted = true;
        } else if (root.popupOpen && (event.key === Qt.Key_Down || event.key === Qt.Key_Up)) {
            root.suggestionsPopup.move(event.key === Qt.Key_Down ? 1 : -1);
            event.accepted = true;
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            if (root.popupOpen && root.suggestionsPopup.currentIndex >= 0)
                root.suggestionsPopup.choose(root.suggestionsPopup.currentIndex, !!(event.modifiers & Qt.AltModifier));
            else {
                root.hideSuggestions();
                root.searchRequested();
            }
            event.accepted = true;
        }
    }

    Controls.MaterialIcon {
        objectName: root.searchIconObjectName
        anchors.left: parent.left
        anchors.leftMargin: Foundation.controls.search.iconInset
        anchors.verticalCenter: parent.verticalCenter
        name: "search"
        size: Foundation.controls.search.iconSize
        color: root.activeFocus ? root.theme.action : root.theme.secondaryText
    }

    Controls.CompactIconButton {
        objectName: "searchFieldClear"
        anchors.right: parent.right
        anchors.rightMargin: Foundation.controls.search.clearInset
        anchors.verticalCenter: parent.verticalCenter
        width: Foundation.controls.search.clearExtent
        height: Foundation.controls.search.clearExtent
        theme: root.theme
        iconName: "close"
        iconSize: Foundation.controls.search.clearIconSize
        toolTip: qsTr("Clear search")
        visible: root.text.length > 0
        enabled: root.enabled && !root.readOnly
        onClicked: root.clearSearch()
    }
}
