import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import QtQuick.Layouts
import "controls" as Controls
import "UserSearch.js" as UserSearch

Controls.ComboBox {
    id: control

    required property var userModel
    property string searchText: ""
    property string currentAvatarUrl: ""
    property string currentInitials: ""
    property string currentAvatarColor: ""

    Connections {
        target: control.userModel
        function onContentReplaced() {
            if (userPopup.opened)
                control.rebuildPopupOptions()
        }
    }

    ListModel {
        id: popupUsers
        objectName: "userComboBoxPopupModel"
    }

    function modelRecord(modelObject, index) {
        if (!modelObject || index < 0)
            return ({})
        if (typeof modelObject.get === "function")
            return modelObject.get(index) || ({})
        return modelObject[index] || ({})
    }

    function profileFor(login) {
        const wantedLogin = String(login || "")
        if (!wantedLogin || !control.userModel)
            return ({})
        return control.userModel.lookup("login", wantedLogin)
    }

    function initialsFor(label) {
        const parts = String(label || "").trim().split(/\s+/)
        if (!parts.length || !parts[0])
            return ""
        return (parts[0].charAt(0)
            + (parts.length > 1 ? parts[parts.length - 1].charAt(0) : ""))
            .toUpperCase()
    }

    function popupIndexForSource(sourceIndex) {
        for (let index = 0; index < popupUsers.count; ++index) {
            if (Number(popupUsers.get(index).sourceIndex) === sourceIndex)
                return index
        }
        return popupUsers.count > 0 ? 0 : -1
    }

    function rebuildPopupOptions() {
        const query = control.searchText.trim().toLowerCase()
        const options = []
        const seen = ({})
        for (let index = 0; index < control.count; ++index) {
            const choice = control.modelRecord(control.model, index)
            const login = String(
                control.optionValue(index, control.valueRole) || "")
            const label = String(
                control.textAt(index) || (login ? login : qsTr("Not assigned"))
            )
            const profile = control.profileFor(login)
            if (!UserSearch.matches(login, label + " " + String(profile.email || ""),
                                    profile.groups, query))
                continue
            const identity = "login:" + login
            if (seen[identity])
                continue
            seen[identity] = true
            options.push({
                "sourceIndex": index,
                "label": label,
                "login": login,
                "avatarUrl": String(
                    choice.avatarUrl || profile.avatarUrl || ""),
                "initials": String(
                    profile.initials || control.initialsFor(label)),
                "avatarColor": String(
                    choice.avatarColor || profile.avatarColor || ""),
                "primaryGroup": String(
                    profile.primaryGroup || "Ungrouped")
            })
        }
        options.sort(function(left, right) {
            const leftEmpty = !left.login
            const rightEmpty = !right.login
            if (leftEmpty !== rightEmpty)
                return leftEmpty ? -1 : 1
            const groupOrder = left.primaryGroup.toLowerCase().localeCompare(
                right.primaryGroup.toLowerCase())
            if (groupOrder)
                return groupOrder
            return left.label.toLowerCase().localeCompare(
                right.label.toLowerCase())
        })
        popupUsers.clear()
        for (let index = 0; index < options.length; ++index)
            popupUsers.append(options[index])
        userList.currentIndex = control.popupIndexForSource(
            control.currentIndex)
        if (userList.currentIndex >= 0)
            userList.positionViewAtIndex(
                userList.currentIndex, ListView.Contain)
    }

    function activatePopupRow(popupIndex) {
        if (popupIndex < 0 || popupIndex >= popupUsers.count)
            return
        const sourceIndex = Number(
            popupUsers.get(popupIndex).sourceIndex)
        control.cancelOpeningTransaction()
        control.currentIndex = sourceIndex
        control.activated(sourceIndex)
        control._restoreFocusAfterClose = true
        userPopup.close()
    }

    function movePopupHighlight(step) {
        if (popupUsers.count <= 0)
            return
        const current = userList.currentIndex >= 0
            ? userList.currentIndex : 0
        userList.currentIndex = (
            current + step + popupUsers.count
        ) % popupUsers.count
        userList.positionViewAtIndex(
            userList.currentIndex, ListView.Contain)
    }

    function activatePopupHighlight() {
        control.activatePopupRow(userList.currentIndex)
        control.forceActiveFocus(Qt.PopupFocusReason)
    }

    onSearchTextChanged: {
        if (userPopup.opened)
            control.rebuildPopupOptions()
    }
    onActivationPressedChanged: {
        if (control.activationPressed && !userPopup.opened)
            control.rebuildPopupOptions()
    }
    onCountChanged: {
        if (userPopup.opened)
            control.rebuildPopupOptions()
    }

    contentItem: RowLayout {
        spacing: 7
        UserAvatar {
            objectName: "userComboBoxCurrentAvatar"
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            theme: control.theme
            userModel: control.userModel
            login: String(control.currentValue || "")
            avatarUrl: control.currentAvatarUrl
            initials: control.currentInitials
            avatarColor: control.currentAvatarColor
            previewSize: 22
        }
        Label {
            objectName: "userComboBoxDisplayLabel"
            Layout.fillWidth: true
            text: control.displayText || qsTr("Select user")
            color: control.enabled
                ? control.theme.primaryText : control.theme.disabledText
            font: control.font
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }



    popup: Controls.Popup {
        id: userPopup
        objectName: "userComboBoxPopup"
        theme: control.theme
        usePopupWindow: true
        coordinateGlobally: true
        coordinateOpenPopups: true
        openingAnchorItem: control
        restoreOwnerActivationOnClose: false
        function cancelOpeningRecovery() {
            control.cancelOpeningTransaction()
        }
        settledClosePolicy: QtControls.Popup.CloseOnEscape
            | QtControls.Popup.CloseOnPressOutside
        y: control.height + 4
        width: Math.min(
            Math.max(control.width, 250, control.preferredPopupWidth + 44),
            control.maximumPopupWidth,
            userPopup.maximumAvailableWidth
        )
        implicitHeight: 286
        padding: 6
        onAboutToShow: {
            userPopup.preparePositionAtItem(
                control, 0, control.height + 4)
            searchField.text = ""
            control.searchText = ""
            control.rebuildPopupOptions()
        }
        onOpened: {
            Qt.callLater(function() {
                searchField.forceActiveFocus()
            })
        }
        onClosed: {
            control.handlePopupClosed()
        }
        Shortcut {
            sequence: "Down"
            context: Qt.WindowShortcut
            enabled: userPopup.visible
            onActivated: {
                if (searchField.activeFocus) {
                    userList.currentIndex = Math.max(
                        0, userList.currentIndex)
                    userList.forceActiveFocus(Qt.TabFocusReason)
                } else {
                    control.movePopupHighlight(1)
                }
            }
        }
        Shortcut {
            sequence: "Up"
            context: Qt.WindowShortcut
            enabled: userPopup.visible && userList.activeFocus
            onActivated: control.movePopupHighlight(-1)
        }
        Shortcut {
            sequence: "Space"
            context: Qt.WindowShortcut
            enabled: userPopup.visible && userList.activeFocus
            onActivated: control.activatePopupHighlight()
        }
        Shortcut {
            sequence: "Return"
            context: Qt.WindowShortcut
            enabled: userPopup.visible && userList.activeFocus
            onActivated: control.activatePopupHighlight()
        }
        Shortcut {
            sequence: "Enter"
            context: Qt.WindowShortcut
            enabled: userPopup.visible && userList.activeFocus
            onActivated: control.activatePopupHighlight()
        }
        Shortcut {
            sequence: "Esc"
            context: Qt.WindowShortcut
            enabled: userPopup.visible
            onActivated: {
                control._restoreFocusAfterClose = true
                userPopup.close()
            }
        }
        contentItem: ColumnLayout {
            spacing: 6
            Controls.SearchField {
                id: searchField
                objectName: "userComboBoxSearchField"
                Layout.fillWidth: true
                theme: control.theme
                placeholderText: qsTr("Search users")
                onTextChanged: control.searchText = text
                Keys.priority: Keys.BeforeItem
                Keys.onDownPressed: {
                    if (popupUsers.count <= 0)
                        return
                    userList.currentIndex = Math.max(
                        0, userList.currentIndex)
                    userList.forceActiveFocus()
                }
                Keys.onReturnPressed: {
                    if (popupUsers.count > 0)
                        control.activatePopupRow(
                            Math.max(0, userList.currentIndex))
                }
                Keys.onEnterPressed: {
                    if (popupUsers.count > 0)
                        control.activatePopupRow(
                            Math.max(0, userList.currentIndex))
                }
                Keys.onEscapePressed: userPopup.close()
            }
            ListView {
                id: userList
                objectName: "userComboBoxPopupList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: popupUsers
                reuseItems: true
                keyNavigationWraps: true
                Keys.priority: Keys.BeforeItem
                section.property: "primaryGroup"
                section.criteria: ViewSection.FullString
                section.delegate: UserGroupSection {
                    required property string section
                    width: ListView.view.width
                    theme: control.theme
                    title: section
                    compact: true
                }
                delegate: ItemDelegate {
                    id: option
                    objectName: "userComboBoxOption_" + option.login
                    required property int index
                    required property int sourceIndex
                    required property string label
                    required property string login
                    required property string avatarUrl
                    required property string initials
                    required property string avatarColor

                    width: userList.width
                    height: 48
                    leftPadding: 8
                    rightPadding: 9
                    hoverEnabled: true
                    highlighted: ListView.isCurrentItem || hovered
                    onHoveredChanged: {
                        if (hovered)
                            userList.currentIndex = option.index
                    }
                    onClicked: control.activatePopupRow(option.index)

                    contentItem: RowLayout {
                        spacing: 9
                        Controls.ItemPreview {
                            objectName: "userComboBoxAvatar_" + option.login
                            Layout.preferredWidth: 32
                            Layout.preferredHeight: 32
                            theme: control.theme
                            source: option.avatarUrl
                            fallbackIcon: "person"
                            fallbackText: option.initials
                            previewSize: 32
                            round: true
                            outlined: true
                            animateAppearance: false
                            accent: option.avatarColor.length
                                ? option.avatarColor : control.theme.action
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Label {
                                Layout.fillWidth: true
                                text: option.label
                                color: control.theme.primaryText
                                font.family: control.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: option.login.length > 0
                                text: option.login
                                color: control.theme.secondaryText
                                font.family: control.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                        Controls.MaterialIcon {
                            visible: option.sourceIndex
                                === control.currentIndex
                            name: "check-circle"
                            size: 16
                            color: control.theme.action
                        }
                    }
                    background: Rectangle {
                        radius: control.theme.itemRadius
                        color: option.highlighted
                            ? control.theme.secondaryContainer
                            : "transparent"
                    }
                }
                Keys.onReturnPressed:
                    control.activatePopupRow(currentIndex)
                Keys.onEnterPressed:
                    control.activatePopupRow(currentIndex)
                Keys.onSpacePressed:
                    control.activatePopupRow(currentIndex)
                Keys.onEscapePressed: userPopup.close()
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: Controls.ScrollBar {
                    objectName: "userComboBoxScrollBar"
                    theme: control.theme
                    flickableTarget: userList
                }
            }
        }
    }
}
