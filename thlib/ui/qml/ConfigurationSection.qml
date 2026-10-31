import "tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

Rectangle {
    id: root

    required property var theme
    property string title: ""
    property string description: ""
    property string iconName: "settings"
    property bool fillContentHeight: false
    default property alias contentData: sectionContent.data

    implicitHeight: sectionLayout.implicitHeight
    color: "transparent"

    ColumnLayout {
        id: sectionLayout
        anchors.fill: parent
        spacing: root.theme.spacing.compact

        Label {
            Layout.fillWidth: true
            Layout.leftMargin: 0
            text: root.title
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: 14
            font.weight: Font.DemiBold
        }

        Label {
            visible: root.description.length > 0
            Layout.fillWidth: true
            Layout.leftMargin: 0
            Layout.rightMargin: 0
            text: root.description
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: Foundation.textStyles.caption
            wrapMode: Text.WordWrap
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.fillHeight: root.fillContentHeight
            implicitHeight: sectionContent.implicitHeight + root.theme.spacing.content * 2
            radius: root.theme.sectionRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            ColumnLayout {
                id: sectionContent
                anchors.fill: parent
                anchors.margins: root.theme.spacing.content
                spacing: 0
            }
        }
    }
}
