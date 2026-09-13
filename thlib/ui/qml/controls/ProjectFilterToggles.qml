import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

ColumnLayout {
    id: root

    objectName: "projectFilterToggles"
    required property var theme
    required property var model
    property bool showSummary: false
    spacing: 3

    Flow {
        Layout.fillWidth: true
        Layout.preferredHeight: implicitHeight
        spacing: 12

        Controls.CheckBox {
            objectName: "projectFilterRetiredToggle"
            theme: root.theme
            compact: true
            text: qsTr("Retired") + " · " + root.model.retiredCount
            checked: root.model.showRetired
            onToggled: root.model.setShowRetired(checked)
        }

        Controls.CheckBox {
            objectName: "projectFilterTemplatesToggle"
            theme: root.theme
            compact: true
            text: qsTr("Templates") + " · " + root.model.templateCount
            checked: root.model.showTemplates
            onToggled: root.model.setShowTemplates(checked)
        }

        Controls.CheckBox {
            objectName: "projectFilterBuiltinsToggle"
            theme: root.theme
            compact: true
            text: qsTr("Built-in") + " · " + root.model.builtinCount
            checked: root.model.showBuiltins
            onToggled: root.model.setShowBuiltins(checked)
        }
    }

    Label {
        visible: root.showSummary
        text: qsTr("%1 of %2 projects shown")
            .arg(root.model.visibleCount).arg(root.model.totalCount)
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Typography.label
        elide: Text.ElideRight
        Layout.fillWidth: true
    }
}
