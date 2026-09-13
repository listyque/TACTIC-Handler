import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    objectName: "sobjectFieldFrame_" + fieldName

    required property var theme
    required property string title
    required property string fieldName
    required property string description
    required property string iconName
    required property string errorText
    required property bool requiredField
    required property bool readOnlyField
    default property alias editorData: editorHost.data
    readonly property bool compact: width < 700

    implicitHeight: surface.implicitHeight

    Rectangle {
        id: surface
        objectName: "sobjectFieldSurface_" + root.fieldName

        anchors.fill: parent
        implicitHeight: fieldLayout.implicitHeight + 28
        radius: root.theme.surfaceRadius
        color: root.theme.surfaceContainerLow
        border.width: 1
        border.color: root.errorText.length > 0
            ? root.theme.error : root.theme.outlineVariant

        GridLayout {
            id: fieldLayout

            anchors.fill: parent
            anchors.margins: 14
            columns: 2
            columnSpacing: 20
            rowSpacing: 12

            RowLayout {
                Layout.row: 0
                Layout.column: 0
                Layout.columnSpan: root.compact ? 2 : 1
                Layout.fillWidth: root.compact
                Layout.preferredWidth: root.compact ? -1 : 220
                Layout.minimumWidth: 0
                Layout.alignment: Qt.AlignTop
                spacing: 11

                Rectangle {
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 34
                    radius: root.theme.itemRadius
                    color: root.errorText.length > 0
                        ? root.theme.errorContainer
                        : root.theme.secondaryContainer

                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: root.iconName
                        size: 17
                        color: root.errorText.length > 0
                            ? root.theme.error
                            : root.theme.action
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Label {
                            Layout.fillWidth: true
                            text: root.title
                            color: root.errorText.length > 0
                                ? root.theme.error : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }

                        Label {
                            visible: root.requiredField
                            text: "*"
                            color: root.theme.error
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.Bold
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: root.description.length > 0
                            ? root.description : root.fieldName
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }

                    Label {
                        visible: root.readOnlyField
                        text: qsTr("Read only")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.DemiBold
                    }
                }
            }

            ColumnLayout {
                id: editorColumn

                Layout.row: root.compact ? 1 : 0
                Layout.column: root.compact ? 0 : 1
                Layout.columnSpan: root.compact ? 2 : 1
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.alignment: Qt.AlignTop
                spacing: 5

                Item {
                    id: editorHost
                    objectName: "sobjectFieldEditorHost_" + root.fieldName

                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(
                        root.theme.controlHeight,
                        childrenRect.height
                    )
                }

                Label {
                    Layout.fillWidth: true
                    visible: root.errorText.length > 0
                    text: root.errorText
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
