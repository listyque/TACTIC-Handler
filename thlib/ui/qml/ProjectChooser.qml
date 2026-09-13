import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

// QML counterpart of Ui_projectsChooserWidget + Ui_projectItemWidget:
// categorized, three-column project cards with Ui_projectLinkWidget previews.
Controls.Popup {
    id: root
    required property var model
    objectName: "projectChooser"
    surfaceRadius: theme.dialogRadius
    property double lastClosedAt: 0
    signal projectSelected(string code)

    parent: Overlay.overlay
    width: Math.max(520, Math.min(800, parent.width - 40))
    height: Math.max(400, Math.min(680, parent.height - 72))
    modal: false
    dim: true
    focus: true
    padding: 0
    settledClosePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    onClosed: lastClosedAt = Date.now()

    function toggle(sourceItem) {
        root.protectOpeningFrom(sourceItem)
        if (root.openingInputGuardActive) {
            root.sourceWasOpen = false
            return
        }
        if (root.sourceWasOpen || root.opened) {
            root.close()
        } else {
            root.openCenteredIn(root.parent)
        }
        root.sourceWasOpen = false
    }

    enter: Transition {
        enabled: root.animationsEnabled
        NumberAnimation {
            property: "opacity"; from: 0; to: 1
            duration: root.theme.popupMotionMedium
        }
        NumberAnimation {
            property: "scale"; from: 0.97; to: 1
            duration: root.theme.popupMotionSlow
            easing.type: Easing.OutCubic
        }
    }
    exit: Transition {
        enabled: root.animationsEnabled
        NumberAnimation {
            property: "opacity"; from: 1; to: 0
            duration: root.theme.popupMotionFast
        }
        NumberAnimation {
            property: "scale"; from: 1; to: 0.985
            duration: root.theme.popupMotionFast
        }
    }
    contentItem: ColumnLayout {
        spacing: 0
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 132
            ColumnLayout {
                objectName: "projectChooserTitle"
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.top: parent.top
                anchors.topMargin: 14
                anchors.right: closeButton.left
                anchors.rightMargin: 10
                spacing: 1
                Label {
                    text: qsTr("Projects")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }
                Label {
                    text: qsTr("%1 of %2 projects shown")
                        .arg(root.model.visibleCount).arg(root.model.totalCount)
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                }
            }
            Controls.ProjectFilterToggles {
                id: filtersRow
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 8
                theme: root.theme
                model: root.model
            }
            Controls.CompactIconButton {
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
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

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
                            delegate: Controls.ProjectCard {
                                id: projectCard
                                required property var modelData
                                width: Math.floor((categoryColumn.width - 16) / 3)
                                details: modelData
                                theme: root.theme
                                compact: false
                                onClicked: {
                                    root.projectSelected(modelData.code)
                                    root.close()
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
