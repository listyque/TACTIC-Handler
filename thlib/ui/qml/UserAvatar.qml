import QtQuick
import "controls" as Controls

Controls.ItemPreview {
    id: root

    required property var userModel
    property string login: ""
    property string avatarUrl: ""
    property string initials: ""
    property string avatarColor: ""
    property int profileRevision: 0
    readonly property var profile: {
        const revision = root.profileRevision
        return root.login && root.userModel
            ? root.userModel.lookup("login", root.login) : ({})
    }

    source: root.avatarUrl || root.profile.avatarUrl || ""
    fallbackIcon: "person"
    fallbackText: root.initials || root.profile.initials || ""
    accent: root.avatarColor || root.profile.avatarColor || root.theme.action
    round: true
    outlined: true
    animateAppearance: false

    Connections {
        target: root.userModel
        function onContentReplaced() { root.profileRevision++ }
    }
}
