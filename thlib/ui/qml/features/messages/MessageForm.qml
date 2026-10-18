import QtQuick
import "../.." as Messages
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/messages/forms.ui.mjs" as UI

Frame.FrameView {
    id: root
    property string mode: "create"
    property string text: ""
    property var selectedLogins: []
    property var peopleItem: null
    property bool busy: false
    property bool valid: true
    property bool canCreateGroup: true
    property bool activeSearch: false
    property real availableBodyHeight: 500
    property real descriptionHeight: 72
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    signal submitted
    signal cancelled
    signal searchCleared
    signal selectionChanged(var logins)
    implicitWidth: 408
    implicitHeight: UI.form(presentation, implicitWidth, availableBodyHeight, language, {
        description: descriptionHeight
    }).height
    readonly property var presentation: ({
            mode,
            text,
            count: selectedLogins.length,
            busy,
            valid,
            canCreateGroup,
            activeSearch
        })
    scene: UI.form(presentation, width, availableBodyHeight, language, {
        description: descriptionHeight
    })
    views: ({
            people: peoplePort,
            description: descriptionPort
        })
    function reset() {
        text = "";
        if (peopleItem)
            peopleItem.reset();
    }
    function clear() {
        text = "";
    }
    function setSelection(logins) {
        if (peopleItem)
            peopleItem.setSelection(logins);
    }
    function focusEditor() {
        focusControl(mode === "edit" ? "messageEditBody" : mode === "rename" ? "messageChatTitle" : mode === "search" ? "messageSearchField" : "messageGroupTitle");
    }
    onEvent: action => {
        if (action.type === "text")
            text = action.value;
        else if (action.type === "cancel")
            cancelled();
        else if (action.type === "clear-search")
            searchCleared();
        else if (action.type === "submit" && valid && !busy)
            submitted();
    }
    Component {
        id: peoplePort
        Messages.UserPicker {
            id: picker
            theme: root.theme
            selectedLogins: root.selectedLogins
            enabled: !root.busy
            onSelectionChanged: logins => root.selectionChanged(logins)
            Component.onCompleted: root.peopleItem = picker
            Component.onDestruction: if (root.peopleItem === picker)
                root.peopleItem = null
        }
    }
    Component {
        id: descriptionPort
        Text {
            id: description
            text: UI.description(root.mode, root.language)
            color: root.theme.primaryText
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 13
            })
            wrapMode: Text.Wrap
            function measure() {
                Qt.callLater(function () {
                    root.descriptionHeight = description.contentHeight;
                });
            }
            onWidthChanged: measure()
            onContentHeightChanged: measure()
            Component.onCompleted: measure()
        }
    }
}
