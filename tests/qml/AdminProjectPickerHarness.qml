import QtQuick
import QtQuick.Controls
import "../../thlib/ui/qml" as TH
import "../../thlib/ui/qml/features/administration" as Admin

ApplicationWindow {
    id: root
    visible: true
    width: 1100
    height: 760
    required property var data
    property string language: "en"
    property alias dark: theme.dark
    color: theme.workspace
    TH.Theme {
        id: theme
        dark: true
        popupAnimationsEnabled: false
        clickAnimationsEnabled: false
        hoverAnimationsEnabled: false
    }
    Admin.AdminProjectPicker {
        x: 20
        y: 100
        width: 226
        height: 38
        theme: theme
        model: root.data
        language: root.language
        onSelected: code => root.data = Object.assign({}, root.data, {
                project: code
            })
    }
}
