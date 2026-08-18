import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

Item {
    id: root
    required property var theme
    required property var suggestionModel
    required property var controller
    property alias text: searchInput.text
    property bool popupOpen: suggestionsPopup.visible
    property string placeholderText: qsTr("Search")

    implicitHeight: 38
    implicitWidth: 360

    function positionPopup() {
        if (!suggestionsPopup.parent)
            return
        const point = root.mapToItem(suggestionsPopup.parent, 0, root.height)
        suggestionsPopup.x = point.x
        suggestionsPopup.y = point.y + 6
        suggestionsPopup.width = root.width
    }

    function showSuggestions() {
        if (!searchInput.activeFocus || suggestionList.count < 1)
            return
        positionPopup()
        if (!suggestionsPopup.visible)
            suggestionsPopup.open()
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
        controller.accept_search_suggestion(suggestionList.currentIndex)
        hideSuggestions()
        return true
    }

    DropShadow {
        anchors.fill: fieldBackground
        source: fieldBackground
        horizontalOffset: 0
        verticalOffset: 2
        radius: 9
        samples: 19
        color: "#38000000"
        transparentBorder: true
    }
    Rectangle {
        id: fieldBackground
        anchors.fill: parent
        radius: height / 2
        color: root.theme.dark ? "#646464" : "#ffffff"
        border.width: searchInput.activeFocus ? 1 : 0
        border.color: root.theme.action
        antialiasing: true
        Behavior on color { ColorAnimation { duration: 100 } }
    }
    MaterialIcon {
        anchors.left: parent.left
        anchors.leftMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        name: "search"
        size: 19
        color: root.theme.dark ? "#dedede" : root.theme.secondaryText
    }
    TextInput {
        id: searchInput
        anchors.left: parent.left
        anchors.leftMargin: 42
        anchors.right: clearButton.left
        anchors.rightMargin: 5
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        verticalAlignment: Text.AlignVCenter
        color: root.theme.dark ? "#ffffff" : root.theme.primaryText
        selectionColor: "#a9a9a9"
        selectedTextColor: "#ffffff"
        font.family: root.theme.fontFamily
        font.pixelSize: 13
        selectByMouse: true
        clip: true

        onTextEdited: {
            root.controller.update_search_text(text)
            suggestionTimer.restart()
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
                if (!root.acceptCurrentSuggestion()) {
                    root.controller.search(text)
                    root.hideSuggestions()
                }
                event.accepted = true
            }
        }
    }
    Label {
        anchors.fill: searchInput
        verticalAlignment: Text.AlignVCenter
        visible: searchInput.text.length === 0
        text: root.placeholderText
        color: root.theme.dark ? "#d0d0d0" : root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pixelSize: 13
    }
    CompactIconButton {
        id: clearButton
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.verticalCenter: parent.verticalCenter
        width: 28
        height: 28
        theme: root.theme
        iconName: "close"
        iconSize: 17
        toolTip: qsTr("Clear search")
        visible: searchInput.text.length > 0
        onClicked: {
            searchInput.clear()
            root.controller.update_search_text("")
            root.controller.clear_search_suggestions()
            searchInput.forceActiveFocus()
        }
    }

    HoverHandler {
        id: fieldHover
        objectName: "tacticSearchCursorHandler"
        cursorShape: Qt.IBeamCursor
    }
    Md3ToolTip {
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

    Md3Popup {
        id: suggestionsPopup
        theme: root.theme
        parent: Overlay.overlay
        padding: 4
        modal: false
        focus: false
        closePolicy: Popup.NoAutoClose
        height: Math.min(20, suggestionList.count) * 34 + topPadding + bottomPadding
        onOpened: root.positionPopup()

        property bool hovered: popupHover.hovered

        contentItem: ListView {
            id: suggestionList
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
            delegate: Item {
                id: suggestionRow
                required property int index
                required property string title
                required property string description
                required property string keyword
                required property string code
                required property bool selected
                property string suggestionTitle: title
                width: suggestionList.width
                height: 34

                function acceptSuggestion() {
                    suggestionTimer.stop()
                    searchInput.text = suggestionRow.title
                    root.controller.accept_search_suggestion(
                        suggestionRow.index)
                    root.hideSuggestions()
                    searchInput.forceActiveFocus()
                }

                Rectangle {
                    anchors.fill: parent
                    color: suggestionRow.index === suggestionList.currentIndex
                        ? root.theme.selected
                        : suggestionMouse.containsMouse
                            ? root.theme.rowHover
                            : suggestionRow.index % 2
                                ? root.theme.panelRaised : root.theme.row
                }
                RowLayout {
                    z: 2
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 10
                    spacing: 9
                    MaterialIcon {
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
                        font.pointSize: Typography.bodyLarge
                        elide: Text.ElideRight
                    }
                    Rectangle {
                        visible: suggestionRow.keyword.length > 0
                        Layout.preferredWidth: visible
                            ? keywordLabel.implicitWidth + 12 : 0
                        Layout.preferredHeight: 24
                        radius: 12
                        color: keywordMouse.containsMouse
                            ? root.theme.selected : "transparent"
                        Label {
                            id: keywordLabel
                            anchors.centerIn: parent
                            text: qsTr("#") + suggestionRow.keyword
                            color: root.theme.action
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        MouseArea {
                            id: keywordMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: suggestionRow.acceptSuggestion()
                        }
                    }
                }
                MouseArea {
                    id: suggestionMouse
                    z: 1
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: mouse => suggestionRipple.burst(mouse.x, mouse.y)
                    onEntered: {
                        suggestionList.currentIndex = suggestionRow.index
                        root.suggestionModel.select_row(suggestionRow.index)
                    }
                    onClicked: suggestionRow.acceptSuggestion()
                }
                MaterialRipple {
                    id: suggestionRipple
                    color: root.theme.ripple
                    shapeRadius: 6
                }
            }
            ScrollBar.vertical: Md3ScrollBar {
                theme: root.theme
                policy: suggestionList.count > 20
                    ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
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
            if (suggestionsPopup.visible)
                root.positionPopup()
        }
    }
    Component.onCompleted: searchInput.text = root.controller.current_search_text
}
