import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Rectangle {
    id: root
    objectName: "projectCard"

    required property var theme
    property var details: ({})
    property bool compact: false
    property bool selected: false
    property bool interactive: true
    signal clicked()
    signal doubleClicked()

    readonly property string lifecycleText: details.isBuiltin
        ? qsTr("BUILT-IN")
        : details.isTemplate
            ? qsTr("TEMPLATE")
            : details.isRetired
                ? qsTr("ARCHIVED")
                : qsTr("ACTIVE")
    readonly property color lifecycleColor: details.isRetired
        ? theme.yellow
        : details.isBuiltin
            ? theme.secondaryText
            : theme.action

    implicitHeight: compact ? 116 : 258
    radius: theme.sectionRadius
    color: cardMouse.pressed
        ? theme.selected
        : cardMouse.containsMouse && interactive
            ? theme.rowHover
            : theme.surfaceContainerHigh
    border.width: 1
    border.color: selected ? theme.action : theme.outlineVariant
    antialiasing: true

    Behavior on color {
        ColorAnimation {
            duration: root.selected
                ? root.theme.clickMotionFast : root.theme.hoverMotionFast
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 12
        visible: root.compact

        Controls.ItemPreview {
            Layout.preferredWidth: 96
            objectName: "projectCompactPreview"
            Layout.fillHeight: true
            theme: root.theme
            previewSize: 96
            cornerRadius: root.theme.itemRadius
            outlined: true
            accent: root.theme.toolBar
            source: root.details.preview || ""
            fallbackText: root.details.initials || ""
            decodeAtItemSize: true
            Layout.minimumWidth: 0
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.fillHeight: true
            spacing: 3

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Label {
                    Layout.fillWidth: true
                    text: root.details.title || root.details.code || ""
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Controls.StatusChip {
                    theme: root.theme
                    text: root.lifecycleText
                    accentColor: root.lifecycleColor
                }
            }

            Label {
                Layout.fillWidth: true
                text: [
                    root.details.code || "",
                    root.details.category || "",
                    root.details.projectType || ""
                ].filter(value => value.length > 0).join(" · ")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.label
                elide: Text.ElideRight
            }

            Label {
                Layout.fillWidth: true
                Layout.fillHeight: true
                text: root.details.description
                    || qsTr("No project description")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.label
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }

            Label {
                Layout.fillWidth: true
                visible: !!root.details.status
                text: qsTr("Status") + ": " + root.details.status
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
                elide: Text.ElideRight
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 9
        spacing: 7
        visible: !root.compact

        Controls.ItemPreview {
            Layout.preferredWidth: 120
            objectName: "projectGridPreview"
            Layout.preferredHeight: 120
            Layout.alignment: Qt.AlignHCenter
            theme: root.theme
            previewSize: 120
            cornerRadius: root.theme.itemRadius
            outlined: true
            accent: root.theme.toolBar
            source: root.details.preview || ""
            fallbackText: root.details.initials || ""
            decodeAtItemSize: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Label {
                Layout.fillWidth: true
                text: root.details.title || root.details.code || ""
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Controls.StatusChip {
                theme: root.theme
                text: root.lifecycleText
                accentColor: root.lifecycleColor
            }
        }

        Label {
            Layout.fillWidth: true
            text: root.details.description || qsTr("No project description")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Typography.label
            maximumLineCount: 2
            wrapMode: Text.Wrap
            elide: Text.ElideRight
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 8
            rowSpacing: 2

            Label {
                text: qsTr("Category")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
            }
            Label {
                Layout.fillWidth: true
                text: root.details.category || qsTr("Not set")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
                elide: Text.ElideRight
            }
            Label {
                text: qsTr("Type")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
            }
            Label {
                Layout.fillWidth: true
                text: root.details.projectType || qsTr("Not set")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
                elide: Text.ElideRight
            }
        }
    }

    Controls.MaterialRipple {
        id: ripple
        theme: root.theme
        anchors.fill: parent
        shapeRadius: root.radius
        color: root.theme.rippleStrong
        enabled: root.interactive
    }

    MouseArea {
        id: cardMouse
        anchors.fill: parent
        enabled: root.interactive
        hoverEnabled: true
        cursorShape: root.interactive ? Qt.PointingHandCursor : Qt.ArrowCursor
        onPressed: mouse => ripple.burst(mouse.x, mouse.y)
        onClicked: root.clicked()
        onDoubleClicked: root.doubleClicked()
    }
}
