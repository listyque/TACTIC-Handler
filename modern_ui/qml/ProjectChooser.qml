import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// QML counterpart of Ui_projectsChooserWidget + Ui_projectItemWidget:
// categorized, three-column project cards with Ui_projectLinkWidget previews.
Md3Popup {
    id: root
    required property var model
    surfaceRadius: theme.dialogRadius
    property double lastClosedAt: 0
    property bool sourceWasOpen: false
    signal projectSelected(string code)

    parent: Overlay.overlay
    x: Math.round((parent.width - width) / 2)
    y: Math.round((parent.height - height) / 2)
    width: Math.max(520, Math.min(800, parent.width - 40))
    height: Math.max(400, Math.min(680, parent.height - 72))
    modal: false
    dim: true
    focus: true
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnReleaseOutside
    onClosed: lastClosedAt = Date.now()

    function toggle() {
        if (root.sourceWasOpen || root.opened) {
            root.close()
        } else {
            root.open()
        }
        root.sourceWasOpen = false
    }

    Overlay.modeless: Rectangle {
        color: root.theme.scrim
        Behavior on opacity {
            NumberAnimation { duration: root.theme.motionMedium }
        }
    }
    enter: Transition {
        NumberAnimation {
            property: "opacity"; from: 0; to: 1
            duration: root.theme.motionMedium
        }
        NumberAnimation {
            property: "scale"; from: 0.97; to: 1
            duration: root.theme.motionSlow
            easing.type: Easing.OutCubic
        }
    }
    exit: Transition {
        NumberAnimation {
            property: "opacity"; from: 1; to: 0
            duration: root.theme.motionFast
        }
        NumberAnimation {
            property: "scale"; from: 1; to: 0.985
            duration: root.theme.motionFast
        }
    }
    contentItem: ColumnLayout {
        spacing: 0
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 82
            ColumnLayout {
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: filtersRow.left
                anchors.rightMargin: 16
                spacing: 1
                Label {
                    text: qsTr("Projects")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }
                Label {
                    text: root.model.visibleCount + qsTr(" shown  ·  ")
                        + root.model.totalCount + qsTr(" total  ·  ")
                        + root.model.retiredCount + qsTr(" retired  ·  ")
                        + root.model.templateCount + qsTr(" templates")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                }
            }
            Row {
                id: filtersRow
                anchors.right: closeButton.left
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4
                Md3CheckBox {
                    id: retiredCheck
                    theme: root.theme
                    text: qsTr("Show retired")
                    checked: root.model.showRetired
                    onToggled: root.model.setShowRetired(checked)
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                }
                Md3CheckBox {
                    id: templatesCheck
                    theme: root.theme
                    text: qsTr("Show templates")
                    checked: root.model.showTemplates
                    onToggled: root.model.setShowTemplates(checked)
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                }
            }
            CompactIconButton {
                id: closeButton
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.top: parent.top
                anchors.topMargin: 8
                width: 44
                height: 44
                theme: root.theme
                iconName: "close"
                iconSize: 20
                iconColor: root.theme.primaryText
                round: true
                toolTip: qsTr("Close")
                onClicked: root.close()
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.separator
        }
        ListView {
            id: categories
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 12
            Layout.rightMargin: 12
            Layout.bottomMargin: 12
            clip: true
            spacing: 4
            model: root.model.groups
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

            delegate: Item {
                id: categoryDelegate
                required property var modelData
                width: categories.width
                height: categoryColumn.implicitHeight

                Column {
                    id: categoryColumn
                    width: parent.width
                    spacing: 6
                    Item {
                        width: parent.width
                        height: 42
                        Label {
                            anchors.left: parent.left
                            anchors.leftMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            text: (categoryDelegate.modelData.title
                                || qsTr("No Category"))
                                + "  ·  " + categoryDelegate.modelData.projects.length
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }
                    }
                    Flow {
                        width: parent.width
                        spacing: 8
                        Repeater {
                            model: categoryDelegate.modelData.projects
                            delegate: Item {
                                id: projectCard
                                required property var modelData
                                width: Math.floor((categoryColumn.width - 16) / 3)
                                height: 154

                                Rectangle {
                                    id: cardSurface
                                    anchors.fill: parent
                                    radius: 14
                                    color: cardMouse.pressed ? root.theme.selected
                                        : cardMouse.containsMouse ? root.theme.rowHover : root.theme.panel
                                    border.width: 1
                                    border.color: root.theme.outline
                                    Behavior on color { ColorAnimation { duration: 100 } }
                                    MaterialRipple {
                                        id: cardRipple
                                        shapeRadius: cardSurface.radius
                                        color: root.theme.dark ? "#36ffffff" : "#23000000"
                                    }
                                }
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 6
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 72
                                        spacing: 10
                                        ItemPreview {
                                            Layout.preferredWidth: 72
                                            Layout.preferredHeight: 72
                                            theme: root.theme
                                            previewSize: 72
                                            cornerRadius: 10
                                            outlined: true
                                            accent: root.theme.toolBar
                                            source: projectCard.modelData.preview || ""
                                            fallbackText: projectCard.modelData.initials
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            spacing: 2
                                            Label {
                                                Layout.fillWidth: true
                                                text: projectCard.modelData.title
                                                color: root.theme.primaryText
                                                font.family: root.theme.fontFamily
                                                font.pixelSize: 12
                                                font.weight: Font.DemiBold
                                                wrapMode: Text.Wrap
                                                maximumLineCount: 2
                                                elide: Text.ElideRight
                                            }
                                            Label {
                                                Layout.fillWidth: true
                                                text: projectCard.modelData.code
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Typography.body
                                                elide: Text.ElideRight
                                            }
                                            Label {
                                                Layout.fillWidth: true
                                                text: projectCard.modelData.description
                                                    || projectCard.modelData.projectType
                                                    || categoryDelegate.modelData.title
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pointSize: Typography.label
                                                wrapMode: Text.Wrap
                                                maximumLineCount: 2
                                                elide: Text.ElideRight
                                            }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 5
                                        Label {
                                            text: projectCard.modelData.isTemplate
                                                ? qsTr("TEMPLATE")
                                                : projectCard.modelData.isRetired
                                                    ? qsTr("RETIRED")
                                                    : qsTr("ACTIVE")
                                            color: projectCard.modelData.isRetired
                                                ? root.theme.yellow : root.theme.action
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.label
                                            font.weight: Font.DemiBold
                                        }
                                        Item { Layout.fillWidth: true }
                                        Label {
                                            visible: !!projectCard.modelData.projectType
                                            text: projectCard.modelData.projectType
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.label
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 10
                                        Label {
                                            visible: !!(projectCard.modelData.created || projectCard.modelData.updated)
                                            text: qsTr("Created: ") + String(
                                                projectCard.modelData.created
                                                || projectCard.modelData.updated
                                            ).slice(0, 10)
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.label
                                        }
                                        Label {
                                            visible: projectCard.modelData.userCount > 0
                                            text: projectCard.modelData.userCount
                                                + qsTr(" users")
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.label
                                        }
                                        Label {
                                            visible: !!projectCard.modelData.lead
                                            Layout.fillWidth: true
                                            text: qsTr("Lead: ") + projectCard.modelData.lead
                                            horizontalAlignment: Text.AlignRight
                                            elide: Text.ElideRight
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.label
                                        }
                                    }
                                }
                                MouseArea {
                                    id: cardMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onPressed: mouse => cardRipple.burst(mouse.x, mouse.y)
                                    onClicked: {
                                        root.projectSelected(projectCard.modelData.code)
                                        root.close()
                                    }
                                }
                            }
                        }
                    }
                }
            }
            Label {
                anchors.centerIn: parent
                visible: categories.count === 0
                text: qsTr("No projects match the current filters")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
            }
        }
    }
}
