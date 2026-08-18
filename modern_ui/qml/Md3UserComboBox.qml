import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Md3ComboBox {
    id: control

    required property var userModel
    property string searchText: ""
    property string currentAvatarUrl: ""
    property string currentInitials: ""

    function profileFor(login) {
        if (!login || !control.userModel || !control.userModel.count)
            return ({})
        for (let index = 0; index < control.userModel.count(); ++index) {
            const profile = control.userModel.get(index)
            if (String(profile.login || "") === String(login))
                return profile
        }
        return ({})
    }

    function matches(index) {
        const query = control.searchText.trim().toLowerCase()
        if (!query)
            return true
        return String(control.optionValue(index, control.textRole))
                .toLowerCase().indexOf(query) >= 0
            || String(control.optionValue(index, control.valueRole))
                .toLowerCase().indexOf(query) >= 0
    }

    function groupHasMatches(group) {
        if (!control.userModel || !control.userModel.count)
            return false
        for (let index = 0; index < control.userModel.count(); ++index) {
            const user = control.userModel.get(index)
            if (String(user.primaryGroup || "") === String(group || "")
                    && control.matches(index))
                return true
        }
        return false
    }

    contentItem: RowLayout {
        spacing: 7
        ItemPreview {
            readonly property var profile:
                control.currentAvatarUrl.length || control.currentInitials.length
                    ? ({
                        "avatarUrl": control.currentAvatarUrl,
                        "initials": control.currentInitials
                    })
                    : control.profileFor(control.currentValue)
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            theme: control.theme
            source: profile.avatarUrl || ""
            fallbackIcon: "person"
            fallbackText: profile.initials || ""
            previewSize: 22
            round: true
            outlined: true
            animateAppearance: false
        }
        Label {
            Layout.fillWidth: true
            text: control.displayText || qsTr("Select user")
            color: control.enabled
                ? control.theme.primaryText : control.theme.disabledText
            font: control.font
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    delegate: ItemDelegate {
        id: option
        required property int index
        readonly property bool matchesSearch: control.matches(option.index)
        readonly property string login: String(
            control.optionValue(option.index, control.valueRole)
        )
        readonly property var profile: control.profileFor(option.login)

        width: control.popup.width - 10
        height: matchesSearch ? 48 : 0
        visible: matchesSearch
        leftPadding: 8
        rightPadding: 9
        highlighted: control.highlightedIndex === option.index

        contentItem: RowLayout {
            spacing: 9
            ItemPreview {
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                theme: control.theme
                source: option.profile.avatarUrl || ""
                fallbackIcon: "person"
                fallbackText: option.profile.initials || ""
                previewSize: 32
                round: true
                outlined: true
                animateAppearance: false
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Label {
                    Layout.fillWidth: true
                    text: control.textAt(option.index)
                    color: control.theme.primaryText
                    font.family: control.theme.fontFamily
                    font.pointSize: Typography.body
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    visible: option.login.length > 0
                    text: option.login
                    color: control.theme.secondaryText
                    font.family: control.theme.fontFamily
                    font.pointSize: Typography.caption
                    elide: Text.ElideRight
                }
            }
            MaterialIcon {
                visible: option.index === control.currentIndex
                name: "check-circle"
                size: 16
                color: control.theme.action
            }
        }
        background: Rectangle {
            radius: control.theme.itemRadius
            color: option.highlighted
                ? control.theme.secondaryContainer : "transparent"
        }
    }

    popup: Md3Popup {
        id: userPopup
        theme: control.theme
        y: control.height + 4
        width: Math.max(control.width, 250)
        implicitHeight: 286
        padding: 6
        onOpened: {
            control.searchText = ""
            searchField.forceActiveFocus()
        }

        contentItem: ColumnLayout {
            spacing: 6
            Md3TextField {
                id: searchField
                Layout.fillWidth: true
                theme: control.theme
                placeholderText: qsTr("Search users")
                onTextChanged: control.searchText = text
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                currentIndex: control.highlightedIndex
                model: control.delegateModel
                section.property: "primaryGroup"
                section.criteria: ViewSection.FullString
                section.delegate: UserGroupSection {
                    required property string section
                    width: ListView.view.width
                    theme: control.theme
                    title: section
                    compact: true
                    shown: control.groupHasMatches(section)
                }
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: Md3ScrollBar {
                    theme: control.theme
                    flickableTarget: parent
                }
            }
        }
    }
}
